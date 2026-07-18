#!/usr/bin/env bash
# Plugin hooks fire in every session; silence outside worklog repos.
[ -x bin/worklog ] || exit 0

# Fires on every prompt — keep it to one short line.
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"worklog policy: if this request produces work, record it first (bin/worklog add / work-track skill), move items in_progress/done as you go, and roadmap-render before committing."}}
EOF
