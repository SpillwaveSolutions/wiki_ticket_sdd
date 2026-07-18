---
date: 2026-07-18
slug: docs-wiki-dogfood
title: Docs, wiki publishing & dogfood discipline
epic: 01KXSNNSWJV2H5QS5CSTYASS6M
items: [01KXSNNSWJ3QKFCRBB3A12H5GT, 01KXSNNSWJDK16TMR50CNR3T3V, 01KXSNNSWJ8RHP53Z2VQJH4D9J, 01KXSNNSWJQ91JPN4QRVMJQ296, 01KXSNNSWJ72MM7XHEJBHM6A1Y, 01KXSNNSWJEP1V1JMSXH2MQWYV, 01KXSNNSWJMS2914A0JJYX3KEZ, 01KXSNNSWJN9C584RF3NNJK0W9, 01KXSNNSWJKRR3BF33CBK3E4Q7, 01KXSNNSWJ0P23QC3SYXRQ01WA, 01KXSNNSWJVJW87EPCZXE6QDCA, 01KXSNNSWJWK58BS457Y2NG3JA, 01KXSNNSWJZMQQH7H68XVB654Y, 01KXSNNSWKC64M1XX0Y7WVT67Z, 01KXSNNSWK0HC96WQ3HV98DHT8, 01KXSNNSWK2PPBHVJ21MBT65ER, 01KXSNNSWKPDG9Q4404RPTWZY9, 01KXSNNSWKTJX2QWW4PYFDEZHS]
---

# WikiTicket SDD: docs, wiki publishing, dogfood discipline, roadmap v0.2

## Context

v0.1.0 (plugin epic) is merged to `main` (PR #1). The project now gets its identity and public face: **WikiTicket SDD** (pronounced "wicked ticket") — spec-driven development where AI-driven work is fishbowled: every plan becomes tickets, every ticket syncs to whatever tracker/wiki the team already uses (GitHub, GitLab, Azure DevOps, Jira, Confluence…), and roadmap/status/history are visible artifacts, multi-team friendly.

**Direction set by the user (supersedes spec §9's coded-CLI-adapter contract):** the core stays generic and the *edges stay vague* — no shipped per-system adapter code. Publishing/syncing is done by **skills that instruct the model** to use whatever CLI/MCP/skill is available for the configured system, researching missing tooling at runtime. LLMs already know these systems; we don't ship a repository of integrations. This gets recorded as a roadmap item to revise the spec (v1.4), not silent drift.

Also new standing discipline (dogfood): **every user request gets broken into worklog items before the work starts.** This plan itself is captured via `worklog plan-capture` as step one.

Current state: local is on `feature/claude-plugin` (merged); roadmap is empty (10/10 closed); GitHub wiki is **enabled** on the private repo but almost certainly uninitialized (first page must be created once in the web UI — handled at publish time).

## Execution skeleton

1. `git checkout main && git pull`, branch `feature/docs-wiki-dogfood`.
2. **Capture this plan**: `bin/worklog plan-capture --slug docs-wiki-dogfood --title "Docs, wiki publishing & dogfood discipline" --file <this plan's Tasks section as draft>` → epic + tasks in `.work/todo.jsonl`, `roadmap-render`, commit. (The ExitPlanMode hook demands exactly this.)
3. Fan out subagents on independent tasks (README / user guide / code+tests / skills+installer), orchestrator commits between waves, worklog items moved `in_progress`→`done` per task.
4. Seed future-feature epics, render + snapshot roadmap, publish wiki pages, bump to 0.2.0, PR.

## Tasks

- [ ] (P1) Rewrite README.md — what/why: WikiTicket SDD ("wicked ticket"), fishbowled AI development, spec-driven (plans are the spec, tickets are the WIP), multi-team, system-agnostic edges (GitHub/GitLab/ADO/Jira/Confluence — they pick), epics/stories/tasks/bugs/subtasks, event-log history, generated roadmap/status. Keep quick-start + plugin sections, tightened.
- [ ] (P1) Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
  - [ ] Write docs/user_guide/user-guide.md — concepts (event log, fold, visible WIP), core workflows (plan→capture→work→close→sync, unplanned work, PR flow incl. roadmap merge recovery)
  - [ ] Write docs/user_guide/cli-reference.md — every worklog subcommand with examples, hooks, invariants
  - [ ] Write docs/user_guide/plugin-guide.md — plugin vs repo install levels, /worklog:* commands, skills, version/doctor, harness notes (Claude Code + Grok build now; OpenCode/Codex ports on roadmap)
- [ ] (P1) worklog roadmap-snapshot [--name] subcommand — copy docs/roadmap.md to docs/roadmap/<YYYY-MM-DD>_<name>.md, frozen (refuse overwrite), + tests; re-copy worklog to plugin/scripts (canon sync)
- [ ] (P1) wiki-publish skill (repo + plugin canonical copy) — system-vague: read .work/config.yml wiki block, publish named files using available tooling for that system (gh/git for GitHub wiki, MCP/CLI for Confluence/ADO/GitLab), research missing tooling, maintain .work/published.json ledger {key: {url, rev, source_hash}}, skip unchanged hashes, surface one-time init steps (e.g. GitHub wiki first page) to the human
- [ ] (P1) Dogfood policy in CLAUDE.md — every request is broken into worklog items via work-track BEFORE work starts; mirror line in work-track skill
- [ ] (P1) Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
  - [ ] UserPromptSubmit hook — inject a one-line reminder: requests that produce work get worklog items first (work-track), keep statuses moving
  - [ ] Stop hook — if the working tree has non-.work changes but .work/todo.jsonl is unchanged vs HEAD, block once with "record the work items or explain" (honor stop_hook_active from stdin JSON to prevent loops)
- [ ] (P1) SessionStart hook — doctor-lite on session open: verify CLAUDE.md carries the worklog policy block (marker or heading), core.hooksPath=hooks, and installed: version vs plugin version; emit additionalContext naming what's missing and pointing at /worklog:init or /worklog:doctor; silent when repo has no bin/worklog
- [ ] (P1) Seed roadmap: future epics via worklog add (ticket-sync skill-based w/ GitHub Issues first P1; spec v1.4 skill-based edges P2; wiki breadth Confluence/ADO/GitLab P2; compaction+nightly CI P2; status reports + plan-next P2; OpenCode/Codex ports P2; multi-tracker simultaneous P3)
- [ ] (P1) Render roadmap, snapshot as docs/roadmap/<date>_v0.2-roadmap.md
- [ ] (P1) Publish wiki: Home, User-Guide, CLI-Reference, Plugin-Guide, Roadmap (current), dated snapshot page; record in .work/published.json; add .work/wiki-checkout/ to .gitignore
- [ ] (P2) Plugin installer/uninstaller at repo root — install-plugin.sh (claude plugin marketplace add + install, graceful message if claude CLI absent), uninstall-plugin.sh (reverse)
- [ ] (P2) Packaging guard in tests/test_plugin.py — plugin/ contains no docs/user_guide content; canon list still passes
- [ ] (P2) Bump version 0.2.0 (plugin.json, worklog VERSION, skills frontmatter incl. new skill) + CHANGELOG entry

## Key files

- `README.md` — rewrite (vision + quick start; existing content as base)
- `docs/user_guide/{user-guide,cli-reference,plugin-guide}.md` — new; source of wiki pages
- `docs/wiki-home.md` — tiny Home page source, committed
- `bin/worklog` — add `cmd_roadmap_snapshot` (pattern: `cmd_plan_capture` refuse-overwrite wording); **must re-copy to `plugin/scripts/worklog`** or canon-sync test fails
- `.claude/skills/wiki-publish/SKILL.md` + `plugin/skills/wiki-publish/SKILL.md` — new skill (thin, vague, ledger-keeping); existing skills' frontmatter pattern
- `CLAUDE.md`, `.claude/skills/work-track/SKILL.md` — dogfood bullet
- `tests/test_snapshot.py` (new, small), `tests/test_plugin.py` (packaging + version list grows to include wiki-publish skill)
- `install-plugin.sh`, `uninstall-plugin.sh` — new, repo root
- `plugin/hooks/hooks.json` — gains UserPromptSubmit, Stop, SessionStart entries; scripts in `plugin/hooks/scripts/` (`prompt-reminder.sh`, `stop-worklog-check.sh`, `session-doctor.sh`), each guarded like `exit-plan-capture.sh` (silent without `bin/worklog`); repo `.claude/settings.json` + `hooks/` mirror them; tests assert JSON validity + guard silence + Stop-hook loop safety
- `.work/config.yml` — wiki.system: github-wiki (adapter key becomes advisory: "skill-based")
- `plugin/.claude-plugin/plugin.json`, `plugin/CHANGELOG.md` — 0.2.0
- `.gitignore` — `.work/wiki-checkout/`

## Wiki publish mechanics (this repo, GitHub — executed by me via the new skill's process, not shipped as code)

Clone `<origin>.wiki.git` into gitignored `.work/wiki-checkout/`, copy page files (flat namespace: `User-Guide.md` → "User Guide"), commit, push. If clone/push fails with not-found, the wiki is uninitialized → ask the user to open the repo's wiki tab and click "Create the first page" once, then retry. Update `published.json` with url + wiki commit sha + source hash.

## Verification

- All suites green: `for t in tests/test_*.py; do python3 "$t"; done` (incl. new snapshot + packaging tests).
- `worklog roadmap-snapshot` refuses a second same-day/name snapshot.
- `bin/worklog list` shows the seeded epics; `docs/roadmap.md` Now/Next/Later populated; snapshot file frozen under `docs/roadmap/`.
- Wiki pages visible at `https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki` (Home links resolve); `.work/published.json` committed.
- Plugin dir contains no user-guide docs; canon + version sync tests pass at 0.2.0.
- PR opened from `feature/docs-wiki-dogfood`; CI green.
