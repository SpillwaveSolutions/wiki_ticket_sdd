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
- **A four-axis work taxonomy.** Every item sits on `level`
  (epic/story/task/subtask), `kind` (feature/bug/ops/triage), `milestone`
  (what ships together), and planned-vs-discovered. The unclassified default
  is `triage` — visible in the roadmap's needs-classification queue, never a
  silent guess.
- **Generated roadmap and status reports.** `docs/roadmap.md` is rendered
  from the log — no hand-editing, no drift.
- **Syncs to the team's OWN systems** — wiki *and* tickets. Your work log
  publishes to whatever your team already uses.

## System-agnostic edges, deliberately

Works equally with GitHub, GitLab, Azure DevOps (wiki + work items), Jira,
Linear, AWS CodeCatalyst, Confluence — and `other` is a first-class config
value for anything else. The team picks. (GCP ships no native tracker;
GCP-hosted teams pick from the list like everyone else.)

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
bin/worklog add "Extract auth middleware" --level task --kind feature \
    --milestone v0.7.0 --priority P0
bin/worklog add "Fix flaky retry" --kind bug --unplanned --discovered-during <id>
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

## House rules, enforced

Policy that holds because tooling holds it, not because people remember:

- **PRs merge only when every gate is green.** The merge-green skill (or
  `/worklog:merge`) polls checks every 5 minutes via `merge-when-green.sh`;
  never `--admin`, never bypass. Auto-merge on green is on by default;
  teams that want a human on the trigger set
  `features.auto_merge_on_green: false` in `.work/config.yml` (advisory
  mode: report green, human merges).
- **Coverage floor.** CI enforces >=80% line coverage on `bin/*.py`; the
  target is 95%.
- **Frozen artifacts.** Plans, roadmap snapshots, and published status
  reports are written once and never regenerated — corrections go in new
  documents.
- **The roadmap is generated.** Never hand-edited; to change it, change the
  work items and re-render.

## Claude Code plugin

The plugin (in [plugin/](plugin/)) packages the skills, `/worklog:*`
commands (including `/worklog:merge`, the green-gates merge loop), and the
ExitPlanMode capture hook. Install from this repo's marketplace:

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
violations without changing anything. Ticket sync runs through a typed
adapter contract: `worklog adapter check` validates an adapter against the
contract before anything activates.

### Other harnesses (Codex, OpenCode, Grok build)

The repo scaffold is harness-independent: `bin/worklog`, the git hooks, and
CI are committed and work from any shell. The `AGENTS.md` symlink (created
by `/worklog:init`, pointing at `CLAUDE.md`) carries the full worklog policy
to any harness that reads `AGENTS.md`. Grok Build is fully compatible with
Claude Code with zero configuration — per the xAI docs it automatically reads
Claude Code marketplaces, plugins, skills, MCPs, agents, hooks, and
instruction files. See
[plugin/PORTS.md](plugin/PORTS.md) for the support matrix and porting guide.

## How it works

The full design — event schema, fold semantics, merge behavior, sync model —
is in [docs/worklog-spec.md](docs/worklog-spec.md). Task-oriented guides
(concepts, CLI reference, plugin guide) live in
[docs/user_guide/](docs/user_guide/).

## Layout

| Path | What |
|---|---|
| `.work/` | Append-only event log (`todo.jsonl`, `done.jsonl`) and `config.yml` |
| `adapters/` | Ticket-sync adapters: shipped `fake` (CI double) and `github` (worked example), plus authoring rules |
| `schema/` | JSON Schemas for the adapter contract (capabilities, adapter I/O) |
| `bin/` | `worklog` CLI plus its Python modules (`fold.py`, `sync_dispatch.py`, `render_roadmap.py`, `plan_capture.py`, `ulid.py`) |
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
