#!/usr/bin/env python3
"""Check the offline site without third-party packages or network requests."""

import html
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".site-check", "__pycache__"}
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", re.I)
CSS_IMPORT = re.compile(r"@import\s+(?:url\(\s*)?['\"]?([^'\"\s;)]+)", re.I)


class Page(HTMLParser):
    """Parse explicit HTML/SVG nesting and collect linkable IDs and resources."""

    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.links = []
        self.errors = []
        self.stack = []
        self.tags = set()
        self.doctype = False
        self.style_depth = 0
        self.css = []

    def error(self, message):
        self.errors.append(f"{self.path.relative_to(ROOT)}:{self.getpos()[0]}: {message}")

    def handle_decl(self, decl):
        if decl.casefold() == "doctype html":
            self.doctype = True

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)
        values = dict(attrs)
        if len(values) != len(attrs):
            self.error(f"duplicate attribute on <{tag}>")
        for key, value in attrs:
            if value is None:
                continue
            if key == "id":
                if value in self.ids:
                    self.error(f"duplicate id '{value}'")
                self.ids.add(value)
            if key in {"href", "src", "xlink:href", "poster"}:
                self.links.append((value, self.getpos()[0], tag, key))
            if key == "srcset":
                # Each comma-separated candidate starts with its resource URL.
                for candidate in value.split(","):
                    fields = candidate.split()
                    if fields:
                        self.links.append((fields[0], self.getpos()[0], tag, key))
            if key == "style":
                self.css.append((value, self.getpos()[0]))
        if tag == "base":
            self.error("<base> is unsupported; use ordinary relative links")
        if tag == "link" and "stylesheet" in values.get("rel", "").lower().split():
            href = values.get("href", "")
            if is_external(href):
                self.error("external stylesheet load")
        if tag == "script" and is_external(values.get("src", "")):
            self.error("external script load")
        if tag == "style":
            self.style_depth += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.error(f"unexpected </{tag}>; expected {self.stack[-1] if self.stack else 'no closing tag'}")
            return
        self.stack.pop()
        if tag == "style":
            self.style_depth -= 1

    def handle_data(self, data):
        if self.style_depth:
            self.css.append((data, self.getpos()[0]))

    def finish(self):
        self.close()
        if self.stack:
            self.error("unclosed elements: " + ", ".join(self.stack))
        if not self.doctype:
            self.error("missing HTML doctype")
        if not {"html", "head", "title", "body"}.issubset(self.tags):
            self.error("missing html/head/title/body structure")
        for css, line in self.css:
            for match in list(CSS_URL.finditer(css)) + list(CSS_IMPORT.finditer(css)):
                value = match.group(1).strip()
                if is_external(value):
                    self.errors.append(f"{self.path.relative_to(ROOT)}:{line}: external CSS resource")
                else:
                    self.links.append((value, line, "style", "url"))


def is_external(value):
    parsed = urlsplit(value)
    return bool(parsed.scheme or parsed.netloc)


def files_in_repo():
    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not (Path(directory) / d).is_symlink())
        for name in sorted(names):
            path = Path(directory) / name
            if not path.is_symlink():
                yield path


def main():
    errors = []
    files = list(files_in_repo())
    pages = {}
    for path in files:
        if path.suffix.lower() not in {".html", ".htm"}:
            continue
        page = Page(path)
        try:
            page.feed(path.read_text(encoding="utf-8"))
            page.finish()
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: parse failed ({type(exc).__name__})")
        pages[path.resolve()] = page
        errors.extend(page.errors)
    if not pages:
        errors.append("No HTML pages found")

    external = set()
    internal_count = 0
    for path, page in pages.items():
        for value, line, tag, attr in page.links:
            location = f"{path.relative_to(ROOT)}:{line}"
            try:
                parts = urlsplit(value)
            except ValueError:
                errors.append(f"{location}: invalid URL")
                continue
            if parts.scheme or parts.netloc:
                external.add(value)
                if parts.scheme.lower() in {"javascript", "file"}:
                    errors.append(f"{location}: disallowed URL scheme")
                # Offline means resources cannot require a remote network load.
                if (tag != "a" or attr != "href") and parts.scheme.lower() != "data":
                    errors.append(f"{location}: external resource load")
                continue
            internal_count += 1
            target = (ROOT / unquote(parts.path).lstrip("/")) if parts.path.startswith("/") else (path.parent / unquote(parts.path))
            if not parts.path:
                target = path
            target = target.resolve()
            if not target.is_relative_to(ROOT):
                errors.append(f"{location}: local target escapes site root")
                continue
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                errors.append(f"{location}: missing local target '{value}'")
                continue
            if parts.fragment:
                fragment = unquote(parts.fragment)
                if target in pages:
                    ids = pages[target].ids
                elif target.suffix.lower() == ".svg":
                    try:
                        ids = {e.attrib["id"] for e in ET.parse(target).iter() if "id" in e.attrib}
                    except (ET.ParseError, OSError):
                        errors.append(f"{location}: cannot parse linked SVG")
                        continue
                else:
                    errors.append(f"{location}: cannot verify fragment in non-HTML/SVG target")
                    continue
                if fragment not in ids:
                    errors.append(f"{location}: missing anchor '{value}'")

    forbidden_path = os.environ.get("FORBIDDEN_TERMS_FILE")
    term_count = 0
    terms = []
    if forbidden_path is not None:
        try:
            term_file = Path(forbidden_path).expanduser().resolve()
            terms = [line.strip().casefold() for line in term_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            term_count = len(terms)
        except (OSError, UnicodeError, ValueError):
            errors.append("FORBIDDEN_TERMS_FILE could not be read as UTF-8")
            terms = []
            term_file = None
        for path in files:
            if path.resolve() == term_file:
                continue
            try:
                raw = path.read_bytes()
                if b"\x00" in raw:
                    continue
                content = raw.decode("utf-8")
            except UnicodeError:
                continue
            except OSError:
                errors.append(f"{path.relative_to(ROOT)}: cannot read for forbidden-term scan")
                continue
            # Decode character references so markup cannot hide a forbidden term.
            variants = [content]
            if path.suffix.lower() in {".html", ".htm", ".svg"}:
                variants.append(html.unescape(content))
                variants.append(re.sub(r"<[^>]*>", "", html.unescape(content)))
            seen = set()
            for variant in variants:
                for line_number, line in enumerate(variant.splitlines(), 1):
                    for rule, term in enumerate(terms, 1):
                        if term in line.casefold() and rule not in seen:
                            errors.append(f"{path.relative_to(ROOT)}:{line_number}: forbidden term matched rule {rule}")
                            seen.add(rule)

    print(f"HTML pages parsed: {len(pages)}")
    print(f"Internal references checked: {internal_count}")
    print("External script/stylesheet loads: " + ("FAILED (see errors)" if any("external" in e for e in errors) else "none"))
    print(f"Forbidden-term scan: {term_count} rules" if forbidden_path is not None else "Forbidden-term scan: not requested")
    def redact(text):
        """Withhold any output line that would reveal a forbidden term.

        Matching uses the same casefold() semantics as detection, so Unicode
        case expansions (for example a sharp s) cannot slip through.
        """
        folded = text.casefold()
        if any(term in folded for term in terms):
            return "[withheld: contains a forbidden term]"
        return text

    print(f"External links ({len(external)}; listed only, not fetched):")
    for value in sorted(external):
        print(f"  {redact(value)}")
    if errors:
        print(f"FAIL: {len(errors)} error(s)", file=sys.stderr)
        for error in errors:
            print(f"  {redact(error)}", file=sys.stderr)
        return 1
    print("PASS: site checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
