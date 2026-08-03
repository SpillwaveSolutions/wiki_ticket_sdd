---
id: 8
slug: document-provenance-depends-on-merge-com
title: Document provenance depends on merge commits
date: 2026-08-03
status: accepted
git_hash: "78af76952e1348b3acf70829ecfb08bad11acc7c"
tags: [provenance, docs]
wiki_key: adr/0008-document-provenance-depends-on-merge-com
truth_state: current
---

# ADR-0008: Document provenance depends on merge commits

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

Generated documents now record `git_hash`: the commit their claims were read
against. `worklog doc-verify` resolves each code citation at that commit
rather than at HEAD, which is what separates a **fabricated** citation (wrong
even in the tree the author had open) from **drift** (right then, moved
since). Only the first is a defect; before this, the two were
indistinguishable and all of them were ignored.

That verification rests on an assumption nobody had written down: **the
stamped commit is still reachable in a fresh clone.**

It holds today because this repository merges with merge commits — 134 of
them across 404 commits, every one a `Merge pull request #N`. A feature
branch's commits become ancestors of `main` and survive.

Under squash-merge they would not. The branch commit is never on `main`; it
survives only as `refs/pull/N/head` on the remote, which a normal clone does
not fetch. Every `git_hash` stamped on a branch would name a commit that
cannot be resolved, and `merged_in` could not be derived at all.

## Decision

**Doc provenance assumes merge commits. Do not enable squash-merge or
rebase-merge on this repository without first deciding what happens to
`git_hash`.**

When a stamped commit cannot be resolved — squashed history, a shallow CI
checkout, a fork — `doc_verify` reports `unresolvable` and **skips the
document**. It must never fall back to HEAD.

That refusal is the important half. Falling back would re-create bug #294
exactly: citations checked against the wrong tree, reporting drift as
fabrication and fabrication as fact, while looking like it worked.

## Consequences

- `doc-verify` is skipped, not failed, on shallow clones. CI's `invariants`
  job already uses `fetch-depth: 0`, so the strict run at release time has
  the history it needs; no workflow change was required.
- `provenance-backfill` returns nothing rather than guessing when the
  ancestry cannot be walked. A wrong merge sha is worse than an absent one,
  because it looks like evidence.
- If this repository ever adopts squash-merge, existing stamps degrade
  gracefully to `unresolvable` — the verifier goes quiet rather than wrong.
  New documents would need a different anchor, and that is a new decision,
  not a silent adjustment.
- The GitHub branch-protection setting that permits squash-merging is now
  load-bearing. It is the kind of thing that gets toggled during unrelated
  repository housekeeping, which is precisely why it is recorded here.

## Alternatives

**Store the file's content hash instead of a commit.** Immune to squash,
because it identifies the bytes rather than the history. Rejected: it answers
"has this file changed?" but not "what did `bin/fold.py` look like when this
was written?", which is the question a citation check has to ask. It also
cannot place a document in git time, which was the broader goal.

**Fall back to HEAD when the commit will not resolve.** Rejected above; it is
the defect this work exists to remove.

**Tag every stamped commit so it survives squashing.** A tag per generated
document is hundreds of refs carrying no meaning of their own, and it would
still fail for documents written before the scheme existed.

**Do nothing and rely on the workflow staying as it is.** That is the actual
status quo — the difference this ADR makes is that the assumption is written
down where someone changing the merge strategy will find it, rather than
being discovered when the verifier quietly stops finding anything.
