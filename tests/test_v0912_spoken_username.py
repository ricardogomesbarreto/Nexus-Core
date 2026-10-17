"""v0.9.12 spoken greeting: first local Linux name, once, no network."""

from types import SimpleNamespace

from nexus.desktop.welcome import desktop_spoken_welcome


def test_linux_gecos_full_name_is_reduced_to_first_name(monkeypatch):
    import pwd
    monkeypatch.setattr(
        pwd, "getpwuid",
        lambda uid: SimpleNamespace(
            pw_gecos="Ricardo Gomes Barreto,Room,12345", pw_name="ricardobarreto"
        ),
    )
    assert desktop_spoken_welcome() == "Bem-vindo ao Nexus Core, Ricardo."


def test_login_fallback_when_gecos_is_blank(monkeypatch):
    import pwd
    monkeypatch.setattr(
        pwd, "getpwuid",
        lambda uid: SimpleNamespace(pw_gecos="", pw_name="ricardo"),
    )
    assert desktop_spoken_welcome() == "Bem-vindo ao Nexus Core, ricardo."


def test_no_unsolicited_network_or_extra_audio_in_greeting(monkeypatch):
    import pwd
    monkeypatch.setattr(
        pwd, "getpwuid",
        lambda uid: SimpleNamespace(pw_gecos="Ana Maria", pw_name="ana"),
    )
    def prohibit_network(*args, **kwargs):
        raise AssertionError("Boas-vindas não devem acessar a rede")
    import socket
    monkeypatch.setattr(socket, "create_connection", prohibit_network)
    greeting = desktop_spoken_welcome()
    assert greeting == "Bem-vindo ao Nexus Core, Ana."
    assert greeting.count(".") == 1
    assert "iniciado" not in greeting
    assert "câmera" not in greeting


def test_unsafe_markup_and_long_name_are_never_spoken():
    assert desktop_spoken_welcome("Ricardo<script>") == "Bem-vindo ao Nexus Core."
    assert desktop_spoken_welcome("Ricardo\n*atuar*") == "Bem-vindo ao Nexus Core."
    assert desktop_spoken_welcome("X" * 125) == "Bem-vindo ao Nexus Core."
