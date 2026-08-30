# Acme Platform

## Work tracking policy

Work items live in `.work/todo.jsonl`. **Settings live in `.work/config.yml` — read that
file; do not infer settings from this document.** This file is policy only, which is why
`AGENTS.md` is a symlink to it: one policy, every harness. Do not add harness-specific
notes here.

- **Every request that produces work is broken into worklog items FIRST.** Run
  `bin/worklog add` (see the work-track skill) before starting, and move items
  `in_progress` → `done` as the work happens — the UserPromptSubmit and Stop hooks
  enforce this. Unrecorded work is invisible work.

- **Exiting plan mode is not optional bookkeeping.** Every plan MUST end by running
  `worklog plan-capture`, which writes `docs/plans/<date>-<name>.md` and appends the
  plan's steps as work items. This is also enforced by a hook; if you find yourself
  ending a plan without it, that's a bug, not a shortcut. After capture, plans and
  their items are published (tickets + wiki) by a background subagent; implementation
  never waits on publishing.

- **Plans are the permanent design record.** `docs/plans/` is where the *why* lives — it
  is the specification half of spec-driven development, checked into the repo and
  published to the wiki for exactly that reason. A plan is written once and never
  regenerated or rewritten. If the design changed, write a NEW plan with
  `supersedes: <slug>` in its front matter. Do not edit history: the record of why the
  first approach was abandoned is the most valuable thing in the file. When you need to
  know why a decision was made, read the plan, not the ticket.

- **If you discover work mid-flight that wasn't in the plan** — a bug, a missing
  migration, a broken test — run `worklog add --unplanned --discovered-during <item>`
  BEFORE doing the work. Do not silently absorb it. Unplanned work that never gets
  recorded is why estimates never improve.

- **When a plan is complete, run `worklog sync`.** This closes items, updates the
  ticketing system, regenerates the roadmap, and publishes. Partial failure is expected
  and fine — sync is best-effort by design and reports its drift.

- **When asked for a status report**, run `worklog status --kind <daily|weekly|timecard>`.
  It writes `docs/status/<date>-<kind>.md`, commits, and publishes to the wiki. Never
  paste a status report into chat without writing the file — an unrecorded status report
  is a rumour.

- **Status reports are frozen once published.** If last Tuesday's daily was wrong, write
  the correction into today's report. Do not regenerate an old one: someone read it and
  made a decision from it.

- **Never hand-edit `docs/roadmap.md`.** It is generated and CI-checked. To change the
  roadmap, change the work items.

- **Design docs and code walkthroughs are generated, never hand-edited.** The design-docs
  skill regenerates `docs/designs/` at release via background agents: the `current_*`
  pair is a sanctioned in-place rewrite (like `docs/roadmap.md`), the dated copies are
  frozen. A hand-edit is either overwritten at the next release or corrupts a frozen
  record — fix the code or the skill instead.

- **Tests must hold coverage.** CI enforces >=80% line coverage on `bin/*.py`; the
  target is 95%. New modules ship with tests, and a PR that drops coverage below the
  floor does not merge.

- **PRs merge only when every quality gate is green.** Arm `gh pr merge --auto --merge`
  (or `/worklog:merge`) so GitHub merges when required checks pass; the poll loop is
  fallback. Pending means wait; failing means fix. Never `--admin`, never squash
  (ADR-0008), never bypass a gate, never merge blind.

- **Never edit `.work/*.jsonl` with an editor or a shell redirect.** Use `worklog`. Every
  write must be a well-formed event terminated with a newline; a hand-edit that drops the
  trailing newline corrupts the next merge.

- **One session per working directory.** Two assistant sessions sharing a checkout switch
  branches out from under each other mid-operation and independently "fix" the same
  problem in different ways. Give each session its own `git worktree`. `worklog` warns
  when it sees more than one session active here, but the warning is advisory and arrives
  after the fact — the worktree is the actual fix.

<!-- worklog:taxonomy:start -->
## Work taxonomy

Every work item sits on four independent axes:

| Axis | Field | Values | Answers |
|---|---|---|---|
| Level | `level` | epic / story / task / subtask | size & place in the parent tree |
| Kind | `kind` | feature / bug / ops / triage | nature of the work |
| Milestone | `milestone` | free string (e.g. v0.6.0) or null | what ships together |
| Planned | `unplanned` + `discovered_during` | bool + ULID | deliberate vs discovered |

Rules (the validator enforces these; apply them when proposing items):
1. Kind is free at story/task/subtask.
2. Epics are `feature` or `ops` only — a bug is never epic-sized.
3. `kind` defaults to `triage` when omitted — never silently default to feature.
4. `bug.parent` is optional; bugs may float free of any epic.
5. `milestone` lives on leaves (story and below); an epic's milestone derives from its children.
6. `triage` and `ops` both trend down: triage shrinks by classifying, ops by automating.

When trackable work surfaces in conversation, propose an item inline as part of
the normal response — "want me to file this? `level:story kind:feature
parent:<ulid> milestone:v0.6.0`" — and create it only on assent, via the
work-track or plan-capture skill. When unsure of the kind, propose `kind:triage`
with the open question stated — triage is the honest default, never a confident
guess. This inline path is the default; the flag-gated classifier (`classifier:`
in `.work/config.yml`, off by default) is the escape hatch for teams where work
keeps escaping the log.
<!-- worklog:taxonomy:end -->
