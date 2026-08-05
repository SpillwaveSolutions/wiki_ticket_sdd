# Harness ports

Tracking: GitHub issue #9. The shared `plugin/` package is canonical; each
host has a small native manifest or lifecycle adapter where required.

## Support matrix

| Harness | Status | What you get |
|---|---|---|
| Claude Code | Canonical | Full experience: auto-invoked skills, `/worklog:*` commands, ExitPlanMode/Stop/SessionStart hooks |
| Grok build | Full native compatibility, zero configuration | Same as Claude Code: marketplaces, plugins, skills, MCPs, agents, hooks, instruction files |
| Codex | Native plugin: skills + hooks | `.codex-plugin/plugin.json`, all bundled skills, the prompt/stop/session hooks, policy via `AGENTS.md`, and the repo scaffold. Plan capture stays policy-driven — see below |
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

Codex gets the hooks as well as the skills. It supports `UserPromptSubmit`,
`Stop`, `SessionStart`, `SessionEnd` and the tool events, it reads the same
`hookSpecificOutput` / `additionalContext` shape our scripts already emit, and
it sets `CLAUDE_PLUGIN_ROOT` for plugin-sourced hooks. So the scripts are
shared verbatim and only the wrapper differs: `hooks/codex-hooks.json` nests
the event map under a `hooks` key, where `hooks/hooks.json` has it flat.

The one hook that does not port is plan capture, and the reason is specific.
It fires on `PostToolUse` with a matcher for the `ExitPlanMode` **tool**;
Codex has the event but no such tool, so the matcher could never fire.
Shipping it would be dead configuration that reads like coverage. On Codex,
plan capture is enforced by `AGENTS.md` and the model runs
`bin/worklog plan-capture` before implementing.

This distinction matters more than it looks. `UserPromptSubmit` and `Stop` are
the two hooks the policy file names as the enforcement mechanism for work
tracking, and those are exactly the two that port. Codex is not on prose-only
enforcement; it is missing one capture convenience.

## Porting table

| Plugin piece | Claude Code / Grok build | Codex / OpenCode |
|---|---|---|
| Skills (`plugin/skills/`) | Auto-invoked by the harness | Native Codex skills; OpenCode relies on policy prose |
| Hooks (Stop, SessionStart, UserPromptSubmit) | Enforced by the harness | Same scripts via `hooks/codex-hooks.json`; OpenCode falls back to policy prose and the committed git hooks |
| Hook (plan capture, `PostToolUse`/`ExitPlanMode`) | Enforced by the harness | No `ExitPlanMode` tool exists — policy prose plus `worklog plan-capture` |
| Commands (`/worklog:init`, `/worklog:doctor`, `/worklog:uninstall`) | Slash commands | Codex/OpenCode shell invocations: `plugin/scripts/init.sh`, `plugin/scripts/doctor.sh`, and `plugin/scripts/uninstall.sh` |
| Settings | `.work/config.yml` | Same file — nothing harness-specific to port |
| Policy | `CLAUDE.md` block | Same block, read via the `AGENTS.md` symlink |

## When do real ports ship?

The Codex port ships as a native skills plugin. For hosts without a
native extension format, the repo scaffold remains the port.
