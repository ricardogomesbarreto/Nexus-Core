"""Portal selection is explicit and a window request never captures the full display."""

import asyncio

import pytest

from nexus.vision import portal
from nexus.vision.local import LocalVision, VisionError
from nexus.config.settings import Settings


def test_selected_window_reads_only_portal_file(monkeypatch, tmp_path):
    from PIL import Image
    import io
    output = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(output, format="PNG")
    file = tmp_path / "selected.png"
    file.write_bytes(output.getvalue())
    calls = []
    monkeypatch.setattr(portal, "choose_screenshot", lambda *, window:
                        calls.append(window) or file)
    result = LocalVision(Settings()).selected_screen(window=True)
    assert result.startswith(b"\x89PNG")
    assert calls == [True]


def test_unsupported_window_target_refuses_fullscreen_fallback(monkeypatch):
    dbus = pytest.importorskip("dbus_next")
    from dbus_next import Message, MessageType, Variant
    from dbus_next.aio import MessageBus

    class Bus:
        unique_name = ":1.30"
        def disconnect(self):
            pass
        async def connect(self):
            return self
        async def call(self, message):
            assert message.member == "Get", "Screenshot must not be called"
            return Message(message_type=MessageType.METHOD_RETURN,
                           reply_serial=1, body=[Variant("u", 1)])

    monkeypatch.setattr("dbus_next.aio.MessageBus", Bus)
    with pytest.raises(portal.PortalError, match="não oferece"):
        asyncio.run(portal._choose(2))


def test_portal_waits_for_user_selected_window(monkeypatch, tmp_path):
    pytest.importorskip("dbus_next")
    from dbus_next import Message, MessageType, Variant
    file = tmp_path / "selected.png"
    file.write_bytes(b"image")

    class Bus:
        unique_name = ":1.31"
        handler = None
        selected_target = None
        def disconnect(self):
            pass
        async def connect(self):
            return self
        def add_message_handler(self, handler):
            self.handler = handler
        async def call(self, message):
            if message.member == "Get":
                return Message(message_type=MessageType.METHOD_RETURN,
                               reply_serial=1, body=[Variant("u", 3)])
            if message.member == "AddMatch":
                return Message(message_type=MessageType.METHOD_RETURN, reply_serial=1)
            assert message.member == "Screenshot"
            self.selected_target = message.body[1]["target"].value
            token = message.body[1]["handle_token"].value
            request_path = f"{portal_path}/request/1_31/{token}"
            signal = Message(path=request_path, interface="org.freedesktop.portal.Request",
                             member="Response", message_type=MessageType.SIGNAL,
                             signature="ua{sv}", body=[0, {"uri": Variant("s", file.as_uri())}])
            asyncio.get_running_loop().call_soon(self.handler, signal)
            return Message(message_type=MessageType.METHOD_RETURN, reply_serial=1,
                           body=[request_path])

    portal_path = "/org/freedesktop/portal/desktop"
    bus = Bus()
    monkeypatch.setattr("dbus_next.aio.MessageBus", lambda: bus)
    assert asyncio.run(portal._choose(2)) == file
    assert bus.selected_target == 2


def test_legacy_screenshot_portal_supports_interactive_screen_without_target(monkeypatch, tmp_path):
    """v2 Screenshot lacks AvailableTargets but still offers interactive screen."""
    pytest.importorskip("dbus_next")
    from dbus_next import Message, MessageType, Variant

    selected = tmp_path / "user-chosen.png"
    selected.write_bytes(b"test-image")

    class Bus:
        unique_name = ":1.44"
        handler = None
        options = None
        def disconnect(self): pass
        async def connect(self): return self
        def add_message_handler(self, handler): self.handler = handler
        async def call(self, request):
            if request.member == "Get":
                return Message(message_type=MessageType.ERROR, reply_serial=1,
                               error_name="org.freedesktop.DBus.Error.UnknownProperty")
            if request.member == "AddMatch":
                return Message(message_type=MessageType.METHOD_RETURN, reply_serial=1)
            if request.member == "Screenshot":
                self.options = request.body[1]
                token = self.options["handle_token"].value
                request_path = (
                    "/org/freedesktop/portal/desktop/request/1_44/" + token
                )
                event = Message(
                    path=request_path, interface="org.freedesktop.portal.Request",
                    member="Response", message_type=MessageType.SIGNAL,
                    signature="ua{sv}", body=[
                        0, {"uri": Variant("s", selected.as_uri())}
                    ],
                )
                asyncio.get_running_loop().call_soon(self.handler, event)
                return Message(message_type=MessageType.METHOD_RETURN, reply_serial=1,
                               body=[request_path])
            raise AssertionError(request.member)

    bus = Bus()
    monkeypatch.setattr("dbus_next.aio.MessageBus", lambda: bus)
    assert asyncio.run(portal._choose(1)) == selected
    assert bus.options["interactive"].value is True
    assert "target" not in bus.options  # v2 backend cannot accept target


def test_legacy_portal_refuses_window_without_target_property(monkeypatch):
    pytest.importorskip("dbus_next")
    from dbus_next import Message, MessageType

    class Bus:
        unique_name = ":1.45"
        def disconnect(self): pass
        async def connect(self): return self
        async def call(self, request):
            assert request.member == "Get", "Do not capture screen silently"
            return Message(message_type=MessageType.ERROR, reply_serial=1,
                           error_name="org.freedesktop.DBus.Error.UnknownProperty")

    monkeypatch.setattr("dbus_next.aio.MessageBus", Bus)
    with pytest.raises(portal.PortalError, match="não oferece seleção exclusiva"):
        asyncio.run(portal._choose(2))
