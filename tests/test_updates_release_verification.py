"""v0.8.1: no unverified GitHub release may become executable code."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from nexus.updates import releases
from nexus.updates.releases import UpdateError, parse_release, version_tuple


WHEEL = b"wheel-contents-under-test"
SHA = hashlib.sha256(WHEEL).hexdigest()
VERSION = "0.8.2"
NAME = f"nexus_core-{VERSION}-py3-none-any.whl"
URL = f"https://github.com/ricardogomesbarreto/Nexus-Core/releases/download/v{VERSION}/{NAME}"


def sample_release():
    return {
        "tag_name": "v" + VERSION,
        "draft": False,
        "prerelease": False,
        "assets": [{
            "name": NAME, "digest": "sha256:" + SHA,
            "size": len(WHEEL), "browser_download_url": URL,
            "state": "uploaded",
        }],
    }


def test_accept_only_newer_stable_wheel_with_official_url_and_hash():
    result = parse_release(json.dumps(sample_release()), "0.8.1")
    assert result.version == VERSION
    assert result.filename == NAME
    assert result.sha256 == SHA
    assert result.url == URL
    assert parse_release(json.dumps(sample_release()), VERSION) is None
    assert parse_release(json.dumps(sample_release()), "1.0.0") is None


@pytest.mark.parametrize("version", [
    "v0.8.1", "1.0", "01.2.3", "1.2.3-rc1", "1.2.3+dev",
    "", None, True, "2.3.4/../../x",
])
def test_versions_cannot_escape_strict_stable_semver(version):
    with pytest.raises(UpdateError):
        version_tuple(version)


@pytest.mark.parametrize("patch", [
    lambda p: p.update({"draft": True}),
    lambda p: p.update({"prerelease": True}),
    lambda p: p.update({"tag_name": "v0.8.2-rc.1"}),
    lambda p: p.update({"assets": []}),
    lambda p: p["assets"][0].update({"digest": None}),
    lambda p: p["assets"][0].update({"digest": "md5:" + SHA}),
    lambda p: p["assets"][0].update({"digest": "sha256:" + "0" * 64}),
    lambda p: p["assets"][0].update({"browser_download_url": "https://evil.test/setup.sh"}),
    lambda p: p["assets"][0].update({"size": 25 * 1024 * 1024 + 1}),
    lambda p: p["assets"][0].update({"size": -1}),
    lambda p: p["assets"][0].update({"size": True}),
    lambda p: p["assets"][0].update({"name": "source.tar.gz"}),
    lambda p: p["assets"].append(dict(p["assets"][0])),
])
def test_dangerous_release_metadata_rejected(patch):
    payload = sample_release()
    patch(payload)
    # Distinct bad digest is not itself detectable until file download,
    # but a syntactically valid alternative digest is legitimate metadata.
    if payload["assets"] and payload["assets"][0].get("digest") == "sha256:" + "0" * 64:
        assert parse_release(json.dumps(payload), "0.8.1").sha256 == "0" * 64
    else:
        with pytest.raises(UpdateError):
            parse_release(json.dumps(payload), "0.8.1")


def test_malformed_metadata_rejected():
    for text in ("", "not json", "[]", "{}", "a" * (releases.MAX_METADATA + 1)):
        with pytest.raises(UpdateError):
            parse_release(text, "0.8.1")


def test_verified_wheel_is_written_only_with_correct_sha_and_size(tmp_path, monkeypatch):
    asset = parse_release(json.dumps(sample_release()), "0.8.1")
    monkeypatch.setattr(releases, "_https_get", lambda url, *, maximum: WHEEL)
    path = releases.download_verified(asset, tmp_path)
    assert path.name == NAME
    assert path.read_bytes() == WHEEL
    assert not list(tmp_path.glob(".nexus-wheel-*"))


def test_bad_wheel_preserves_existing_file(tmp_path, monkeypatch):
    asset = parse_release(json.dumps(sample_release()), "0.8.1")
    target = tmp_path / NAME
    target.write_bytes(b"already verified existing wheel")
    monkeypatch.setattr(releases, "_https_get", lambda url, *, maximum: b"tampered" + WHEEL)
    with pytest.raises(UpdateError):
        releases.download_verified(asset, tmp_path)
    assert target.read_bytes() == b"already verified existing wheel"
    assert not list(tmp_path.glob(".nexus-wheel-*"))


def test_download_cannot_overwrite_symlink(tmp_path, monkeypatch):
    asset = parse_release(json.dumps(sample_release()), "0.8.1")
    important = tmp_path / "important"
    important.write_text("keep")
    (tmp_path / NAME).symlink_to(important)
    monkeypatch.setattr(releases, "_https_get", lambda url, *, maximum:
                        pytest.fail("must not download to symlink"))
    with pytest.raises(UpdateError):
        releases.download_verified(asset, tmp_path)
    assert important.read_text() == "keep"


def test_official_api_release_response_is_allowed(monkeypatch):
    class Fake:
        def geturl(self):
            return releases.API
        def read(self, n):
            return b'{"ok":true}'
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
    monkeypatch.setattr(releases, "urlopen", lambda *a, **kw: Fake())
    assert releases._https_get(releases.API, maximum=256) == b'{"ok":true}'


def test_official_api_cannot_redirect_to_download_cdn(monkeypatch):
    class Fake:
        def geturl(self):
            return "https://objects.githubusercontent.com/untrusted"
        def read(self, n):
            return b"trick"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
    monkeypatch.setattr(releases, "urlopen", lambda *a, **kw: Fake())
    with pytest.raises(UpdateError, match="Redirecionamento"):
        releases._https_get(releases.API, maximum=256)


def test_https_get_rejects_untrusted_redirect(monkeypatch):
    class Fake:
        def geturl(self):
            return "https://evil.test/untrusted"
        def read(self, n):
            return b"x"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
    monkeypatch.setattr(releases, "urlopen", lambda *a, **kw: Fake())
    with pytest.raises(UpdateError, match="Redirecionamento"):
        releases._https_get(releases.API, maximum=256)


def test_online_version_discovery_not_triggered_during_import(monkeypatch):
    monkeypatch.setattr(releases, "urlopen", lambda *a, **kw:
                        pytest.fail("module imports must be passive"))
    assert releases.REPOSITORY == "ricardogomesbarreto/Nexus-Core"
