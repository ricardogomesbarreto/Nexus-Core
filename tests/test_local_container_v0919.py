"""Opt-in local container never pulls, mounts, networks or accepts commands."""
import json
import subprocess
import sys
from threading import Event
from types import SimpleNamespace

import pytest

from nexus.tools import local_container as module
from nexus.updates.launcher import should_run_maintenance
from nexus.security import AuditLogger, SecurityGate

IMAGE = "sha256:" + "a" * 64


def test_image_id_and_fixed_isolation_flags():
    args = module._command("/usr/bin/podman", IMAGE, "/tmp/private/cid")
    assert args[-1] == IMAGE
    assert "--pull=never" in args
    assert "--network=none" in args
    assert "--image-volume=ignore" in args
    assert "--read-only" in args
    assert "--memory=256m" in args
    assert "--log-driver=none" in args
    assert not any("--privileged" in arg or "--mount" in arg for arg in args)
    with pytest.raises(module.LocalContainerError):
        module._command("/usr/bin/podman", "remote/image:latest", "/tmp/cid")
    with pytest.raises(module.LocalContainerError):
        module.run_local_image(IMAGE + " --privileged")


def test_security_gate_audits_explicit_decision(tmp_path):
    log = tmp_path / "audit.log"
    gate = SecurityGate(audit_logger=AuditLogger(log))
    with pytest.raises(module.LocalContainerError, match="não autorizada"):
        module.authorize_local_image(IMAGE, lambda request: False, gate=gate)
    assert "DENIED" in log.read_text()
    approved = module.authorize_local_image(IMAGE, lambda request: True, gate=gate)
    assert approved is gate
    assert "APPROVED" in log.read_text()


def test_remote_or_rootful_runtime_is_rejected(monkeypatch):
    def report(**updates):
        info = {"serviceIsRemote": False, "host": {
            "security": {"rootless": True}, "cgroupVersion": "v2"}}
        info.update(updates)
        return SimpleNamespace(returncode=0, stdout=json.dumps(info).encode())
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: report())
    module._check_rootless("/usr/bin/podman", {})
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs:
                        report(serviceIsRemote=True))
    with pytest.raises(module.LocalContainerError, match="sem root"):
        module._check_rootless("/usr/bin/podman", {})
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs:
                        report(host={"security": {"rootless": False},
                                     "cgroupVersion": "v2"}))
    with pytest.raises(module.LocalContainerError, match="sem root"):
        module._check_rootless("/usr/bin/podman", {})


def test_local_run_and_output_limit_without_container_daemon(monkeypatch, tmp_path):
    script = tmp_path / "fake-podman"
    script.write_text("#!/usr/bin/python3\n"
                      "import sys\n"
                      "if sys.argv[1:3] == ['image', 'exists']: sys.exit(0)\n"
                      "if '--pull=never' not in sys.argv: sys.exit(1)\n"
                      "print('isolated')\n")
    script.chmod(0o700)
    monkeypatch.setattr(module, "_runtime", lambda: str(script))
    monkeypatch.setattr(module, "_check_rootless", lambda *args: None)
    result = module.run_local_image(IMAGE)
    assert result.exit_code == 0
    assert result.output == "isolated\n"
    script.write_text("#!/usr/bin/python3\n"
                      "import sys\n"
                      "if sys.argv[1:3] == ['image', 'exists']: sys.exit(0)\n"
                      "sys.stdout.write('x' * 20000)\n")
    with pytest.raises(module.LocalContainerError, match="16 KiB"):
        module.run_local_image(IMAGE)


def test_cancelled_run_kills_process(monkeypatch, tmp_path):
    script = tmp_path / "fake-podman"
    script.write_text("#!/usr/bin/python3\n"
                      "import sys, time\n"
                      "if sys.argv[1:3] == ['image', 'exists']: sys.exit(0)\n"
                      "time.sleep(5)\n")
    script.chmod(0o700)
    monkeypatch.setattr(module, "_runtime", lambda: str(script))
    monkeypatch.setattr(module, "_check_rootless", lambda *args: None)
    cancelled = Event()
    cancelled.set()
    with pytest.raises(module.LocalContainerError, match="cancelada"):
        module.run_local_image(IMAGE, cancel=cancelled)


def test_cli_rejects_untrusted_image_before_runtime_or_services():
    process = subprocess.run([sys.executable, "-m", "nexus.main",
                              "--local-image-run", "registry.example/app:latest"],
                             capture_output=True, timeout=10)
    assert process.returncode != 0
    assert b"sha256" in process.stderr
    assert b"Inicializando" not in process.stderr
    assert not should_run_maintenance(["--local-image-run", IMAGE])
