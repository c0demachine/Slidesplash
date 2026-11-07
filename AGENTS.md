# AGENTS.md

Rules for any AI coding agent (and human) working on **Slide Splash**, a
browser game shipped as a single static page: `index.html` (all HTML, CSS and
JS inline) plus `music.mp3`. It uses three.js r128 from cdnjs. There is no
build step and no package manager.

The owner is not an experienced web developer. Agents must explain what they
changed and why in plain language, flag risks, and never assume the owner
will catch a mistake in review.

## Hard rules (enforced automatically)

These are checked by `scripts/check_sri.py` and `scripts/check_version.py`, which run in the git
pre-commit hook and in GitHub Actions (`.github/workflows/checks.yml`).
A failing check means **do not commit**: fix the cause, never bypass it
(no `git commit --no-verify`, no deleting or weakening the check).

### External resources must have Subresource Integrity (SRI)

Every `<script src>` and `<link rel="stylesheet" | "preload" | "modulepreload">`
that loads from another origin must:

1. Use `https://` (never `http://`).
2. Pin an **exact** version in the URL (`three.js/r128/`, `react@18.3.1`),
   never `latest` or a range, because a hash only matches one exact file.
3. Carry `integrity="sha512-..."` (or `sha384-`) for that exact file.
4. Carry `crossorigin="anonymous"`, without which the browser can't verify the hash.
5. Should carry `referrerpolicy="no-referrer"`.

Example (the one in `index.html` today):

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
        integrity="sha512-dLxUelApnYxpLt6K2iomGngnHO83iUvZytA3YjDUCjT0HDOHKXnVYdf3hU4JjM8uEhxf9nD1/ey98U3t2vZ0qQ=="
        crossorigin="anonymous" referrerpolicy="no-referrer"></script>
```

**Getting the hash:** prefer the hash the CDN publishes (cdnjs shows a
"Copy SRI" button for each file). Cross-check it by hashing the file yourself:

```sh
curl -sL <url> | openssl dgst -sha512 -binary | openssl base64 -A
```

Never invent, guess, or copy a hash from memory or an unrelated page. Then
**load the page in a browser and confirm the library works**: a wrong hash
makes the browser refuse the file, with a console error mentioning "integrity".

**Allowed CDNs:** `cdnjs.cloudflare.com` (preferred), `cdn.jsdelivr.net`,
`unpkg.com`. Ask the owner before adding any other origin or any new
dependency at all.

### Raise the version number with every game change

The version shows at the bottom of Settings as `Version MAJOR.MINOR.PATCH`
(`id="gameVersion">Version 1.4.1<` in `index.html`), standard semantic versioning:

- **PATCH + 1** for a small change: bug fix, balance tweak, wording, notices (1.4.1 → 1.4.2)
- **MINOR + 1**, PATCH to 0, for a new feature: mode, screen, shop items (1.4.2 → 1.5.0)
- **MAJOR + 1**, the rest to 0, for a huge overhaul (1.5.0 → 2.0.0). Ask the owner first.

Whenever `index.html` or `music.mp3` differs from `main`, the version must be
exactly one of those steps past `main`'s. Bump once per branch, not once per
commit. If unsure whether a change is a fix or a feature, ask the owner.
`scripts/check_version.py` enforces this in the pre-commit hook and in GitHub
Actions. If two branches both took the same number, the second one to merge
must bump again on top of the first.

Scripts created at runtime (`document.createElement('script')`, `import()`
from a URL) aren't caught by the checker. Don't load remote code that way.

## Best practices (follow, and review for)

### Security
- No secrets, API keys, passwords, emails, real names or other personal data
  in the code, comments, commit messages or asset metadata.
- Don't put untrusted text into `innerHTML`. Use `textContent` for anything
  that came from the user, the URL, `localStorage` or the network.
  (`innerHTML` with strings built entirely from the game's own constants is OK.)
- No `eval`, `new Function`, or string arguments to `setTimeout`/`setInterval`.
- Wrap `localStorage` reads/writes in `try/catch`, since it can throw in private
  browsing. Validate parsed save data before trusting it.

### Code quality
- Keep the single-file structure unless the owner agrees to change it.
- Match the existing style: `const`/`let` (never `var`), the same naming and
  comment density as surrounding code.
- Make the smallest change that does the job. Don't reformat or reorganize
  code you weren't asked to touch, since that hides the real change in the diff.
- No new frameworks, build tools or npm packages without asking.

### Web basics
- Keep `<!DOCTYPE html>`, `<html lang="en">`, `<meta charset="utf-8">`
  and the viewport meta.
- It's a touch game: test at phone width (about 375px) as well as desktop, and
  make sure touch and keyboard/mouse input both still work.
- Buttons must be real `<button>` elements with readable text, and colour
  must not be the only way information is shown.
- Respect performance: avoid allocating objects inside the render loop,
  and keep assets small (compress audio/images before adding them).
- Audio must start only after a user gesture (browsers block autoplay).

## Workflow for agents

1. Before finishing any change, run `python3 scripts/check_sri.py`.
2. Open `index.html` in a browser and check that the game starts, there are
   no console errors, and the changed feature works. Say plainly what you
   tested and what you couldn't.
3. Don't commit, push or publish unless the owner asks. Commit messages
   describe *why*, in one short summary line plus detail if needed.
4. Work on a branch for anything non-trivial. `main` should always be playable.

## Setup (once per clone)

```sh
git config core.hooksPath .githooks
```

This turns on the pre-commit hook. It needs `python3` (preinstalled on macOS
with the Xcode command line tools).
