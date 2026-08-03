---
date: 2026-08-02
slug: plan-banner-state
title: A plan's banner should say which plan it is
items: [01KZ2KGPRMKG9B98Q6YVD3MZVJ]
status: completed
---

# A plan's banner should say which plan it is

## Context

Issue #292 reported that every published plan page opens with a banner written
for status reports:

> **Current** — the latest status report. Reports freeze once published;
> corrections appear in later reports.

That half of the defect was already fixed. The `doc_type` guard landed in
`7a9184a` and shipped in **v0.19.0**; no plan page in this repo has said
"status report" since. The issue was filed from a downstream repo running an
older plugin, and reproduces there, not here.

What did reproduce is the quieter half. All 20 non-superseded plan pages
rendered the *same* banner — "the current plan" — whether the plan was
finished, in progress, or not yet started:

```
16  completed
 4  planned (in three prose variants)
 1  active
```

The record carried `status` the whole time. `banner()` read `truth_state` and
nothing else. A reader could not tell a plan completed three weeks ago from one
nobody has begun.

Two smaller things travelled with it. `rec.get("kind", "status")` supplied a
default for a field the schema *requires* on status records, so a malformed
record rendered plausible prose instead of failing. And no test anywhere
asserted what a **plan** page's banner says — `tests/test_ia.py` checked the
supersede wording and the render-hash flip, both via status records. That gap
is why the original defect shipped and why this one outlived it.

## The decision: read the leading word, and only the leading word

A plan's `status` is free prose, not an enum. The real values today:

```
completed
active
planned
planned — not yet scheduled
planned — not yet scheduled; implementation tasks attach to the epic when work starts
```

The last is a full sentence. Nothing can interpolate it into a one-line banner
and stay readable. But every one of them opens with a word that *is* the state,
and the remainder is elaboration that belongs in the page body where the reader
already is.

So: split on whitespace, take the first token, map it through a three-entry
table, and render the label. `completed` → "completed plan", `active` → "plan
in flight", `planned` → "plan not yet started".

**Unknown prose returns nothing and the banner says nothing about state**,
falling back to wording byte-identical to today's. This is the load-bearing
part of the decision. Inventing a label for prose we cannot read is precisely
how the banner came to announce plans as status reports: a default that looked
reasonable at the call site and was wrong for most of its inputs. A banner that
declines to guess is strictly better than one that guesses confidently, and the
fallback costs one `or`.

### Alternatives considered

The issue offered three options. **Normalise to a small display set** is what
this is, done cheaply — the normalisation is the first token rather than a
migration of every plan's front matter. **Truncate at the first `;` or `—`**
was rejected: it still emits arbitrary author prose into a banner, so
`"planned — not yet scheduled"` would render as `"planned"` only by accident of
punctuation, and a plan whose status began with a clause would render garbage.
**A boolean complete/in-flight split** loses the distinction between work not
started and work underway, which is the one a reader scanning an index most
wants.

## Deliberately not done

**Not touching `truth_state` for plans.** `ia.py:385` assigns every
non-superseded plan `truth_state: current` unconditionally, and the issue
correctly observes that deriving it from `status` — the way the `adr` branch
two lines above already does — is the more honest model. It is also much larger:
`_assign_truth` begins `if "truth_state" in rec: continue`, and every plan
sidecar already persists `truth_state: current` on disk, so changing the
derivation alone would do nothing until all 23 sidecars are regenerated. That
is a separate decision with its own blast radius, and the banner is what
readers actually see.

**Not editing any plan source.** Plans are frozen. This is a render-layer
defect and is fixed at the render layer — which is the point the downstream
repo made by having to correct two plan pages at the source because it could
not be fixed anywhere else.

## Consequences

Banner text folds into `render_hash`, so every frozen plan page republishes on
the next `wiki-publish`. That is the mechanism working as designed, not
ledger churn to investigate.

`bin/ia_render.py` and `plugin/scripts/ia_render.py` move together;
`tests/test_plugin.py` enforces it. The module's byte-determinism contract is
unaffected — the new code reads one field of one record and touches no clock,
no git, and no file.

The new tests live in a standalone `TestBanner` rather than in `TestRender`,
which is subclassed twice: a case parked there runs three times and builds
three throwaway git repos to assert one string. `banner()` is a pure function
of a single record and needs no fixture at all.
