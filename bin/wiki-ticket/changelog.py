#!/usr/bin/env python3
"""
changelog.py -- draft the unreleased CHANGELOG section from git history.

Item #136: the release skill requires a hand-written `## X.Y.Z — unreleased`
section before a release can be cut, but nothing enforced writing it as
features landed. v0.13.0's section had to be reconstructed from `git log`
after 36 commits had piled up unlogged.

This does not write release notes. It writes the STARTING POINT for them, so
the failure mode is "these bullets need better prose" instead of "nobody
remembers what shipped". A human or agent still edits before stamping.

Two deliberate refusals:
  - It never guesses the version. Which digit moves is a semver judgement, so
    the placeholder stays literal until someone passes --version.
  - It never silently drops a commit. Everything excluded is reported on
    stderr, with the reason. stdout stays clean markdown so it can be piped.
"""
import re
import subprocess
import sys

# Conventional-commit type -> the bullet label this changelog already uses.
LABELS = {
    "feat": "New",
    "fix": "Fix",
    "perf": "Change",
    "refactor": "Change",
    "ops": "Change",
    "chore": "Change",
    "docs": "Docs",
    "test": "Tests",
}

# Types that describe process rather than the product. A plan is its own
# permanent record in docs/plans and a release commit is the stamp itself;
# neither belongs in the notes for what shipped.
PROCESS_TYPES = ("plan", "release")

# Paths that are generated or are the log itself. A commit touching ONLY
# these changed no behaviour a reader of the changelog cares about.
HOUSEKEEPING = (".work/", "docs/.index/", "docs/roadmap.md", "docs/status/",
                "docs/plans/")

SUBJECT = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?!?:\s*(?P<rest>.+)$")
# Trailing worklog ids -- internal provenance, noise in release notes.
ULID_REF = re.compile(r"\s*\((?:01[A-HJKMNP-TV-Z0-9]{24}(?:,\s*)?)+\)\s*$")


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def last_tag():
    p = _git("describe", "--tags", "--abbrev=0")
    return p.stdout.strip() if p.returncode == 0 else None


def commits(since=None):
    """[(subject, [files])] for each non-merge commit after `since`.

    One `git log` call, not one per commit: the file list is what decides
    housekeeping, and asking git per commit turns a release-sized range into
    hundreds of subprocesses.
    """
    rng = f"{since}..HEAD" if since else "HEAD"
    p = _git("log", rng, "--no-merges", "--reverse", "--name-only",
             "--format=%x00%s")
    if p.returncode != 0:
        return []
    out = []
    for chunk in p.stdout.split("\x00"):
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        out.append((lines[0].strip(), [f for f in lines[1:] if f.strip()]))
    return out


def _housekeeping(files):
    return bool(files) and all(f.startswith(HOUSEKEEPING) for f in files)


def classify(subject, files):
    """(label, text) to render, or (None, reason) to exclude."""
    m = SUBJECT.match(subject)
    ctype = m.group("type") if m else None
    text = (m.group("rest") if m else subject).strip()
    text = ULID_REF.sub("", text).strip()

    if ctype in PROCESS_TYPES:
        return None, f"{ctype}: commit (process, not product)"
    if _housekeeping(files):
        return None, "touches only the log and generated files"
    if not text:
        return None, "empty subject"
    return LABELS.get(ctype, "Change"), text


def draft(version=None, since=None):
    """(markdown, excluded) -- excluded is [(subject, reason)]."""
    since = since or last_tag()
    entries, excluded = [], []
    for subject, files in commits(since):
        label, payload = classify(subject, files)
        if label is None:
            excluded.append((subject, payload))
        else:
            entries.append((label, payload))

    # Group in a stable, meaningful order rather than raw git order: readers
    # of a release want the new things first and the incidental last.
    order = ["New", "Fix", "Change", "Docs", "Tests"]
    entries.sort(key=lambda e: order.index(e[0]) if e[0] in order else len(order))

    head = f"## {version or 'X.Y.Z'} — unreleased"
    if not entries:
        body = ["", "_No product changes since "
                    f"{since or 'the start of history'}._"]
    else:
        body = [""] + [f"- **{label}**: {text}" for label, text in entries]
    return "\n".join([head] + body) + "\n", excluded


def main(argv):
    version = since = None
    args = argv[1:]
    for flag, target in (("--version", "version"), ("--since", "since")):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                print(f"changelog-draft: {flag} needs a value", file=sys.stderr)
                return 2
            if target == "version":
                version = args[i + 1]
            else:
                since = args[i + 1]

    resolved = since or last_tag()
    text, excluded = draft(version, since)
    sys.stdout.write(text)

    # stderr, so stdout stays pipeable into the CHANGELOG. Never silent: a
    # draft that quietly dropped a commit is how "we forgot to write it"
    # comes back wearing a different hat.
    print(f"\nchangelog-draft: since {resolved or '(no tag)'}; "
          f"{len(excluded)} commit(s) excluded", file=sys.stderr)
    for subject, reason in excluded:
        print(f"  - {subject}  [{reason}]", file=sys.stderr)
    if not version:
        print("changelog-draft: version left as X.Y.Z — pass --version to set it",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
