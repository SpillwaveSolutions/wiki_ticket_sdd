# WikiTicket SDD — Plugin Guide

How the Claude Code plugin packages WikiTicket SDD, and how the two install
levels fit together. For concepts see the [User Guide](user-guide.md); for
command flags see the [CLI Reference](cli-reference.md).

## Two install levels

The tooling installs at two distinct levels, and the distinction matters:

1. **Plugin install (per person).** Installing the plugin via the Claude Code
   marketplace gives *you* the skills, slash commands, and hooks in every
   repo you open. Nothing in any repo changes.

2. **Repo scaffold (per repo, committed).** Running `/worklog:init` inside a
   repo copies the CLI (`bin/`), the git hooks (`hooks/`), the union-merge
   `.gitattributes` lines, `.work/` (config + empty logs), the docs
   directories, a CI workflow, and a CLAUDE.md policy block — and you commit
   all of it. That's deliberate: **teammates and CI need no plugin.** Anyone
   who clones the repo gets working hooks, a working `bin/worklog`, and CI
   that enforces the invariants, whether or not they've ever heard of the
   plugin.

## The slash commands

### /worklog:init

Scaffold or upgrade the current repo. Idempotent — re-running on an
installed repo *is* the upgrade path: `bin/` and `hooks/` are re-copied from
the plugin, everything data-shaped is left alone. It records the installed
plugin version in `.work/config.yml` and **never touches existing
`.work/*.jsonl` logs**. Commit the scaffolding in one commit.

### /worklog:uninstall

Remove exactly what init added — the tooling, not the data. It asks for
confirmation first, then removes `bin/` scripts, `hooks/`, the
`.gitattributes` union-merge lines, the CI workflow, and the CLAUDE.md
policy block. **Preserved, always:** `.work/` (the event logs are the work
record), `docs/plans/` (the permanent design record), `docs/status/`, and
`docs/roadmap.md`. Data outlives tooling.

### /worklog:doctor

Read-only health report; it fixes nothing. Checks: installed version vs
plugin version (skew means "run `/worklog:init` to upgrade"), `bin/` files
present, executable, and byte-identical to the plugin's copies, hooks
present and `core.hooksPath` wired, and the invariant checks (newline,
schema, roadmap freshness) passing. Exit 0 healthy, 1 with problems.

## The skills

Skills are the judgment layer: the model decides *when*, the deterministic
`bin/worklog` scripts decide *what*.

| Skill | Trigger | What it does |
|---|---|---|
| `plan-capture` | exiting plan mode, "capture this plan" | Writes the plan doc and creates the epic + items via `worklog plan-capture`, renders the roadmap, commits together |
| `work-track` | creating/updating/closing items, mid-flight discoveries | Runs the right `worklog` command; enforces "record unplanned work BEFORE doing it" |
| `plan-next` | "what should we do next?" | Read-only: folds the log, filters open unblocked items, ranks by priority and epic, presents top candidates |
| `wiki-publish` | "publish the docs", plan completion | Reads the `wiki:` block in `.work/config.yml` and publishes the named docs to that system using whatever tooling is available (`gh`/git for GitHub wiki, MCP/CLI for Confluence, ADO, GitLab — researching missing tooling at runtime). Keeps the `.work/published.json` ledger so pages update instead of duplicating, skips unchanged files, and surfaces one-time setup steps (like creating a GitHub wiki's first page) to the human |

## The hooks

Prose policy holds maybe 80% of the time; a hook holds 100%. The plugin
ships hooks for the invariants:

| Hook | When | What |
|---|---|---|
| `ExitPlanMode` (PostToolUse) | a plan is approved | Invokes plan-capture non-optionally — every plan becomes tracked items |
| `UserPromptSubmit` | each prompt | One-line reminder: requests that produce work get worklog items first; keep statuses moving |
| `Stop` | Claude finishes responding | If the working tree changed but `.work/todo.jsonl` didn't, block once: record the work items or explain |
| `SessionStart` | session opens | Doctor-lite: checks the CLAUDE.md policy block, hook wiring, and version skew; points at `/worklog:init` or `/worklog:doctor` if something's off |

All hooks are silent outside worklog repos (no `bin/worklog`, no output), so
the plugin doesn't nag in repos that don't use it.

## Harness support

The Claude plugin format works with **Claude Code and Grok build today** —
all real settings live in `.work/config.yml` (never in the agent file), and
`AGENTS.md` is a symlink to `CLAUDE.md`, so one policy file serves both.
**OpenCode and Codex ports are on the roadmap.** Because `/worklog:init`
commits everything a repo needs, teammates on any harness — or none — can
still run `bin/worklog` and get the hooks; the plugin only adds the
skills-and-hooks convenience layer on top.
