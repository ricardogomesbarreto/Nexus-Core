"""Physical acceptance must not silently test hardware or leak raw payloads."""

import io

import pytest

from nexus.platforms import acceptance
from nexus.updates import launcher


def _passive(monkeypatch, *, camera=None):
    called = []

    def invoke(args, **kwargs):
        called.append(tuple(args))
        assert args == ["--version"]
        return True, "Nexus Core 0.9.12\n"

    def diagnose(args, **kwargs):
        called.append(tuple(args))
        if args == ["--ubuntu-preflight"]:
            return {"checks": {"postgresql_authenticated": True,
                               "ollama_model_listed": True,
                               "voice_input_dependencies": True,
                               "voice_output_dependencies": True}}
        if args == ["--status"]:
            return {"schema": "nexus.recovery.v1"}
        if args == ["--camera-list"]:
            return {"devices": camera if camera is not None else []}
        pytest.fail(f"Hardware invoked without consent: {args}")

    monkeypatch.setattr(acceptance, "_invoke", invoke)
    monkeypatch.setattr(acceptance, "_json", diagnose)
    monkeypatch.setattr(acceptance, "_checkout_sha", lambda: "a" * 40)
    return called


def test_noninteractive_log_never_opens_microphone_or_camera(monkeypatch):
    calls = _passive(monkeypatch, camera=[{"index": 0, "name": "Private Webcam"}])
    output = io.StringIO()
    assert acceptance.run_acceptance(out=output, interactive=False) == 0
    report = output.getvalue()
    assert "[PASSOU] Câmeras acessíveis — quantidade=1" in report
    assert "[PENDENTE] Captura de câmera" in report
    assert "[PENDENTE] Sinal do microfone" in report
    assert "[PENDENTE] Reconhecimento de voz" in report
    assert "Private Webcam" not in report
    assert calls == [("--version",), ("--ubuntu-preflight",), ("--status",), ("--camera-list",)]


def test_physical_results_are_distinct_from_observations_and_secrets(monkeypatch):
    _passive(monkeypatch, camera=[{"index": 2, "name": "Sensitive Camera"}])
    monkeypatch.setattr(acceptance, "_invoke", lambda args, **kw: (
        (True, "Nexus Core 0.9.12\n") if args == ["--version"] else
        (True, "╚════╝\nNEXUSCOREOK\nfinalizado\n")
    ))

    original = acceptance._json
    def diagnose(args, **kwargs):
        if args == ["--microphone-test"]:
            return {"microphone_tested": True, "signal_detected": True, "status": "signal_detected"}
        if args == ["--recognition-test"]:
            return {"recognition_tested": True, "status": "transcribed",
                    "transcript": "minha senha confidencial", "backend": "pipewire",
                    "peak_percent": 42, "level_samples": 123}
        if args == ["--camera-test", "2"]:
            return {"status": "frame_captured", "image_saved": False,
                    "image_data": "PRIVATE_IMAGE"}
        return original(args, **kwargs)

    monkeypatch.setattr(acceptance, "_json", diagnose)
    replies = iter(["SIM", "SIM", "SIM", "SIM", "s", "f", "n", "s", "", "n", "s"])
    output = io.StringIO()
    assert acceptance.run_acceptance(ask=lambda _: next(replies), out=output, interactive=True) == 1
    report = output.getvalue()
    assert "[PASSOU] Reconhecimento de voz" in report
    assert "backend=pipewire; pico=42%; amostras=123; conteúdo omitido" in report
    assert "[PASSOU] Captura de câmera" in report
    assert "[RELATADO] Chat na janela" in report
    assert "[FALHOU] Escuta contínua" in report
    assert "[PENDENTE] Voz feminina e masculina" in report
    assert "[PENDENTE] Abrir aplicativo autorizado" in report
    assert "[RELATADO] Criar pasta autorizada" in report
    assert "[RELEASE] PENDENTE" in report
    for secret in ("minha senha confidencial", "PRIVATE_IMAGE", "Sensitive Camera", "NEXUSCOREOK"):
        assert secret not in report


def test_recognition_failure_logs_bounded_metrics_and_untried_manual_steps(monkeypatch):
    _passive(monkeypatch)
    original = acceptance._json

    def diagnose(args, **kwargs):
        if args == ["--recognition-test"]:
            return {"recognition_tested": True, "status": "no_transcript",
                    "backend": "private-device-name", "peak_percent": "secret",
                    "level_samples": -1, "transcript": "private speech"}
        return original(args, **kwargs)

    monkeypatch.setattr(acceptance, "_json", diagnose)
    replies = iter(["", "", "SIM", "", "n", "", "n", "", "", "", ""])
    output = io.StringIO()
    assert acceptance.run_acceptance(ask=lambda _: next(replies), out=output, interactive=True) == 1
    report = output.getvalue()
    assert "[FALHOU] Reconhecimento de voz — status=no_transcript; backend=indisponível; pico=indisponível%; amostras=indisponível; conteúdo omitido" in report
    assert "[PENDENTE] Chat na janela" in report
    assert "[PENDENTE] Voz feminina e masculina" in report
    for secret in ("private speech", "private-device-name", "secret"):
        assert secret not in report


def test_malformed_diagnostics_fail_closed_and_never_claim_release(monkeypatch):
    monkeypatch.setattr(acceptance, "_invoke", lambda *a, **kw: (False, ""))
    monkeypatch.setattr(acceptance, "_json", lambda *a, **kw: {})
    monkeypatch.setattr(acceptance, "_checkout_sha", lambda: "não identificado")
    output = io.StringIO()
    assert acceptance.run_acceptance(out=output, interactive=False) == 1
    assert "[FALHOU] PostgreSQL autenticado" in output.getvalue()
    assert "[FALHOU] Status de recuperação" in output.getvalue()
    assert "[RELEASE] PENDENTE" in output.getvalue()


def test_acceptance_diagnostics_skip_prelaunch_updates():
    assert launcher.should_run_maintenance(["--acceptance-log"]) is False
    assert launcher.should_run_maintenance(["--microphone-test"]) is False
    assert launcher.should_run_maintenance(["--recognition-test"]) is False


def test_entrypoint_dispatches_acceptance_without_starting_application(monkeypatch):
    import nexus.main as main

    monkeypatch.setattr(main, "build_application", lambda: pytest.fail("must not start desktop app"))
    monkeypatch.setattr(acceptance, "run_acceptance", lambda: 1)
    with pytest.raises(SystemExit) as exc:
        main.cli(["--acceptance-log"])
    assert exc.value.code == 1


def test_folder_and_application_outcomes_are_independent(monkeypatch):
    _passive(monkeypatch)
    answers = iter(["", "", "", "", "n", "n", "n", "n", "f", "s", "n"])
    output = io.StringIO()
    assert acceptance.run_acceptance(
        ask=lambda _: next(answers), out=output, interactive=True,
    ) == 1
    report = output.getvalue()
    assert "[FALHOU] Criar pasta autorizada" in report
    assert "[RELATADO] Abrir aplicativo autorizado" in report
    assert "[FALHOU] Pasta e aplicativo" not in report
    assert "NexusCoreTeste" not in report  # No action content recorded.
    assert "[RELEASE] PENDENTE" in report
