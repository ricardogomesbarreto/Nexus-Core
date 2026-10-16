"""The guided installer prepares local assets without touching existing ones."""

from dataclasses import replace
from io import BytesIO
from pathlib import Path
import tarfile
import zipfile

import pytest

from nexus.config.settings import settings
from scripts import install_linux, local_models


class Source(BytesIO):
    def __init__(self, content, url=local_models.VOSK_URL):
        super().__init__(content)
        self.url = url

    def geturl(self):
        return self.url


def test_official_vosk_archive_is_installed_and_existing_copy_is_preserved(tmp_path):
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as zipped:
        zipped.writestr(local_models.VOSK_NAME + "/am/final.mdl", b"model")
        zipped.writestr(local_models.VOSK_NAME + "/conf/model.conf", b"config")
    target = tmp_path / "voice" / local_models.VOSK_NAME
    calls = []

    def open_archive(url, *, timeout):
        calls.append(url)
        return Source(stream.getvalue())

    local_models.install_portuguese_voice_model(target, opener=open_archive)
    assert (target / "am" / "final.mdl").read_bytes() == b"model"
    local_models.install_portuguese_voice_model(
        target, opener=lambda *a, **k: pytest.fail("existing model must not be fetched")
    )
    assert calls == [local_models.VOSK_URL]


@pytest.mark.parametrize("filename,url", [
    (local_models.VOSK_NAME + "/../escape", local_models.VOSK_URL),
    ("/absolute", local_models.VOSK_URL),
    (local_models.VOSK_NAME + "/am/final.mdl", "http://example.com/model.zip"),
])
def test_vosk_download_rejects_unsafe_archive_or_redirect(tmp_path, filename, url):
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as zipped:
        zipped.writestr(filename, b"model")
    target = tmp_path / "voice" / local_models.VOSK_NAME
    with pytest.raises(ValueError):
        local_models.install_portuguese_voice_model(
            target, opener=lambda *a, **k: Source(stream.getvalue(), url)
        )
    assert not target.exists()
    assert not (tmp_path / "escape").exists()


def test_missing_voice_asset_is_offered_during_guided_install(tmp_path, monkeypatch):
    import nexus.config.settings as config
    import nexus.platforms.preflight as preflight
    monkeypatch.setattr(config, "settings", replace(settings, data_dir=tmp_path,
                                                     voice_model_path=None))
    monkeypatch.setattr(install_linux.shutil, "which", lambda cmd: "/usr/bin/ollama")
    monkeypatch.setattr(preflight, "ollama_model_probe",
                        lambda **k: {"installed": True, "status": "model_listed"})
    questions = []
    monkeypatch.setattr(install_linux, "confirm",
                        lambda question: questions.append(question) or True)

    def download(destination):
        (destination / "am").mkdir(parents=True)
        (destination / "am" / "final.mdl").write_text("model")

    monkeypatch.setattr(local_models, "install_portuguese_voice_model", download)
    assert install_linux.prepare_local_models()
    assert len(questions) == 1 and "Vosk" in questions[0]
    assert install_linux.prepare_local_models()
    assert len(questions) == 1


def test_missing_ollama_model_is_pulled_and_verified(tmp_path, monkeypatch):
    import nexus.config.settings as config
    import nexus.platforms.preflight as preflight
    model = tmp_path / "voice" / local_models.VOSK_NAME
    model.mkdir(parents=True)
    monkeypatch.setattr(config, "settings", replace(settings, data_dir=tmp_path,
                                                     voice_model_path=None))
    monkeypatch.setattr(install_linux.shutil, "which", lambda cmd: "/usr/bin/ollama")
    status = {"installed": False, "status": "model_not_listed"}
    monkeypatch.setattr(preflight, "ollama_model_probe", lambda **k: status.copy())
    monkeypatch.setattr(install_linux, "confirm", lambda _: True)
    calls = []

    def pull(args, **kwargs):
        calls.append((args, kwargs))
        status.update(installed=True, status="model_listed")

    monkeypatch.setattr(install_linux, "_run", pull)
    assert install_linux.prepare_local_models()
    assert calls[0][0] == ["/usr/bin/ollama", "pull", settings.local_model_name]
    assert calls[0][1]["progress"] is True


def test_vendor_ollama_archive_installs_without_root(tmp_path, monkeypatch):
    monkeypatch.setattr(local_models.platform, "machine", lambda: "x86_64")
    archive = BytesIO()
    # The downloader only sees compressed bytes; fake zstd expands a tar stream.
    tar = BytesIO()
    with tarfile.open(fileobj=tar, mode="w") as output:
        data = b"local ollama"
        info = tarfile.TarInfo("bin/ollama")
        info.size = len(data)
        output.addfile(info, BytesIO(data))

    def unpack(args, *, stdout, **kwargs):
        assert args[0] == "zstd"
        stdout.write(tar.getvalue())

    monkeypatch.setattr(local_models.subprocess, "run", unpack)
    target = tmp_path / "runtime" / "ollama"
    binary = local_models.install_ollama_runtime(
        target, opener=lambda url, **k: Source(archive.getvalue(), url)
    )
    assert binary.read_bytes() == b"local ollama"
    assert binary.stat().st_mode & 0o111


def test_neural_voice_model_downloads_fixed_pair_atomically(tmp_path):
    destination = tmp_path / "piper" / (local_models.PIPER_VOICE + ".onnx")
    calls = []

    def open_voice(url, *, timeout):
        calls.append(url)
        body = (b'{"language":{"code":"pt_BR"}}' if url.endswith(".json")
                else b"x" * 1_100_000)
        return Source(body, url)

    local_models.install_piper_voice(destination, opener=open_voice)
    assert destination.stat().st_size == 1_100_000
    assert destination.with_suffix(".onnx.json").is_file()
    local_models.install_piper_voice(destination, opener=lambda *a, **k: pytest.fail())
    assert calls == [local_models.PIPER_VOICE_URL, local_models.PIPER_VOICE_URL + ".json"]


def test_neural_voice_rejects_wrong_language_without_installing(tmp_path):
    destination = tmp_path / "piper" / (local_models.PIPER_VOICE + ".onnx")

    def open_voice(url, *, timeout):
        body = (b'{"language":{"code":"en_US"}}' if url.endswith(".json")
                else b"x" * 1_100_000)
        return Source(body, url)

    with pytest.raises(ValueError, match="inválida"):
        local_models.install_piper_voice(destination, opener=open_voice)
    assert not destination.exists()


def test_female_voice_package_is_installed_only_after_confirmation(monkeypatch):
    from nexus.voice.local import LocalSpeaker
    available = {"value": False}
    monkeypatch.setattr(LocalSpeaker, "female_voice_ready",
                        staticmethod(lambda: available["value"]))
    monkeypatch.setattr(install_linux, "installed", lambda name: True)
    calls = []
    monkeypatch.setattr(install_linux, "confirm", lambda question: False)
    monkeypatch.setattr(install_linux, "_run", lambda *a, **k: calls.append(a))
    assert install_linux.prepare_female_voice() is False
    assert calls == []
    monkeypatch.setattr(install_linux, "confirm", lambda question: True)

    def install(args, **kwargs):
        calls.append(args)
        available["value"] = True

    monkeypatch.setattr(install_linux, "_run", install)
    assert install_linux.prepare_female_voice() is True
    assert calls == [["sudo", "apt-get", "install", "-y", "rhvoice",
                      "rhvoice-brazilian-portuguese"]]
