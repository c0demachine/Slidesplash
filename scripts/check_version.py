#!/usr/bin/env python3
"""Fail if the game changed but its version number in index.html didn't go up.

The version is  id="gameVersion">Version MAJOR.MINOR.PATCH<  (shown in Settings),
the standard "semantic versioning" style:
  PATCH + 1  for a small fix or tweak            (1.4.1 -> 1.4.2)
  MINOR + 1  for a new feature, PATCH back to 0  (1.4.2 -> 1.5.0)
  MAJOR + 1  for a huge overhaul, rest back to 0 (1.5.0 -> 2.0.0)
If index.html or music.mp3 differ from the base branch (main by default), the
version must be exactly one of those three steps past the base's version.

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
VERSION = re.compile(r'id="gameVersion">Version (\d+)\.(\d+)\.(\d+)<')


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def version_of(html):
    m = VERSION.search(html or "")
    return tuple(int(g) for g in m.groups()) if m else None


def show(v):
    return ".".join(map(str, v))


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
    old = version_of(git("show", f"{base}:index.html").stdout)

    if new is None:
        print('index.html: missing the version line  id="gameVersion">Version MAJOR.MINOR.PATCH<  in Settings.')
        return 1
    if old is not None:
        ma, mi, pa = old
        steps = {"a small fix": (ma, mi, pa + 1), "a new feature": (ma, mi + 1, 0),
                 "a huge overhaul (ask the owner first)": (ma + 1, 0, 0)}
        if new not in steps.values():
            options = ", ".join(f"{show(v)} for {k}" for k, v in steps.items())
            print(f"index.html: the game changed, so the version must be one step past "
                  f"{base}'s {show(old)}: {options} (it says {show(new)}).")
            return 1
    print(f"Version check passed (Version {show(new)}, {base} has "
          f"{show(old) if old else 'none'}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
