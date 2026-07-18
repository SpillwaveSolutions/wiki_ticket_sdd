---
date: 2026-07-18
slug: claude-plugin
title: Worklog Claude plugin
epic: 01KXSFEWNCJMXPZDNT7RNYTG8X
items: [01KXSFEWNDT1B5D0PRK16NX14T, 01KXSFEWND18ATDAPCWJXKV8C1, 01KXSFEWNDZ55K8AQJBCN9MRD6, 01KXSFEWNDR0ZDTHHGQVN3PG9Z, 01KXSFEWNDM44B8A8RV30PF6X1, 01KXSFEWND2PG3PQW8GMZ9B319, 01KXSFEWND595MAFB1GMB9KECF, 01KXSFEWNDBM4RHBFMNYJWR9CE, 01KXSFEWND3DGDF12DSWJEKVDF, 01KXSFEWND4TYQ2V26KRPFHW9M]
---

# Worklog Claude plugin — design

Package the worklog system as an installable Claude Code plugin so any repo
gets visible-WIP tracking without hand-copying files. Designed against the
plugin spec: manifest in `.claude-plugin/plugin.json`, components at plugin
root, `${CLAUDE_PLUGIN_ROOT}` for every intra-plugin path.

## Shape

The plugin lives in `plugin/` in this repo — the repo root stays a working
worklog installation, which makes it the plugin's own first dogfood:

    plugin/
      .claude-plugin/
        plugin.json              # name: worklog, semver version, metadata
      commands/
        init.md                  # /worklog:init      — scaffold the current repo
        uninstall.md             # /worklog:uninstall — remove scaffolding
        doctor.md                # /worklog:doctor    — version skew + invariants
      skills/
        plan-capture/SKILL.md    # generic; moved from .claude/skills
        work-track/SKILL.md
        plan-next/SKILL.md
      hooks/
        hooks.json               # PostToolUse on ExitPlanMode
        scripts/
          exit-plan-capture.sh   # exits 0 silently if repo has no bin/worklog
      scripts/                   # canonical copies: worklog, fold.py, ulid.py,
                                 # render_roadmap.py, plan_capture.py,
                                 # pre-commit, pre-merge-commit
      CHANGELOG.md

## Install / uninstall semantics — two levels, deliberately distinct

1. **Plugin install** (`claude plugin install worklog@<marketplace>`): every
   session gets the skills, the `/worklog:*` commands, and the ExitPlanMode
   hook. Global; changes no repo.
2. **Repo install** (`/worklog:init`): scaffolds the CURRENT repo by copying
   from `${CLAUDE_PLUGIN_ROOT}/scripts/` into the repo: `bin/`, both git
   hooks, `.gitattributes` union-merge lines, empty `.work/` + `config.yml`,
   the CLAUDE.md policy block, and the CI workflow. Copies are COMMITTED so
   hooks and CI work for teammates who do not have the plugin. The plugin
   version is recorded in `.work/config.yml` as `installed: x.y.z`.

`/worklog:uninstall` removes what init added (bin/, hook wiring, gitattributes
lines, policy block) but NEVER touches `.work/*.jsonl`, `docs/plans/`,
`docs/status/`, or `docs/roadmap.md` — the data outlives the tooling. It
prints what it kept and why.

The ExitPlanMode hook script must exit 0 silently when the current repo has no
`bin/worklog` (plugin installed, repo not initialized) — a plugin hook fires
in every session, and noise in uninitialized repos would get the plugin
disabled.

## Versioning

- Semver in `plugin.json`; `CHANGELOG.md` entry per release.
- `bin/worklog --version` prints the version baked in at scaffold time.
- `/worklog:doctor` compares the repo's scaffold version against the plugin
  version, runs the invariant checks (newline, schema, roadmap freshness),
  and reports drift without changing anything.
- `/worklog:init` on an already-initialized repo is the upgrade path:
  re-copies scripts, shows the diff, never touches `.work/` data.

## Open questions

- Marketplace: separate repo, or `.claude-plugin/marketplace.json` here?
- After the move, do repo-local `.claude/skills` become thin pointers to the
  plugin skills, or get deleted outright?

## Tasks

- [ ] (P1) Scaffold plugin/ with .claude-plugin/plugin.json manifest v0.1.0
- [ ] (P1) Move the three skills into plugin/skills, canonical copies
- [ ] (P1) /worklog:init command — scaffold bin, hooks, .work, .gitattributes, CI into the current repo
  - [ ] (P1) Record installed plugin version in .work/config.yml
- [ ] (P1) /worklog:uninstall command — remove scaffolding, always preserve .work data and docs
- [ ] (P2) /worklog:doctor — version skew report + invariant checks
- [ ] (P2) Plugin hooks.json ExitPlanMode hook with uninitialized-repo guard
- [ ] (P2) bin/worklog --version + plugin CHANGELOG.md
- [ ] (P2) Marketplace manifest + README install docs
- [ ] (P2) Integration test: init, track, uninstall in a sandbox repo
