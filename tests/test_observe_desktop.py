"""The observer reports coarse metrics and never launches hardware in tests."""

import importlib.util
import io
from contextlib import redirect_stdout
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "observe_desktop.py"
    spec = importlib.util.spec_from_file_location("observe_desktop", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sample_logs_only_bounded_numbers():
    observer = _module()
    output = io.StringIO()
    with redirect_stdout(output):
        result = observer._sample(1, elapsed=7, inspect=lambda: {
            "memory": {"status": "available", "available_mib": 1870,
                       "swap_used_mib": 900, "private": "do not log"},
            "ollama": {"status": "available", "loaded_models": 1,
                       "name": "private model"}}, rss=lambda _: 320)
    assert result["nexus_rss_mib"] == 320
    assert output.getvalue().strip() == (
        "[MEDICAO-LOCAL] tempo_s=7 ram_disponivel_mib=1870 "
        "swap_usada_mib=900 modelos_carregados=1 nexus_rss_mib=320"
    )


def test_unknown_metrics_are_not_claimed_as_zero():
    observer = _module()
    output = io.StringIO()
    with redirect_stdout(output):
        observer._sample(1, elapsed=1, inspect=lambda: {
            "memory": {"status": "unavailable"},
            "ollama": {"status": "unavailable", "loaded_models": "secret"}},
            rss=lambda _: None)
    assert "modelos_carregados=indisponivel" in output.getvalue()
    assert "nexus_rss_mib=indisponivel" in output.getvalue()
    assert "secret" not in output.getvalue()


def test_process_tree_sums_descendant_rss_without_repeating_pid(monkeypatch):
    observer = _module()
    monkeypatch.setattr(observer, "_children", lambda pid: {11: [12, 13], 12: [13]}.get(pid, []))
    monkeypatch.setattr(observer, "_rss_kib", lambda pid: {11: 1024, 12: 2048, 13: 3072}.get(pid))
    assert observer._tree_rss_mib(11) == 6


def test_observer_launches_managed_session_and_reports_extrema(monkeypatch):
    observer = _module()
    launched = []

    class Process:
        pid = 123
        returncode = None

        def poll(self):
            return self.returncode

        def wait(self, timeout):
            self.returncode = 0
            return 0

    def popen(command, **kwargs):
        launched.append(command)
        return Process()

    monkeypatch.setattr(observer.subprocess, "Popen", popen)
    monkeypatch.setattr(observer, "_sample", lambda *args, **kwargs: {
        "ram_disponivel_mib": 1200, "swap_usada_mib": 450,
        "nexus_rss_mib": 300})
    output = io.StringIO()
    with redirect_stdout(output):
        assert observer.main(["--interval", "2"]) == 0
    assert launched == [["bash", str(observer.ROOT / "scripts/nexus_core_session.sh"), "desktop"]]
    assert "amostras=1 ram_disponivel_min_mib=1200" in output.getvalue()
    assert "swap_usada_max_mib=450 nexus_rss_max_mib=300" in output.getvalue()
