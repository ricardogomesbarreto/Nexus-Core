"""Contract discovery tests use disposable CLI stand-ins, never source ZIP code."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nexus.tools.craft_capabilities import (
    CONTRACTS, _read_command, inspect_craft_capabilities,
)


class CraftCapabilitiesTests(unittest.TestCase):
    def test_missing_is_not_accepted(self):
        result = inspect_craft_capabilities(find_binary=lambda _: None)
        self.assertEqual([tool["status"] for tool in result["tools"]], ["missing"] * 3)
        self.assertFalse(result["real_operation_tested"])
        self.assertFalse(result["external_network_used"])

    def test_version_and_whole_command_match(self):
        def query(binary, flag):
            contract = next(x for x in CONTRACTS if x.binary == binary)
            if flag == "--version":
                return f"{binary} {contract.snapshot_version}\nWeb: https://example.invalid"
            return "\n".join(f"{binary} {name} <file>" for name in contract.commands)

        result = inspect_craft_capabilities(find_binary=lambda name: name, query=query)
        self.assertEqual([x["status"] for x in result["tools"]], ["available"] * 3)
        self.assertNotIn("https://", json.dumps(result))
        self.assertNotIn("/home/", json.dumps(result))

    def test_incompatible_and_degraded_are_distinct(self):
        def query(binary, flag):
            if flag == "--version":
                return f"{binary} 99.0.0" if binary == "photocraft-cli" else f"{binary} 0.7.0"
            if binary == "pdfcraft-cli":
                return None
            return f"{binary} conversion <file>\n{binary} info <file>"

        result = inspect_craft_capabilities(find_binary=lambda name: name, query=query)
        self.assertEqual([x["status"] for x in result["tools"]],
                         ["incompatible", "degraded", "incompatible"])
        self.assertEqual(result["tools"][1]["advertised_commands"], ["info"])

    def test_real_probe_limits_output_and_kills_hanging_process(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "slow-cli"
            script.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(5)\n")
            script.chmod(0o700)
            with patch("nexus.tools.craft_capabilities._TIMEOUT", 0.15):
                self.assertIsNone(_read_command(str(script), "--help"))
            script.write_text("#!/usr/bin/env python3\nprint('x' * 65537)\n")
            self.assertIsNone(_read_command(str(script), "--help"))

    def test_cli_isolated_from_app_and_maintenance(self):
        if importlib.util.find_spec("psycopg") is None:
            self.skipTest("psycopg presente apenas no ambiente de CI/instalação")
        from nexus import main
        from nexus.updates.launcher import should_run_maintenance

        self.assertFalse(should_run_maintenance(["--craft-capabilities"]))
        output = io.StringIO()
        with patch.object(main, "build_application", side_effect=AssertionError("startup")), \
             patch("nexus.tools.craft_capabilities.inspect_craft_capabilities",
                   return_value={"schema": "nexus.craft-capabilities.v1"}), \
             contextlib.redirect_stdout(output):
            main.cli(["--craft-capabilities"])
        self.assertEqual(json.loads(output.getvalue())["schema"], "nexus.craft-capabilities.v1")


if __name__ == "__main__":
    unittest.main()
