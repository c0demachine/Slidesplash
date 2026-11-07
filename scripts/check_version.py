#!/usr/bin/env python3
"""Fail if the game changed but its version number in index.html didn't go up.

The version is the number in  id="gameVersion">Version N<  (shown in Settings).
If index.html or music.mp3 differ from the base branch (main by default), N must
be bigger than the base branch's N, so every change that ships gets a new number.

Usage:
  python3 scripts/check_version.py --staged   # pre-commit: what you're about to commit
  python3 scripts/check_version.py [BASE]     # CI: the checked-out files (BASE default origin/main)
Exit code 0 = all good, 1 = version needs bumping.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME_FILES = ["index.html", "music.mp3"]
VERSION = re.compile(r'id="gameVersion">Version (\d+)<')


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def version_of(html):
    m = VERSION.search(html or "")
    return int(m.group(1)) if m else None


def main():
    args = sys.argv[1:]
    staged = "--staged" in args
    args = [a for a in args if a != "--staged"]
    base = args[0] if args else "origin/main"

    if git("rev-parse", "--verify", "--quiet", base + "^{commit}").returncode != 0:
        print(f"Version check skipped: can't find {base} (run: git fetch origin main).")
        return 0

    diff = git("diff", "--quiet", *(["--cached"] if staged else []), base, "--", *GAME_FILES)
    if diff.returncode == 0:
        return 0  # game files same as base: nothing to bump

    if staged:
        new_html = git("show", ":index.html").stdout
    else:
        new_html = (ROOT / "index.html").read_text(encoding="utf-8")
    new = version_of(new_html)
    old = version_of(git("show", f"{base}:index.html").stdout) or 0

    if new is None:
        print('index.html: missing the version line  id="gameVersion">Version N<  in Settings.')
        return 1
    if new <= old:
        print(f"index.html: the game changed but the version is still {new} "
              f"({base} has {old}). Change it to Version {old + 1}.")
        return 1
    print(f"Version check passed (Version {new}, {base} has {old}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
