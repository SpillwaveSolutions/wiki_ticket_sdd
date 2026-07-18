# Worklog: Visible-WIP Work Tracking Spec

**Version:** 1.3
**Status:** Implemented through §18 step 4 (this repo)

**Changes since 1.2:** §8.2 corrected by measurement — git's `ort` union driver *repairs* a missing final newline at merge time; the real fusion risk is the local append path, and `append()` now self-heals it. Added `hooks/pre-merge-commit` (merge auto-commits bypass `pre-commit`), mktemp in the freshness check, and a PR-simulation integration suite (`tests/test_integration.py`).

**Changes since 1.1:** reference implementation + 32 passing tests added as Appendix A; repo skeleton as Appendix B; two spec bugs found by implementing it — `item` is not required on `compact` events (§5.2), and §7's `_moved` tombstone was redundant and is removed.

**Changes since 0.1:** `bin/` and sync scratch paths added to the layout (§3); ingested-event `ts` corrected (§10.2); open question #2 closed via config-only settings + agent-file symlink (§4.1); status reports rewritten into three named kinds with frozen semantics (§13.3).
**Audience:** Implementers of the skill pack; junior devs and PMs reading the generated roadmap.

---

## 1. Purpose

A local-first, git-native work tracking layer for agentic coding (Claude Code, Grok build, or any harness that can read `CLAUDE.md` and run scripts).

Three properties drive every decision:

1. **Visible WIP.** Everything in flight is in the repo, in the ticketing system, and on the wiki. No hidden work.
2. **Plans produce tickets.** Planning that doesn't emit tracked items is planning that evaporates.
3. **Generic core, pluggable edges.** The core never knows the word "Jira." Ticketing and wiki specifics live in separate, swappable adapter skills.

---

## 2. Goals and non-goals

### Goals

- Append-only event log of work items in the repo, mergeable across branches and devs.
- Human-readable roadmap, plans, and status reports generated from that log.
- Best-effort bidirectional sync with one ticketing system (Jira / Azure DevOps / GitHub Issues).
- Publish to one wiki (Confluence / GitHub Wiki / ADO Wiki).
- Capture unplanned work discovered mid-flight, attributed to what it interrupted.

### Non-goals

- **Not** a replacement for the ticketing system. It's a mirror with a local source of truth.
- **Not** strongly consistent. Drift happens; the spec's job is to make drift *visible*, not impossible.
- **Not** a scheduler, estimator, or burndown tool. Those read the log; they aren't in it.
- **No** hand-editing of generated artifacts. Humans change work through the agent, not by editing `roadmap.md`.

---

## 3. Repository layout

```
CLAUDE.md                        # policy prose + pointer to config
AGENTS.md -> CLAUDE.md           # symlink; see §4.1
.work/
  config.yml                     # machine-readable settings (committed)
  todo.jsonl                     # append-only event log, open items
  done.jsonl                     # append-only, closed items (written by compactor only)
  published.json                 # doc path -> wiki page id/url (committed)
  sync-state.json                # per-clone sync bookkeeping (GITIGNORED)
  changeset.json                 # sync phase-1 output (GITIGNORED)
  results/                       # sync phase-2 output (GITIGNORED)
    ticket.json
    wiki.json
  schema/
    item.schema.json
    event.schema.json
bin/
  worklog                        # CLI entry point; everything below is a subcommand
  fold.py                        # state derivation (§6)
  compact.py                     # §7, CI-only
  render_roadmap.py              # §13.1
  ulid.py
.claude/skills/                  # or .grok/skills/ — see §4.1
docs/
  roadmap.md                     # GENERATED, CI-guarded
  plans/
    2026-07-16-auth-refactor.md  # written once, never regenerated
  status/
    2026-07-16-daily.md          # frozen once published
    2026-07-13-weekly.md
    2026-07-16-timecard.md
```

`.gitignore` must contain `.work/sync-state.json`, `.work/changeset.json`, and `.work/results/`.

**Why sync scratch lives in `.work/` and not `/tmp`:** a failed sync leaves `changeset.json` and whatever `results/` got written on disk, next to the log they describe. That's the difference between a debuggable failure and a mystery.

---

## 4. Configuration

### 4.1 The agent file — policy only

Prose the model reads. **Contains no values the scripts need**, which is what closes the Claude Code / Grok Build parity question: every real setting is in `.work/config.yml`, so the agent file is a thin policy document and `AGENTS.md` is a symlink to `CLAUDE.md`. One file, one policy, no fork. Skills are discovered per-harness (`.claude/skills/`, `.grok/skills/`); the `bin/worklog` CLI is identical under both.

Do not write harness-specific notes into the policy. "Grok reads this file too" is a fact about Grok that only Claude will ever read.

Recommended block:

```markdown
## Work tracking policy

- Work items live in `.work/todo.jsonl`. Settings live in `.work/config.yml`. Read the
  config file; do not infer settings from this document.
- **Exiting plan mode is not optional bookkeeping.** Every plan MUST end by running
  `worklog plan-capture`, which writes `docs/plans/<date>-<name>.md` and appends the
  plan's steps as work items.
- **Plans are the permanent design record.** `docs/plans/` is where the *why* lives —
  it is the specification half of spec-driven development, and it is checked into the
  repo and published to the wiki for exactly that reason. A plan is written once and
  never regenerated or rewritten. If the design changed, write a NEW plan that
  supersedes the old one; do not edit history. When you need to know why a decision
  was made, read the plan, not the ticket.
- If you discover work mid-flight that was not in the plan (a bug, a missing migration,
  a broken test), run `worklog add --unplanned --discovered-during <current-item>`
  BEFORE doing the work. Do not silently absorb it.
- When a plan is complete, run `worklog sync`. This closes items, moves them to
  `done.jsonl`, updates the ticketing system, regenerates the roadmap, and publishes.
- When asked for a status report, run `worklog status --kind <daily|weekly|timecard>`.
  It writes `docs/status/<date>-<kind>.md`, commits it, and publishes it to the wiki.
  Never paste a status report into chat without writing the file — an unrecorded status
  report is a rumour.
- Status reports are FROZEN once published. If last Tuesday's daily is wrong, write a
  correction in today's report. Do not regenerate an old one.
- Never hand-edit `docs/roadmap.md`. It is generated. To change the roadmap, change
  the work items.
- Never edit `.work/*.jsonl` with a text editor or a shell redirect. Use `worklog`.
```

### 4.2 `.work/config.yml` — settings only

```yaml
version: 1

project:
  key: PROJ                    # prefix for human-facing item refs
  name: "Acme Platform"

ticketing:
  system: jira                 # jira | ado | github | none
  adapter: ticket-jira         # skill/binary name; resolved via $PATH or .claude/skills
  project: PROJ
  # everything below here is adapter-specific and passed through untouched
  options:
    site: acme.atlassian.net
    epic_link_field: customfield_10014

wiki:
  system: confluence           # confluence | github-wiki | ado-wiki | none
  adapter: wiki-confluence
  root_url: https://acme.atlassian.net/wiki/spaces/ENG
  options:
    space: ENG
    root_page_id: "12345"

paths:
  plans: docs/plans
  status: docs/status
  roadmap: docs/roadmap.md

status:
  default_kind: daily
  week_starts: monday
  timecard:
    include_hours: false       # see §17 open question 4
    actor: rick                # whose work the timecard covers
  publish: true                # push status reports to the wiki on generation

sync:
  active_window_days: 14       # scope of `sync --scope active`
  conflict_policy: report      # report | local-wins | remote-wins
  push_on_capture: true
```

**Not configurable, deliberately:** the body-size cap (§8.3) is derived from `PIPE_BUF`, not chosen. It lives in the code as a constant with a comment. Exposing it as `max_body_kb` invites someone setting it to 64 and silently losing atomic appends — a knob whose only valid value is the default is a trap, not a feature.

**Resolution rule:** the core reads `ticketing.adapter`, resolves that name to an executable, and shells out. It never branches on `ticketing.system` beyond `none`. If the adapter is missing, the core degrades to local-only and emits a warning — it does not fail.

---

## 5. Data model

### 5.1 The log is a sequence of events, not snapshots

Each line of `todo.jsonl` is one immutable event. State is a **fold** over events. This is what makes concurrent multi-dev edits merge instead of clobber.

```jsonl
{"ev":"01J8X2K4A0","ts":"2026-07-16T14:02:11Z","actor":"rick","item":"01J8X0M2QQ","op":"create","set":{"type":"task","title":"Extract auth middleware","parent":"01J8WZZ100","status":"todo","priority":"P1"}}
{"ev":"01J8X2M900","ts":"2026-07-16T14:09:03Z","actor":"rick","item":"01J8X0M2QQ","op":"update","set":{"status":"in_progress"}}
{"ev":"01J8X4RR10","ts":"2026-07-16T15:40:00Z","actor":"jira","item":"01J8X0M2QQ","op":"update","set":{"priority":"P0"},"src":{"system":"jira","key":"PROJ-412","rev":"2026-07-16T15:39:58Z"}}
```

### 5.2 Event envelope

| Field | Type | Req | Notes |
|---|---|---|---|
| `ev` | ULID | yes | Event ID. Primary sort key and dedupe key. |
| `ts` | RFC3339 UTC | yes | Human/debug timestamp. **Not** used for ordering. |
| `actor` | string | yes | `rick`, `claude`, `jira`, `sync`, `compactor`. Who caused this. |
| `item` | ULID | yes* | The work item this event concerns. *Except `op: compact`, which is log-level, not item-level — see §7. Validators must special-case it. |
| `op` | enum | yes | See 5.3. |
| `set` | object | — | Scalar field assignments. |
| `add` / `del` | object | — | Set-valued field mutations (see 5.5). |
| `src` | object | — | Provenance for ingested remote changes: `{system, key, rev}`. |
| `note` | string | — | Free text; shown in history, never parsed. |

### 5.3 Operations

| `op` | Meaning |
|---|---|
| `create` | First event for an item. `set` must include `type` and `title`. |
| `update` | Field changes. |
| `close` | Sets `status` to `done` or `cancelled`; requires `set.status` and optional `set.resolution`. |
| `reopen` | Moves a closed item back. The compactor pulls it from `done.jsonl` on next run. |
| `link` | Records external identity: `set.external`. Emitted after a successful adapter push. |
| `conflict` | Records an unresolved both-sides-changed field. Never changes state; surfaced in reports. |
| `snapshot` | Compactor output only. Full item state; supersedes all events with `ev` ≤ watermark. |
| `compact` | Compactor watermark marker. `{"op":"compact","through":"<ulid>"}` |

### 5.4 Item fields

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | Implicit (the `item` field). **The primary key, always.** |
| `type` | `epic` \| `story` \| `task` \| `subtask` \| `bug` | |
| `title` | string | ≤ 120 chars. |
| `body` | markdown | Optional longer description. |
| `parent` | ULID \| null | Single parent. Hierarchy is the parent chain. |
| `status` | `todo` \| `in_progress` \| `blocked` \| `done` \| `cancelled` | |
| `priority` | `P0` \| `P1` \| `P2` \| `P3` | |
| `estimate` | `XS` \| `S` \| `M` \| `L` \| `XL` | Optional. |
| `depends_on` | ULID[] | Set-valued. Blocks scheduling, distinct from `parent`. |
| `labels` | string[] | Set-valued. |
| `assignee` | string | Optional. |
| `plan` | path | The plan doc that produced this item. |
| `unplanned` | bool | True if discovered mid-flight. |
| `discovered_during` | ULID | What it interrupted. Required when `unplanned` is true. |
| `resolution` | string | Set on close. |
| `external` | object | `{system, key, url, synced_at, hash}` |

**On `epic`:** there is no separate `epic` field. An epic is an item with `type: epic`. Ancestry is walked. The roadmap renderer denormalizes to a root epic for grouping; the log does not.

**On IDs:** the ULID is the key. Never key on `external.key` — items exist locally before they exist remotely, and remote keys don't survive a system migration.

### 5.5 Set-valued fields

`labels` and `depends_on` use `add`/`del`, not `set`, so two devs adding different labels don't clobber each other:

```json
{"ev":"...","item":"...","op":"update","add":{"labels":["backend"]},"del":{"labels":["triage"]}}
```

Fold applies `del` then `add` per event. `set` on a set-valued field is legal but replaces wholesale — reserved for the compactor.

---

## 6. The fold algorithm

State is derived, never stored (except as compactor snapshots).

```
fold(lines) -> {item_id: item_state}

1. Parse each line. On parse error: emit to stderr, skip the line, do NOT abort.
   A corrupt line must never prevent reading the rest of the log.
2. Dedupe by `ev`. First occurrence wins (they're identical by construction).
3. Sort ascending by `ev`. ULIDs are lexicographically time-ordered, so this is a
   plain string sort. Ties broken by `actor` then full-line hash — deterministic
   across machines.
4. Discard every event with `ev` <= the highest `compact.through` watermark,
   EXCEPT `snapshot` events.
5. Apply in order:
     create   -> initialize item, apply `set`
     snapshot -> replace item state entirely
     update   -> per-field last-writer-wins: apply `set`, `del`, `add`
     close    -> apply `set`, mark closed
     reopen   -> clear closed
     link     -> apply `set.external`
     conflict -> append to item._conflicts, no state change
6. Events for an unknown item (no `create`, no `snapshot`) create a partial item
   with `_orphan: true`. Report; do not crash. This happens legitimately mid-rebase.
```

**Ordering is by `ev` (ULID), not `ts`.** ULIDs are wall-clock derived, so a dev with a fast clock wins LWW ties. Accepted for v1 (see §16). `actor` and `ts` are on every event precisely so "why did my priority flip back?" is answerable by reading the log.

**Both files fold together.** `fold(todo.jsonl + done.jsonl)` is the full history. Most commands only need `todo.jsonl`.

---

## 7. Compaction

Compaction is the only operation that rewrites a file, and therefore the only one that can truly conflict.

### Rules

1. **Main branch only. CI only. Never on a feature branch.**
2. **Its commit contains nothing else.** Message: `chore(worklog): compact through <ulid>`.
3. Devs rebase after. A rebase across a compaction is safe because union merge (§8) re-adds any branch events, and they sort after the watermark.

### Algorithm

```
1. Fold todo.jsonl.
2. watermark = max(ev) across all input lines.
3. Partition items: open (status in todo/in_progress/blocked) vs closed (done/cancelled).
4. Write todo.jsonl:
     - one {"op":"snapshot", "item": id, "set": <full state>} per OPEN item
     - one {"op":"compact","through": watermark} line
5. APPEND to done.jsonl:
     - one snapshot per newly-CLOSED item
     - a compact watermark
6. Reopened items: **no tombstone needed.** A `reopen` event necessarily has a higher
   `ev` than the `done` snapshot that precedes it, so folding `todo.jsonl + done.jsonl`
   together by `ev` yields the reopened state for free. (0.1 specified a `_moved`
   tombstone here; implementing it revealed it was redundant. Removed.) What the
   compactor *does* owe: **prune from `done.jsonl` any item that is currently open**,
   or stale snapshots accumulate there forever. They're harmless — a later snapshot
   always outsorts them — but the file grows without bound.
7. Verify: fold(new) == fold(old) for all items. Abort and leave the file untouched
   if not. Compaction that loses state is the worst failure mode in this system.
8. Verify trailing newline. Verify every line parses.
```

**Closing an item does not move a file at runtime.** `close` is just an event. The compactor is what physically relocates state into `done.jsonl`. This is deliberate: it means no runtime command ever writes two files, which removes the write-conflict from the parallel-subagent phase (§11).

### Trigger

Scheduled (nightly) or when `todo.jsonl` exceeds a line threshold (default 5000). Never automatic on a dev's machine.

---

## 8. Git integration

### 8.1 Union merge

```
# .gitattributes
.work/todo.jsonl merge=union
.work/done.jsonl merge=union
```

Union merge takes both sides of a conflict, always. No merge conflicts on the log, ever. Three consequences the design already absorbs:

| Consequence | Why it's fine |
|---|---|
| Line order after merge is arbitrary | The fold sorts by `ev`. The file is a bag, not a sequence. |
| Duplicate lines appear | The fold dedupes by `ev`. |
| **A missing trailing newline fuses two lines into one corrupt line** | Enforced by writer invariant + pre-commit hook. See below. |

### 8.2 The trailing-newline invariant

**Every write to a `.jsonl` file must terminate with `\n`.**

*(Corrected in 1.3, by measurement.)* The 1.2 text claimed union merge fuses `{...}{...}` when one side's last line lacks a newline. Integration testing shows git's `ort` union driver **repairs** a missing final newline at merge time. The real fusion path is local: an `O_APPEND` write onto a file whose last line lost its newline (a hand edit) fuses two events into one unparseable line — losing both.

Enforcement, four layers:

- `append()` self-heals: if the file's last byte is not `\n` (a hand edit the hook hasn't caught yet), the next append prepends `\n` — still one `write()` call.
- Writers open with `O_APPEND` and write `json + "\n"` in a single `write()` call.
- Pre-commit hook: `[ -z "$(tail -c1 .work/todo.jsonl)" ] || exit 1` — plus `hooks/pre-merge-commit` running the same script, because git does not run `pre-commit` for merge auto-commits (a merge could otherwise land a stale roadmap or a smuggled corrupt line that only CI would catch).
- CI: same check, plus every line parses as JSON against `event.schema.json`.

### 8.3 Atomicity

Single `write()` of a line under `O_APPEND` is atomic for lines under `PIPE_BUF` (4096 bytes on Linux). Lines exceeding that (a long `body`) must take an advisory lock (`flock` on `.work/.lock`). Simpler alternative: cap `body` in the log at 2 KB and store longer prose in the plan doc, referenced by path. **Recommended: cap it.**

---

## 9. Adapter contract

The boundary is a **CLI**, not prose. An adapter is any executable that satisfies this contract. It can be a shell script, a Python file, or a skill wrapping either. The core shells out and parses stdout.

### 9.1 Ticket adapter

```
ticket-<system> capabilities
ticket-<system> push   --item <file.json> [--dry-run]
ticket-<system> pull   --since <rfc3339> [--keys k1,k2,...]
ticket-<system> close  --key <K> --resolution <string>
ticket-<system> comment --key <K> --body-file <f.md>
```

**`capabilities`** → stdout JSON. Lets the core degrade gracefully instead of guessing.

```json
{
  "system": "jira",
  "supports": ["push", "pull", "close", "comment"],
  "types": {"epic":"Epic","story":"Story","task":"Task","subtask":"Sub-task","bug":"Bug"},
  "supports_parent": true,
  "supports_depends_on": true,
  "max_title": 255
}
```

If `supports_depends_on` is false, the core stops trying to sync dependencies and notes it in the drift report. It does not error.

**`push`** takes canonical item JSON on a file path (not argv — bodies contain newlines). Returns:

```json
{"key":"PROJ-412","url":"https://...","rev":"2026-07-16T15:39:58Z","hash":"a3f1..."}
```

`push` **must be idempotent.** The item ULID is passed in the payload; the adapter uses it as the external idempotency key (a Jira label, an ADO tag, a GH issue marker line). A retried push finds the existing ticket and updates it. **This is the single most important adapter requirement** — without it, a retried subagent opens duplicate tickets.

**`pull`** emits NDJSON of canonical items on stdout, one per line, each with `external.key` and `external.rev` populated.

**Exit codes:**

| Code | Meaning | Core behavior |
|---|---|---|
| 0 | Success | Continue |
| 2 | Auth failure | Abort sync, tell the human to re-auth |
| 3 | Not found | Clear `external`, mark for re-push |
| 4 | Rate limited / transient | Retry with backoff (3 attempts), then defer |
| 5 | Remote conflict | Emit `op:"conflict"` event |
| 1 | Other | Report, continue with next item |

Field mapping is entirely the adapter's problem. Canonical item in, adapter maps `type: subtask` to whatever Jira calls it this week.

### 9.2 Wiki adapter

```
wiki-<system> capabilities
wiki-<system> publish --file <path> --key <logical-key> --title <string> [--parent <id>]
```

`--key` is a stable logical identity (`roadmap`, `plan/2026-07-16-auth-refactor`, `status/2026-07-16`). Returns `{"page_id":"...","url":"...","rev":"..."}`.

The core maintains `.work/published.json`:

```json
{"roadmap": {"page_id": "88213", "url": "https://...", "rev": "12", "source_hash": "a3f1..."},
 "plan/2026-07-16-auth-refactor": {"page_id": "88219", "url": "https://...", "rev": "1", "source_hash": "b7c2..."}}
```

**Without this map you create duplicate Confluence pages on every republish.** It is committed, because page identity is shared across the team. If `source_hash` is unchanged, skip the publish.

---

## 10. Sync

### 10.1 Principle: the remote is just another writer

Do not build a second merge path. Remote changes are **ingested as events into the same log** with `actor: "<system>"` and a `src` block. The existing per-field LWW fold handles them. One code path, one conflict story.

### 10.2 Deterministic event IDs for ingested changes

```
ev = ULID(time = remote.rev_timestamp, entropy = sha256(system | key | remote.rev)[:10 bytes])
```

Two devs polling Jira independently produce the **identical line**. Union merge takes both, the fold dedupes by `ev`, one survives. Ingest is therefore idempotent across clones — which means there's no need for a single blessed syncer, and any dev running `sync` is safe.

**`ts` on an ingested event is `remote.rev`, not `now()`.** Otherwise two devs polling the same change produce lines that share an `ev` but differ in `ts` — dedupe still works, but §5.2's claim that duplicates are "identical by construction" becomes false, and a byte-comparison in a test or a CI check would flag a phantom difference. Ingested events carry the remote's clock, not the poller's.

**The hash goes in the ULID's entropy field, not a sidecar.** A ULID is 48 bits of timestamp + 80 bits (10 bytes) of entropy; `sha256(...)[:10]` fills it exactly. A tempting-looking alternative is to keep `ev` random and put the hash in a separate field like `ev_remote`. Do not do this. The fold dedupes by `ev`, so a random `ev` means both devs' ingests survive, and this fails in a way that looks harmless:

```
dev A ingests Jira P0    -> ev = X
Rick sets priority P2    -> ev = Y      (X < Y)
dev B ingests same P0    -> ev = Z      (Y < Z)

fold order: X(P0), Y(P2), Z(P0)  ->  P0
```

Rick's local edit is silently reverted by a duplicate of a change that predates it — violating invariant §15.11. Applying the same `set` twice is idempotent *in isolation*, which is exactly why this survives casual testing. Deterministic `ev` means there is only ever one X, and the fold yields P2. A sidecar field would require a second dedupe path keyed on it, in a design whose whole premise is that the remote is just another writer through one code path.

### 10.3 Echo suppression

Without this you get an infinite loop: push → remote `updated_at` bumps → poll → see "remote change" → ingest your own push → push again.

`.work/sync-state.json` (gitignored, per-clone):

```json
{
  "cursors": {"jira": "2026-07-16T15:40:00Z"},
  "items": {
    "01J8X0M2QQ": {
      "last_pushed_hash": "a3f1...",
      "last_remote_rev": "2026-07-16T15:39:58Z",
      "last_pull": "2026-07-16T15:45:00Z"
    }
  }
}
```

On pull, ingest an item only if `hash(remote_synced_fields) != last_pushed_hash`. The hash covers only the fields we actually sync (§10.4) — a Jira watcher change must not read as drift.

```
hash = sha256(canonical_json({title, body, type, status, priority, parent, labels, assignee}))[:16]
```

Canonical JSON = sorted keys, no whitespace, arrays sorted for set-valued fields.

**Note the per-clone gap:** a fresh clone has no `sync-state.json`, so its first pull sees everything as remote-changed. Mitigation: on first pull, if `hash(remote) == hash(local)`, write `last_pushed_hash` and ingest nothing. Only genuine differences produce events.

### 10.4 What syncs, and which way

| Field | Local → Remote | Remote → Local | Notes |
|---|---|---|---|
| `title`, `body` | yes | yes | LWW |
| `type` | yes | on create only | Type changes remotely are ignored; noted in drift |
| `status` | yes | yes | Mapped by adapter |
| `priority` | yes | yes | LWW — the PM re-prioritizing in Jira is a feature |
| `parent` | yes | yes | If `supports_parent` |
| `labels` | yes | yes | Union, not LWW |
| `assignee` | yes | yes | LWW |
| `depends_on` | if supported | if supported | Often lossy; report |
| `estimate` | yes | no | Local-authoritative |
| `plan`, `unplanned`, `discovered_during` | as a comment/label | no | Local-only concepts |
| `id` (ULID) | as idempotency key | never | |

### 10.5 Scopes

```
worklog sync                       # == sync --scope active --apply
worklog sync --scope active        # status in (todo,in_progress,blocked)
                                   #   OR updated within active_window_days
                                   #   OR external.dirty
worklog sync --scope all           # everything open; slow; manual only
worklog sync --keys PROJ-412,...   # targeted
worklog sync --report              # print drift, change NOTHING
worklog sync --apply               # apply LWW, emit conflicts
worklog sync --dry-run             # print the events that WOULD be appended
```

**Closed and archived items never reconcile.** That's what keeps the scope bounded. If someone reopens a ticket in Jira, `pull` catches it only while it's inside `active_window_days`; past that, it's a manual `--keys` sync. Documented limitation, not a bug.

### 10.6 Conflicts

A conflict is: the same field changed on both sides since `last_pushed_hash`, to different values.

Under `conflict_policy: report` (the default):

```json
{"ev":"01J8X9...","ts":"...","actor":"sync","item":"01J8X0M2QQ","op":"conflict",
 "set":{"field":"priority","local":"P1","remote":"P0","remote_rev":"2026-07-16T15:39:58Z"}}
```

State does not change. The conflict appears in:
- `worklog sync --report` output
- the next generated status report, under **Needs attention**
- `worklog show <item>`

**Best-effort with visible drift beats eventual consistency with silent loss.** Resolve with `worklog resolve <item> --field priority --take local|remote`, which appends a normal `update` event and clears the conflict.

`local-wins` / `remote-wins` policies skip the conflict event and just apply. Available, not recommended.

---

## 11. Orchestration: the sync phases

Your instinct to fan out subagents is right, but the naive version has three writers racing on `todo.jsonl`. Phase it:

### Phase 1 — Single writer

One agent. Folds the log, computes what changed, appends events, emits `changeset.json` to a temp path:

```json
{"changeset":"01J8XA...","items":[
  {"id":"01J8X0M2QQ","action":"push","state":{...}},
  {"id":"01J8X0M3RR","action":"close","state":{...}},
  {"id":"01J8X0M4SS","action":"create","state":{...}}
]}
```

### Phase 2 — Parallel, side-effects only

Three subagents, all **reading** `changeset.json`, none writing the log:

| Subagent | Does | Writes to |
|---|---|---|
| `ticket-sync` | push/close/comment via adapter | `results/ticket.json` |
| `wiki-publish` | publish roadmap, plans, status | `results/wiki.json` |
| `roadmap-render` | regenerate `docs/roadmap.md` | the doc |

Every phase-2 action is idempotent and keyed by item ULID. A retried subagent must be a no-op, not a duplicate. Phase 2 may fail partially — that's what best-effort means.

### Phase 3 — Single writer

Folds `results/*.json` back into the log as events:

```jsonl
{"ev":"...","actor":"sync","item":"01J8X0M2QQ","op":"link","set":{"external":{"system":"jira","key":"PROJ-412","url":"...","synced_at":"...","hash":"a3f1..."}}}
```

Updates `.work/published.json` and `.work/sync-state.json`. Prints a summary: pushed, closed, conflicted, deferred.

**Invariant: exactly one process appends to the log at a time within a single `worklog` invocation.** Concurrency across devs is handled by union merge, not by locking.

---

## 12. Skills

Each is a thin skill wrapping a deterministic script. The model decides *when*; the script decides *what*.

| Skill | Trigger | Behavior |
|---|---|---|
| `plan-capture` | Plan mode exits; user says "capture this plan" | Writes `docs/plans/<date>-<slug>.md`. Parses plan steps → items with `plan` set. Appends `create` events. Optionally pushes (per `sync.push_on_capture`). |
| `work-add` | "we need to also…", mid-flight discovery | Appends a `create`. Flags `--unplanned --discovered-during <id>`. |
| `work-update` | "mark that in progress", "bump priority" | Appends `update`. |
| `work-close` | Task finished | Appends `close`. Does **not** touch `done.jsonl`. |
| `plan-next` | "what should we do next?" | Folds log. Filters open, unblocked (`depends_on` all closed), sorts by priority then epic order. Presents top N with rationale. **Read-only.** |
| `roadmap-render` | Called by sync; manual | Regenerates `docs/roadmap.md`. |
| `status-report` | "status report", "what did I do this week", "timecard for last week" | Picks `--kind` from the ask (default `status.default_kind`). Calls `worklog status --emit-facts`, writes the prose, calls `worklog status --write`. Commits and publishes. Refuses to overwrite a frozen report without `--force`. See §13.3. |
| `roadmap-sync` | Plan complete; "sync everything" | The three-phase orchestrator (§11). |
| `worklog-compact` | CI only | §7. |

### Hooks, not hope

**"Anytime we do planning, output tasks" will get skipped if it depends on the model remembering.** Back the policy with mechanism:

| Hook | Action |
|---|---|
| `PostToolUse` on `ExitPlanMode` | Invoke `plan-capture` non-optionally. |
| `Stop` | If `todo.jsonl` has open `in_progress` items with no matching git activity, warn. |
| `PreCommit` (git) | Trailing-newline check; schema validation; `roadmap.md` freshness. |
| `PreMergeCommit` (git) | Same script as PreCommit — merge auto-commits bypass `pre-commit`. |

A CLAUDE.md instruction holds maybe 80% of the time. A hook holds 100%. Use prose for judgment, hooks for invariants.

---

## 13. Generated artifacts

### 13.1 Roadmap — read-only for humans

`docs/roadmap.md` opens with:

```markdown
<!-- GENERATED by worklog roadmap-render. DO NOT EDIT. -->
<!-- source-hash: a3f1c9e2 -->
<!-- generated-at: 2026-07-16T16:00:00Z -->

> This file is generated from `.work/todo.jsonl`. Edits will be overwritten.
> To change the roadmap, ask Claude Code — e.g. "move the SSO epic ahead of billing"
> — or run `worklog update`.
```

**Because the roadmap is read-only, there is no parser.** No anchors, no round-trip, no ambiguity about which bullet became which ticket. This is the single biggest simplification in the spec.

**CI check:** regenerate, diff, fail the build if it differs. That's what teaches the team where to make changes, and it costs one job.

Structure — written for a junior dev or a PM, so: prose first, tables second, no ULIDs in the reading path.

```markdown
# Roadmap — Acme Platform

_Generated 2026-07-16. 3 epics in flight, 14 open items, 2 blocked._

## Now

### Auth refactor  ·  P0  ·  6 of 9 done
Replacing hand-rolled session handling with middleware. Blocks the SSO work.

| # | Item | Type | Priority | Status | Blocked by |
|---|---|---|---|---|---|
| [PROJ-412](https://...) | Extract auth middleware | task | P0 | in progress | — |
| [PROJ-418](https://...) | Session store migration | task | P1 | todo | PROJ-412 |

## Next
...
## Later
...

## Needs attention
- **PROJ-412** — priority conflicts: local `P1`, Jira `P0`. Resolve with
  `worklog resolve 01J8X0M2QQ --field priority --take remote`.
```

Ordering: `Now` = P0 + anything `in_progress`. `Next` = P1 + unblocked P2. `Later` = the rest. Within a section, epic order then priority then creation order.

### 13.2 Plans

`docs/plans/<YYYY-MM-DD>-<slug>.md`. Committed **and** published. Front matter links the plan to its items:

```markdown
---
date: 2026-07-16
slug: auth-refactor
items: [01J8X0M2QQ, 01J8X0M3RR]
epic: 01J8WZZ100
wiki: https://acme.atlassian.net/wiki/spaces/ENG/pages/88219
---
```

Plans are **written by a human/agent conversation and never regenerated.** They're the record of *why*, and the fact that they can go stale is fine — that's what a dated document is.

**Plans are the spec half of spec-driven development.** The ticket says *what* and *when*; the plan says *why, and what we considered instead*. That's the artifact that survives the ticket being closed, the sprint ending, and everyone forgetting. Three consequences:

- **A plan supersedes, it never edits.** A design that changed gets a new dated plan with `supersedes: 2026-07-16-auth-refactor` in its front matter. The renderer chains them so the wiki shows the current one with a link back. Editing a plan in place destroys the only record you have of why the first approach was abandoned — which is precisely the thing someone will ask about in six months.
- **Plans publish to the wiki like everything else** (`published.json` key `plan/<slug>`), so the PM reading the roadmap can click from an epic to the plan that produced it.
- **Plans are the one generated-adjacent artifact with no CI hash check.** They're prose, written once. Guarding them would only prevent typo fixes.

Front matter fields: `date`, `slug`, `items[]`, `epic`, `wiki`, optional `supersedes`, optional `superseded_by` (written by `plan-capture` when a successor appears).

### 13.3 Status reports

`docs/status/<YYYY-MM-DD>-<kind>.md`. Generated on demand, committed, and published to the wiki — same adapter, same `published.json`, key `status/<date>-<kind>`.

```
worklog status --kind daily                    # default window: since last daily
worklog status --kind weekly [--week 2026-W29]
worklog status --kind timecard [--since 2026-07-13] [--until 2026-07-17]
worklog status --kind daily --dry-run          # print, write nothing
```

#### Frozen, not regenerated

This is the fork worth being explicit about. The roadmap is regenerated and CI hash-checked because it describes *the present*, which has exactly one correct value. **A status report describes a moment, and it was sent to people who acted on it.**

So: status reports are **generated on demand, then frozen.** Regenerating last Tuesday's daily today would produce different text — conflicts have since resolved, priorities moved, an item got reopened — and you'd have silently rewritten something a human read and made a decision from. They get no CI hash check, and `worklog status` refuses to overwrite an existing file without `--force`.

They are, however, **reproducible**: front matter records the exact watermark, so anyone can reconstruct the inputs.

```markdown
---
kind: daily
date: 2026-07-16
window: {from: 2026-07-15T09:00:00Z, to: 2026-07-16T09:00:00Z}
through: 01J8XA4K20        # max ev included; the report is a fold over ev <= this
generated_at: 2026-07-16T09:00:12Z
wiki: https://acme.atlassian.net/wiki/spaces/ENG/pages/88231
---
```

If a report was wrong, **the correction goes in the next report**, not into the old one. Same rule as the plans, for the same reason.

#### The three kinds

| | `daily` | `weekly` | `timecard` |
|---|---|---|---|
| **Audience** | the standup | PM, stakeholders, whoever missed the week | you, and whoever you bill |
| **Window** | since last daily | `week_starts` → +7d | arbitrary `--since/--until` |
| **Shape** | terse bullets | prose + tables, grouped by epic | one paragraph per day, in date order |
| **Detail** | item-level | epic-level rollup with item tables | narrative only — **no ticket tables** |
| **Answers** | what changed, what's blocked | what shipped, what slipped, what's next | what did I spend the day on |

**`daily`** — for the meeting. Shipped since yesterday, in flight, blocked (and by what), conflicts needing a human. Bullets, no prose, fits on a screen.

**`weekly`** — everything closed in the window grouped by epic, plus slippage (items still open that were `in_progress` at the start of the window), plus the unplanned rollup, plus what's queued next per `plan-next`. Tables are fine here.

**`timecard`** — one paragraph per day, and *deliberately nothing else*. No tables, no ticket IDs in the reading path, no status columns. It answers "what did Monday consist of" in a couple of sentences a human can skim. Days with no activity are omitted, not padded.

```markdown
## Monday, 14 July
Spent most of the day on the auth middleware extraction (PROJ-412), which turned out
to depend on the session store schema more than the plan assumed — filed PROJ-431 as
unplanned work and got the migration written. Afternoon went to review on the billing
epic.

## Tuesday, 15 July
Finished PROJ-431 and landed PROJ-412. Started the SSO spike; nothing to show yet.
```

#### Where the prose comes from

Worth being precise, because this is the one place the pipeline isn't deterministic. `render_roadmap.py` is pure code: fold in, markdown out. **A timecard paragraph is a synthesis job — that's the model's, not the script's.**

So the split is:

1. `bin/worklog status --kind timecard --emit-facts` folds the log and emits per-day structured facts (items closed, items opened, unplanned items and what they interrupted, commits touched if available) to stdout. Deterministic.
2. The `status-report` **skill** reads those facts and writes the prose.
3. `worklog status --write` takes the prose on stdin, adds front matter with `through`, writes the file, commits, publishes.

This is also *why* status reports can't be CI-hash-checked: step 2 isn't reproducible byte-for-byte, and that's fine. Freeze the output instead of trying to verify it.

#### Common sections

`daily` and `weekly` both carry:

- **Shipped** — closed in window, grouped by epic
- **In flight** — `in_progress`, with age (age is the useful column; a 9-day-old "in progress" is the whole story)
- **Blocked** — plus what blocks them
- **Unplanned work** — items with `unplanned: true`, and what they interrupted
- **Needs attention** — open conflicts (§10.6), deferred syncs, adapter failures

**The unplanned section is the point.** "38% of last week's closed items were unplanned, mostly interrupting PROJ-412" is the most useful number a team can have and almost nobody tracks it. It falls out of this schema for free — which is why `discovered_during` is required, not optional. `timecard` gets it as prose, not a percentage.

---

## 14. CI

| Check | When | Failure |
|---|---|---|
| Trailing newline on every `.jsonl` | pre-commit, PR | hard fail |
| Every line parses; validates against `event.schema.json` | PR | hard fail |
| `fold()` succeeds with zero orphans | PR | warn |
| `roadmap.md` matches regenerated output | PR | hard fail |
| Compaction | nightly, main | hard fail, no partial write |
| `sync --report` drift summary | nightly | post as a comment; never fail |
| PR-simulation integration suite (`tests/test_integration.py`) | PR | hard fail |

---

## 15. Invariants

Violating any of these is a bug, not a tradeoff:

1. Every `.jsonl` write ends in `\n`.
2. Nothing but the compactor rewrites a `.jsonl` file.
3. The compactor runs on main, in CI, in a commit of its own, and verifies `fold(new) == fold(old)`.
4. Nothing but `worklog` writes `.jsonl` — no editors, no `echo >>`.
5. Adapter `push` is idempotent, keyed by item ULID.
6. The core never branches on `ticketing.system` beyond checking for `none`.
7. `docs/roadmap.md` is never hand-edited.
8. A plan in `docs/plans/` is never edited or regenerated. Designs change by superseding.
9. A published status report is never regenerated. Corrections go in the next one.
10. A missing adapter degrades to local-only; it never fails a command.
11. Sync never silently discards a local change.

---

## 16. Known limitations

| Limitation | Why we accept it |
|---|---|
| **Clock skew decides LWW ties.** A dev 30s fast silently wins. | NTP-synced org, one team. `actor` + `ts` on every event make it debuggable. Fix in v2 with a per-item Lamport counter ordered by `(lamport, ev)` if it ever bites. |
| Closed items don't reconcile | Bounds sync scope. Manual `--keys` escape hatch exists. |
| One ticketing system per repo | Multi-system needs `external` to be an array. Not worth it yet. |
| `pull` is polling, not webhooks | Webhooks need a server. Polling on `sync` is best-effort by design. |
| Body text capped at 2 KB in the log | Keeps appends atomic under `PIPE_BUF`. Long prose lives in the plan doc. |
| Union merge can resurrect events from an abandoned branch | Rare; the fold is idempotent so the worst case is a stale field, visible in `worklog history`. |

---

## 17. Open questions

1. **Does `plan-next` write anything?** Spec'd read-only. If it should mark the chosen items `in_progress`, that's a different skill (`plan-start`) — keep them separate.
2. ~~**Grok build parity.**~~ **Closed in 1.1.** All settings live in `.work/config.yml`, so the agent file is policy-only and `AGENTS.md` is a symlink to `CLAUDE.md`. Skills are discovered per-harness; `bin/worklog` is identical under both.
3. **Do epics sync as remote epics, or only as labels?** Jira epics are a real type; GitHub Issues has no epic. `capabilities.types` covers it, but the roadmap grouping degrades on GitHub. Milestones as a fallback?
4. **Does the timecard need hours?** Spec'd `include_hours: false` — narrative only. If a timecard is ever going to back an invoice, hours are the whole point, and the log has no duration data: `in_progress` → `done` elapsed time counts overnight and weekends. Getting real hours means either a `worklog start/stop` (an activity model this spec doesn't have) or reading git commit timestamps as a proxy (rough, but free, and it's what actually happened). **Decide before building `timecard`** — it's the difference between a narrative feature and a time-tracking subsystem.
5. **Multi-repo.** One roadmap across three repos is a real need and this spec has no answer. Probably a separate aggregator reading N logs. Note the timecard has the same problem, and worse: a consultant's week spans repos, so a per-repo timecard is the wrong unit.
6. **Should `plan-capture` push immediately** (`push_on_capture: true`) or batch until the plan completes? Immediate = visible sooner (fishbowl), more churn in Jira.
7. **Does a superseded plan get unpublished from the wiki?** Leaning no — leave it with a banner linking to its successor. Deleting the record of a rejected approach defeats the purpose of keeping plans.

---

---

## Appendix A — Reference implementation

`bin/fold.py`, `bin/ulid.py`, `bin/worklog`, and the test suite ship alongside this spec and are **executable, not illustrative**. 32 tests pass. The end-to-end union-merge scenario in §8.1 has been run against a real git repo: two branches editing the same item merged with no conflict, and both label additions plus both scalar edits survived.

Where prose and code disagree, the tests are the tiebreak — they encode §6 step by step.

### Test vectors

`tests/test_fold.py` opens with four regressions, in this order and on purpose. Each is a real bug from a proposed implementation that produced plausible-looking output and silently corrupted state:

| Test | Guards | Naive implementation gives |
|---|---|---|
| `test_newest_ev_wins_regardless_of_file_position` | §6 step 3 — sort by `ev` | file-order fold: remote P0 lost, reports P1 |
| `test_cancelled_stays_cancelled` | §5.3 — `close` reads status from `set` | hardcodes `done`: **abandoned work reports as shipped** |
| `test_add_and_del_labels` | §5.5 — set-valued fields | `add`/`del` ignored: labels silently vanish |
| `test_snapshot_replaces_state_entirely` | §7, §6 step 4 | watermark ignored, snapshot merged instead of replacing |

Then: `test_fold_is_deterministic_across_shuffles` (all permutations of an event set fold identically — the property union merge depends on), `test_corrupt_line_is_skipped_not_fatal` (one fused line costs one line, not the log), `test_orphan_is_flagged_not_invented`, `test_link_sets_external_not_ticket` (`src` is provenance, `external` is identity — conflating them corrupts the field sync keys on), `test_reopen_across_files_beats_done_snapshot`.

### The `ev_remote` question, settled executably

`tests/test_ulid.py::TestTheBugThisPrevents` is a pair. Both run the §10.2 scenario — two devs poll the same Jira change, Rick edits locally in between, union merge brings both ingests in:

- `test_deterministic_ev_preserves_the_local_edit` — dedupe collapses the ingests, Rick's P2 stands.
- `test_random_ev_silently_reverts_the_local_edit` — **passes, and documents the failure.** With a random `ev` per ingest (which is what putting the remote hash in a sidecar field like `ev_remote` gives you), dev B's duplicate sorts above Rick's edit and reverts him to P0. Nothing errors. Nothing warns.

That second test exists because this design keeps getting proposed. It's cheaper to have it fail loudly in CI than to argue about it.

### Two spec bugs the implementation found

Worth recording, because they're the argument for writing the code before finalizing the prose:

1. **§5.2 required `item` on every event, but `op: compact` is log-level.** A strict validator rejects the compactor's own output. Fixed: `item` is required except for `compact`.
2. **§7 step 6's `_moved` tombstone was unnecessary.** A `reopen` always has a higher `ev` than the `done` snapshot it follows, so folding both files together by `ev` handles it with no extra machinery. Removed — and replaced with the thing actually needed: pruning stale snapshots from `done.jsonl`.

### Running

```bash
python3 tests/test_fold.py      # 21 tests
python3 tests/test_ulid.py      # 11 tests
git config core.hooksPath hooks # arms the pre-commit invariant checks
```

---

## Appendix B — Repo skeleton

```
CLAUDE.md              policy only; AGENTS.md is a symlink to it
.gitattributes         union merge for *.jsonl (§8.1)
.gitignore             sync-state.json, changeset.json, results/
hooks/pre-commit       trailing newline + schema + roadmap freshness + fold tests
bin/
  worklog              CLI. add/update/close/list/show/fold implemented;
                       plan-capture/sync/status/roadmap-render/compact stubbed
  fold.py              §6 reference implementation
  ulid.py              §5.2, §10.2 — incl. deterministic remote ev
tests/
  test_fold.py
  test_ulid.py
.work/
  config.yml           all settings
  todo.jsonl           empty
  done.jsonl           empty
  schema/
docs/plans/  docs/status/  .claude/skills/
```

### The one non-obvious bit

`bin/worklog`'s `append()` is **the only writer in the repo** (invariant §15.4). Single `os.write()` under `O_APPEND`, always newline-terminated, body capped at `MAX_BODY = 2048` — a module constant with a comment pointing at `PIPE_BUF`, deliberately not a config key.

### Verified end to end

```
$ worklog add "Extract auth middleware" --priority P1
$ git checkout -b alice && worklog update $A --add-label backend --status in_progress
$ git checkout -b bob   && worklog update $A --add-label urgent --priority P0
$ git merge alice && git merge bob
Auto-merging .work/todo.jsonl        <- no conflict
$ worklog show $A
  priority: P0          <- bob's
  status:   in_progress <- alice's
  labels:   [backend, urgent]   <- both

$ printf '{"ev":"01ZZZ",...}' >> .work/todo.jsonl   # no trailing newline
$ git commit -m bad
worklog: .work/todo.jsonl has no trailing newline (invariant 15.1)
  -> blocked, exit 1
```

Concurrent edits from two branches, zero conflicts, nothing lost — and the one failure union merge can't survive is caught at commit time.

## 18. Implementation order

1. ~~Schema + `fold` + `worklog add/update/close/show/list`.~~ **Done** — see Appendix A/B. No sync, no adapters, useful on day one.
2. ~~`.gitattributes`, newline invariant, pre-commit hook.~~ **Done.** CI schema check still outstanding (the hook is local-only; CI must re-run it).
3. `roadmap-render` + the CI freshness check.
4. `plan-capture` + the `ExitPlanMode` hook.
5. Compaction + its CI job.
6. Adapter contract + one adapter (`ticket-github` is the cheapest to build and test).
7. Push-only sync. Ship it. Live with it for two weeks.
8. Pull + echo suppression + conflicts.
9. Wiki adapter + publish.
10. `status-report` — `daily` and `weekly` first; `timecard` only once open question 4 is settled. `plan-next`.

Steps 1–4 are a genuinely useful tool with no adapters at all. If the project stalls there, it still paid for itself. **Do not build sync before you've lived with the log.**
