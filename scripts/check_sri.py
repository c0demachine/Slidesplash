#!/usr/bin/env python3
"""Fail if any HTML file loads an external script or stylesheet without SRI.

Every <script src> and <link rel="stylesheet"|"preload"|"modulepreload" href>
that points off-site (http://, https:// or protocol-relative //) must have:
  - integrity="sha384-..." or "sha512-..."  (sha256 is accepted but discouraged)
  - crossorigin="anonymous"

Usage: python3 scripts/check_sri.py [file.html ...]
With no arguments, checks every .html file in the repo (skipping .git).
Exit code 0 = all good, 1 = problems found.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL = re.compile(r"^(https?:)?//", re.I)
INTEGRITY = re.compile(r"^sha(256|384|512)-[A-Za-z0-9+/]+={0,2}$")
LINK_RELS = {"stylesheet", "preload", "modulepreload"}


class Checker(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.errors = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "script":
            url = a.get("src", "")
        elif tag == "link" and LINK_RELS & set(a.get("rel", "").lower().split()):
            url = a.get("href", "")
        else:
            return
        if not EXTERNAL.match(url):
            return
        line = self.getpos()[0]
        where = f"{self.path}:{line}"
        if url.lower().startswith("http://"):
            self.errors.append(f"{where}: uses insecure http:// - use https:// ({url})")
        integrity = a.get("integrity", "").split()
        if not integrity:
            self.errors.append(f"{where}: missing integrity attribute ({url})")
        elif not all(INTEGRITY.match(h) for h in integrity):
            self.errors.append(f"{where}: malformed integrity value ({url})")
        if a.get("crossorigin", None) != "anonymous":
            self.errors.append(f'{where}: needs crossorigin="anonymous" ({url})')


def main(argv):
    files = [Path(p) for p in argv] or [
        p for p in ROOT.rglob("*.html") if ".git" not in p.parts
    ]
    errors = []
    for f in files:
        c = Checker(f.relative_to(ROOT) if f.is_relative_to(ROOT) else f)
        c.feed(f.read_text(encoding="utf-8"))
        errors += c.errors
    for e in errors:
        print(e, file=sys.stderr)
    if errors:
        print(
            f"\nSRI check failed ({len(errors)} problem(s)). "
            "See AGENTS.md > 'External resources' for how to fix.",
            file=sys.stderr,
        )
        return 1
    print(f"SRI check passed ({len(files)} file(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
