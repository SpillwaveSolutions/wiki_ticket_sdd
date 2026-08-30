# Onboarding — WikiTicket SDD

WikiTicket SDD (pronounced "wicked ticket") is a local-first, git-native
work tracking layer for teams doing AI-assisted development. This file is
the first hour. The [User Guide](user_guide/user-guide.md) is the rest.

OKF / second-brain knowledge-tree writes used to ship in this plugin.
They do not anymore. That product lives in
[okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin) and
[second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core).

## What this plugin owns

The append-only work log (`.work/todo.jsonl`), generated roadmap / plans /
status, wiki publish, and ticket sync. Union merge, event fold, hook-enforced
policy. `bin/worklog` is the only writer of the log.

## Install

Plugin (skills, slash commands, hooks in every repo you open):

```sh
claude plugin marketplace add SpillwaveSolutions/wiki_ticket_sdd
claude plugin install worklog@worklog-marketplace
```

Then in a repo you want tracked:

```sh
/worklog:init
```

That copies `bin/worklog`, git hooks, and `.work/config.yml`. `worklog doctor`
is the health check; `worklog doctor --fix-wiring` repairs `core.hooksPath`
and `merge.ours.driver` on a fresh clone.

Settings live in `.work/config.yml`. Policy lives in `CLAUDE.md` (symlinked
as `AGENTS.md`). Do not infer settings from the policy file.

## First hour

1. **File the work before doing it.** `bin/worklog add --level story --kind feature --priority P1 "…"`.
   Unrecorded work is invisible work. The Stop hook will block a dirty tree
   with no items recorded this session.
2. **Plans are the spec.** Exiting plan mode runs `worklog plan-capture`. The
   plan is written once under `docs/plans/` and never regenerated. A changed
   design gets a new plan with `supersedes: <slug>`.
3. **Never hand-edit the log or the roadmap.** `bin/worklog` appends events.
   `worklog roadmap-render` regenerates `docs/roadmap.md`.
4. **Merge only when green.** `/worklog:merge <pr>` arms
   `gh pr merge --auto --merge` (never squash — ADR-0008). Pending means
   wait; failing means fix; never `--admin`.
5. **One session per working directory.** Two assistants in one checkout
   switch branches under each other. Use a `git worktree` per session.

## Concepts in one screen

- **Visible WIP.** Everything in flight lives in the repo. When an agent
  does work, that work is fishbowled: plans become tracked items before the
  work starts, status changes are events, the roadmap is regenerated from
  those events.
- **Generic core, system-agnostic edges.** The core never knows the word
  "Jira." `.work/config.yml` names your tracker and wiki. Skills instruct
  the agent to use whatever CLI or MCP that system has.
- **A hook holds 100%.** A `CLAUDE.md` instruction holds maybe 80%. Branch
  guard, schema, trailing newline, CI invariants — those are the floor.

## Next

- [User Guide](user_guide/user-guide.md) — day-to-day workflows
- [Plugin Guide](user_guide/plugin-guide.md) — install, commands, skills
- [CLI Reference](user_guide/cli-reference.md) — every flag
- [ADR-0003](adr/0003-green-gates-merge.md) / [ADR-0010](adr/0010-native-auto-merge-once-required-checks-e.md) — merge when green
