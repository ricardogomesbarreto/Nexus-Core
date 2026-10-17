"""Local desktop actions must remain individually authorized and bounded."""

import os
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.agent import AgentPlanner
from nexus.tools import CreateDirectoryTool, LaunchApplicationTool, ToolExecutor, ToolRegistry


class Confirmation:
    def __init__(self, approved: bool):
        self.approved = approved
        self.requests = []

    def confirm(self, request):
        self.requests.append(request)
        return self.approved


def executor_for(tmp_path, tool, confirmation=None):
    home = tmp_path / "home"
    home.mkdir()
    paths = PathSecurity()
    paths.home = home
    paths.protected_paths = [home / ".ssh", Path("/etc")]
    registry = ToolRegistry()
    registry.register(tool)
    gate = SecurityGate(path_security=paths, audit_logger=AuditLogger(tmp_path / "audit.log"))
    return ToolExecutor(registry, gate, confirmation), home


def test_create_directory_requires_one_confirmation_per_request(tmp_path):
    confirm = Confirmation(True)
    executor, home = executor_for(tmp_path, CreateDirectoryTool(), confirm)
    result = executor.execute("create_directory", path=str(home / "Projetos"))
    assert result.success and (home / "Projetos").is_dir()
    assert os.stat(home / "Projetos").st_mode & 0o777 == 0o700
    assert confirm.requests[0].resources[0].path == str(home / "Projetos")
    assert executor.execute("create_directory", path=str(home / "Outra")).success
    assert len(confirm.requests) == 2


@pytest.mark.parametrize("approve", [None, False])
def test_create_directory_fails_closed(tmp_path, approve):
    confirmation = None if approve is None else Confirmation(approve)
    executor, home = executor_for(tmp_path, CreateDirectoryTool(), confirmation)
    result = executor.execute("create_directory", path=str(home / "not_created"))
    assert not result.success and not (home / "not_created").exists()


def test_create_directory_rejects_protected_and_symlink_parents(tmp_path):
    executor, home = executor_for(tmp_path, CreateDirectoryTool(), Confirmation(True))
    (home / "link").symlink_to(home / "real", target_is_directory=True)
    (home / "real").mkdir()
    assert not executor.execute("create_directory", path=str(home / ".ssh" / "x")).success
    assert not executor.execute("create_directory", path=str(home / "link" / "x")).success
    assert not (home / "real" / "x").exists()


def test_create_directory_blocks_parent_swap_during_confirmation(tmp_path):
    executor, home = executor_for(tmp_path, CreateDirectoryTool())
    parent = home / "parent"
    parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    class Swap:
        def confirm(self, request):
            parent.rmdir()
            parent.symlink_to(outside, target_is_directory=True)
            return True

    executor.confirmation_handler = Swap()
    assert not executor.execute("create_directory", path=str(parent / "x")).success
    assert not (outside / "x").exists()


def test_spoken_directory_request_uses_one_explicit_home_child_and_consent(
    tmp_path, monkeypatch,
):
    confirm = Confirmation(True)
    executor, home = executor_for(tmp_path, CreateDirectoryTool(), confirm)
    monkeypatch.setattr(Path, "home", lambda: home)

    class NoModel:
        def generate(self, request):
            pytest.fail("Um comando exato de pasta não deve aguardar o Ollama")

    agent = AgentPlanner(NoModel(), executor.registry, executor)
    prompt = json.dumps({"historico": [{"usuario": "crie uma pasta chamada Velha"}],
                         "mensagem_atual": "Nexus, crie uma pasta chamada Projetos"})
    outcome = agent.run(prompt)
    assert outcome.success and (home / "Projetos").is_dir()
    assert not (home / "Velha").exists()
    assert len(confirm.requests) == 1
    assert confirm.requests[0].resources[0].path == str(home / "Projetos")


@pytest.mark.parametrize("phrase", [
    "crie uma pasta chamada ../fora", "crie uma pasta chamada /tmp/fora",
    "crie uma pasta chamada .ssh", "crie uma pasta chamada nome/com/barra",
    "é possível criar uma pasta chamada Projetos?",
])
def test_spoken_directory_shortcut_rejects_paths_and_capability_questions(phrase):
    from nexus.agent.planner import _simple_directory_request
    assert _simple_directory_request(phrase) is None


def test_suggestion_mode_cannot_use_exact_desktop_shortcuts():
    from nexus.agent.planner import _simple_app_request, _simple_directory_request
    for request in ("Abra o navegador", "Crie uma pasta chamada Projetos"):
        prompt = json.dumps({"modo": "sugestao_sem_ferramentas", "mensagem_atual": request})
        assert _simple_app_request(prompt) is None
        assert _simple_directory_request(prompt) is None


def test_wake_word_keeps_application_shortcut_bounded():
    from nexus.agent.planner import _simple_app_request
    assert _simple_app_request("Nexus, abra o navegador") == "browser"
    assert _simple_app_request("Nexus, abra o navegador e execute código") is None


def test_launch_application_is_whitelisted_and_sanitizes_environment(tmp_path, monkeypatch):
    confirm = Confirmation(True)
    executor, _ = executor_for(tmp_path, LaunchApplicationTool(), confirm)
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("NEXUS_DATABASE_PASSWORD", "do-not-inherit")
    monkeypatch.setattr(LaunchApplicationTool, "SYSTEM_BIN_DIRS", (str(tmp_path),))
    browser = tmp_path / "firefox"
    browser.write_text("#!/bin/sh\n")
    browser.chmod(0o700)
    calls = []
    monkeypatch.setattr("nexus.tools.desktop_apps.subprocess.Popen",
                        lambda *args, **kwargs: calls.append((args, kwargs)) or SimpleNamespace())
    result = executor.execute("launch_application", application="browser")
    assert result.success and calls[0][0] == ([str(browser)],)
    assert "NEXUS_DATABASE_PASSWORD" not in calls[0][1]["env"]
    assert calls[0][1]["start_new_session"] is True
    assert len(confirm.requests) == 1
    denied = executor.execute("launch_application", application="bash -c evil")
    assert not denied.success and len(calls) == 1


def test_launch_application_denied_without_confirmation_or_display(tmp_path, monkeypatch):
    executor, _ = executor_for(tmp_path, LaunchApplicationTool())
    assert not executor.execute("launch_application", application="browser").success
    executor.confirmation_handler = Confirmation(True)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert not executor.execute("launch_application", application="browser").success


def test_exact_spoken_application_request_skips_slow_model_but_requires_consent(tmp_path):
    registry = ToolRegistry()
    registry.register(LaunchApplicationTool())
    executor = ToolExecutor(registry, SecurityGate(audit_logger=AuditLogger(tmp_path / "audit.log")))

    class NoModel:
        def generate(self, request):
            pytest.fail("Um comando exato não precisa acionar o Ollama")

    planner = AgentPlanner(NoModel(), registry, executor)
    prompt = json.dumps({"mensagem_atual": "Abra o navegador", "historico": []})
    result = planner.run(prompt)
    assert not result.success and result.error_code == "CONFIRMATION_REQUIRED"
    assert planner.plan(prompt).arguments == {"application": "browser"}
