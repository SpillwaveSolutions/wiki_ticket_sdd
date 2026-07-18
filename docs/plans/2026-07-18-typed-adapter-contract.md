---
date: 2026-07-18
slug: typed-adapter-contract
title: Typed Adapter Contract for ticket-sync
epic: 01KXV0NQPPPK2K948CK20QJSS1
items: [01KXV0NQPPPK2K948CK20QJSS1]
status: planned — not yet scheduled; implementation tasks attach to the epic when work starts
origin: authored by Rick with the claude.ai design session, stored verbatim
---

# Spec: Typed Adapter Contract for `ticket-sync`

**Target repo:** `SpillwaveSolutions/wiki_ticket_sdd` (at/after `v0.5.0`)
**Deliverable:** a typed process boundary between the generic `worklog` core and per-system ticketing, so the sync invariants that are currently prose in `ticket-sync/SKILL.md` become executable against a fake — with **no live tracker required** to test them.
**Audience:** Claude Code, implementing directly in the repo. And a human reviewer.

---

## 0. Read first

Before writing anything, read these files in the repo so this layer matches what already ships:

- `bin/worklog` — note `cmd_ingest` (deterministic `ev`, `--system/--key/--rev/--rev-ts-ms/--set`), `INGEST_FIELDS`, `STATUSES`, `PRIORITIES`.
- `bin/fold.py` — the canonical item shape and `_conflicts` handling.
- `.claude/skills/ticket-sync/SKILL.md` — the prose invariants this layer will make testable. Sections 3 (canonical hash), 4 (idempotency marker), 8 (pull) are the ones being promoted to code.
- `.work/config.yml` — the `ticketing:` block.
- `.work/sync-state.json` semantics as referenced by the skill (`last_pushed_hash`, `cursors.<system>`).
- `docs/worklog-spec.md` §9, §10.3, §10.5, §10.6, §15.

**Do not change** `fold.py`, `ulid.py`, or the event-log format. This layer sits beside the existing sync, it does not alter the core.

---

## 1. Why this exists (the one-paragraph rationale)

v0.5 moved ticketing from a per-system adapter binary to a skill with no per-system code. That won portability (Codex/OpenCode with zero port) but demoted three invariants from code-enforced to prose-enforced: **idempotency** (search-before-create), **pull parsing** (extracting the fields that seed the deterministic `ev`), and **capability degradation** (what happens when a tracker has no epic type). This layer restores a **typed contract** at the boundary — a schema plus a dispatcher — while keeping the per-platform mapping in an AI-generated adapter. The point is not "define the CLI." The point is that a **fake adapter** lets CI test those three invariants without a network, which is exactly what regressed.

The design rule that keeps this from re-creating the maintenance burden it escaped: **the dispatcher owns every invariant; the adapter is a dumb translator.** If idempotency logic leaks into the adapter, this has failed.

---

## 2. Architecture

```
worklog sync (skill or command)
        │
        ▼
bin/sync_dispatch.py        ← owns hash, marker, scope, echo suppression, capabilities check
        │  JSON over stdin/stdout, one process call per verb
        ▼
$WORKLOG_TICKET_ADAPTER      ← dumb translator: canonical JSON ⇄ platform API. Generated at setup.
        │
        ▼
  gh / jira / az / glab       ← real CLI for the target system
```

- **Dispatcher** (`bin/sync_dispatch.py`, new): the only place that knows the sync rules. Never calls a tracker directly. Calls the adapter's verbs and makes all create-vs-update / conflict / scope decisions itself.
- **Adapter** (`$WORKLOG_TICKET_ADAPTER`, generated): a single executable. Maps a canonical item to the platform and back. Contains **zero** worklog invariant logic — no hashing, no marker search, no scope. It creates when told to create, updates when told to update.
- **Fake adapter** (`adapters/fake/adapter`, shipped): a reference implementation backed by a local JSON file instead of a tracker. Satisfies the contract exactly. This is what the invariant tests run against.
- **Example adapter** (`adapters/github/adapter`, shipped): one worked, real implementation over `gh`. Generation adapts *this*, it does not write from scratch.

`WORKLOG_TICKET_ADAPTER` unset or the file missing → dispatcher runs **local-only** and says so (spec §15.8). Never an error.

---

## 3. The contract

Five verbs. JSON on stdin where noted, JSON (or NDJSON) on stdout, meaning in the exit code. The adapter reads config-forwarded connection details from env (`WORKLOG_TICKET_SYSTEM`, `WORKLOG_TICKET_PROJECT`, plus whatever that system needs), never from argv.

### 3.1 `capabilities`

No input. Stdout: a capabilities object. **The dispatcher calls this first, every run, and validates it against the schema before any push.** This is the gate that makes a generated adapter safe — a subtly wrong adapter fails here, at a typed boundary, not three steps later as a silent mis-map.

```json
{
  "system": "github",
  "supports": ["push", "pull", "get", "close"],
  "types": {"epic": null, "story": "Issue", "task": "Issue", "subtask": "Issue", "bug": "Issue"},
  "marker": {"style": "html_comment", "template": "<!-- worklog:{ulid} -->"},
  "fields": {"parent": "task-list", "depends_on": "unsupported", "assignee": "assignee"},
  "max_title": 256
}
```

- `types`: canonical type → platform type name, or `null` if the platform has no equivalent (GitHub has no epic). `null` triggers the documented degrade (§6.3), deterministically.
- `marker`: how the idempotency key is embedded. The **dispatcher** owns marker logic; this only tells it the syntax.
- `fields.depends_on: "unsupported"` → dispatcher stops trying to sync that field and notes it in the drift report. Never errors.

### 3.2 `push`  — stdin: one canonical item + an explicit op

**The dispatcher has already decided create vs update** (via §4). The adapter does not search, does not dedupe. It does what `op` says.

Stdin:
```json
{
  "op": "create",
  "key": null,
  "marker": "<!-- worklog:01J8X0M2QQ -->",
  "item": { }
}
```

Stdout:
```json
{"key": "SpillwaveSolutions/wiki_ticket_sdd#412", "url": "https://...", "rev": "2026-07-18T15:39:58Z", "hash": null}
```

`rev` is the platform's post-write revision stamp (updated_at / changelog id). The dispatcher writes `last_pushed_hash` itself from the canonical hash it computed; `hash` in the response may be `null`.

### 3.3 `pull`  — argv: `--since <rev>` `[--keys k1,k2]`

Stdout: **NDJSON**, one canonical item per line, each carrying `external.key` and `external.rev`. This is the verb whose output seeds `worklog ingest`, so the fields it emits are the fields the deterministic `ev` is built from — `system`, `key`, `rev` must be exact and stable. A mis-parse here corrupts the dedupe key silently, which is why §7.2 tests it hardest.

```json
{"external":{"key":"...#412","rev":"2026-07-18T16:02:11Z"},"id":"01J8X0M2QQ","title":"...","status":"in_progress","priority":"P0","labels":["backend"]}
```

The adapter extracts the `id` from the marker in the ticket body. A ticket with no worklog marker is **remote-origin** — emit it with `id: null` and let the dispatcher decide (default: create a local item; that's how a ticket filed by hand in Jira enters the log).

### 3.4 `get <key>` — stdout: one canonical item. For targeted reconcile of a closed/out-of-window item (spec §10.5 escape hatch).

### 3.5 `close <key> <resolution>` — stdout: `{"key","rev"}`. Maps to the platform's close/resolve.

### 3.6 Exit codes (identical to spec §9.1, now enforced by the dispatcher)

| Code | Meaning | Dispatcher behavior |
|---|---|---|
| 0 | success | continue |
| 2 | auth failure | abort sync, tell the human to re-auth |
| 3 | not found | clear `external`, mark for re-push |
| 4 | rate limited / transient | retry w/ backoff ×3, then defer |
| 5 | remote conflict | emit `op:"conflict"` event |
| 1 | other | report, continue with next item |

---

## 4. What the dispatcher owns (and the adapter must never touch)

This section is the whole design. Implement every item here in `sync_dispatch.py`; ensure **none** of it appears in any adapter.

1. **Scope** (spec §10.5). Open items ∪ items whose canonical hash ≠ `last_pushed_hash` ∪ `--keys`. Closed+in-sync items are inert.
2. **Canonical hash** (spec §10.3): `sha256(canonical_json({title,body,type,status,priority,parent,labels,assignee}))[:16]`, sorted keys, no whitespace, set-valued arrays sorted. Reuse the exact function the skill specifies; factor it into `bin/canonical.py` and have both call it.
3. **Idempotency / create-vs-update.** BEFORE calling `push`, the dispatcher determines whether the item already exists remotely: if the item has `external.key`, it's an update; else the dispatcher asks the adapter to `pull --keys` by marker OR (first sync) trusts local `external` absence. The **adapter never decides this.** The marker travels in the `push` payload so the adapter can embed it, but the search that prevents duplicates is the dispatcher's.
4. **Echo suppression** (spec §10.3): after a successful push, write `last_pushed_hash`. On pull, ingest a remote change only if its canonical hash ≠ `last_pushed_hash`. Per-clone, in `.work/sync-state.json`.
5. **Conflict detection** (spec §10.6): both-sides-changed since `last_pushed_hash` → emit `worklog conflict`, do not auto-resolve under the default `report` policy.
6. **Capabilities validation:** call `capabilities`, validate against `schema/capabilities.schema.json`, refuse to proceed on a schema violation with a clear message naming the offending field.
7. **`worklog ingest` invocation:** build the `--system/--key/--rev/--rev-ts-ms/--set` call from pull output. This is the seam to §10.2; the dispatcher owns the field extraction, the adapter only provides clean NDJSON.

---

## 5. Setup & generation

`worklog adapter init` (new subcommand or a step in `/worklog:init`):

1. Read `ticketing.system` from config.
2. If an adapter for that system already exists in `adapters/<system>/adapter`, point `WORKLOG_TICKET_ADAPTER` at it and run `worklog adapter check`.
3. Otherwise **generate** by adapting `adapters/github/adapter` (the worked example) to the target platform's CLI — this is the skill/AI step. Generation fills in a known shape; it does not invent one.
4. Run `worklog adapter check` and refuse to activate an adapter that fails.

`worklog adapter check`:

- Runs the fake-suite (§7) against the **generated** adapter where possible (capabilities schema, exit-code contract, round-trip shape).
- For verbs that need a live tracker, runs a `--dry-run` that validates I/O shape without mutating the remote.
- Green → writes the `WORKLOG_TICKET_ADAPTER` path into `.work/sync-state.json` (per-clone) or prints the export line. Red → prints the contract violation and stops.

**Generation is only trustworthy because `check` validates the generated thing against the contract.** Ship the fake and the one example; never ask the model to write an adapter from a blank file.

---

## 6. Adapter authoring rules (goes in `adapters/README.md`)

1. **Translate, don't think.** No hashing, no marker search, no scope, no conflict logic. Create when `op:"create"`, update when `op:"update"`.
2. **Env for connection, stdin for data, argv for flags.** Never parse item data from argv (bodies contain newlines).
3. **Stdout is data only.** All logging to stderr. One JSON object (or NDJSON for pull) on stdout, nothing else.
4. **Exit codes carry meaning** (§3.6). A rate limit is `4`, not `1`.
5. **`capabilities` must be honest.** If the platform has no epic, say `"epic": null`. Lying here defeats the gate.
6. **Degrade, never crash.** Unsupported field → omit it and let the dispatcher report drift.

---

## 7. Tests (the actual deliverable)

These are why the contract exists. All run in CI with **no network**, against the fake.

### 7.1 Idempotency — the invariant that regressed

```
test_push_twice_same_ulid_is_one_ticket:
    dispatcher.push(item)          # fake starts empty → create
    dispatcher.push(item)          # hash unchanged → skipped OR update, never a 2nd create
    assert fake.ticket_count() == 1
    assert fake.saw_create_once()
```

```
test_retry_after_transient_does_not_duplicate:
    fake.fail_next(code=4)         # rate limit on first attempt
    dispatcher.push(item)          # dispatcher retries
    assert fake.ticket_count() == 1
```

### 7.2 Pull → deterministic `ev` — the seam flagged hardest

```
test_pull_output_yields_stable_ev_across_runs:
    ndjson = dispatcher.pull(since=rev)
    ev1 = ingest_events_from(ndjson)
    ev2 = ingest_events_from(ndjson)      # same input, different run/clone
    assert [e["ev"] for e in ev1] == [e["ev"] for e in ev2]   # byte-identical ev
```

```
test_two_clones_polling_same_change_dedupe:
    # the §10.2 property, end to end through the contract
    log = clone_A.pull_and_ingest() + clone_B.pull_and_ingest()
    assert fold(log).items[id] applied once   # dedupe by ev
```

### 7.3 Capabilities gate

```
test_malformed_capabilities_is_rejected_before_push:
    fake.capabilities = {"system": "x"}        # missing required fields
    with raises(ContractError, match="supports"):
        dispatcher.sync()
    assert fake.ticket_count() == 0            # nothing pushed
```

```
test_no_epic_type_degrades_deterministically:
    fake.capabilities.types["epic"] = None
    r = dispatcher.push(epic_item)
    assert r.mapped_type == fake.capabilities.types["story"]   # documented fallback
    assert "epic mapped to story" in drift_report()
```

### 7.4 Conflict path (already shipped in worklog; assert the dispatcher drives it)

```
test_both_sides_changed_records_conflict_not_overwrite:
    local: priority P1→P2 ; remote: priority P0
    dispatcher.sync()
    assert last_event.op == "conflict"
    assert item.priority == "P2"               # local unchanged under report policy
```

### 7.5 Local-only degrade

```
test_missing_adapter_is_local_only_not_error:
    unset WORKLOG_TICKET_ADAPTER
    r = dispatcher.sync()
    assert r.ok and r.mode == "local-only"
```

### 7.6 Adapter dumbness (the architectural guard)

```
test_adapter_contains_no_invariant_logic:
    src = read(example_adapter)
    for banned in ("sha256", "last_pushed_hash", "worklog:", "canonical_json"):
        assert banned not in src   # invariants live in the dispatcher, not here
```

`test_adapter_dumbness` is the test that keeps the design honest over time — it fails the day someone "helpfully" moves marker-search into the adapter.

---

## 8. Files to create

```
bin/sync_dispatch.py               # the dispatcher; owns §4
bin/canonical.py                   # shared canonical_json + hash (factor out of the skill)
schema/capabilities.schema.json    # validates §3.1
schema/adapter-io.schema.json      # validates push/pull payloads
adapters/README.md                 # §6 authoring rules
adapters/fake/adapter              # reference double; backs the §7 tests
adapters/github/adapter            # one worked example over `gh`
tests/test_dispatch.py             # §7.1–7.5
tests/test_adapter_contract.py     # §7.6 + schema round-trips
```

Wire `tests/` into `.github/workflows/worklog.yml`.

`worklog adapter init|check` added to `bin/worklog`. `ticket-sync/SKILL.md` updated: the invariant sections (3,4,8) now say "the dispatcher enforces this" and point here; the skill's job shrinks to "run `worklog adapter check`, then `worklog sync`, then read the drift report."

---

## 9. Non-goals

- Not rebuilding maintained per-system binaries. Adapters are generated/adapted from the example, not shipped per tracker.
- Not moving mapping logic out of the AI's hands — mapping stays in the adapter, which is where per-platform knowledge belongs.
- Not changing the event log, fold, or `ulid.deterministic`. Those shipped correct in v0.5; this layer feeds them.
- Not requiring a live tracker for CI. If a test needs the network, it's the wrong test — use the fake.

---

## 10. Definition of done

1. `sync_dispatch.py` owns every §4 invariant; `test_adapter_dumbness` passes.
2. `adapters/fake/adapter` + `adapters/github/adapter` both satisfy `schema/*.json`.
3. All §7 tests pass in CI with no network.
4. `worklog adapter check` refuses a contract-violating adapter with a field-named error.
5. Missing adapter → local-only, no error.
6. `ticket-sync/SKILL.md` no longer carries the hash/marker/scope logic as prose it hopes the model honors — it delegates to the dispatcher and points here.
7. The v0.5 guarantees still hold: `test_ulid.py::TestTheBugThisPrevents` green, deterministic `ev` unchanged.
