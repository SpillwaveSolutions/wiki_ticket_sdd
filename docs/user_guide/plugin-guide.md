---
doc_type: guide
slug: plugin-guide
title: WikiTicket SDD — Plugin Guide
truth_state: current
wiki_key: plugin-guide
---
# WikiTicket SDD — Plugin Guide

How the plugin packages WikiTicket SDD, and how the two install levels fit
together. One shared `plugin/` tree, one manifest per host: Claude Code (and
Grok Build, which reads the Claude format natively) and, since 0.22.0, Codex.
For concepts see the [User Guide](user-guide.md); for command flags see the
[CLI Reference](cli-reference.md).

## Two install levels

The tooling installs at two distinct levels, and the distinction matters:

1. **Plugin install (per person).** Installing the plugin from the
   marketplace gives *you* the skills, slash commands, and hooks in every
   repo you open. Nothing in any repo changes.

   ```sh
   claude plugin marketplace add <this-repo-url-or-path>
   claude plugin install worklog@worklog-marketplace
   ```

   Codex uses the same marketplace and the native manifest at
   `plugin/.codex-plugin/plugin.json`:

   ```sh
   codex plugin marketplace add SpillwaveSolutions/wiki_ticket_sdd
   codex
   # Open /plugins, install worklog, then start a new session.
   ```

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

**Init writes `CLAUDE.md` and the `AGENTS.md` symlink but does not commit
them** — that is your job, and it is easy to never notice, because everything
works locally either way. Check:

```bash
git ls-files CLAUDE.md AGENTS.md
```

Empty output means a fresh clone of your repo carries no policy at all, and
any agent session started from that clone runs with none of your rules. Fix
it with `git add CLAUDE.md AGENTS.md` and a commit, then confirm the symlink
stored as a symlink rather than a copy — `git ls-files -s AGENTS.md` should
show mode `120000`.

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
`bin/worklog` scripts decide *what*. A skill whose YAML frontmatter fails to
parse is **not rejected** — it loads with empty metadata, so its `name` and
`description` vanish and the model can never match it. Installed and
invisible; 0.22.1 added a check that every shipped skill declares both.

| Skill | What it does |
|---|---|
| `plan-capture` | Turns an approved plan into a frozen plan doc plus tracked items (epic + tasks), renders the roadmap, runs `ia-index`, commits together |
| `work-track` | Runs the right `worklog` command for create/update/close; enforces "record unplanned work BEFORE doing it" and sets `level`/`kind`/`milestone` |
| `plan-next` | Read-only "what should we do next?": folds the log, filters open unblocked items, ranks by priority and epic |
| `ticket-sync` | Runs `worklog adapter check` + `worklog sync` (dispatcher owns the invariants) and reads back the drift report; bodies from `ticket-body` |
| `issue-description` | Durable ticket prose: compose via `worklog ticket-body` (summary, plan/epic context, traceability); enrich source with `update --body` / `link-pr` |
| `pr-description` | Durable PR prose for the change set (pairs with green-gates merge flow) |
| `wiki-publish` | Publishes via `docs/.index/publish-manifest.json` when present (Home, Sidebar, indexes, per-ticket/release/PR artifact pages, banners) and the `.work/published.json` ledger; strips YAML frontmatter for GitHub Wiki |
| `status-report` | Generates and publishes frozen daily/weekly/timecard reports via `worklog status` |
| `release` | Cuts a versioned release: stamp the changelog (first draft from `worklog changelog-draft`), snapshot the roadmap, tag, platform release, publish, sync; refreshes indexes. Gates on `trace-check --strict` and `doc-verify --strict`; runs `provenance-backfill` in the post-release step |
| `design-docs` | Generates/syncs the design doc + code walkthrough pair under `docs/designs/`: frozen dated copies per release, live `current` copies; runs in background agents at release time. Must run `worklog doc-verify` and clear every fabricated citation before reporting done — that check is why the pair's line numbers can be trusted |
| `merge-green` | Merges PRs only when every quality gate is green — polls every 5 minutes via `merge-when-green.sh`, never bypasses |
| `classify` | Flag-gated classifier: sweeps a conversation for untracked work, propose-only into `.work/suggestions.jsonl` — never the event log |
| `integration-guide` | Looks up the wiki-hosted setup guide for a named SDD tool or ticket/wiki system (Superpowers, GSD, SpecKit, OpenSpec, Jira, Confluence, GitHub, GitLab, Azure DevOps, AWS CodeCatalyst, Google Cloud DevOps), falling back to the local copy under `docs/integrations/` on fetch failure |

## The hooks

Prose policy holds maybe 80% of the time; a hook holds 100%. The plugin
ships hooks for the invariants:

| Hook | When | What |
|---|---|---|
| `ExitPlanMode` (PostToolUse) | a plan is approved | Invokes plan-capture non-optionally — every plan becomes tracked items |
| `UserPromptSubmit` | each prompt | One-line reminder: requests that produce work get worklog items first; keep statuses moving. Also heartbeats this session into `.work/.sessions` and appends the concurrent-session warning when another session is live in the same checkout |
| `Stop` | Claude finishes responding | If the working tree changed but `.work/todo.jsonl` didn't, block once: record the work items or explain. With `classifier.enabled: true` in `.work/config.yml` (**off by default**) it also triggers the classify skill — propose-only suggestions to `.work/suggestions.jsonl`, promoted into real items only via `worklog promote` |
| `SessionStart` | session opens | Doctor-lite: checks the CLAUDE.md policy block, hook wiring, and version skew; points at `/worklog:init` or `/worklog:doctor` if something's off |
| `SessionEnd` | session closes | Drops this session from `.work/.sessions`, so a finished session stops warning the next one that opens the directory |

All hooks are silent outside worklog repos (no `bin/worklog`, no output), so
the plugin doesn't nag in repos that don't use it.

**Upgrade to 0.22.1 if you installed the plugin before it.** Until 0.22.1 the
hook manifest declared its events at the top level, where the loader reads
them from under a top-level `hooks` key. The file was valid JSON, so nothing
failed and nothing warned — the loader simply found no events, and **every
hook above silently did nothing for anyone who installed the plugin**,
including plan capture. After upgrading, expect hooks to start firing that
never did: the prompt reminder, the session doctor, the stop check and the
plan-capture prompt are not new features, they are what you already installed
working for the first time. It could not be found from inside this repository,
whose own sessions wire the same scripts through settings rather than through
the plugin loader.

On Codex, `plugin/hooks/codex-hooks.json` wires the same scripts — the prompt
reminder, the stop check and the session doctor all run there. They needed no
porting: Codex sets `CLAUDE_PLUGIN_ROOT` for plugin-sourced hooks and reads
the same `hookSpecificOutput` / `additionalContext` output, so only the
wrapper differs. Plan capture is the exception: it matches the `ExitPlanMode`
**tool** on `PostToolUse`, and Codex has the event but not that tool — so on
Codex plan capture is what `AGENTS.md` says it is, and you run
`bin/worklog plan-capture ...` before implementing. The two hooks the policy
names as the enforcement mechanism for work tracking are exactly the two that
port.

## Harness support

The Claude plugin format works with **Claude Code and Grok build today** (per
the xAI docs, Grok is fully compatible with Claude Code with zero
configuration, automatically reading Claude Code marketplaces, plugins,
skills, MCPs, agents, hooks, and instruction files) —
all real settings live in `.work/config.yml` (never in the agent file), and
`/worklog:init` scaffolds `AGENTS.md` as a symlink to `CLAUDE.md`, so one
policy file serves every harness that reads either name. **Codex has a native
plugin as of 0.22.0** — the same skills, plus every hook except plan capture
(see above). **OpenCode still needs no port**: because `/worklog:init` commits
everything a repo needs, teammates on any harness — or none — can still run
`bin/worklog` and get the git hooks; a plugin only adds the skills-and-hooks
convenience layer on top. The support matrix and porting guide live in
[plugin/PORTS.md](../../plugin/PORTS.md).
