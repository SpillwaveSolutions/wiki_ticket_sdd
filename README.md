# WikiTicket SDD

**Wiki ticket** — pronounced *"wicked ticket"*. WikiTicket Spec-Driven
Development.

## Why

Teams want spec-driven development that works across multiple teams and is
visible to everyone — **fishbowl** AI-assisted development. You can use AI
heavily, but the work is never hidden: every plan becomes tracked tickets,
the history of what was done is readily available, and roadmaps and status
reports are generated artifacts anyone can read. No "the agent did a bunch
of stuff last week and nobody knows what."

## What it does

- **Append-only, git-native work log.** Epics, stories, tasks, subtasks, and
  bugs live in `.work/todo.jsonl` — an event log that multiple people (and
  agents) can work against concurrently. Union merge, event fold: branches
  merge cleanly, state is derived by folding events.
- **Plans are the permanent design record.** Exiting plan mode captures the
  plan to `docs/plans/` and emits tracked items. Planning never evaporates;
  when you need the *why*, read the plan.
- **Generated roadmap and status reports.** `docs/roadmap.md` is rendered
  from the log — no hand-editing, no drift.
- **Syncs to the team's OWN systems** — wiki *and* tickets. Your work log
  publishes to whatever your team already uses.

## System-agnostic edges, deliberately

Works equally with GitHub, GitLab, Azure DevOps (wiki + work items), Jira,
Confluence — and whatever the equivalent is elsewhere. The team picks.

The core never contains per-system code. Publishing and sync are done by
*skills* that instruct the AI to use whatever CLI, MCP server, or skill is
available for the chosen system, researching missing tooling at runtime.
LLMs already know these systems well; shipping a repository of per-system
integrations would be dead weight. You could even run two trackers at once
(GitHub + Jira) — the workflow stays identical.

## Quick start (no plugin)

Clone, then wire the git hooks:

```sh
git config core.hooksPath hooks
```

Track work with the CLI:

```sh
bin/worklog add "Extract auth middleware" --type task --priority P0
bin/worklog add "Fix flaky retry" --unplanned --discovered-during <id>
bin/worklog update <id> --status in_progress
bin/worklog close <id>
bin/worklog list
```

Capture a plan and regenerate the roadmap:

```sh
bin/worklog plan-capture --slug my-plan --title "My plan" --file draft.md
bin/worklog roadmap-render
```

The pre-commit and pre-merge-commit hooks enforce the invariants: trailing
newline on the log, event schema validation, and `roadmap.md` freshness.

## Claude Code plugin

The plugin (in [plugin/](plugin/)) packages the skills, `/worklog:*`
commands, and the ExitPlanMode capture hook. Install from this repo:

```sh
claude plugin marketplace add <this-repo-url-or-path>
claude plugin install worklog@worklog-marketplace
```

Two install levels, deliberately distinct:

- **Plugin install** (above) — every session gets the skills, commands, and
  hook. Global; changes no repo.
- **Repo install** — inside a target repo, run `/worklog:init`. It scaffolds
  `bin/`, the git hooks, an empty `.work/` with `config.yml`, and the CI
  check. The copies are committed, so hooks and CI work for teammates who
  don't have the plugin.

Also: `/worklog:uninstall` removes the tooling but never touches `.work/`
data, `docs/plans/`, `docs/status/`, or `docs/roadmap.md` — the data
outlives the tooling. `/worklog:doctor` reports version drift and invariant
violations without changing anything.

## How it works

The full design — event schema, fold semantics, merge behavior, sync model —
is in [docs/worklog-spec.md](docs/worklog-spec.md). Task-oriented guides
(concepts, CLI reference, plugin guide) live in
[docs/user_guide/](docs/user_guide/).

## Layout

| Path | What |
|---|---|
| `.work/` | Append-only event log (`todo.jsonl`, `done.jsonl`) and `config.yml` |
| `bin/` | `worklog` CLI plus its Python modules (`fold.py`, `render_roadmap.py`, `plan_capture.py`, `ulid.py`) |
| `docs/plans/` | Captured plan documents (frontmatter links plans to items) |
| `docs/status/` | Generated status reports |
| `docs/roadmap.md` | Generated roadmap — do not edit |
| `hooks/` | `pre-commit`, `pre-merge-commit`, `exit-plan-capture.sh` |
| `plugin/` | The Claude Code plugin (manifest, commands, skills, hooks, canonical scripts) |
| `tests/` | Unit and integration tests |

## Testing

```sh
for t in tests/test_*.py; do python3 "$t"; done
```

Stdlib `unittest` only — no pytest, no dependencies. Unit suites cover the
fold, ULIDs, roadmap rendering, and plan capture; `tests/test_integration.py`
simulates full PR flows (branch, track, merge, fold) in throwaway git repos.
