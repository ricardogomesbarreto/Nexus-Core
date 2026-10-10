"""NEXUS CORE v0.8.3 — read-only Ubuntu first-run readiness checks.

This opt-in doctor connects ONLY to local loopback PostgreSQL and Ollama.
It never starts services, installs software, opens a microphone/camera,
reads data rows, executes shell commands or touches database credentials.
"""
from http.client import HTTPConnection, HTTPException
import json
import shutil
import subprocess

from nexus.platforms.linux import linux_profile, platform_capabilities


POSTGRESQL_HOST = "127.0.0.1"
POSTGRESQL_PORT = 5432
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434


def postgres_readiness(*, run=None, which=None) -> dict:
    """Non-authenticating server readiness through bounded pg_isready."""
    run = subprocess.run if run is None else run
    which = shutil.which if which is None else which
    binary = which("pg_isready")
    if not binary:
        return {"status": "missing_client", "reachable": False}
    try:
        result = run(
            [binary, "-h", POSTGRESQL_HOST, "-p", str(POSTGRESQL_PORT), "-t", "2"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unavailable", "reachable": False}
    if result.returncode == 0:
        return {"status": "accepting_connections", "reachable": True}
    return {"status": "unavailable", "reachable": False}


def ollama_readiness(*, connect=None) -> dict:
    """GET only /api/version on fixed loopback; no URL redirects or prompts."""
    connection = (HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=2)
                  if connect is None else connect(OLLAMA_HOST, OLLAMA_PORT, timeout=2))
    try:
        connection.request("GET", "/api/version")
        response = connection.getresponse()
        if response.status != 200:
            return {"status": "unavailable", "reachable": False}
        body = response.read(2049)
        if len(body) > 2048:
            return {"status": "invalid_response", "reachable": False}
        data = json.loads(body.decode("utf-8", errors="strict"))
        if not isinstance(data, dict) or type(data.get("version")) is not str:
            return {"status": "invalid_response", "reachable": False}
        # Suppress server-provided strings; only the status is reported.
        return {"status": "reachable", "reachable": True}
    except (OSError, HTTPException, ValueError, UnicodeError, TimeoutError):
        return {"status": "unavailable", "reachable": False}
    finally:
        try:
            connection.close()
        except OSError:
            pass


def ubuntu_doctor(*, postgres=None, ollama=None, profile=None, inspect=None) -> dict:
    """Return structured, bounded observations and fixed remediation hints."""
    if profile is None:
        profile = linux_profile()
    if inspect is None:
        inventory = platform_capabilities(profile=profile)
    else:
        inventory = inspect(profile=profile)
    pg = postgres_readiness() if postgres is None else postgres()
    llm = ollama_readiness() if ollama is None else ollama()
    required = inventory.get("missing_required", [])
    if type(required) is not list:
        required = []
    # Never echo untrusted system paths, server replies or environment values.
    known_missing = [x for x in (
        "psql", "pg_isready", "espeak-ng", "arecord", "ffmpeg", "python3-tk",
    ) if x in required]
    blockers = []
    if not profile.installer_supported:
        blockers.append("ubuntu_24_04_not_confirmed")
    if known_missing:
        blockers.append("missing_desktop_packages")
    if pg["reachable"] is not True:
        blockers.append("postgresql_not_ready")
    if llm["reachable"] is not True:
        blockers.append("ollama_not_ready")
    actions = []
    if known_missing:
        actions.append("Run the guided Ubuntu installer to review official apt dependencies.")
    if pg["reachable"] is not True:
        actions.append("Verify the local PostgreSQL service and its separate credential configuration.")
    if llm["reachable"] is not True:
        actions.append("Install/start Ollama from its official distribution and provision a local model separately.")
    if profile.session != "x11":
        actions.append("Only optional xdotool window automation requires a local X11 session; Tk desktop UI can use Wayland.")
    if not profile.installer_supported:
        actions.append("Ubuntu 24.04 LTS is the only installer baseline; other distros are diagnostic-only.")
    return {
        "schema": "nexus.ubuntu-doctor.v1",
        "mode": "local_read_only",
        "target": profile.target,
        "session": profile.session,
        "platform_installer_supported": profile.installer_supported,
        "missing_packages": known_missing,
        "postgresql": pg,
        "ollama": llm,
        "core_services_ready_to_try": not blockers,
        "blockers": blockers,
        "recommendations": actions,
        "camera_tested": False,
        "microphone_tested": False,
        "postgresql_authentication_tested": False,
        "ollama_model_tested": False,
        "database_changed": False,
        "services_started": False,
        "packages_installed": False,
        "external_network_used": False,
    }
