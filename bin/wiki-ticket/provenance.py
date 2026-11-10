#!/usr/bin/env python3
"""provenance.py -- backfill `merged_in` onto documents once they land.

A document is stamped with `git_hash` when it is written: the commit its
claims were read against. It cannot know the merge that will bring it to the
default branch, because that merge does not exist yet. This module fills that
in afterwards.

Why a separate module rather than a function in ia.py: `ia.py`'s docstring
promises "no wall clock, no environment", and `ia_render.py`'s promises no git
commands at all. Both promises are load-bearing -- the freshness gates
regenerate and byte-compare whatever those modules produce. Every git call in
the provenance story lives here, off that path, and runs only when a human or
the release routine asks for it.

WORKLOG-SPEC section 9.6 / plan 2026-08-03-doc-provenance-and-verification.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia  # noqa: E402


def _git(*args):
    """-> stdout stripped, or None when git fails or is absent."""
    try:
        p = subprocess.run(["git", *args], capture_output=True, text=True)
    except OSError:
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def default_branch():
    """The ref merges land on. `origin/main` when it exists so the answer is
    stable on a branch that is behind; local `main` in a fresh clone with no
    remote (the scaffolded-repo case)."""
    for ref in ("origin/main", "origin/master", "main", "master"):
        if _git("rev-parse", "--verify", "--quiet", ref):
            return ref
    return None


def added_in(path):
    """The commit that first added `path`, or None."""
    return _git("log", "--diff-filter=A", "--format=%H", "-1", "--", path)


def first_parent_chain(branch):
    """The default branch's first-parent history, newest first.

    One call per run, not per document — the chain is the same for all of
    them and this is the expensive part.
    """
    return (_git("rev-list", "--first-parent", branch) or "").split()


def merged_in(path, branch=None, chain=None):
    """The commit on the default branch that first contained `path`.

    Defined as the OLDEST commit on the branch's first-parent chain that has
    the file's add-commit as an ancestor. For a PR-merge workflow that is the
    "Merge pull request #N" commit, which is the answer people want.

    The two obvious one-liners are both wrong, and quietly:

      rev-list --ancestry-path --merges A..main | tail -1
          returns the earliest merge on the path — which is frequently a
          merge of main INTO the feature branch, not the merge that landed
          it. Verified wrong on this repo's own history.

      rev-list --ancestry-path --first-parent A..main
          returns nothing at all when the branch landed as a merge's SECOND
          parent, which is every PR merge.

    None when the document has not landed yet, when git cannot answer, or
    when history was squashed (see docs/adr — provenance assumes merge
    commits). None is a real answer and is recorded as "absent", never
    guessed: a wrong merge sha is worse than none, because it looks like
    evidence.
    """
    branch = branch or default_branch()
    add = added_in(path)
    if not (branch and add):
        return None
    if chain is None:
        chain = first_parent_chain(branch)
    ancestry = set((_git("rev-list", "--ancestry-path",
                         "%s..%s" % (add, branch)) or "").split())
    ancestry.add(add)   # committed straight to the branch: it landed as itself
    for commit in reversed(chain):          # oldest first
        if commit in ancestry:
            return commit
    return None                             # not on the default branch yet


def backfill(records=None, check=False):
    """Stamp `merged_in` on every landed FROZEN doc that lacks one.

    Frozen only, and that is the whole judgement in this function. A frozen
    document — a plan, a roadmap snapshot, a status report, a dated design
    pair — is written once, so "the commit that landed it" is exact and
    stays true forever. A live document (the roadmap, a guide, an ADR whose
    status flips, the current design pair) has been edited many times since
    it was added, so stamping it with the merge that FIRST carried it would
    be a true fact that reads as a lie: it names a version of the file that
    no longer exists.

    -> list of (wiki_key, path, sha) changed, or that would change in check
    mode. Idempotent for free: ensure_front_matter_fields returns [] when
    the value already matches, so a second run writes nothing.
    """
    if records is None:
        records = ia.build_records()
    branch = default_branch()
    if not branch:
        return []
    chain = first_parent_chain(branch)
    changed = []
    for key in sorted(records):
        rec = records[key]
        src = rec.get("source")
        if not src or not os.path.exists(src):
            continue
        if rec.get("merged_in") or not ia.is_frozen(rec):
            continue
        sha = merged_in(src, branch, chain)
        if not sha:
            continue          # not landed yet, or history cannot answer
        changed.append((key, src, sha))
        if not check:
            # Quoted for the same reason every other writer quotes: an
            # all-digit sha would otherwise be read back as an int.
            ia.ensure_front_matter_fields(src, {"merged_in": sha})
    return changed


def report(changed, check=False):
    verb = "would stamp" if check else "stamped"
    for key, src, sha in changed:
        print("%s %s  %s  %s" % (verb, key, sha[:12], src))
    if not changed:
        print("provenance: nothing to backfill")
    else:
        print("provenance: %s %d document(s)" % (verb, len(changed)))
        if not check:
            print("run `worklog ia-index` and commit the result together "
                  "with these documents")
    return changed


if __name__ == "__main__":
    report(backfill(check="--check" in sys.argv), check="--check" in sys.argv)
