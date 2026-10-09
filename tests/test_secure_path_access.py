"""Adversarial filesystem tests: swap symlinks after authorization."""

from pathlib import Path

from nexus.security import (
    AuditLogger, PathSecurity, PermissionDecision, SecurityGate,
)
from nexus.tools import ListDirectoryTool, ReadFileTool, ToolExecutor, ToolRegistry


def executor_with_home(tmp_path, tool):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home.resolve()
    policy.protected_paths = [home / ".ssh", Path("/etc")]
    gate = SecurityGate(
        path_security=policy,
        audit_logger=AuditLogger(tmp_path / "audit.log"),
    )
    registry = ToolRegistry()
    registry.register(tool)
    return ToolExecutor(registry, gate), home, gate


def swap_after_approval(gate, callback):
    original = gate.evaluate
    switched = False

    def evaluate(request):
        nonlocal switched
        decision = original(request)
        if not switched and decision.decision is PermissionDecision.ALLOW:
            switched = True
            callback()
        return decision

    gate.evaluate = evaluate


def test_file_replaced_with_symlink_after_security_gate_is_blocked(tmp_path):
    executor, home, gate = executor_with_home(tmp_path, ReadFileTool())
    allowed = home / "notes.txt"
    allowed.write_text("normal", encoding="utf-8")
    forbidden = tmp_path / "secret.txt"
    forbidden.write_text("PRIVATE-CONTENT", encoding="utf-8")

    def swap():
        allowed.unlink()
        allowed.symlink_to(forbidden)

    swap_after_approval(gate, swap)
    result = executor.execute("read_file", path=str(allowed))
    assert not result.success
    assert "PRIVATE-CONTENT" not in str(result.as_dict())


def test_parent_directory_symlink_swap_is_blocked(tmp_path):
    executor, home, gate = executor_with_home(tmp_path, ReadFileTool())
    folder = home / "docs"
    folder.mkdir()
    (folder / "readme.txt").write_text("allowed")
    forbidden = tmp_path / "elsewhere"
    forbidden.mkdir()
    (forbidden / "readme.txt").write_text("PRIVATE-CONTENT")

    def swap():
        folder.rename(home / "old_docs")
        folder.symlink_to(forbidden, target_is_directory=True)

    swap_after_approval(gate, swap)
    result = executor.execute("read_file", path=str(folder / "readme.txt"))
    assert not result.success
    assert "PRIVATE-CONTENT" not in str(result.as_dict())


def test_directory_symlink_swap_is_blocked(tmp_path):
    executor, home, gate = executor_with_home(tmp_path, ListDirectoryTool())
    folder = home / "public"
    folder.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")

    def swap():
        folder.rmdir()
        folder.symlink_to(outside, target_is_directory=True)

    swap_after_approval(gate, swap)
    result = executor.execute("list_directory", path=str(folder))
    assert not result.success
    assert "secret.txt" not in str(result.as_dict())


def test_symlink_to_another_allowed_file_is_conservatively_denied(tmp_path):
    executor, home, _ = executor_with_home(tmp_path, ReadFileTool())
    (home / "real.txt").write_text("safe")
    (home / "shortcut.txt").symlink_to(home / "real.txt")
    result = executor.execute("read_file", path=str(home / "shortcut.txt"))
    assert not result.success


def test_regular_file_is_read_from_open_descriptor(tmp_path):
    executor, home, _ = executor_with_home(tmp_path, ReadFileTool())
    path = home / "notes.txt"
    path.write_text("allowed", encoding="utf-8")
    result = executor.execute("read_file", path=str(path))
    assert result.success
    assert result.data["content"] == "allowed"
