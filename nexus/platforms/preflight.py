"""Ubuntu v0.8.4 opt-in preflight: actual local service credentials/model inventory.

Unlike the passive v0.8.3 doctor, this command performs a read-only
authenticated PostgreSQL SELECT 1 and a bounded local Ollama /api/tags GET.
No automatic service installation, model download, microphone or camera use.
All responses are fixed status values; never disclose passwords or model lists.
"""
from http.client import HTTPConnection, HTTPException
import json

from nexus.config.settings import settings as default_settings
from nexus.platforms.doctor import ubuntu_doctor
from nexus.voice.diagnostics import inspect_voice


MAX_TAGS_BYTES = 65_536
MAX_MODELS = 256
ALLOWED_POSTGRES_HOSTS = frozenset(("127.0.0.1", "::1", "localhost"))


def postgres_auth_probe(*, configuration=None, connect=None) -> dict:
    """Prove authorized local PostgreSQL session can SELECT 1 without writes."""
    config = default_settings if configuration is None else configuration
    if (config.database_provider != "postgresql"
            or config.database_host not in ALLOWED_POSTGRES_HOSTS
            or not isinstance(config.database_port, int)
            or not 1 <= config.database_port <= 65535):
        return {"status": "unsupported_local_configuration", "authenticated": False}
    if not config.database_password:
        return {"status": "credentials_missing", "authenticated": False}
    if connect is None:
        import psycopg
        connect = psycopg.connect
    connection = None
    try:
        # Force server transactions read-only. This is NOT a privileged DBA check.
        connection = connect(
            host=config.database_host,
            port=config.database_port,
            dbname=config.database_name,
            user=config.database_user,
            password=config.database_password,
            connect_timeout=3,
            options="-c default_transaction_read_only=on",
        )
        cursor = connection.execute("SELECT 1")
        passed = cursor.fetchone() == (1,)
        return {
            "status": "authenticated_read_only" if passed else "query_failed",
            "authenticated": bool(passed),
        }
    except Exception:
        # Database driver messages may expose passwords or usernames. Never echo.
        return {"status": "connection_or_auth_failure", "authenticated": False}
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def ollama_model_probe(*, model_name=None, connect=None) -> dict:
    """Inspect local model names via Ollama with a bounded GET, no downloads."""
    wanted = default_settings.local_model_name if model_name is None else model_name
    if not isinstance(wanted, str) or not wanted or len(wanted) > 128:
        return {"status": "invalid_model_configuration", "installed": False}
    connection = None
    try:
        factory = HTTPConnection if connect is None else connect
        connection = factory("127.0.0.1", 11434, timeout=3)
        connection.request("GET", "/api/tags")
        response = connection.getresponse()
        if response.status != 200:
            return {"status": "service_unavailable", "installed": False}
        raw = response.read(MAX_TAGS_BYTES + 1)
        if len(raw) > MAX_TAGS_BYTES:
            return {"status": "invalid_response", "installed": False}
        data = json.loads(raw.decode("utf-8", errors="strict"))
        if not isinstance(data, dict) or type(data.get("models")) is not list:
            return {"status": "invalid_response", "installed": False}
        models = data["models"]
        if len(models) > MAX_MODELS:
            return {"status": "invalid_response", "installed": False}
        for item in models:
            if not isinstance(item, dict) or type(item.get("name")) is not str:
                return {"status": "invalid_response", "installed": False}
        installed = any(item["name"] == wanted for item in models)
        return {
            "status": "model_listed" if installed else "model_not_listed",
            "installed": installed,
        }
    except (OSError, HTTPException, ValueError, UnicodeError, TimeoutError):
        return {"status": "service_unavailable", "installed": False}
    finally:
        if connection is not None:
            try:
                connection.close()
            except (OSError, HTTPException):
                pass


def ubuntu_preflight(*, doctor=None, database=None, model=None, voice=None) -> dict:
    """Aggregate independent checks while keeping private source details out."""
    base = ubuntu_doctor() if doctor is None else doctor()
    pg = postgres_auth_probe() if database is None else database()
    llm = ollama_model_probe() if model is None else model()
    audio = inspect_voice() if voice is None else voice()
    # Treat pluggable/dependency results as untrusted; construct only fixed fields.
    pg_ready = pg.get("authenticated") is True
    model_ready = llm.get("installed") is True
    stt_ready = audio.get("recognition_ready_to_try") is True
    tts_ready = audio.get("speech_ready_to_try") is True
    platform_ready = base.get("core_services_ready_to_try") is True
    checks = {
        "ubuntu_services": platform_ready,
        "postgresql_authenticated": pg_ready,
        "ollama_model_listed": model_ready,
        "voice_input_dependencies": stt_ready,
        "voice_output_dependencies": tts_ready,
    }
    statuses = {
        "postgresql": pg.get("status") if pg.get("status") in {
            "unsupported_local_configuration", "credentials_missing",
            "authenticated_read_only", "query_failed", "connection_or_auth_failure",
        } else "check_failed",
        "ollama_model": llm.get("status") if llm.get("status") in {
            "invalid_model_configuration", "service_unavailable",
            "invalid_response", "model_listed", "model_not_listed",
        } else "check_failed",
    }
    return {
        "schema": "nexus.ubuntu-preflight.v1",
        "mode": "explicit_opt_in_local_checks",
        "checks": checks,
        "status": statuses,
        "text_chat_dependencies_ready_to_try": all((
            platform_ready, pg_ready, model_ready,
        )),
        "voice_chat_dependencies_ready_to_try": all((
            platform_ready, pg_ready, model_ready, stt_ready, tts_ready,
        )),
        "unmet": [key for key, ok in checks.items() if not ok],
        "recommendations": [
            "Validate PostgreSQL user/password locally without exposing credentials."
            if not pg_ready else "",
            "Download a trusted Ollama model manually if missing; no automatic pull."
            if not model_ready else "",
            "Check Vosk model/audio tools and Linux device permissions manually."
            if not (stt_ready and tts_ready) else "",
        ],
        "postgresql_data_modified": False,
        "external_network_used": False,
        "model_downloaded": False,
        "microphone_opened": False,
        "camera_opened": False,
        "audio_played": False,
        "full_hardware_or_model_inference_tested": False,
    }
