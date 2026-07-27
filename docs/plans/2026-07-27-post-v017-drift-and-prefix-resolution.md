---
date: 2026-07-27
slug: post-v017-drift-and-prefix-resolution
title: Clear post-v0.17.0 drift and fix the prefix-ULID log corruption
epic: 01KYJYG4PX7NVTS1CZQ8MPES7T
items: [01KYJYG4PY6TE6ZTZMF8CV2VFT, 01KYJYG4PYDA4H10JXXRDRCXPZ, 01KYJYG4PY8S8RZNB9AYP3G8GW, 01KYJYG4PYFFTK74AZ7RW90M7R, 01KYJYG4PYJRAFEHJCP51XVCRA]
---

# Clear post-v0.17.0 drift and fix the prefix-ULID log corruption (#123)

## Context

v0.17.0 shipped cleanly: `main` == `origin/main`, working tree clean apart from
untracked `.claude/worktrees/`, zero open PRs, zero unmerged remote branches,
tag + changelog + frozen design docs + wiki all in place. Nothing is mid-flight.

But a status sweep of `.work/todo.jsonl` against the actual repo turned up four
pieces of drift that the generated roadmap cannot show, plus concrete forensic
evidence that open bug #123 has already corrupted this repo's own work log:

- `bin/worklog trace-check` reports a node with id `01KYA8MD` — an 8-character
  ULID prefix that exists as its own ghost item. That is exactly the failure
  #123 describes, having already happened here.
- Item **#184 "Release v0.16.0"** is still `todo` while v0.16.0, v0.16.1 *and*
  v0.17.0 are all tagged and released. The roadmap renders a phantom v0.16.0
  milestone because of it.
- Epic **#144 "Branch-discipline hooks"** is still `todo` with all 9 children
  `done`. `render_roadmap` only renders epics that have open children, so this
  epic is invisible on the roadmap while still counting as open work — it rots
  silently.
- `hooks/session-doctor.sh:12` string-compares `core.hooksPath != "hooks"`.
  This repo's `core.hooksPath` is the **absolute** path
  `/Users/richardhightower/clients/spillwave/src/wiki_ticket_sdd/hooks` —
  correctly wired, and absolute is the form that actually works from a git
  worktree, where a relative `hooks` resolves against the wrong CWD. The doctor
  fires a false "run /worklog:init to repair" alarm at the top of every session
  on a healthy repo, which trains the reader to ignore doctor output.
- Two worktrees under `.claude/worktrees/` (`agent-a507f94b54428bcb1` → PR #103,
  `docs-sync-v0.16.0` → PR #186) are fully merged into `main` and abandoned.

Outcome: an honest work log, a doctor whose warnings mean something, and the P1
corruption bug fixed at its root so the log stops growing ghosts.

## Work tracking (do this first)

Per `CLAUDE.md`, record before building. On a new branch — the branch guard
rejects commits on `main`, and `hooks/commit-msg` requires a ULID or ticket
reference in every message.

```
git checkout -b fix/prefix-resolution-and-drift
bin/worklog update <ulid-123> --status in_progress          # existing item #123
bin/worklog add "session-doctor false-alarms on an absolute core.hooksPath" \
    --level task --kind bug --priority P2 \
    --unplanned --discovered-during <ulid-123>
```

The two stale closes and the worktree prune are bookkeeping on existing items,
not new work — no new items for those.

## Step 1 — Close the stale items

```
bin/worklog close <ulid-184> --resolution "v0.16.0 shipped 2026-07-26 (tag v0.16.0); \
  superseded by v0.16.1 and v0.17.0"
bin/worklog close 01KYBD2HYJVNHX698WR1JD96YC --resolution "all 9 children done; \
  hooks shipped in v0.16.0"
```

Resolve #184's full ULID with `bin/worklog fold` first — **do not pass a prefix
to `close` until Step 3 lands**; that is the bug being fixed. Epic #144's full
ULID is given above.

## Step 2 — Fix the session-doctor false alarm

Root cause is a literal string compare in three places that must stay in sync:

- `hooks/session-doctor.sh:12` — the live SessionStart hook
- `plugin/hooks/scripts/session-doctor.sh:12` — byte-identical mirror (verified
  with `diff`); both must change together
- `plugin/scripts/doctor.sh:61-65` — the `/worklog:doctor` command

Replace the equality test with one that accepts either the relative `hooks` or
any path that resolves to the repo's own `hooks` directory. Keep it to a few
lines of shell — no new helper file:

```sh
hp=$(git config core.hooksPath 2>/dev/null || true)
# absolute is legitimate: a relative "hooks" resolves against CWD and breaks in worktrees
if [ "$hp" != "hooks" ] && [ "$(cd "${hp:-/nonexistent}" 2>/dev/null && pwd -P)" != "$(pwd -P)/hooks" ]; then
  fails+=("git core.hooksPath is '${hp:-unset}' — run /worklog:init to repair")
fi
```

`plugin/scripts/init.sh:95` keeps setting the relative `hooks`; this change only
widens what the doctor *accepts*, so `tests/test_plugin.py:126`
(`assertEqual(hookspath, "hooks")`) still passes untouched.

Verify: with the current absolute `core.hooksPath`, `bash hooks/session-doctor.sh`
must print nothing, and `bash plugin/scripts/doctor.sh` must report the hook
wiring OK.

## Step 3 — Fix #123 at the root

`bin/worklog` already resolves id prefixes correctly in **three** places, each a
copy of the same four lines (`bin/worklog:153` in `cmd_reopen`, `:234` in
`cmd_resolve`, `:293` in `cmd_show`):

```python
match = [i for k, i in r.items.items() if k.startswith(a.item)]
if not match:
    sys.exit(f"worklog: no item matching {a.item}")
item = match[0]
```

`cmd_close` and `cmd_update` skip it entirely, and that omission is the bug:

- `cmd_close` calls `base(a.item, "close", ...)` on the raw string, appending a
  close event under the prefix — which folds into a brand-new orphan item.
- `cmd_update` does `fold(...).items.get(a.item, {})`, so a prefix yields `{}`;
  `check_taxonomy` then runs against `level=None` and the
  "closed items need `reopen`" guard is silently skipped.

The fix is to extract the duplicated block into one module-level helper beside
`_require_item` and route all five commands through it — a smaller diff than the
code it replaces, and it fixes both symptoms at the single point all callers pass
through:

```python
def _resolve(item):
    """Resolve a full ULID or unambiguous prefix to the real item (bug #123).
    close/update wrote events under the raw prefix, minting orphan ghost items."""
    _require_item(item)
    r = fold([LOG, ".work/done.jsonl"])
    match = [i for k, i in r.items.items() if k.startswith(item)]
    if not match:
        sys.exit(f"worklog: no item matching {item}")
    if len(match) > 1:
        sys.exit(f"worklog: {item} is ambiguous: {', '.join(i['id'] for i in match)}")
    return match[0]
```

Then in `cmd_close` and `cmd_update`, resolve once and use `item["id"]` for the
event id and `item` for the current-state checks — never `a.item`. Point
`cmd_reopen` / `cmd_resolve` / `cmd_show` at the helper too, deleting their
copies.

The ambiguity check is new behaviour but is the correct edge case: two items
sharing a prefix previously took `match[0]` arbitrarily. Erroring is right for a
write path, and `cmd_show` erroring on an ambiguous prefix is an improvement over
silently showing one of them.

**Do not** try to repair the existing `01KYA8MD` ghost in this pass. The log is
append-only and event-sourced; rewriting history is a separate decision. Note it
in the PR body and let it stand as the bug's evidence.

### Test

Add to `tests/test_taxonomy.py` (which already covers `check_taxonomy` on
update) or a small new `tests/test_resolve.py`, following the existing
`tempfile.mkdtemp` + subprocess-CLI pattern used across `tests/`:

1. `add` an item, `close` it by 8-char prefix → the real item is `done` and
   `fold` gains **no** new item.
2. `update --status` by prefix on a closed item → exits non-zero telling the
   caller to use `reopen` (proves the guard now fires).
3. `close` a non-existent prefix → exits non-zero, log unchanged.
4. Two items sharing a prefix → `close` exits with the ambiguity error.

## Step 4 — Prune the merged worktrees

Both branches are contained in `main`; confirm before removing.

```
git worktree remove .claude/worktrees/agent-a507f94b54428bcb1
git worktree remove .claude/worktrees/docs-sync-v0.16.0
git worktree prune
```

Leaves the two scratchpad worktrees alone — they live outside the repo and are
cleaned up by the harness.

## Step 5 — Close out

```
bin/worklog close <ulid-123> --resolution "close/update now resolve id prefixes \
  via shared _resolve(); ambiguous prefixes error"
bin/worklog close <ulid-doctor> --resolution "doctor accepts an absolute hooksPath \
  resolving to ./hooks"
bin/worklog roadmap-render     # required before committing
git add -A && git commit       # message must cite the ULIDs
gh pr create                   # use the pr-description skill
```

Merge via the **merge-green** skill — poll until every gate is green, never
`--admin`. After merge, `bin/worklog sync`.

## Critical files

| File | Change |
|---|---|
| `bin/worklog` | New `_resolve()` helper; `cmd_close`/`cmd_update` routed through it; `cmd_reopen`/`cmd_resolve`/`cmd_show` deduped onto it |
| `hooks/session-doctor.sh` | hooksPath check accepts an absolute path resolving to `./hooks` |
| `plugin/hooks/scripts/session-doctor.sh` | identical mirror — must match byte-for-byte |
| `plugin/scripts/doctor.sh` | same widened check |
| `tests/test_taxonomy.py` (or new `tests/test_resolve.py`) | prefix-resolution regression tests |
| `.work/todo.jsonl` | via `bin/worklog` only — never hand-edited |
| `docs/roadmap.md` | regenerated by `roadmap-render`, never hand-edited |

## Verification

1. `python3 tests/test_taxonomy.py` (or the new file) — new prefix cases pass.
2. `for t in tests/test_*.py; do python3 "$t"; done` — full suite green;
   `test_plugin.py` in particular must still pass unchanged.
3. `bash hooks/session-doctor.sh` prints nothing on this repo (currently prints
   the false alarm). Re-check after `git config core.hooksPath hooks` too — both
   forms must be accepted.
4. `bash plugin/scripts/doctor.sh` reports hook wiring OK.
5. Live repro of the bug being gone: in a scratch repo, `worklog add` then
   `worklog close <8-char-prefix>`; `worklog fold` shows one item, status
   `done`, and no ghost.
6. `bin/worklog roadmap-render && git diff docs/roadmap.md` — the phantom
   v0.16.0 milestone section is gone and the open count drops from 13 to 10.
7. `git worktree list` shows only the main checkout (plus harness scratchpads).
8. Coverage stays ≥80% on `bin/*.py` (CI gate).

## Out of scope

- Repairing the existing `01KYA8MD` ghost item — append-only log, separate call.
- The 167 `trace-check` unlinked-evidence gaps — pre-existing, mostly historical
  items with no plan link; a backfill is its own piece of work.
- P2 bugs #141, #142, #137 and feature #138 — deliberately deferred this session.

## Tasks

- [ ] (P2) Accept an absolute core.hooksPath in the doctor checks
  The session-start health check compares the configured git hooks path
  against the literal string "hooks", so a repo wired with the full absolute
  path — the form that actually works inside a git worktree — is reported as
  broken every session. Widen the check to accept any path that resolves to
  the repo's own hooks directory, in the session hook, its plugin mirror, and
  the doctor command.

- [ ] (P1) Resolve work-item id prefixes in close and update
  Closing or updating an item by the short 8-character id that the tool itself
  prints creates a brand-new phantom item instead of touching the real one,
  silently corrupting the work log. Three other commands already resolve short
  ids correctly; extract that logic into one shared helper, route every command
  through it, and error clearly when a short id matches more than one item.

- [ ] (P1) Regression tests for id-prefix resolution
  Cover the cases that were broken: closing by short id updates the real item
  and creates no phantom, updating a closed item by short id is refused, an
  unknown id fails loudly, and an ambiguous short id names the candidates.

- [ ] (P2) Close out stale work-log bookkeeping
  Two items no longer reflect reality: a release task for a version that
  shipped three releases ago, and an epic whose every child is finished but
  which is itself still open — and therefore invisible on the generated
  roadmap. Close both and regenerate the roadmap.

- [ ] (P3) Remove two abandoned git worktrees
  Two worktrees left over from earlier agent runs sit in the repo; both of
  their branches are already merged. Remove them so the working tree is clean.
