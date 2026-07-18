# Changelog

## 0.6.0 — unreleased

- Typed adapter contract (plan 2026-07-18): bin/sync_dispatch.py owns every sync
  invariant (capabilities gate, scope, create-vs-update, marker idempotency, echo
  suppression, §3.6 exit-code handling, conflicts, drift report); adapters are dumb
  translators — shipped fake (CI double) + github worked example; worklog adapter
  init|check; worklog sync is real — no stubs remain.
- Spec v1.6: §8.1 hosted-platform merge caveat + recovery; §9.5 typed contract layer.
- CI coverage gate: >=80% enforced on bin/*.py, target 95% (CLAUDE.md policy).
- ticket-sync skill delegates invariants to the dispatcher; per-system notes moved
  to adapters/README.md.

## 0.5.0 — 2026-07-18

- release skill: cutting a release is a wiki-ticket capability (stamp,
  snapshot, tag, platform release, publish, sync).
- Pull sync: `worklog ingest` (deterministic ev per spec §10.2 — identical polls
  dedupe across clones), `worklog conflict`, `worklog resolve --take local|remote`;
  fold clears conflicts when a later event writes the field. ticket-sync is now
  push AND pull with §10.3 echo suppression.
- Spec v1.5: adapter strays purged; pull CLI documented; §18 step 8 done.
- wiki-publish: per-system guidance (GitHub/GitLab/ADO/Confluence) + ledger field
  semantics across systems.
- Harness ports: /worklog:init scaffolds the AGENTS.md symlink; plugin/PORTS.md
  matrix — Codex/OpenCode work today with zero port.

## 0.4.0 — unreleased

- Compaction (`bin/compact.py`, `worklog compact --yes`) per spec §7 with fold-equality
  verification; nightly CI job commits `chore(worklog): compact through <watermark>`.
- `worklog status --kind daily|weekly` (`--emit-facts` / `--write`, frozen reports) +
  status-report skill. Timecard deferred on spec §17 open question 4.
- ticket-sync closes remote tickets when local items close (external.dirty scope).
- plan-capture publishes tickets + wiki via a background subagent — never blocks.
- Spec v1.4: §9 rewritten to skill-based edges.

## 0.3.0 — unreleased

- `worklog link`: attach external identities to work items via §5.3 link events.
- `worklog wiki-add`: register documents in the wiki publish set.
- ticket-sync skill: push-only sync to external trackers with ULID-marker
  idempotency; GitHub via `gh`, system-vague guidance elsewhere.
- /worklog:init system detection: confident yes/no path, multi-select
  pick-and-mix, upgrade skip.
- wiki-publish: default publish set + `source` field in the ledger.

## 0.2.0 — unreleased

- `worklog roadmap-snapshot` subcommand.
- `wiki-publish` skill: system-agnostic wiki publishing with a `published.json` ledger.
- Dogfood enforcement hooks: UserPromptSubmit reminder, Stop worklog check,
  SessionStart doctor-lite.
- Plugin installer/uninstaller scripts.
- User guide + README; docs live in the repo/wiki, deliberately NOT packaged
  in the plugin.

## 0.1.0 — unreleased

- Plugin scaffold: manifest, design captured as tracked work items
  (`docs/plans/2026-07-18-claude-plugin.md` in the source repo).
- `worklog --version`; version recorded in scaffolded repos and checked by `/worklog:doctor`.
