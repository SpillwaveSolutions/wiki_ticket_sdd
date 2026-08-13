---
id: 9
slug: a-frozen-document-s-fabricated-citations
title: A frozen document's fabricated citations are reported, never gated
date: 2026-08-13
status: accepted
git_hash: "6bd91ec483a200e8a38e4fad66baa27c46d7cb0b"
tags: [docs, verification]
wiki_key: adr/0009-a-frozen-document-s-fabricated-citations
truth_state: current
---

# ADR-0009: A frozen document's fabricated citations are reported, never gated

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

Two rules that were each right on their own could not both hold.

**The freeze rule** (§15.8/§15.9): a plan, a roadmap snapshot, a status report
and a dated design pair are written once and never edited. The record of what
was believed at the time is the thing being kept; a correction goes in the next
document, never into the old one.

**The gate**: `worklog doc-verify --strict` exits 1 on a *fabricated* citation —
one that was wrong even in the tree the author had open — wherever it appears.
Unlike drift, fabrication is a genuine defect, so gating it anywhere looked
obviously correct.

It is not, because the only way to clear a fabrication is to edit the document,
and for a frozen document the freeze rule forbids exactly that. The gate had no
passing state. In this repository at v0.23.0:

    doc-verify: 267 citation(s) ok, 48 fabricated, 122 drifted across 31 document(s)

All 48 are in dated design pairs from v0.11.0 through v0.21.0. Not one of them
is legally correctable. `--strict` is what the release skill runs, so the
release gate had been red since the verifier shipped, and the fix in every case
was to not run it. A gate nobody can pass is a gate nobody runs.

The v0.20.0 release notes had already chosen a side in prose — *"the frozen
0.18.0 pair keeps its errors, as frozen records do, and the current walkthrough
names them for readers"* — and the code contradicted it. Reported as issue #345
by a consumer repo hitting the same wall at smaller scale.

## Decision

**`--strict` gates a defect only in a document that can still be fixed.**

The predicate is *editability*, not freeze state, and the difference is the
whole decision. A frozen document is editable at exactly one moment: the commit
that creates it. `doc-verify --staged` scopes the run to the documents a commit
touches, so in that run every finding is in a document being written right now
and fabrication gates normally. Afterwards the same document is history, and its
fabrications are reported on every run and gate nothing.

Drift is unchanged: it fails only on a document claiming to describe HEAD
(`current_design_doc.md`, `current_code_walkthrough.md`), because only those
promise to be current.

`failing()` in `bin/doc_verify.py` is the whole implementation; `verify()`
computes an `editable` flag per finding, because it is the only place that
knows both the record and whether the run was commit-scoped.

## Consequences

- The release gate is passable, and every fabrication is still caught **once**,
  at the only moment it could have been fixed — the pre-commit hook already runs
  `doc-verify --staged --strict`.
- The 48 existing fabrications stay. They print on every run tagged
  `[frozen record — reported, not gated]`, and the summary names the count
  explicitly so silence never reads as absence.
- A document that lands through `--no-verify` carries its fabrications forever
  and is never gated again. That is the escape hatch's cost, not this rule's;
  the report still shows it.
- The gate now depends on `--staged` being wired into the commit hook. If that
  wiring is removed, fabrication in a new frozen document is caught by nothing.
  `hooks/pre-commit` is the load-bearing half of this decision.

## Alternatives

**Gate fabrication everywhere, and add a freeze exception for provably-wrong
citations.** Coherent — the verifier proves the claim wrong, so correcting it
adds no interpretation. Rejected because "provably wrong" is not where it stops:
the same argument licenses fixing the surrounding prose that the wrong citation
supported, and then the frozen record is being rewritten by whoever has the
newest tooling. The line has to sit somewhere a rule can hold it, and "never"
is the only such place.

**Gate fabrication only in the two live documents.** Simplest change, and wrong:
`docs/user_guide/` and `README.md` are neither live nor frozen. A fabrication
there is fixable, and this alternative would stop gating it.

**Regenerate the frozen pairs with correct citations.** Rejected outright — it
is the dishonesty `doc-verify` exists to catch, performed by the tool built to
catch it.
