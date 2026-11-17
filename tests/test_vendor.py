"""Vendored design-system and site-shell files must match vendor-manifest.json.

Run with: python3 -I -m unittest discover -s tests
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "vendor-manifest.json"
VENDORED = [ROOT / "site" / "vendor", ROOT / "site" / "js"]


class VendorTest(unittest.TestCase):
    def test_vendored_files_match_manifest(self):
        listed = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
        present = {
            p.relative_to(ROOT).as_posix()
            for base in VENDORED for p in base.rglob("*") if p.is_file()
        }
        self.assertEqual(sorted(present - set(listed)), [], "vendored file missing from the manifest")
        self.assertEqual(sorted(set(listed) - present), [], "manifest lists a missing file")
        for name, digest in sorted(listed.items()):
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, digest, f"{name} differs from its vendored source; never edit vendored files in place")


if __name__ == "__main__":
    unittest.main()
