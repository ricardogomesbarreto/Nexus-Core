"""Safe, bounded ZIM reading through optional local zimdump executable."""
import os
from pathlib import Path
import sys

import pytest

import nexus.knowledge.zim_article as module
from nexus.knowledge.zim_article import LocalZimReader, ZimArticleError
from nexus.security.paths import PathSecurity


def fake_zimdump(tmp_path, text):
    command = tmp_path / "zimdump-fake"
    script = ("#!" + sys.executable + "\n"
              "import sys\n"
              "assert sys.argv[1] == 'show'\n"
              "assert sys.argv[2].startswith('--url=')\n"
              "assert sys.argv[3] == '--'\n"
              "assert open(sys.argv[4], 'rb').read(3) == b'ZIM'\n"
              "sys.stdout.write(" + repr(text) + ")\n")
    command.write_text(script, encoding="utf-8")
    command.chmod(0o700)
    return command


def make_reader(tmp_path):
    guard = PathSecurity()
    guard.home = tmp_path.resolve()
    guard.protected_paths = []
    return LocalZimReader(guard)


def test_zim_article_is_local_and_strips_active_html(tmp_path, monkeypatch):
    fake = fake_zimdump(tmp_path, "<html><script>do-not-run</script>"
                       "<body><h1>Planetas</h1><p>Júpiter é gigante.</p></body></html>")
    monkeypatch.setattr(module.shutil, "which",
                        lambda name: str(fake) if name == "zimdump" else None)
    archive = tmp_path / "enciclopedia.zim"
    archive.write_bytes(b"ZIM" + b"x" * 100)
    result = make_reader(tmp_path).read(archive, "A/Planetas.html")
    assert "Júpiter" in result and "Planetas" in result
    assert "do-not-run" not in result and "<script>" not in result


def test_zim_no_binary_does_not_run_service(tmp_path, monkeypatch):
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    with pytest.raises(ZimArticleError, match="zim-tools"):
        make_reader(tmp_path).read(tmp_path / "book.zim", "A/Article")


@pytest.mark.parametrize("article", [
    "", "../private", "A/../private", "A/../../private", "--help",
    "http://evil.com/a", "bad query", "a" * 201,
])
def test_zim_rejects_untrusted_article_args(tmp_path, monkeypatch, article):
    monkeypatch.setattr(module.shutil, "which",
                        lambda _: pytest.fail("invalid arguments must fail before binary"))
    with pytest.raises(ZimArticleError, match="URL"):
        make_reader(tmp_path).read(tmp_path / "book.zim", article)


def test_zim_symlink_is_refused(tmp_path, monkeypatch):
    fake = fake_zimdump(tmp_path, "test")
    monkeypatch.setattr(module.shutil, "which", lambda _: str(fake))
    target = tmp_path / "real.zim"
    target.write_bytes(b"ZIM" + b"x" * 100)
    linked = tmp_path / "alias.zim"
    linked.symlink_to(target)
    with pytest.raises(ZimArticleError, match="autorizado"):
        make_reader(tmp_path).read(linked, "A/Article")


def test_large_article_is_bounded(tmp_path, monkeypatch):
    fake = fake_zimdump(tmp_path, "A" * 130000)
    monkeypatch.setattr(module.shutil, "which", lambda _: str(fake))
    archive = tmp_path / "big.zim"
    archive.write_bytes(b"ZIM" + b"x" * 100)
    with pytest.raises(ZimArticleError, match="limite"):
        make_reader(tmp_path).read(archive, "A/Article")
