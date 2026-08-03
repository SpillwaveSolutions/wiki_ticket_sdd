---
date: 2026-08-02
slug: trace-check-scope
title: Scope the traceability gate to the claim it actually makes
items: [01KZ2JAT7PCV6B34W2RK34WBX7]
---

# Scope the traceability gate to the claim it actually makes

## Context

`worklog trace-check --strict` is described in the release skill as "the
pre-release evidence gate". It asks whether shipped work can be traced from the
decision that caused it to the code that delivered it — three links per item: a
plan that produced it, an external ticket that tracks it, a PR or commit it
landed in.

Its docstring scopes that question to *"every item in a released milestone"*.
The implementation never applied that scope. `trace_check()` computed

```python
scope = "released" if it.get("milestone") else "closed"
```

interpolated it into each message, and filtered on nothing. The loop ran over
every closed item in the log.

The result on `main` at v0.19.1: **401 gaps across 214 items**, out of 267 done
items — 80% of all closed work flagged. Only 39 items carry a milestone, so
**323 of the 401 gaps were on items the docstring excludes**. The count was 389
at the v0.19.0 release two days earlier. A gate whose failure count rises
monotonically with normal work is not a gate; it is a number people learn to
scroll past.

This is a "the label became the enforcement" failure. The variable meant to
gate the check ended up only decorating its output. Nothing threw, the output
stayed plausible, so it survived from the check's introduction until now.

## Why fixing the scope alone is not enough

Filtering to milestone items takes 401 to 78. It does not make those 78
actionable, because release items *do* carry milestones, and 24 of the 39
milestone items are `kind:ops`:

```
released-scope items: 39
by kind: ops 24, bug 14, feature 1
```

Every one of the `Cut vX.Y.Z release` items would still be reported as
`no external ticket` — and would be reported that way forever, because the
release skill says so explicitly:

> Release items are local-only by convention — no external ticket is filed for
> them... don't file a redundant issue just to have something for ticket-sync
> to close.

The same holds for the other ops work in that set: daily status reports,
removing abandoned worktrees, closing out stale bookkeeping. None of them has a
plan, a ticket, or a PR, and none of them should. A gate that permanently
flags work for correctly following documented process teaches people to ignore
it, which is the failure mode we already have.

So the fix is scope *plus* the exemptions the conventions already imply. Both
halves are needed; either alone leaves the gate unusable.

## The rule

Three conditions, each derived from a rule the project already documents
elsewhere rather than invented here:

1. **Scope is the released milestone set.** This is the docstring's own claim,
   finally enforced. An item with no milestone has not shipped in anything
   named, so there is no release for it to be evidence of.

2. **`kind:ops` is exempt entirely.** Release cuts, status reports, log
   compactions and worktree cleanup are not delivered features. The taxonomy
   already says ops is its own axis and that it "trends down by automating" —
   it is not work that traces to a plan, a ticket and a PR, and never was.

3. **`unplanned` items are exempt from the plan check only.** The taxonomy
   sanctions work discovered mid-flight and records it with `--unplanned
   --discovered-during`. Demanding a plan link from an item defined as having
   arrived without a plan is a contradiction. Such items must still show a
   ticket and a PR — being unplanned excuses the plan, not the evidence.

Applied to `main`, this leaves **16 gaps**: 15 missing PR links and one missing
ticket, all on real `bug`/`feature` work that shipped in a named milestone.
That is a list somebody can finish in an afternoon with `worklog link-pr`,
which is the property the gate needed and did not have.

## What we are deliberately not doing

**Not wiring `--strict` into CI in this change.** It is named in the release
skill's prose and enforced nowhere. Making it blocking is the right end state,
but it should happen only after the count has been driven to zero and held
there for a release — otherwise we replace a warning nobody reads with a red
build everybody bypasses, which is strictly worse. Wiring it up is follow-on
work, gated on the backlog being clean.

**Not auto-exempting `cancelled`.** Already handled: the existing status filter
excludes it.

**Not touching the graph.** The edges were always correct. This change is only
about which items the gate interrogates.

## Consequences

`tests/test_ia.py::test_trace_check_warn_and_strict` asserted that an
unmilestoned `kind:ops` item is reported for having no plan. That assertion
encodes the bug precisely, and it has to be rewritten rather than preserved.
Doing so is the point of the change, but it is worth naming: the regression
suite was holding the defect in place, which is why the mismatch survived
review. The replacement tests assert the boundary in both directions — an item
just inside the scope is reported, an otherwise identical item just outside it
is not — so a future silent widening fails loudly.

`plugin/scripts/ia_graph.py` is a mirrored copy and moves in lockstep;
`tests/test_plugin.py` enforces it.

Repos scaffolded from the plugin inherit the corrected gate. Their gap counts
will drop sharply at the next upgrade. That is the fix landing, not data being
lost — the underlying graph is unchanged, and non-strict `trace-check` remains
warn-only at commit time either way.
