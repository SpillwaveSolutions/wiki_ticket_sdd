# Migration 0002 — IA & content model (wiki_key, truth_state, sidecars)

**Plan:** `docs/plans/2026-07-22-ia-content-model.md` · **Date:** 2026-07-22

## Why

The repo had four frontmatter dialects (ADR, plan, status, design) plus two
doc families with none (roadmap family: HTML comments; guides: nothing), and
no stable cross-cutting identity. "Is this page current?" was inferable only
from path conventions, and the requirement→plan→item→ticket→PR→release
evidence chain existed in the log but was never materialized or checked.

## What changes

1. **`wiki_key` is formalized.** The logical key `published.json` already
   uses becomes the explicit, stable identity of every doc. For **legacy**
   docs it is seeded **verbatim from the existing ledger key** — including
   the bare keys (`home`, `spec`, `cli-reference`, `plugin-guide`,
   `user-guide`) and the mixed snapshot shapes (`roadmap-snapshot/…` and
   legacy `roadmap/…`). **No URL, path, or page name changes.** A normalized
   `canonical_key` + `aliases[]` are recorded alongside for future renames
   (`docs/.index/aliases.json`). New docs derive keys by rule (plan §5.5);
   new plans use `plan/<date>-<slug>` so successors can never collide.
2. **`truth_state` labels every doc** (`current` / `snapshot` /
   `superseded` / `archived`), orthogonal to lifecycle `status`, so readers
   (and renderers) can tell current truth from historical evidence.
3. **Frozen docs are normalized by sidecar, never edited.** Metadata a
   frozen doc lacks (plans, roadmap snapshots, status reports, dated
   designs) lives in `docs/.index/<wiki_key>.yml`. In-place frontmatter
   edits are reserved for the sanctioned-live docs (live roadmap, current
   designs, user guides, ADR status flips). Invariants §15.8/§15.9 hold.
4. **A unified schema** (`schema/doc.schema.json`, mirrored in `bin/ia.py`)
   validates the merged record (frontmatter ∪ sidecar) with per-type
   required subsets. Deliberately relaxed vs. the plan's aspirational
   table where history can't comply (e.g. `epic` is optional on plans —
   `epic: null` plans exist; legacy snapshots lack `git_hash`).
5. **Generated artifacts under `docs/.index/`** (inventory, graph, rendered
   pages, publish manifest) are byte-deterministic pure functions of
   committed files — no wall clock — so the freshness gate can
   regenerate-and-diff exactly like `docs/roadmap.md`. Where the plan's
   examples showed `generated_at` wall-clock fields on these artifacts,
   determinism won.

## What teams must do

Nothing beyond running `worklog ia-normalize` (once, or any time; it is
idempotent and additive). CI gates run warn-only for one release cycle
before promotion to hard fail.
