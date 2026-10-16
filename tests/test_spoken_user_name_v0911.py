"""Spoken welcome must only include the local user's first name."""

from types import SimpleNamespace
import pwd

from nexus.desktop.welcome import desktop_spoken_welcome


def test_only_short_user_name_is_spoken(monkeypatch):
    monkeypatch.setattr(
        pwd, "getpwuid",
        lambda uid: SimpleNamespace(
            pw_gecos="Ricardo Gomes Barreto", pw_name="ricardobarreto",
        ),
    )
    assert desktop_spoken_welcome() == "Bem-vindo ao Nexus Core, Ricardo."


def test_login_is_used_if_full_name_is_empty(monkeypatch):
    monkeypatch.setattr(
        pwd, "getpwuid",
        lambda uid: SimpleNamespace(pw_gecos="", pw_name="ricardo"),
    )
    assert desktop_spoken_welcome() == "Bem-vindo ao Nexus Core, ricardo."


def test_name_with_invalid_punctuation_is_safely_replaced(monkeypatch):
    monkeypatch.setattr(
        pwd, "getpwuid",
        lambda uid: SimpleNamespace(pw_gecos="**", pw_name="123_user"),
    )
    assert desktop_spoken_welcome() == "Bem-vindo ao Nexus Core, usuário."
