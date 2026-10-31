"""Render temporary documents to verify project and cell error handling."""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

QUARTO = shutil.which(os.environ.get("QUARTO", "quarto"))
JUPYTER_AVAILABLE = all(
    importlib.util.find_spec(module) is not None
    for module in ("nbclient", "nbformat", "ipykernel", "yaml")
)


@unittest.skipUnless(
    QUARTO and JUPYTER_AVAILABLE, "requires Quarto and Python Jupyter packages"
)
class QuartoExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="econ-quarto-test-")
        self.root = Path(self.temp.name)
        shutil.copyfile(
            Path(__file__).resolve().parents[1] / "_quarto.yml",
            self.root / "_quarto.yml",
        )
        self.env = {
            **os.environ,
            "QUARTO_PYTHON": sys.executable,
            "JUPYTER_CONFIG_DIR": str(self.root / "jupyter-config"),
            "JUPYTER_DATA_DIR": str(self.root / "jupyter-data"),
            "JUPYTER_RUNTIME_DIR": str(self.root / "jupyter-runtime"),
            "IPYTHONDIR": str(self.root / "ipython"),
            "XDG_CACHE_HOME": str(self.root / "cache"),
            "XDG_CONFIG_HOME": str(self.root / "config"),
            "XDG_DATA_HOME": str(self.root / "data"),
        }

    def tearDown(self):
        self.temp.cleanup()

    def render(self, cells):
        (self.root / "example.qmd").write_text(
            "---\ntitle: Error policy regression\njupyter: python3\n---\n\n" + cells,
            encoding="utf-8",
        )
        return subprocess.run(
            [QUARTO, "render", "example.qmd", "--to", "html", "--no-execute-daemon"],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    def test_default_exception_stops_before_later_cell_and_output(self):
        result = self.render(
            '```{python}\nraise RuntimeError("unexpected-cell-error")\n```\n\n'
            '```{python}\nfrom pathlib import Path\nPath("continued").touch()\n```\n'
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("unexpected-cell-error", result.stdout + result.stderr)
        self.assertFalse((self.root / "continued").exists())
        self.assertFalse((self.root / "example.html").exists())

    def test_explicit_cell_error_is_rendered_and_execution_continues(self):
        result = self.render(
            '```{python}\n#| error: true\nraise RuntimeError("intentional-cell-error")\n```\n\n'
            '```{python}\nfrom pathlib import Path\nPath("continued").touch()\nprint("continued-successfully")\n```\n'
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.root / "continued").exists())
        output = (self.root / "example.html").read_text(encoding="utf-8")
        self.assertIn("intentional-cell-error", output)
        self.assertIn("continued-successfully", output)

    def test_cell_override_does_not_allow_errors_in_other_cells(self):
        result = self.render(
            '```{python}\n#| error: true\nraise RuntimeError("intentional-cell-error")\n```\n\n'
            '```{python}\nraise RuntimeError("later-unexpected-error")\n```\n\n'
            '```{python}\nfrom pathlib import Path\nPath("continued").touch()\n```\n'
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("later-unexpected-error", result.stdout + result.stderr)
        self.assertFalse((self.root / "continued").exists())
        self.assertFalse((self.root / "example.html").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
