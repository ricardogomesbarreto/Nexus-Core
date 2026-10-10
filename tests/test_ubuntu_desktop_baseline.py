"""Ubuntu 24.04 is the only installation baseline; other Linux distros are read-only."""
import json
from types import SimpleNamespace

import pytest

from nexus.platforms import linux_profile, parse_os_release, platform_capabilities
from scripts import install_linux


UBUNTU = 'NAME="Ubuntu"\nID=ubuntu\nVERSION_ID="24.04"\nID_LIKE=debian\n'
DEBIAN = 'ID=debian\nVERSION_ID="12"\n'
ARCH = 'ID=arch\nVERSION_ID=rolling\n'
STEAMOS = 'ID=steamos\nID_LIKE="arch"\nVERSION_ID="3.7"\n'
FEDORA = 'ID=fedora\nVERSION_ID="43"\n'
UBUNTU_FUTURE = 'ID=ubuntu\nVERSION_ID="26.04"\n'


@pytest.mark.parametrize("content,expected", [
    (UBUNTU, ("ubuntu", "24.04")),
    (DEBIAN, ("debian", "12")),
    (ARCH, ("arch", "rolling")),
    (STEAMOS, ("steamos", "3.7")),
    (FEDORA, ("fedora", "43")),
    ('ID="ubuntu"\nVERSION_ID=24.04\n', ("ubuntu", "24.04")),
    ('ID=ubuntu; touch /tmp/untrusted\nVERSION_ID=24.04\n',
     ("unknown", "24.04")),
    ('ID=ubuntu\nVERSION_ID="$(do_bad)"\n', ("ubuntu", "unknown")),
    ("", ("unknown", "unknown")),
])
def test_readonly_os_release_parsing(content, expected):
    assert parse_os_release(content) == expected


@pytest.mark.parametrize("os_release,system,target,supported", [
    (UBUNTU, "Linux", "ubuntu_24_04_lts", True),
    (UBUNTU_FUTURE, "Linux", "ubuntu_not_yet_validated", False),
    (DEBIAN, "Linux", "linux_other_distro_future", False),
    (ARCH, "Linux", "linux_other_distro_future", False),
    (STEAMOS, "Linux", "linux_other_distro_future", False),
    (FEDORA, "Linux", "linux_other_distro_future", False),
    (UBUNTU, "Darwin", "non_linux", False),
])
def test_explicit_installer_support_boundary(os_release, system, target, supported):
    profile = linux_profile(
        os_release=os_release, system=system,
        environment={"XDG_SESSION_TYPE": "wayland"},
    )
    assert profile.target == target
    assert profile.installer_supported is supported


def test_ubuntu_wayland_gui_vs_x11_automation_distinction():
    wayland = linux_profile(
        os_release=UBUNTU, system="Linux",
        environment={"XDG_SESSION_TYPE": "wayland"},
    )
    x11 = linux_profile(
        os_release=UBUNTU, system="Linux",
        environment={"XDG_SESSION_TYPE": "x11"},
    )
    locate = lambda cmd: "/usr/bin/" + cmd
    result = platform_capabilities(
        profile=wayland, locate=locate, tkinter_available=True,
    )
    assert result["installer_supported"] is True
    assert result["desktop_gui_ready_to_try"] is True
    assert result["x11_automation_ready_to_try"] is False
    assert result["postgresql_service_tested"] is False
    assert result["changes_performed"] is False
    assert platform_capabilities(
        profile=x11, locate=locate, tkinter_available=True,
    )["x11_automation_ready_to_try"] is True


def test_report_makes_missing_dependencies_explicit():
    profile = linux_profile(os_release=UBUNTU, system="Linux")
    report = platform_capabilities(
        profile=profile, locate=lambda _: None, tkinter_available=False,
    )
    assert "psql" in report["missing_required"]
    assert "pg_isready" in report["missing_required"]
    assert "python3-tk" in report["missing_required"]
    assert report["optional"]["docker"] is False
    assert report["optional"]["ollama"] is False
    assert report["desktop_gui_ready_to_try"] is False


def test_cli_platform_check_is_read_only_and_does_not_open_database(monkeypatch, capsys):
    import nexus.main as entry
    monkeypatch.setattr(entry, "build_application",
                        lambda: pytest.fail("No app/database startup for platform-check"))
    monkeypatch.setattr(entry, "platform", SimpleNamespace()) if False else None
    entry.cli(["--platform-check"])
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "passive"
    assert result["changes_performed"] is False
    assert "target" in result


@pytest.mark.parametrize("arguments", [
    ["--platform-check", "--agent-prompt", "hello"],
    ["--platform-check", "--memory-list"],
    ["--platform-check", "--vision-question", "describe"],
    ["--platform-check", "--knowledge-search", "word"],
])
def test_cli_platform_check_rejects_mixed_operations(arguments):
    import nexus.main as entry
    with pytest.raises(SystemExit) as err:
        entry.cli(arguments)
    assert err.value.code == 2


@pytest.mark.parametrize("distro_text", [
    DEBIAN, ARCH, STEAMOS, FEDORA, UBUNTU_FUTURE,
])
def test_installer_refuses_all_unverified_distros_before_commands(
    distro_text, monkeypatch, capsys,
):
    profile = linux_profile(os_release=distro_text, system="Linux")
    monkeypatch.setattr(install_linux, "linux_profile", lambda: profile)
    monkeypatch.setattr(install_linux.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(install_linux, "install_system_packages",
                        lambda: pytest.fail("Unsupported distro may not run apt"))
    monkeypatch.setattr(install_linux, "provision_postgresql",
                        lambda: pytest.fail("Unsupported distro may not touch PostgreSQL"))
    monkeypatch.setattr(install_linux, "install_managed_python",
                        lambda: pytest.fail("Unsupported distro may not install Python"))
    assert install_linux.main([]) == 2
    assert "Nada foi instalado" in capsys.readouterr().err


def test_installer_check_is_passive_even_on_unsupported_linux(monkeypatch, capsys):
    monkeypatch.setattr(install_linux, "install_system_packages",
                        lambda: pytest.fail("No apt in check mode"))
    monkeypatch.setattr(install_linux, "provision_postgresql",
                        lambda: pytest.fail("No DB in check mode"))
    assert install_linux.main(["--check"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["changes_performed"] is False


def test_installer_rejects_apt_refusal_before_any_setup(monkeypatch):
    profile = linux_profile(os_release=UBUNTU, system="Linux")
    monkeypatch.setattr(install_linux, "linux_profile", lambda: profile)
    monkeypatch.setattr(install_linux.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(install_linux, "install_system_packages", lambda: False)
    monkeypatch.setattr(install_linux, "provision_postgresql",
                        lambda: pytest.fail("No DB before deps"))
    monkeypatch.setattr(install_linux, "install_managed_python",
                        lambda: pytest.fail("No venv before deps"))
    assert install_linux.main([]) == 2


def test_no_sudo_when_user_declines(monkeypatch):
    profile = linux_profile(os_release=UBUNTU, system="Linux")
    monkeypatch.setattr(install_linux, "linux_profile", lambda: profile)
    monkeypatch.setattr(install_linux, "system_requirements", lambda: ["psql"])
    monkeypatch.setattr(install_linux, "installed", lambda cmd: True)
    monkeypatch.setattr(install_linux, "confirm", lambda question: False)
    monkeypatch.setattr(install_linux, "_run",
                        lambda *args, **kw: pytest.fail("No sudo without consent"))
    assert install_linux.install_system_packages() is False


def test_approved_ubuntu_packages_use_argument_array_not_shell(monkeypatch):
    profile = linux_profile(os_release=UBUNTU, system="Linux")
    monkeypatch.setattr(install_linux, "linux_profile", lambda: profile)
    results = [["psql"], []]
    monkeypatch.setattr(install_linux, "system_requirements",
                        lambda: results.pop(0))
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    monkeypatch.setattr(install_linux, "confirm", lambda question: True)
    captured = []
    monkeypatch.setattr(install_linux, "_run",
                        lambda argv, **kw: captured.append(argv))
    assert install_linux.install_system_packages() is True
    assert captured[0] == ["sudo", "apt-get", "update"]
    assert captured[1][:4] == ["sudo", "apt-get", "install", "-y"]
    assert "postgresql" in captured[1]


def test_python_version_and_non_root_are_prerequisites(monkeypatch, capsys):
    monkeypatch.setattr(install_linux.os, "geteuid", lambda: 0)
    monkeypatch.setattr(install_linux, "install_system_packages",
                        lambda: pytest.fail("No packages as root"))
    assert install_linux.main([]) == 2
