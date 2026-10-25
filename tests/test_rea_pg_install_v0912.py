"""Installer detects a stopped local cluster before PostgreSQL auth.

Never enable units, select the wrong cluster or treat pg_isready as successful
credential verification. No test contacts an actual service or uses sudo.
"""
import subprocess
from types import SimpleNamespace

import pytest

from scripts import install_linux


def test_installer_skips_sudo_if_local_postgresql_is_ready(monkeypatch):
    calls = []
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    def run(argv, **kwargs):
        calls.append(argv)
        if argv[0] != "pg_isready":
            pytest.fail("No systemd or pg_lsclusters when the server is ready")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(install_linux, "_run", run)
    monkeypatch.setattr(install_linux, "confirm",
                        lambda _: pytest.fail("No consent request when ready"))
    assert install_linux.ensure_postgresql_running_for_install()
    assert calls == [["pg_isready", "-q", "-h", "127.0.0.1", "-p", "5432"]]


def test_stopped_postgresql_is_started_only_after_explicit_consent(monkeypatch):
    calls = []
    allowed = []
    started = False
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    monkeypatch.setattr(install_linux, "confirm",
                        lambda prompt: allowed.append(prompt) or True)
    def run(argv, **kwargs):
        nonlocal started
        calls.append(argv)
        if argv[0] == "pg_isready":
            if not started:
                raise subprocess.CalledProcessError(2, argv)
            return SimpleNamespace(returncode=0)
        if argv[0] == "pg_lsclusters":
            return SimpleNamespace(stdout=(
                "16 main 5433 down postgres /tmp/16 /tmp/16.log\n"
                "18 main 5432 down postgres /tmp/18 /tmp/18.log\n"
            ), returncode=0)
        if argv[:3] == ["systemctl", "is-active", "--quiet"]:
            raise subprocess.CalledProcessError(3, argv)
        if argv[:3] == ["sudo", "systemctl", "start"]:
            assert argv[3] == "postgresql@18-main.service"
            started = True
            return SimpleNamespace(returncode=0)
        pytest.fail(f"Unexpected command: {argv}")
    monkeypatch.setattr(install_linux, "_run", run)
    assert install_linux.ensure_postgresql_running_for_install()
    assert len(allowed) == 1
    assert "postgresql@18-main.service" in allowed[0]
    assert not any("enable" in args for args in calls)
    assert started


def test_installer_respects_denial_and_preserves_stopped_service(monkeypatch):
    calls = []
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    monkeypatch.setattr(install_linux, "confirm", lambda _: False)
    def run(argv, **kwargs):
        calls.append(argv)
        if argv[0] == "pg_isready":
            raise subprocess.CalledProcessError(2, argv)
        if argv[0] == "pg_lsclusters":
            return SimpleNamespace(stdout=(
                "18 main 5432 down postgres /tmp /tmp/log\n"
            ))
        pytest.fail(f"Unauthorized command: {argv}")
    monkeypatch.setattr(install_linux, "_run", run)
    assert not install_linux.ensure_postgresql_running_for_install()
    assert not any("sudo" in argv for argv in calls)


@pytest.mark.parametrize("port", ["5432; rm -rf /", "-1", "99999", "0", "foo"])
def test_untrusted_pg_port_never_reaches_shell_or_sudo(monkeypatch, port):
    monkeypatch.setenv("NEXUS_DATABASE_PORT", port)
    monkeypatch.setattr(install_linux, "installed",
                        lambda _: pytest.fail("Invalid port must fail before lookup"))
    assert not install_linux.ensure_postgresql_running_for_install()


def test_two_clusters_on_same_port_are_rejected(monkeypatch):
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    monkeypatch.setattr(install_linux, "confirm",
                        lambda _: pytest.fail("Ambiguous cluster must not be started"))
    def run(argv, **kwargs):
        if argv[0] == "pg_isready":
            raise subprocess.CalledProcessError(2, argv)
        if argv[0] == "pg_lsclusters":
            return SimpleNamespace(stdout=(
                "16 main 5432 down postgres /tmp /tmp/a\n"
                "18 main 5432 down postgres /tmp /tmp/b\n"
            ))
        pytest.fail("no start allowed")
    monkeypatch.setattr(install_linux, "_run", run)
    assert not install_linux.ensure_postgresql_running_for_install()
