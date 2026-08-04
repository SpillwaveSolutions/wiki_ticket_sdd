---
date: 2026-08-03
slug: doc-provenance-and-verification
title: Git provenance on generated docs, and the verifier it enables
epic: 01KZ30X6HZ6FKJXJX386J44CB1
items: [01KZ30X6JD7M4XV6Y5194E1D32, 01KZ30X6JDXDZ38RY6AQEYE7VY, 01KZ30X6JDYF6YQWN6WYMVQ5Y4, 01KZ30X6JD06D11ACPVF8Q5GMW, 01KZ30X6JDSYHB6FQB7RRCGKQQ, 01KZ30X6JDHPRBESZDQ2CSNJZ2, 01KZ30X6JECK0M9G04ZHMS4SMA, 01KZ30X6JEXH4TTKHDNV3ZW0Q2, 01KZ30X6JEH1Z7D5AC5ZAMM5V8, 01KZ30X6JE1ERVS43QVXEEGVXA, 01KZ30X6JE0QSQF6BE8S0YRPBW, 01KZ30X6JE8542ERDW1B8A9P8H, 01KZ30X6JEF29Z5AEEWXBSJWHV, 01KZ30X6JEWCD74E81Y555DAYP, 01KZ30X6JEETVQZG7YYFM7B998, 01KZ30X6JEBXN08HQTQ77ESSTV]
merged_in: 08c535978f2facd8e1ee00343a6aaad81bfe4fe3
---

# Git provenance on generated docs, and the verifier it enables

## Context

Issue **#294** was filed after the v0.19.1 doc sync found the generated design
docs quoting code that no longer existed. The v0.20.0 sync then measured it
properly: **12 of 26 line-number citations were stale** — a 46% error rate on
the single most mechanically checkable claim in the document — plus a wrong
`MAX_BODY` line and a `fold.py` import claim that was *introduced while
hand-fixing the previous wrong import claim*.

That last detail is the whole argument. Correcting prose by hand without a
check just relocates the error. Nothing in the pipeline verifies a generated
doc's claims against the code it describes.

The fix is not "check citations against HEAD" — HEAD moves, and a frozen doc
is *allowed* to age. The fix is to **pin each doc to the commit it was written
against**, then resolve its citations at *that* commit. This makes two things
distinguishable that today are not:

- **fabricated** — the citation was wrong even in the tree the author had open
- **drifted** — the citation was right then, and the code has moved since

Only the first is a defect. Today they are indistinguishable, so all 26 look
equally suspect and nobody triages them.

The broader goal (the user's framing) is to place *every* generated doc in the
stream of git history — authoring commit and merge-to-main point — so the
roadmap, plans, snapshots and status reports can all answer "what was true
when this was written?". #294's verifier is the first consumer, not the only
one.

## What already exists — reuse, don't rebuild

| Thing | Where | Note |
|---|---|---|
| `git_hash` front matter | 26 design docs | **Required** for `design` in `bin/ia.py:53`. Full 40-hex. Already means exactly what we want. |
| `git_commit()` | `bin/ulid.py:46` | Memoised short sha, honours `WORKLOG_NO_GIT_PROVENANCE`. Reuse its *env contract*, not its format — see Decision 2. |
| `git` on every event | `bin/worklog:86` `base()` | Since v0.19.1. **This is what lets regenerated docs carry a commit with no git call.** |
| `ensure_front_matter_fields()` | `bin/ia.py:519` | Additive, never touches the body, **already idempotent** (`changed = [...]`, returns `[]` when values match). The backfill needs no new write logic. |
| `mark_superseded()` | `bin/adr.py:193` | Existing precedent for one sanctioned in-place mutation of an otherwise-stable doc. |
| `max_ev()` | `bin/render_roadmap.py:28` | Already scans every event and keeps the newest — it just discards the event object. |

## Design decisions, and the evidence for them

**1. Flat keys, never nested.** `bin/ia.py:87` does `line.partition(":")` after
`.strip()`, so an indented `provenance:` block flattens its children to
top-level keys, and the `provenance:` line itself hits the empty-value branch
at `ia.py:91-93` and becomes `[]`. Nesting is not a style choice here; the
parser cannot represent it.

**2. Full 40-hex shas, never short.** `ia._scalar` (`ia.py:113`) does
`re.fullmatch(r"-?\d+", v)` and returns `int(v)`. A 7-char short sha is
all-digits with probability (10/16)⁷ ≈ **1 in 27**, and `0123456` would
silently become `123456` — a corrupted sha that still looks like one. This is
why we reuse `git_hash` (already full-length on 26 design docs) rather than
`ulid.git_commit()`'s short form.

**3. Omit the key, never write it empty.** `ia.py:91-93`: an empty value sets
`meta[k] = []` *and arms block-list mode*, so it corrupts the parse of every
following line. `bin/worklog:86` already documents the right rule — *"Omitted
entirely outside a git repo rather than written empty."* Absent means "not
verifiable, skip and say so"; present means "verify, or fail."

**4. Nothing on the regenerate-and-diff path may call git.**
`hooks/pre-commit:110-118` regenerates `docs/roadmap.md` and `diff -q`s it;
`ia_render.write_all(check=True)` byte-compares every rendered target. Both run
in CI (`.github/workflows/worklog.yml` runs the whole hook). A commit cannot
know its own sha, so a `git rev-parse` in either would fail **every** commit —
and on `pull_request`, `actions/checkout` uses a synthetic `refs/pull/N/merge`
sha that exists in no local clone, so no stored value could ever match. The
roadmap takes its commit from **the newest event's `git` field**, exactly as it
already takes `generated_at` from the newest event's ULID.

**5. Hash the body, not the file — do this first.** `ia_render.py:691` computes
`render_hash = sha256(_file_hash(source) + banner)`. Since publish strips front
matter (`wiki-publish` SKILL.md §3), a front-matter-only change produces
**byte-identical published output**, yet currently moves the hash and trips the
frozen-source guard. Hashing the body makes that guard mean *"the prose
changed"* — which is the invariant §15.8/§15.9 actually protects — and makes
every provenance stamp in this plan cause **zero republish**. It also
retroactively legalises `ia-normalize`'s own `wiki_key` stamps and
`adr.mark_superseded`, both of which technically trip the guard today.

Only the **87 `doc+banner`** manifest entries use `_file_hash`; the 344 `as-is`
rendered pages hash rendered content and are unaffected. One-time churn is at
most 87 pages, not 430.

## Implementation — five commits, each green

Every commit: `cp` touched `bin/*` into `plugin/scripts/`, mirror any skill
edit between `plugin/skills/` and `.claude/skills/`, run `worklog ia-index`
before staging. `tests/test_plugin.py` enforces all three.

### 1. Body-hashing (`bin/ia_render.py`)

Add `_body_hash(path)` beside `_file_hash` (`ia_render.py:636`), using
`ia.parse_front_matter(text)[1]` — `ia` is already imported and the function
already returns `(fm, body)`. Use it in the `doc+banner` branch at
`ia_render.py:691`. Emit `source_hash` per page so the publisher compares
manifest-to-ledger instead of hashing files itself.

Update `plugin/skills/wiki-publish/SKILL.md:31-34` (and the `.claude/skills/`
twin) so the frozen-source guard reads the body hash, and say *why* — the guard
gets stronger, not weaker.

Regenerate and commit the manifest. The one-time ≤87-page republish lands here,
alone, where it is easy to reason about.

### 2. Roadmap provenance (`bin/render_roadmap.py`)

Split `max_ev` (`render_roadmap.py:28`) into:

- `top_event(paths)` → the newest event **dict** (same scan, keep the object)
- `max_ev(paths)` → `(top_event(paths) or {}).get("ev")` — **signature
  unchanged**, so all six callers (`bin/worklog:924,994,1038`,
  `bin/compact.py:32,151`, tests) stay untouched

In `render()` (line ~131), emit `git_hash: {ev["git"]}` only when present.
Verified: the newest event carries `git: e95ad4d`; 40 of 325 events carry it
(everything since v0.19.1), and older logs degrade to *key absent*, not *key
wrong*.

Roadmap snapshots need **no code change** — `bin/worklog:513` is a
`shutil.copyfile` of `docs/roadmap.md`, so a snapshot inherits the roadmap's
provenance, which is exactly the right value. Pin that with a test or it rots
silently.

### 3. Stamp authored-once docs

Three writers, one line each, all using a new full-sha helper that mirrors
`ulid.git_commit()`'s env contract (`WORKLOG_NO_GIT_PROVENANCE`, `""` outside
a repo) but calls `git rev-parse HEAD`:

- `bin/plan_capture.py:69` `front_matter()` — take the sha as a **parameter**
  so the function stays pure and testable; pass it from `cmd_plan_capture`
- `bin/worklog:1067` `cmd_status` — one more f-string line
- `bin/adr.py:171` `scaffold()` — optional but cheap

Add `git_hash` and `merged_in` to `schema/doc.schema.json` properties for
documentation. **No `REQUIRED_BY_TYPE` change**: `merged_in` can never be
required (a doc on a branch has not merged, so requiring it rejects the commit
that creates any plan), and requiring `git_hash` would fail 49 existing docs
that cannot be honestly stamped.

Note the honesty caveat in a comment: at generation time HEAD is the commit
*before* the one the doc lands in. `git_hash` means "the tree this doc was
written against" — which is what design docs have always meant and what a
reader diffing stale prose actually wants.

### 4. Manifest-level provenance (`bin/ia_render.py`)

`build_manifest` (`ia_render.py:641`) returns `{"version": 1, "pages": [...],
"sidebar": {...}}`. Add top-level `git_hash` and `generated_at` from
`render_roadmap.top_event` — pure, no git call, no per-page churn. The rendered
set is one build from one log, so the commit is a property of the build.

### 5. Backfill + the verifier

**`bin/provenance.py`** (~40 lines) + `worklog provenance-backfill [--check]`.
A separate module because `ia.py`'s docstring promises "no git commands" and
that is load-bearing.

Per doc whose front matter lacks `merged_in`:

1. `git log --diff-filter=A --format=%H -1 -- <path>` → the commit that added it
2. `git merge-base --is-ancestor <add> origin/main` → false ⇒ **skip** (still on
   a branch; leave the key absent)
3. `git rev-list --ancestry-path --merges <add>..main | tail -1` → the merge
   that landed it; empty (fast-forward) ⇒ use the add commit
4. `ia.ensure_front_matter_fields(path, {"merged_in": sha})` — idempotent for
   free
5. caller runs `worklog ia-index` in the **same commit**

Verified on real history — 134 merge commits, all PR merges:
`9b97fab → b2bf3cf`, `d23bcfe → 9369638`, `651c00e → e95ad4d`.

Runs from the **release skill §7 "After"** step, which already creates a
post-release branch and lands a commit. Not a git hook — `post-merge` fires on
`main`, where `hooks/pre-commit:24-34` forbids committing.

**`bin/doc_verify.py`** + `worklog doc-verify [--strict]`:

1. read `git_hash`; absent ⇒ `unstamped`, skip. **Never fall back to HEAD** —
   that fallback *is* #294 with extra steps
2. `git rev-parse --is-shallow-repository` / `git cat-file -e <sha>` ⇒
   `unresolvable`, skip and say so
3. `git show <sha>:<path>` — a path absent at the pinned commit is a
   **fabricated** citation, not drift
4. range within file length, and any cited symbol appears inside the cited
   range *at that commit* ⇒ this is what catches the 12-of-26
5. diff the pinned range against HEAD ⇒ **drift**, reported separately.
   Informational for frozen docs; **hard failure for the two `current_*`
   files**, which claim to describe HEAD
6. warn-level in `hooks/pre-commit` beside `trace-check`; `--strict` at release

Citations use an **en-dash** (`lines 249–259`), not a hyphen — a regex written
for `-` matches nothing.

## Verification

Existing tests that must change (all assert exact front matter):
`tests/test_render_roadmap.py:59-64` (and `:268` — the empty-log case must
assert the key is **absent**), `tests/test_plan_capture.py:67-71`,
`tests/test_status.py:113,169`, `tests/test_snapshot.py`.

New `tests/test_provenance.py` — presence assertions are worthless here; each
of these fails when the sha is **wrong**:

1. **The stamp names a commit whose tree holds what the doc read.** Temp repo:
   commit C0 with known `foo.py`; stamp; assert `git show <git_hash>:foo.py`
   equals C0's content. Commit C1 changing it; assert the stamp still yields
   **C0** bytes. Fails if the stamper records post-commit HEAD, the wrong
   parent, or a short sha.
2. **All-digit sha round-trip** — two lines, guards the `_scalar` int-coercion
   trap.
3. **Determinism guard** — monkeypatch `subprocess.run` to raise, then call
   `render_roadmap.render()` and `ia_render.render_all()`. This is what
   protects Decision 4; it fails loudly the day someone "fixes" provenance with
   a `git rev-parse`.
4. `top_event`/`max_ev` agree on the ULID (the refactor didn't move the
   watermark).
5. Backfill idempotence; backfill skips a doc not yet an ancestor of main;
   `git merge --squash` returns `None`, not a wrong answer.
6. `_body_hash` invariant under a front-matter-only edit, changed by a body
   edit.
7. **The #294 regression test** — doc citing `foo.py` lines 10-12, stamped at
   C0 where those lines hold a known symbol; commit C1 deleting them; assert
   the verifier reports **fresh** (it reads at C0) and that reading at HEAD
   would report stale.

End-to-end: `worklog doc-verify` against the 26 real design docs, and confirm
it independently rediscovers the 12 stale citations the v0.20.0 sync found by
hand. That is the acceptance test for the whole plan.

Then `python3 tests/test_plugin.py`, `worklog ia-render --check`,
`worklog ia-inventory --check`, and the full suite file-by-file.

## Out of scope

- **Front matter on the 344 rendered pages.** Regenerate-and-diffed in CI,
  stripped before any reader sees them, and 344 copies of one fact about one
  build. Manifest-level provenance (commit 4) carries the same information in
  one place with zero churn.
- **`merged_in` on `docs/roadmap.md`.** It is live and regenerated every
  commit; a merge sha would be stale within a commit and break the pre-commit
  diff. Its *snapshots* are the frozen things that carry it.
- **Backfilling `git_hash` onto the 49 existing plans/snapshots/status docs.**
  The add-commit is not the authoring HEAD. Absent means "predates provenance",
  which is true; a guessed value would be exactly the #294 failure class.
- **Requiring provenance in `REQUIRED_BY_TYPE`.** Add a forward-only gate (fail
  when `date:` ≥ cutover and `git_hash` absent) only if a doc ever slips past
  the four writers.

## Risk to accept explicitly

If this repo ever switches to **squash-merge**, the authoring commit never
lands on main, `git show <sha>:path` fails in a fresh clone, and the verifier
loses its ground truth. It must then report `unresolvable` and refuse — never
degrade to HEAD. Worth one ADR stating that doc provenance depends on merge
commits, with the verifier's error message pointing at it.

## Tasks

- [ ] (P2) Hash the document body, not the whole file, when deciding what to republish
  - [ ] (P2) Add a body-only hash and use it for pages published with a banner
  - [ ] (P2) Teach the wiki publisher's frozen-document guard to read it, in both skill trees
- [ ] (P2) Record on the roadmap which commit its data came from
  - [ ] (P2) Keep the newest event object during the scan without changing the existing helper's signature
  - [ ] (P2) Pin the rule that a roadmap snapshot inherits the roadmap's provenance
- [ ] (P2) Stamp the authoring commit onto plans, status reports and new decision records
  - [ ] (P2) Add a full-length commit helper that mirrors the existing environment contract
  - [ ] (P3) Document the two new fields in the document schema
- [ ] (P3) Record build provenance once on the publish manifest rather than on every rendered page
- [ ] (P2) Backfill the merge commit onto documents once they land on the default branch
  - [ ] (P2) Run the backfill from the release routine rather than a git hook
- [ ] (P2) Verify document citations against the commit the document was written against
  - [ ] (P2) Separate a fabricated citation from one that merely drifted
  - [ ] (P2) Refuse to fall back to the current checkout when the recorded commit cannot be resolved
  - [ ] (P3) Record that document provenance depends on merge commits, not squash merges
