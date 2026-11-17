"""Regression tests for tools/check_site.py (stdlib only).

Run with: python3 -I -m unittest discover -s tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[1] / "tools" / "check_site.py"


class RedactionTest(unittest.TestCase):
    def run_checker(self, page, terms):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            shutil.copy(CHECKER, root / "tools" / "check_site.py")
            (root / "index.html").write_text(page, encoding="utf-8")
            term_file = Path(tmp).parent / f"terms-{os.getpid()}.txt"
            term_file.write_text("\n".join(terms) + "\n", encoding="utf-8")
            try:
                env = dict(os.environ, FORBIDDEN_TERMS_FILE=str(term_file))
                return subprocess.run(
                    [sys.executable, "-I", str(root / "tools" / "check_site.py")],
                    capture_output=True, text=True, env=env, check=False)
            finally:
                term_file.unlink()

    def test_forbidden_term_fails_without_being_printed(self):
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title></head>'
                '<body><a href="https://Sensitive.Internal/status">x</a></body></html>')
        result = self.run_checker(page, ["sensitive.internal"])
        self.assertEqual(result.returncode, 1)
        combined = (result.stdout + result.stderr).casefold()
        self.assertNotIn("sensitive.internal", combined)
        self.assertIn("[withheld", result.stdout)

    def test_unicode_casefold_term_is_withheld(self):
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title></head>'
                '<body><a href="https://example.org/STRASSE/status">x</a></body></html>')
        result = self.run_checker(page, ["Straße"])
        self.assertEqual(result.returncode, 1)
        out = (result.stdout + result.stderr).casefold()
        self.assertNotIn("strasse", out)

    def test_backslash_term_in_diagnostic_is_withheld(self):
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title></head>'
                '<body><a href="#sec\\ret-anchor">x</a></body></html>')
        result = self.run_checker(page, ["sec\\ret"])
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("sec\\ret", result.stdout + result.stderr)

    def test_clean_page_passes(self):
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title></head>'
                '<body><a href="https://example.org/">x</a></body></html>')
        result = self.run_checker(page, ["sensitive.internal"])
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
