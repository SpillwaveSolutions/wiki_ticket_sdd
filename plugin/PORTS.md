# Harness ports

Tracking: GitHub issue #9. The shared `plugin/` package is canonical; each
host has a small native manifest or lifecycle adapter where required.

## Support matrix

| Harness | Status | What you get |
|---|---|---|
| Claude Code | Canonical | Full experience: auto-invoked skills, `/worklog:*` commands, ExitPlanMode/Stop/SessionStart hooks |
| Grok build | Full native compatibility, zero configuration | Same as Claude Code: marketplaces, plugins, skills, MCPs, agents, hooks, instruction files |
| Codex | Native skills plugin | `.codex-plugin/plugin.json`, all bundled skills, policy via `AGENTS.md`, and the repo scaffold |
| OpenCode | Works today, zero port needed for the core | Same as Codex |

### Grok build

Per the xAI docs (Skills, Plugins & Marketplaces): "Grok is fully compatible
with Claude Code with zero configuration needed. Grok automatically reads
Claude Code marketplaces, plugins, skills, MCPs, agents, hooks, and
instruction files (CLAUDE.md, Claude.md, CLAUDE.local.md, and .claude/rules/)
alongside .grok/." So the worklog plugin — manifest, commands, skills, hooks —
and the `/worklog:init` scaffold work in Grok Build natively; nothing to port.

Note: this claim is sourced from the xAI docs; a verification task is
pending — run `/worklog:init` plus one `/worklog:*` command under Grok Build
and record the result here.

The core is harness-independent by design: ALL real settings live in
`.work/config.yml`, ALL policy lives in `CLAUDE.md`, and `AGENTS.md` is a
symlink to it — so any harness that reads `AGENTS.md` gets the full worklog
policy, and `bin/worklog` works identically everywhere.

Codex installs from this repository's existing marketplace. Run
`codex plugin marketplace add SpillwaveSolutions/wiki_ticket_sdd`, open
`/plugins`, install `worklog`, and start a new session.

Codex and Claude Code use different hook configuration schemas, and Codex has
no documented `ExitPlanMode` event. The Codex manifest therefore packages the
skills without the Claude lifecycle hooks. `AGENTS.md` remains the work-track
and plan-capture enforcement point, and the model runs
`bin/worklog plan-capture` before implementation. Claude Code and Grok Build
continue to load `hooks/hooks.json` unchanged.

## Porting table

| Plugin piece | Claude Code / Grok build | Codex / OpenCode |
|---|---|---|
| Skills (`plugin/skills/`) | Auto-invoked by the harness | Native Codex skills; OpenCode relies on policy prose |
| Hooks (ExitPlanMode, Stop, SessionStart, UserPromptSubmit) | Enforced by the harness | Policy prose and committed git hooks |
| Commands (`/worklog:init`, `/worklog:doctor`, `/worklog:uninstall`) | Slash commands | Codex/OpenCode shell invocations: `plugin/scripts/init.sh`, `plugin/scripts/doctor.sh`, and `plugin/scripts/uninstall.sh` |
| Settings | `.work/config.yml` | Same file — nothing harness-specific to port |
| Policy | `CLAUDE.md` block | Same block, read via the `AGENTS.md` symlink |

## When do real ports ship?

The Codex port ships as a native skills plugin. For hosts without a
native extension format, the repo scaffold remains the port.
