"""Quality Make targets reject broad inputs and preserve literal path arguments."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE_TARGETS = ("quality", "lint", "format", "format-check", "typecheck", "r-parse")
SPECIAL_NAMES = (
    "space name.py",
    "single'quote.py",
    'double"quote.py',
    "`touch BACKTICK_EXECUTED`.py",
    "$(touch SHELL_EXECUTED).py",
    "$(shell touch MAKE_EXECUTED).py",
    "-leading.py",
)


class QualityCommandTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="quality commands ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copy(ROOT / "Makefile", self.root)
        shutil.copy(ROOT / ".pre-commit-config.yaml", self.root)
        self.calls = self.root / "calls.json"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        pixi = self.bin / "pixi"
        pixi.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "Path(os.environ['PIXI_CALLS']).write_text(json.dumps(args))\n"
            "if os.environ.get('REAL_CHECKERS') == '1':\n"
            "    assert args[:3] == ['run', '-e', 'quality'], args\n"
            "    os.execvp(args[3], args[3:])\n"
            "sys.exit(int(os.environ.get('CHECKER_EXIT', '0')))\n"
        )
        pixi.chmod(0o755)
        self.environment = {
            **os.environ,
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "PIXI_CALLS": str(self.calls),
        }
        # Do not let an enclosing make invocation override this fixture's inputs.
        for name in ("MAKEFLAGS", "MFLAGS", "MAKELEVEL", "MAKEOVERRIDES"):
            self.environment.pop(name, None)

    def run_make(self, target, **variables):
        return subprocess.run(
            ["make", target, *[f"{key}={value}" for key, value in variables.items()]],
            cwd=self.root,
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def assert_no_side_effects(self):
        for marker in ("BACKTICK_EXECUTED", "SHELL_EXECUTED", "MAKE_EXECUTED"):
            self.assertFalse((self.root / marker).exists(), marker)

    def test_file_targets_reject_empty_missing_and_directory_before_tool(self):
        (self.root / "directory").mkdir()
        for target in FILE_TARGETS:
            for value in (None, "", "missing.py", "directory"):
                with self.subTest(target=target, value=value):
                    result = self.run_make(
                        target, **({} if value is None else {"FILE": value})
                    )
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertFalse(self.calls.exists())

    def test_file_targets_preserve_literal_paths_and_choose_environment(self):
        for name in SPECIAL_NAMES:
            (self.root / name).write_text("value = 1\n")
            for target in FILE_TARGETS:
                with self.subTest(target=target, name=name):
                    result = self.run_make(target, FILE=name)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    args = json.loads(self.calls.read_text())
                    self.assertEqual(args[-1], "./" + name)
                    self.assertEqual(args.count("./" + name), 1)
                    expected = (
                        ["run"] if target == "r-parse" else ["run", "-e", "quality"]
                    )
                    self.assertEqual(args[: len(expected)], expected)
                    self.assert_no_side_effects()

    def test_absolute_path_and_checker_failure_are_preserved(self):
        source = self.root / "absolute file.py"
        source.write_text("value = 1\n")
        self.environment["CHECKER_EXIT"] = "7"
        for target in FILE_TARGETS:
            with self.subTest(target=target):
                result = self.run_make(target, FILE=str(source))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(self.calls.read_text())[-1], str(source))

    def test_test_node_and_base_are_literal_not_recipe_or_make_expressions(self):
        value = '$(shell touch MAKE_EXECUTED)`touch BACKTICK_EXECUTED`"quote'
        for target, variable, expected in (
            ("test", "TEST", value + "::test_name"),
            ("quality-changed", "BASE", value),
        ):
            with self.subTest(target=target):
                result = self.run_make(target, **{variable: expected})
                self.assertEqual(result.returncode, 0, result.stderr)
                args = json.loads(self.calls.read_text())
                argument = "--from-ref=" + expected if variable == "BASE" else expected
                self.assertIn(argument, args)
                self.assert_no_side_effects()

    @unittest.skipUnless(
        shutil.which("ruff"), "Ruff is required for real checker tests"
    )
    def test_real_ruff_accepts_literal_paths_and_reports_a_defect(self):
        self.environment["REAL_CHECKERS"] = "1"
        for name in SPECIAL_NAMES:
            source = self.root / name
            source.write_text("value = 1\n")
            for target in ("lint", "format-check", "format"):
                with self.subTest(target=target, name=name):
                    result = self.run_make(target, FILE=name)
                    self.assertEqual(
                        result.returncode, 0, result.stdout + result.stderr
                    )
                    self.assertEqual(source.read_text(), "value = 1\n")
                    self.assert_no_side_effects()
        source.write_text("print(missing_quality_fixture)\n")
        result = self.run_make("lint", FILE=source.name)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("F821", result.stdout)

    @unittest.skipUnless(
        all(shutil.which(tool) for tool in ("pre-commit", "ruff", "shellcheck")),
        "pre-commit, Ruff and ShellCheck are required for real hook tests",
    )
    def test_real_hooks_accept_leading_dash_and_shell_without_extension(self):
        self.environment["REAL_CHECKERS"] = "1"
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        # Include the key hook: pre-commit normalizes ./-name back to -name.
        for name, source, hook in (
            ("-leading.py", "value = 1\n", "Ruff correctness"),
            (
                "-leading-shell",
                '#!/usr/bin/env bash\nprintf "%s\\n" "$1"\n',
                "ShellCheck",
            ),
        ):
            path = self.root / name
            path.write_text(source)
            path.chmod(0o755)
            result = self.run_make("quality", FILE=name)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            line = next(
                line for line in result.stdout.splitlines() if line.startswith(hook)
            )
            self.assertIn("Passed", line)


if __name__ == "__main__":
    unittest.main()
