"""Regression tests for the shared Make and LaTeX Workshop build entry point."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / ".vscode/settings.json").read_text())
ENTRIES = ("script", "build-paper", "build-slides", "vscode")
FAKE_ENGINE = r"""
import json
import os
from pathlib import Path
import sys

engine = Path(sys.argv[0]).name
log = Path("events.jsonl")
events = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
with log.open("a") as stream:
    stream.write(json.dumps({"engine": engine, "args": sys.argv[1:]}) + "\n")
if engine == "pbibtex":
    if os.environ.get("FAIL_BIB"):
        sys.exit(23)
    Path(sys.argv[1] + ".bbl").write_text(Path("../references.bib").read_text())
else:
    pass_number = 1 + sum(event["engine"] == "lualatex" for event in events)
    if str(pass_number) == os.environ.get("FAIL_LATEX_PASS"):
        sys.exit(19)
    source = Path(sys.argv[-1])
    output = Path(".")
    aux = output / (source.stem + ".aux")
    aux.write_text(r"\bibdata{../references}" if "bibliography" in source.read_text() else "")
    if os.environ.get("WITH_BACKREF"):
        (output / (source.stem + ".brf")).write_text("backreference data")
    bbl = output / (source.stem + ".bbl")
    if not os.environ.get("OMIT_PDF"):
        (output / (source.stem + ".pdf")).write_text(bbl.read_text() if bbl.exists() else "plain document")
"""


def command(entry: str, workspace: Path, source: Path) -> list[str]:
    if entry == "vscode":
        recipe = next(
            recipe
            for recipe in SETTINGS["latex-workshop.latex.recipes"]
            if recipe["name"] == SETTINGS["latex-workshop.latex.recipe.default"]
        )
        assert len(recipe["tools"]) == 1
        tool = next(
            tool
            for tool in SETTINGS["latex-workshop.latex.tools"]
            if tool["name"] == recipe["tools"][0]
        )
        return [tool["command"]] + [
            arg.replace("%WORKSPACE_FOLDER%", str(workspace)).replace(
                "%DOC_EXT%", str(source)
            )
            for arg in tool["args"]
        ]
    if entry in ("build-paper", "build-slides"):
        variable = "PAPER" if entry == "build-paper" else "SLIDES"
        return ["make", entry, f"{variable}={source.relative_to(workspace)}"]
    return [sys.executable, str(workspace / "scripts/build_latex.py"), str(source)]


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="latex regression ")
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name) / "workspace with spaces"
        (self.workspace / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / "scripts/build_latex.py", self.workspace / "scripts")
        shutil.copy(ROOT / "Makefile", self.workspace)
        self.source = self.workspace / "documents with spaces" / "paper's final.v2.tex"
        self.source.parent.mkdir()
        self.source.write_text(r"\bibliography{../references}")
        self.references = self.workspace / "references.bib"
        self.references.write_text("initial bibliography")
        self.pdf = self.source.with_suffix(".pdf")
        self.log = self.source.parent / "events.jsonl"
        bin_dir = self.workspace / "bin"
        bin_dir.mkdir()
        for engine in ("lualatex", "pbibtex"):
            executable = bin_dir / engine
            executable.write_text(f"#!{sys.executable}\n" + FAKE_ENGINE)
            executable.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
        }

    def run_build(self, entry: str, **environment: str) -> subprocess.CompletedProcess:
        self.log.unlink(missing_ok=True)
        return subprocess.run(
            command(entry, self.workspace, self.source),
            check=False,
            cwd=self.workspace if entry != "vscode" else self.source.parent,
            env={**self.env, **environment},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def engines(self) -> list[str]:
        return [
            json.loads(line)["engine"] for line in self.log.read_text().splitlines()
        ]

    def test_all_entries_build_and_refresh_bibliography_with_spaced_paths(self):
        for entry in ENTRIES:
            with self.subTest(entry=entry):
                for text in ("initial bibliography", "updated bibliography"):
                    self.references.write_text(text)
                    result = self.run_build(entry)
                    self.assertEqual(result.returncode, 0, result.stdout)
                    self.assertEqual(self.pdf.read_text(), text)
                    self.assertEqual(
                        self.engines(), ["lualatex", "pbibtex", "lualatex", "lualatex"]
                    )
                    self.assertTrue(self.source.with_suffix(".aux").is_file())

    def test_documents_without_bibliography_skip_pbibtex(self):
        self.source.write_text("plain document")
        for entry in ENTRIES:
            with self.subTest(entry=entry):
                result = self.run_build(entry)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertEqual(self.engines(), ["lualatex"] * 3)

    def test_backreferences_get_an_additional_latex_pass(self):
        for entry in ENTRIES:
            with self.subTest(entry=entry):
                result = self.run_build(entry, WITH_BACKREF="1")
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertEqual(
                    self.engines(),
                    ["lualatex", "pbibtex", "lualatex", "lualatex", "lualatex"],
                )

    def test_each_engine_failure_is_reported_and_preserves_published_pdf(self):
        failures = [
            ({"FAIL_LATEX_PASS": "1"}, ["lualatex"]),
            ({"FAIL_BIB": "1"}, ["lualatex", "pbibtex"]),
            ({"FAIL_LATEX_PASS": "2"}, ["lualatex", "pbibtex", "lualatex"]),
            ({"FAIL_LATEX_PASS": "3"}, ["lualatex", "pbibtex", "lualatex", "lualatex"]),
            (
                {"FAIL_LATEX_PASS": "4", "WITH_BACKREF": "1"},
                ["lualatex", "pbibtex", "lualatex", "lualatex", "lualatex"],
            ),
        ]
        for entry in ENTRIES:
            for environment, engines in failures:
                with self.subTest(entry=entry, environment=environment):
                    self.pdf.write_text("last successful PDF")
                    self.pdf.chmod(0o640)
                    result = self.run_build(entry, **environment)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.pdf.read_text(), "last successful PDF")
                    self.assertEqual(stat.S_IMODE(self.pdf.stat().st_mode), 0o640)
                    self.assertEqual(self.engines(), engines)

    def test_failed_first_build_removes_partial_pdf(self):
        for entry in ENTRIES:
            with self.subTest(entry=entry):
                result = self.run_build(entry, FAIL_LATEX_PASS="2")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.pdf.exists())

    def test_backup_copy_failure_is_reported_and_temporary_directory_is_removed(self):
        self.pdf.mkdir()
        for entry in ENTRIES:
            with self.subTest(entry=entry):
                result = self.run_build(entry)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(self.pdf.is_dir())
                self.assertEqual(list(self.source.parent.glob(".latex-backup-*")), [])

    def test_no_pages_cannot_republish_cached_pdf(self):
        for entry in ENTRIES:
            with self.subTest(entry=entry):
                self.pdf.write_text("last successful PDF")
                result = self.run_build(entry, OMIT_PDF="1")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.pdf.read_text(), "last successful PDF")

    def test_missing_source_is_reported_before_compiling(self):
        self.source.unlink()
        result = self.run_build("script")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_template_magic_comments_select_shared_recipe(self):
        recipe = SETTINGS["latex-workshop.latex.recipe.default"]
        for template in ("tex/paper/ecta_template.tex", "tex/slides/main.tex"):
            with self.subTest(template=template):
                lines = (ROOT / template).read_text().splitlines()
                self.assertIn(f"% !LW recipe = {recipe}", lines[:3])
                self.assertIn("% !TEX program = lualatex", lines[:3])


@unittest.skipUnless(
    all(shutil.which(tool) for tool in ("lualatex", "pbibtex", "pdftotext")),
    "real LuaLaTeX, pbibtex and pdftotext are required for the integration test",
)
class RealLatexTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="real latex ")
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        (self.workspace / "scripts").mkdir()
        shutil.copy(ROOT / "scripts/build_latex.py", self.workspace / "scripts")
        shutil.copy(ROOT / "Makefile", self.workspace)
        self.source = self.workspace / "documents with spaces" / "paper's final.v2.tex"
        self.source.parent.mkdir()

    def run_build(self, entry="script"):
        return subprocess.run(
            command(entry, self.workspace, self.source),
            check=False,
            cwd=self.workspace if entry != "vscode" else self.source.parent,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def test_relative_bibliography_is_refreshed_in_pdf(self):
        styles = self.workspace / "styles"
        styles.mkdir()
        shutil.copy(ROOT / "tex/paper/ecta-fullname.bst", styles)
        self.source.write_text(
            r"\documentclass{article}\usepackage{natbib}\begin{document}"
            r"\cite{test}\bibliographystyle{../styles/ecta-fullname}"
            r"\bibliography{../references}\end{document}"
        )
        for entry, title in (
            ("build-paper", "Firsttitle"),
            ("build-slides", "Secondtitle"),
            ("vscode", "Updatedtitle"),
        ):
            (self.workspace / "references.bib").write_text(
                "@article{test,author={A. Author},title={"
                + title
                + "},journal={Test},year={2026}}"
            )
            result = self.run_build(entry)
            self.assertEqual(result.returncode, 0, result.stdout)
            text = subprocess.check_output(
                ["pdftotext", str(self.source.with_suffix(".pdf")), "-"], text=True
            )
            self.assertIn(title, text)
            if entry == "vscode":
                self.assertNotIn("Firsttitle", text)
                self.assertNotIn("Secondtitle", text)

    def test_nofiles_document_without_aux_succeeds(self):
        self.source.write_text(
            r"\documentclass{article}\nofiles\begin{document}"
            r"Valid nofiles document.\end{document}"
        )
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(self.source.with_suffix(".pdf").is_file())
        self.assertFalse(self.source.with_suffix(".aux").exists())

    def test_clean_econsocart_build_resolves_page_backreferences(self):
        for filename in (
            "econsocart.cls",
            "econsocart.cfg",
            "fonts.latex",
            "ecta-fullname.bst",
        ):
            shutil.copy(ROOT / "tex/paper" / filename, self.source.parent)
        (self.workspace / "references.bib").write_text(
            "@article{test,author={A. Author},title={Test title},"
            "journal={Test},year={2026}}"
        )
        self.source.write_text(
            r"\documentclass[ecta,nameyear,draft]{econsocart}"
            r"\RequirePackage[colorlinks,pagebackref]{hyperref}"
            r"\begin{document}\section{Test}\cite{test}"
            r"\bibliographystyle{ecta-fullname}"
            r"\bibliography{../references}\end{document}"
        )
        result = self.run_build("build-paper")
        self.assertEqual(result.returncode, 0, result.stdout)
        text = subprocess.check_output(
            ["pdftotext", str(self.source.with_suffix(".pdf")), "-"], text=True
        )
        self.assertRegex(text, r"Test\.\s*\[1\]")
        final_log = self.source.with_suffix(".log").read_text()
        self.assertNotIn("Rerun to get bibliographical references right", final_log)

    def test_nested_include_keeps_auxiliary_paths(self):
        chapter = self.source.parent / "chapters" / "topic" / "one.tex"
        chapter.parent.mkdir(parents=True)
        chapter.write_text("Included chapter.")
        self.source.write_text(
            r"\documentclass{article}\begin{document}"
            r"\include{chapters/topic/one}\end{document}"
        )
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(self.source.with_suffix(".pdf").is_file())
        self.assertTrue(chapter.with_suffix(".aux").is_file())

    def test_invalid_latex_restores_previous_pdf(self):
        self.source.write_text(
            r"\documentclass{article}\begin{document}"
            r"\UndefinedCommand\end{document}"
        )
        pdf = self.source.with_suffix(".pdf")
        pdf.write_bytes(b"previous successful PDF")
        result = self.run_build("vscode")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(pdf.read_bytes(), b"previous successful PDF")


if __name__ == "__main__":
    unittest.main(verbosity=2)
