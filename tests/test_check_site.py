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
            (root / "site").mkdir()
            (root / "site" / "index.html").write_text(page, encoding="utf-8")
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


class LinkRulesTest(unittest.TestCase):
    def run_checker(self, body, head="", files=None):
        """Run the checker on a temporary repository whose page is site/index.html.

        `files` maps extra paths (relative to the repository root) to text.
        """
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title>'
                + head + '</head><body>' + body + '</body></html>')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            shutil.copy(CHECKER, root / "tools" / "check_site.py")
            (root / "site").mkdir()
            (root / "site" / "index.html").write_text(page, encoding="utf-8")
            (root / "README.md").write_text("# not published\n", encoding="utf-8")
            for name, text in (files or {}).items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-I", str(root / "tools" / "check_site.py")],
                capture_output=True, text=True, check=False)

    def test_root_relative_page_link_is_listed_not_resolved(self):
        result = self.run_checker('<a href="/team/">Team</a>')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Host-site links", result.stdout)
        self.assertIn("/team/", result.stdout)

    def test_root_relative_resource_load_fails(self):
        result = self.run_checker('<script src="/js/app.js"></script>')
        self.assertEqual(result.returncode, 1)
        self.assertIn("root-relative resource load", result.stderr)

    def test_canonical_link_is_a_reference(self):
        result = self.run_checker('', '<link rel="canonical" href="https://example.org/page/">')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_external_stylesheet_still_fails(self):
        result = self.run_checker('', '<link rel="stylesheet" href="https://example.org/a.css">')
        self.assertEqual(result.returncode, 1)
        self.assertIn("external stylesheet load", result.stderr)

    def test_missing_relative_target_still_fails(self):
        result = self.run_checker('<a href="missing.html">x</a>')
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing local target", result.stderr)

    def test_link_outside_published_site_fails(self):
        result = self.run_checker('<a href="../README.md">readme</a>')
        self.assertEqual(result.returncode, 1)
        self.assertIn("escapes the published site/ folder", result.stderr)

    STYLE = '<link rel="stylesheet" href="site.css">'

    def test_external_import_in_stylesheet_fails(self):
        result = self.run_checker('', self.STYLE, {"site/site.css": '@import url("https://example.org/x.css");\n'})
        self.assertEqual(result.returncode, 1)
        self.assertIn("site/site.css:1: external CSS resource", result.stderr)

    def test_root_relative_url_in_stylesheet_fails(self):
        result = self.run_checker('', self.STYLE, {"site/site.css": "a {}\nb { background: url(/images/x.png); }\n"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("site/site.css:2: root-relative resource load", result.stderr)

    def test_missing_font_in_nested_stylesheet_fails(self):
        css = "@font-face { font-family: X; src: url('missing.woff2') format('woff2'); }\n"
        result = self.run_checker('', '<link rel="stylesheet" href="vendor/fonts.css">', {"site/vendor/fonts.css": css})
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing local target 'missing.woff2'", result.stderr)

    def test_stylesheet_urls_resolve_from_their_own_folder(self):
        css = "/* url(ignored-in-comment.png) */\n@font-face { font-family: X; src: url('x.woff2#hint') format('woff2'); }\n.i { background: url(data:image/png;base64,AAAA); }\n"
        result = self.run_checker('', '<link rel="stylesheet" href="vendor/fonts.css">',
                                  {"site/vendor/fonts.css": css, "site/vendor/x.woff2": "font"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Stylesheets checked: 1", result.stdout)


if __name__ == "__main__":
    unittest.main()
