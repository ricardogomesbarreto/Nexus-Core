"""Local, opt-in Ubuntu acceptance log; never prints raw diagnostic payloads.

This is evidence collection, not a release gate. Hardware operations require
individual terminal consent; operator observations are labeled as reports.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from nexus.config.settings import settings


def _invoke(arguments: list[str], *, timeout: int = 20, executable=None):
    # Match the managed launcher's isolated interpreter, never import from cwd.
    command = [sys.executable, "-I", "-m", "nexus.main", *arguments]
    if executable is not None:
        command = [str(executable), *arguments]
    try:
        completed = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    return completed.returncode == 0, completed.stdout[:65536]


def _json(arguments: list[str], *, timeout: int = 20, executable=None):
    ok, output = _invoke(arguments, timeout=timeout, executable=executable)
    if not ok:
        return {}
    try:
        parsed = json.loads(output)
    except (ValueError, UnicodeError):
        return {}
    return parsed if type(parsed) is dict else {}


def _consent(label: str, *, ask, interactive: bool, out) -> bool:
    if not interactive:
        return False
    try:
        return ask(f"{label} Digite SIM para executar, ou Enter para pular: ").strip() == "SIM"
    except (EOFError, KeyboardInterrupt):
        print("\nEtapa omitida.", file=out, flush=True)
        return False


def _observation(label: str, *, ask, interactive: bool, out) -> str:
    if not interactive:
        return "PENDENTE"
    try:
        response = ask(
            f"{label} Testou na janela? "
            "[s=funcionou/f=falhou/n ou Enter=não testado]: "
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nEtapa omitida.", file=out, flush=True)
        return "PENDENTE"
    return {"s": "RELATADO", "f": "FALHOU"}.get(response, "PENDENTE")


def _bounded_metric(value, *, maximum: int) -> str:
    """Expose only coarse numeric diagnostics, never a raw subprocess field."""
    return str(value) if type(value) is int and 0 <= value <= maximum else "indisponível"


def _checkout_sha() -> str:
    """Identify only a Nexus Core checkout, not an unrelated current repo."""
    folder = Path.cwd()
    try:
        if not (folder / "pyproject.toml").is_file() or not (folder / "nexus" / "main.py").is_file():
            return "não identificado"
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=folder, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            timeout=3, check=False,
        )
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha) else "não identificado"
    except (OSError, subprocess.TimeoutExpired):
        return "não identificado"


def run_acceptance(*, ask=input, out=None, interactive=None) -> int:
    """Print fixed-field logs; do not persist transcripts, responses or paths."""
    out = sys.stdout if out is None else out
    interactive = sys.stdin.isatty() if interactive is None else interactive
    results = []

    def log(label: str, status: str, detail: str = ""):
        results.append((label, status))
        print(f"[{status}] {label}" + (f" — {detail}" if detail else ""), file=out, flush=True)

    def begin(label: str):
        print(f"[EXECUTANDO] {label}", file=out, flush=True)

    print("NEXUS CORE — REGISTRO DE ACEITE LOCAL v0.9.12", file=out, flush=True)
    print("Saída resumida para compartilhar: sem senha, áudio, transcrição ou imagem.", file=out, flush=True)
    print("As etapas RELATADO são declarações do operador; não são prova automática.", file=out, flush=True)
    print("Na parte manual, f indica falha após teste; n ou Enter deixa pendente.", file=out, flush=True)
    print(f"[CONTEXTO] checkout_sha={_checkout_sha()} (não comprova o executável instalado)", file=out, flush=True)
    print(f"[CONTEXTO] sessão={os.environ.get('XDG_SESSION_TYPE', 'desconhecida') if os.environ.get('XDG_SESSION_TYPE') in ('wayland', 'x11') else 'desconhecida'}", file=out, flush=True)

    begin("Versão instalada")
    ok, output = _invoke(["--version"])
    log("Versão instalada", "PASSOU" if ok and output.strip() == f"Nexus Core {settings.version}" else "FALHOU",
        f"esperado={settings.version}")

    begin("PostgreSQL, Ollama e dependências")
    preflight = _json(["--ubuntu-preflight"])
    checks = preflight.get("checks", {})
    checks = checks if type(checks) is dict else {}
    for key, label in (("postgresql_authenticated", "PostgreSQL autenticado"),
                       ("ollama_model_listed", "Modelo Ollama disponível"),
                       ("voice_input_dependencies", "Dependências de escuta"),
                       ("voice_output_dependencies", "Dependências de fala")):
        log(label, "PASSOU" if checks.get(key) is True else "FALHOU", "diagnóstico local")

    begin("Status de recuperação (sem rollback)")
    recovery = _json(["--status"], executable=Path.home() / ".local/bin/nexus-core-recover")
    log("Status de recuperação", "PASSOU" if recovery.get("schema") == "nexus.recovery.v1" else "FALHOU",
        "somente consulta; restauração real não testada")

    if _consent("Consultar uma resposta de teste no Ollama local?", ask=ask, interactive=interactive, out=out):
        begin("Resposta do modelo local")
        start = time.monotonic()
        ok, output = _invoke(["--agent-prompt", "Responda apenas com a palavra NEXUSCOREOK."], timeout=90)
        log("Resposta do modelo local", "PASSOU" if ok and "NEXUSCOREOK" in output.split("╚")[-1] else "FALHOU",
            f"marcador_recebido={ok and 'NEXUSCOREOK' in output.split('╚')[-1]}; duração={int(time.monotonic()-start)}s")
    else:
        log("Resposta do modelo local", "PENDENTE")

    if _consent("Gravar três segundos e descartar o áudio do microfone?", ask=ask, interactive=interactive, out=out):
        begin("Sinal do microfone")
        mic = _json(["--microphone-test"], timeout=20)
        log("Sinal do microfone", "PASSOU" if mic.get("microphone_tested") is True and mic.get("signal_detected") is True else "FALHOU",
            f"status={mic.get('status') if mic.get('status') in ('signal_detected', 'no_signal', 'capture_failed', 'recorder_unavailable') else 'erro'}")
    else:
        log("Sinal do microfone", "PENDENTE")

    if _consent("Falar uma frase para o Vosk (até dez segundos, sem guardar a transcrição)?", ask=ask, interactive=interactive, out=out):
        begin("Reconhecimento de voz")
        speech = _json(["--recognition-test"], timeout=45)
        backend = speech.get("backend")
        backend = backend if backend in ("pipewire", "alsa") else "indisponível"
        status = speech.get("status")
        status = status if status in ("transcribed", "no_transcript", "error") else "erro"
        log("Reconhecimento de voz", "PASSOU" if speech.get("recognition_tested") is True and speech.get("status") == "transcribed" and bool(speech.get("transcript")) else "FALHOU",
            f"status={status}; backend={backend}; "
            f"pico={_bounded_metric(speech.get('peak_percent'), maximum=100)}%; "
            f"amostras={_bounded_metric(speech.get('level_samples'), maximum=1000000)}; conteúdo omitido")
    else:
        log("Reconhecimento de voz", "PENDENTE")

    begin("Câmeras acessíveis")
    inventory = _json(["--camera-list"], timeout=20)
    devices = inventory.get("devices")
    valid = [entry["index"] for entry in devices if type(entry) is dict
             and type(entry.get("index")) is int and 0 <= entry["index"] <= 255] if type(devices) is list else []
    log("Câmeras acessíveis", "PASSOU" if valid else "FALHOU", f"quantidade={len(valid)}")
    if valid and _consent("Capturar e descartar um quadro da primeira câmera listada?", ask=ask, interactive=interactive, out=out):
        begin("Captura de câmera")
        camera = _json(["--camera-test", str(valid[0])], timeout=25)
        log("Captura de câmera", "PASSOU" if camera.get("status") == "frame_captured" and camera.get("image_saved") is False else "FALHOU",
            f"dispositivo={valid[0]}; status={camera.get('status') if camera.get('status') in ('frame_captured', 'error') else 'erro'}")
    else:
        log("Captura de câmera", "PENDENTE")

    print("[MANUAL] Abra o assistente em OUTRO terminal: ~/.local/bin/nexus-core --desktop", file=out, flush=True)
    for label, instruction in (
        ("Chat na janela", "Uma pergunta nova recebeu resposta pertinente sem repetir a anterior?"),
        ("Escuta contínua", "Ele respondeu a mais de uma fala sem apertar botão?"),
        ("Voz feminina e masculina", "Você ouviu as duas vozes e testou pausa/retomada?"),
        ("Câmera e análise", "Você viu prévia, print e descrição coerente após permissão?"),
        ("Pasta e aplicativo", "Você testou negar e depois autorizar individualmente cada ação?"),
        ("Permissões", "Você testou confirmar por botão, texto e voz e cancelar?"),
    ):
        log(label, _observation(instruction, ask=ask, interactive=interactive, out=out), "observação humana")
    log("Automação de teclado em Wayland", "PENDENTE" if os.environ.get("XDG_SESSION_TYPE") == "wayland" else "NÃO APLICÁVEL",
        "implementação atual exige X11; não homologar pelo teste de câmera")
    log("Restauração real", "PENDENTE", "ensaiar apenas em instalação descartável")

    counts = {key: sum(status == key for _, status in results)
              for key in ("PASSOU", "FALHOU", "RELATADO", "PENDENTE", "NÃO APLICÁVEL")}
    print("[RESUMO] " + " ".join(f"{key}={value}" for key, value in counts.items()), file=out, flush=True)
    print("[RELEASE] PENDENTE — este log não publica tags; cole a saída no chat para revisão.", file=out, flush=True)
    return 1 if counts["FALHOU"] else 0
