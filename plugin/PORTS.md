# Harness ports

Tracking: GitHub issue #9. The Claude Code plugin format is canonical.

## Support matrix

| Harness | Status | What you get |
|---|---|---|
| Claude Code | Canonical | Full experience: auto-invoked skills, `/worklog:*` commands, ExitPlanMode/Stop/SessionStart hooks |
| Grok build | Canonical (reads the same plugin format) | Same as Claude Code |
| Codex | Works today, zero port needed for the core | Policy via `AGENTS.md` (symlinked to `CLAUDE.md` by `/worklog:init`), plus everything the repo scaffold commits: `bin/worklog`, git hooks, CI |
| OpenCode | Works today, zero port needed for the core | Same as Codex |

The core is harness-independent by design: ALL real settings live in
`.work/config.yml`, ALL policy lives in `CLAUDE.md`, and `AGENTS.md` is a
symlink to it — so any harness that reads `AGENTS.md` gets the full worklog
policy, and `bin/worklog` works identically everywhere.

What Codex/OpenCode lose without a native port: auto-invoked skills, slash
commands, and the ExitPlanMode/Stop/SessionStart hooks. The `AGENTS.md`
policy prose has to carry that weight — it already states the plan-capture
and work-track rules, so the model is told what the hooks would have
enforced.

## Porting table

| Plugin piece | Claude Code / Grok build | Codex / OpenCode |
|---|---|---|
| Skills (`plugin/skills/`) | Auto-invoked by the harness | Policy prose in `AGENTS.md`, or harness-native command files if/when the harness grows a format worth targeting |
| Hooks (ExitPlanMode, Stop, SessionStart, UserPromptSubmit) | Enforced by the harness | None — rely on the policy prose plus the committed git hooks (pre-commit, pre-merge-commit), which run everywhere |
| Commands (`/worklog:init`, `/worklog:doctor`, `/worklog:uninstall`) | Slash commands | Shell invocations: `bin/worklog ...` and `plugin/scripts/*.sh` work from any shell |
| Settings | `.work/config.yml` | Same file — nothing harness-specific to port |
| Policy | `CLAUDE.md` block | Same block, read via the `AGENTS.md` symlink |

## When do real ports ship?

Ports ship when a harness gains a native extension format worth targeting;
until then the repo scaffold IS the port.
