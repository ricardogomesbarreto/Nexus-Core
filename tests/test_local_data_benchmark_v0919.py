"""Bounded local transformations and benchmark contract."""
import hashlib
import json
import subprocess
import sys

import pytest

from nexus.platforms.benchmark import benchmark_local
from nexus.tools.data_local import MAX_BYTES, transform_recipe, transform_text
from nexus.updates.launcher import should_run_maintenance


def test_hashes_and_encodings_match_standard_vectors():
    assert transform_text("sha512", b"abc") == hashlib.sha512(b"abc").hexdigest()
    assert transform_text("sha3-256", b"abc") == hashlib.sha3_256(b"abc").hexdigest()
    assert transform_text("blake2b-256", b"abc") == hashlib.blake2b(b"abc", digest_size=32).hexdigest()
    assert transform_text("base32-decode", b"jbswy3dp") == "Hello"
    assert transform_text("base32-encode", b"Hello") == "JBSWY3DP"
    assert transform_text("rot13", "Olá Abc".encode()) == "Byá Nop"
    assert json.loads(transform_text("json-pretty", b'{"a":1}')) == {"a": 1}
    assert transform_text("json-minify", b'{ "a" : 1 }') == '{"a":1}'


def test_recipe_bounds_each_intermediate_and_rejects_bad_input():
    assert transform_recipe(["base64-encode", "base64-decode"], "Olá".encode()) == "Olá"
    with pytest.raises(ValueError, match="8 operações"):
        transform_recipe(["sha256"] * 9, b"a")
    with pytest.raises(ValueError, match="64 KiB"):
        transform_recipe(["hex-encode"], b"a" * MAX_BYTES)
    with pytest.raises(ValueError):
        transform_recipe(["shell"], b"hello")
    with pytest.raises(ValueError, match="incompleta"):
        transform_text("url-decode", b"a%ZZ")
    with pytest.raises(ValueError):
        transform_text("json-minify", b"{")
    with pytest.raises(ValueError):
        transform_text("json-minify", b'{"x":NaN}')


def test_recipe_cli_stays_local():
    process = subprocess.run(
        [sys.executable, "-m", "nexus.main", "--data-recipe", "base64-encode,base64-decode"],
        input=b"hello", capture_output=True, timeout=10,
    )
    assert process.returncode == 0, process.stderr
    assert process.stdout == b"hello\n"
    assert not should_run_maintenance(["--data-recipe", "sha256"])


def test_benchmark_cpu_memory_is_opt_in_and_bounded():
    with pytest.raises(ValueError):
        benchmark_local(20000)
    result = benchmark_local(200)
    assert result["schema"] == "nexus.benchmark.v2"
    assert result["cpu_hash_mib_per_s"] > 0
    assert result["memory_copy_mib_per_s"] > 0
    assert result["peak_working_buffer_mib"] == 8
    assert result["external_network_used"] is False
    assert result["disk_written"] is False
    assert not should_run_maintenance(["--benchmark-full"])
