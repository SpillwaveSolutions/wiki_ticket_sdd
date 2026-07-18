---
date: 2026-07-18
slug: ticket-sync-and-init-detection
title: Ticket sync (push-only, GitHub Issues) + /worklog:init system detection
epic: 01KXSP26ENPKCT4APD4YE93MMV
story: 01KXSQJ3K19QWBDX482FRT7ETR
items: filled-by-worklog-add (this plan attaches tasks to the pre-seeded epic/story instead of plan-capture, which would duplicate them)
---

# Ticket sync (push-only) + init system detection

Two P1s, one branch.

## Why

The fishbowl is only half-built: work items live in the log and on the wiki,
but not in the ticketing system anyone else watches. Push-only sync closes
that for GitHub Issues first — spec §18 step 7 says ship push-only and live
with it before building pull. And `/worklog:init` should discover what
systems a repo uses instead of leaving `config.yml` on template defaults —
detection with a yes/no confirm, multi-select pick-and-mix when unsure.

Edges stay skill-based (no per-system adapter code) per the standing
direction; spec §10's semantics still govern: the item ULID is the
idempotency key, `link` events record external identity, sync-state hashes
suppress no-op pushes.

## Design decisions

- **`worklog link`** is the one new deterministic core piece for sync: after
  a successful push the skill runs
  `worklog link <item> --system github --key 123 --url ... --rev ... --hash ...`
  which appends the §5.3 `link` event (`set.external`). Nothing else writes
  the log.
- **ticket-sync skill** (push-only): read `ticketing:` config; for each open
  item, compute the §10.3 canonical hash; skip if it matches
  `.work/sync-state.json`'s `last_pushed_hash`; otherwise create/update the
  issue with an idempotency marker `<!-- worklog:<ULID> -->` in the body
  (search for the marker before creating — a retried push must find, not
  duplicate). GitHub mechanics via `gh`; other systems described vaguely
  (the model uses their CLI/MCP and researches gaps). Type/priority map to
  labels (`type:epic`, `P1`); parent/plan referenced in the body. Closed
  items are skipped (spec: closed items don't reconcile).
- **`worklog wiki-add`** registers a file in `.work/published.json` as
  `{key: {source, title, url: null, rev: null, source_hash: null}}`; the
  wiki-publish flow fills url/rev/hash on next publish. Ledger entries gain
  a `source` field (existing entries get it too, so the publish set is
  self-describing). Plans and the roadmap are always in the publish set.
- **`/worklog:init` detection** is model-work in the command file, not
  script-work: after `init.sh`, inspect `git remote -v`, installed CLIs
  (`gh`, `glab`, `az`, `jira`…), and available MCPs; if tickets/PRs/wiki are
  all confidently determined, present one summary for yes/no; otherwise
  AskUserQuestion per area with multi-select (pick and mix, e.g. GitHub PRs
  + Jira tickets + Confluence wiki); write the answers into
  `.work/config.yml`; commit scaffold + config in one commit.

## Tasks

- [ ] (P1) worklog link subcommand + tests (canon re-copy)
- [ ] (P1) ticket-sync skill, repo + plugin copies
- [ ] (P2) Config: ticketing block → github, project SpillwaveSolutions/wiki_ticket_sdd
- [ ] (P1) Rewrite /worklog:init command with detection + confirm/multi-select flow; plugin-guide note
- [ ] (P2) wiki-publish defaults: plans + roadmap always in the publish set; ledger entries carry source (existing item 01KXSQJ3SG)
- [ ] (P2) worklog wiki-add subcommand + tests (existing item 01KXSQJ3Z4)
- [ ] (P1) Dogfood: push open items to GitHub Issues, link events recorded, roadmap shows issue links
- [ ] (P2) Version 0.3.0 + CHANGELOG
- [ ] (P2) Pull + echo suppression + conflicts (§10.3–10.6) — deferred until we've lived with push-only

## Verification

- New suites green plus all existing (`for t in tests/test_*.py; do python3 "$t"; done`).
- `worklog link` then `worklog show` displays `external`; roadmap renders the issue key as a link.
- Second dogfood sync run is a no-op (hash skip + marker search).
- PR from `feature/ticket-sync-init`; CI green; issues visible in the repo.
