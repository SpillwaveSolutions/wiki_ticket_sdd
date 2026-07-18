#!/usr/bin/env bash
# Plugin hooks fire in every session; silence outside worklog repos.
[ -x bin/worklog ] || exit 0

# doctor-lite: read-only, never blocks, reports only failures. Healthy → no output.
fails=()

if [ ! -f CLAUDE.md ] || ! grep -qE 'worklog:policy:start|Work tracking policy' CLAUDE.md; then
  fails+=("CLAUDE.md is missing the worklog policy block — run /worklog:init to repair")
fi

if [ "$(git config core.hooksPath 2>/dev/null)" != "hooks" ]; then
  fails+=("git core.hooksPath is not 'hooks' — run /worklog:init to repair")
fi

installed=""
[ -f .work/config.yml ] && installed=$(awk '/^installed:/ {print $2; exit}' .work/config.yml)
manifest="${CLAUDE_PLUGIN_ROOT:-}/.claude-plugin/plugin.json"
if [ -n "$installed" ] && [ -f "$manifest" ]; then
  plugin_v=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$manifest" 2>/dev/null)
  if [ -n "$plugin_v" ] && [ "$installed" != "$plugin_v" ]; then
    fails+=("version skew: repo $installed vs plugin $plugin_v — /worklog:init to upgrade")
  fi
fi

[ "${#fails[@]}" -eq 0 ] && exit 0

# JSON-encode via python so failure text never breaks the payload.
python3 -c '
import json, sys
ctx = "worklog doctor: " + "; ".join(sys.argv[1:])
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
' "${fails[@]}"
