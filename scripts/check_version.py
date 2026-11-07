#!/usr/bin/env python3
"""Fail if the game changed but its version number in index.html didn't go up.

The version is  id="gameVersion">Version T.B.S<  (shown in Settings):
  T = total updates ever (the first release counts as 1)
  B = how many of them were big changes (new features, modes, screens)
  S = how many were small changes (fixes, tweaks, wording)
so T always equals 1 + B + S. If index.html or music.mp3 differ from the base
branch (main by default), the version must be one update ahead of the base:
T + 1, and either B + 1 or S + 1.

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
        print('index.html: missing the version line  id="gameVersion">Version T.B.S<  in Settings.')
        return 1
    t, b, s = new
    if t != 1 + b + s:
        print(f"index.html: Version {show(new)} doesn't add up: the first number must be "
              f"1 + the other two ({1 + b + s}).")
        return 1
    if old is not None:
        ot, ob, os_ = old
        big, small = (ot + 1, ob + 1, os_), (ot + 1, ob, os_ + 1)
        if new not in (big, small):
            print(f"index.html: the game changed, so the version must be one update past "
                  f"{base}'s {show(old)}: Version {show(big)} for a big change or "
                  f"{show(small)} for a small one (it says {show(new)}).")
            return 1
    print(f"Version check passed (Version {show(new)}, {base} has "
          f"{show(old) if old else 'none'}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
