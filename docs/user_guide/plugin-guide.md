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

On first install it also detects which systems the repo uses — from `git
remote -v` hostnames, installed CLIs (`gh`, `glab`, `az`, `jira`), and any
Jira/Confluence/Notion MCPs in the session. A confident read (say, a single
GitHub origin with `gh` authenticated) gets one yes/no confirmation;
anything less asks per area with multi-select, so teams can pick and mix —
GitHub PRs + Jira tickets + Confluence wiki is a legal combination. Answers
land in `.work/config.yml`'s `ticketing:`/`wiki:` blocks and go into the
same commit. Upgrade re-runs on an already-configured repo skip detection
entirely.

Init also offers the **work-taxonomy block** for `CLAUDE.md` — with
consent, never silently. It shows the block (the four axes, the six rules,
the inline-proposal policy), asks yes/no, and on yes writes it between
`<!-- worklog:taxonomy:start/end -->` markers, idempotently: re-running
updates the block in place, never duplicates it, and plain init never
touches `CLAUDE.md` at all. Because `AGENTS.md` symlinks to `CLAUDE.md`,
other harnesses inherit the taxonomy for free.

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

### /worklog:merge

Merge a PR the house-rules way: runs `merge-when-green.sh <pr>` in the
background, polling the PR's checks every 5 minutes (up to 2 h) and merging
only when every gate is green. Pending means wait; failing means fix; there
is no `--admin`, no bypass. After the merge it pulls the base branch,
deletes the local feature branch, syncs tickets if items closed, and
re-renders the roadmap if the log changed. These are the same house rules
CI enforces on this repo: green gates on every PR, plus a >=80% line
coverage floor on `bin/*.py` (target 95).

## The skills

Skills are the judgment layer: the model decides *when*, the deterministic
`bin/worklog` scripts decide *what*.

| Skill | What it does |
|---|---|
| `plan-capture` | Turns an approved plan into a frozen plan doc plus tracked items (epic + tasks), renders the roadmap, commits together |
| `work-track` | Runs the right `worklog` command for create/update/close; enforces "record unplanned work BEFORE doing it" and sets `level`/`kind`/`milestone` |
| `plan-next` | Read-only "what should we do next?": folds the log, filters open unblocked items, ranks by priority and epic |
| `ticket-sync` | Runs `worklog adapter check` + `worklog sync` (dispatcher owns the invariants) and reads back the drift report |
| `wiki-publish` | Publishes the configured docs to the team's wiki with the `.work/published.json` ledger, whatever the system (GitHub/GitLab/ADO/Confluence) |
| `status-report` | Generates and publishes frozen daily/weekly/timecard reports via `worklog status` |
| `release` | Cuts a versioned release: stamp the changelog, snapshot the roadmap, tag, platform release, publish, sync |
| `design-docs` | Generates/syncs the design doc + code walkthrough pair under `docs/designs/`: frozen dated copies per release, live `current` copies; runs in background agents at release time |
| `merge-green` | Merges PRs only when every quality gate is green — polls every 5 minutes via `merge-when-green.sh`, never bypasses |
| `classify` | Flag-gated classifier: sweeps a conversation for untracked work, propose-only into `.work/suggestions.jsonl` — never the event log |

## The hooks

Prose policy holds maybe 80% of the time; a hook holds 100%. The plugin
ships hooks for the invariants:

| Hook | When | What |
|---|---|---|
| `ExitPlanMode` (PostToolUse) | a plan is approved | Invokes plan-capture non-optionally — every plan becomes tracked items |
| `UserPromptSubmit` | each prompt | One-line reminder: requests that produce work get worklog items first; keep statuses moving |
| `Stop` | Claude finishes responding | If the working tree changed but `.work/todo.jsonl` didn't, block once: record the work items or explain. With `classifier.enabled: true` in `.work/config.yml` (**off by default**) it also triggers the classify skill — propose-only suggestions to `.work/suggestions.jsonl`, promoted into real items only via `worklog promote` |
| `SessionStart` | session opens | Doctor-lite: checks the CLAUDE.md policy block, hook wiring, and version skew; points at `/worklog:init` or `/worklog:doctor` if something's off |

All hooks are silent outside worklog repos (no `bin/worklog`, no output), so
the plugin doesn't nag in repos that don't use it.

## Harness support

The Claude plugin format works with **Claude Code and Grok build today** (per
the xAI docs, Grok is fully compatible with Claude Code with zero
configuration, automatically reading Claude Code marketplaces, plugins,
skills, MCPs, agents, hooks, and instruction files) —
all real settings live in `.work/config.yml` (never in the agent file), and
`/worklog:init` scaffolds `AGENTS.md` as a symlink to `CLAUDE.md`, so one
policy file serves every harness that reads either name. **Codex and
OpenCode therefore work today with no port**: because `/worklog:init`
commits everything a repo needs, teammates on any harness — or none — can
still run `bin/worklog` and get the hooks; the plugin only adds the
skills-and-hooks convenience layer on top. The support matrix and porting
guide live in [plugin/PORTS.md](../../plugin/PORTS.md).
