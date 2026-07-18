# worklog

Local-first, git-native work tracking for agentic coding. Three properties
drive everything:

1. **Visible WIP** — everything in flight lives in the repo, as an
   append-only event log (`.work/todo.jsonl`) that merges cleanly across
   branches.
2. **Plans produce tickets** — exiting plan mode captures the plan to
   `docs/plans/` and emits tracked items; planning never evaporates.
3. **Generated artifacts** — `docs/roadmap.md` is rendered from the log and
   read-only for humans. No parser, no round-trip, no drift.

Full spec: [docs/worklog-spec.md](docs/worklog-spec.md).

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

Also:

- `/worklog:uninstall` removes the tooling that init added, but never
  touches `.work/` data, `docs/plans/`, `docs/status/`, or
  `docs/roadmap.md` — the data outlives the tooling.
- `/worklog:doctor` compares the repo's scaffold version against the plugin
  version and runs the invariant checks, reporting drift without changing
  anything.

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

Stdlib `unittest` only — no pytest, no dependencies.

Four unit suites — `test_fold.py`, `test_ulid.py`, `test_render_roadmap.py`,
`test_plan_capture.py` — plus `tests/test_integration.py`, which simulates
full PR flows (branch, track, merge, fold) in throwaway git repos.
