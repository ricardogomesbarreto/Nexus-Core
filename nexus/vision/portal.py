"""One-shot desktop screenshot through the user's XDG portal chooser."""

import asyncio
from pathlib import Path
from urllib.parse import unquote, urlsplit


class PortalError(RuntimeError):
    pass


async def _choose(target: int) -> Path:
    from dbus_next import Message, MessageType, Variant
    from dbus_next.aio import MessageBus

    destination = "org.freedesktop.portal.Desktop"
    path = "/org/freedesktop/portal/desktop"
    bus = await MessageBus().connect()
    try:
        # A compositor advertises its supported targets. Never capture the
        # entire display when the caller asked for a selected window.
        properties = await bus.call(Message(
            destination=destination, path=path,
            interface="org.freedesktop.DBus.Properties", member="Get",
            signature="ss", body=["org.freedesktop.portal.Screenshot", "AvailableTargets"],
        ))
        if properties.message_type == MessageType.ERROR or not properties.body:
            raise PortalError("Portal de captura não oferece seleção de janelas/telas.")
        if not properties.body[0].value & target:
            raise PortalError("Este ambiente não oferece esse tipo de captura pelo portal.")

        import secrets
        token = "nexus_" + secrets.token_hex(12)
        sender = bus.unique_name.lstrip(":").replace(".", "_")
        request_path = f"{path}/request/{sender}/{token}"
        loop = asyncio.get_running_loop()
        result = loop.create_future()

        def response(message):
            if (message.message_type == MessageType.SIGNAL and
                    message.path == request_path and
                    message.interface == "org.freedesktop.portal.Request" and
                    message.member == "Response" and not result.done()):
                result.set_result(message.body)

        bus.add_message_handler(response)
        # Subscribe before calling Screenshot to avoid missing a fast response.
        match = ("type='signal',interface='org.freedesktop.portal.Request',"
                 f"member='Response',path='{request_path}'")
        await bus.call(Message(destination="org.freedesktop.DBus",
                               path="/org/freedesktop/DBus",
                               interface="org.freedesktop.DBus", member="AddMatch",
                               signature="s", body=[match]))
        reply = await bus.call(Message(
            destination=destination, path=path,
            interface="org.freedesktop.portal.Screenshot", member="Screenshot",
            signature="sa{sv}", body=["", {
                "handle_token": Variant("s", token),
                "interactive": Variant("b", True),
                "target": Variant("u", target),
            }],
        ))
        if reply.message_type == MessageType.ERROR or not reply.body:
            raise PortalError("O portal não abriu a seleção de captura.")
        if reply.body[0] != request_path:
            raise PortalError("O portal retornou uma solicitação inesperada.")
        try:
            status, values = await asyncio.wait_for(result, timeout=90)
        except asyncio.TimeoutError as exc:
            await bus.call(Message(destination=destination, path=request_path,
                                   interface="org.freedesktop.portal.Request", member="Close"))
            raise PortalError("A seleção da janela excedeu o tempo limite.") from exc
        if status != 0:
            raise PortalError("Seleção de tela cancelada ou recusada.")
        uri = values.get("uri")
        if uri is None or uri.signature != "s":
            raise PortalError("O portal não retornou uma imagem.")
        parsed = urlsplit(uri.value)
        if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
            raise PortalError("O portal retornou um endereço inválido.")
        return Path(unquote(parsed.path))
    finally:
        bus.disconnect()


def choose_screenshot(*, window: bool = True) -> Path:
    """Show the compositor's own chooser; return its one-shot file URI."""
    try:
        return asyncio.run(_choose(2 if window else 1))
    except (ImportError, OSError, ValueError) as exc:
        raise PortalError("Portal de tela indisponível; confira xdg-desktop-portal.") from exc
