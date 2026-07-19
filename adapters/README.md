# Adapters

An adapter is a single executable that maps a canonical worklog item to one
ticketing platform and back. The dispatcher (`bin/sync_dispatch.py`) owns every
sync invariant — hashing, idempotency, marker search, scope, echo suppression,
conflict detection. The adapter is a dumb translator. If invariant logic leaks
in here, the design has failed (and `tests/test_adapter_contract.py` will say
so).

## Authoring rules

1. **Translate, don't think.** No hashing, no marker search, no scope, no
   conflict logic. Create when `op:"create"`, update when `op:"update"`. The
   dispatcher has already decided which; the adapter never second-guesses it.
2. **Env for connection, stdin for data, argv for flags.** Never parse item
   data from argv (bodies contain newlines).
3. **Stdout is data only.** All logging to stderr. One JSON object (or NDJSON
   for `pull`) on stdout, nothing else.
4. **Exit codes carry meaning** (table below). A rate limit is `4`, not `1`.
5. **`capabilities` must be honest.** If the platform has no epic, say
   `"epic": null`. Lying here defeats the schema gate.
6. **Degrade, never crash.** Unsupported field → omit it and let the
   dispatcher report drift.

## The contract

JSON over stdin/stdout, one process call per verb. Full spec:
`docs/plans/2026-07-18-typed-adapter-contract.md` §3. Payload shapes:
`schema/adapter-io.schema.json`; capabilities shape:
`schema/capabilities.schema.json`.

| Verb | Input | Output | Spec |
|---|---|---|---|
| `capabilities` | none | one capabilities JSON object | §3.1 |
| `push` | stdin: `push_request` (`op`, `key`, `marker`, `item`) | one `push_response` JSON object | §3.2 |
| `pull` | argv: `--since <rev>` `[--keys k1,k2]` | NDJSON, one `pull_line` per ticket | §3.3 |
| `get <key>` | argv | one canonical item (pull_line shape) | §3.4 |
| `close <key> <resolution>` | argv | `{"key", "rev"}` | §3.5 |

## Taxonomy mapping (worklog-spec §5.4 v1.7; plan 2026-07-18-work-taxonomy §3.4)

Items carry `level` (epic|story|task|subtask), `kind` (feature|bug|ops|triage),
and `milestone` (string|null). `capabilities.types` is keyed by **level**;
`capabilities.kinds` is an optional informational map of kind → platform
treatment. Legacy `type` is a deprecated alias adapters tolerate on input.

| Field | GitHub | Jira (reference) | Notes |
|---|---|---|---|
| `level` | `level:<level>` label; issue vs nothing per `capabilities.types` (`epic: null` → degrade) | issue type (Epic/Story/Task/Sub-task) | keyed by level, never the deprecated `type` |
| `kind` | `kind:<kind>` label; `kind:bug` also gets the platform `bug` label | label; `bug` → Bug issue type | see `capabilities.kinds` |
| `milestone` | GitHub milestone — best-effort `gh issue edit --milestone`, milestone created via `gh api` if missing; errors → stderr, never fatal | `fixVersion` | dispatcher reports drift; adapter never fails on it |
| `type` (deprecated) | pull falls back to `type:*` labels when no `level:*` present (`bug` → `task`/`bug`) | — | pre-1.7 tickets still round-trip; alias dies at next compaction |

## Environment

Connection details come from env, never argv:

- `WORKLOG_TICKET_SYSTEM` — the system name (`github`, `jira`, ...)
- `WORKLOG_TICKET_PROJECT` — the target project/repo
- plus whatever the platform itself needs (tokens, hosts, ...)

## Exit codes (spec §3.6)

| Code | Meaning | Dispatcher behavior |
|---|---|---|
| 0 | success | continue |
| 2 | auth failure | abort sync, tell the human to re-auth |
| 3 | not found | clear `external`, mark for re-push |
| 4 | rate limited / transient | retry w/ backoff ×3, then defer |
| 5 | remote conflict | emit `op:"conflict"` event |
| 1 | other | report, continue with next item |

## Generating a new adapter

Adapt `adapters/github/adapter` (the worked example) to the target platform's
CLI — never write one from a blank file. Then run `worklog adapter check`; it
refuses to activate an adapter that violates the contract.

`adapters/fake/adapter` is the reference double backed by a local JSON file —
the contract tests run against it with no network.
