#!/usr/bin/env bash
# A plugin hook fires in EVERY session, whatever repo the user is in. In a
# repo not initialized for worklog (no bin/worklog) the hook must be silent —
# otherwise users get noise on every plan approval and disable the plugin.
if [ ! -x "bin/worklog" ]; then exit 0; fi

# WORKLOG-SPEC section 12, "Hooks, not hope": a CLAUDE.md instruction holds
# maybe 80% of the time; this hook holds 100%. Fires after ExitPlanMode and
# puts the capture requirement in front of the model, non-optionally.
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"POLICY (worklog): a plan was just approved. Before implementing anything, capture it: save the plan markdown (with a '## Tasks' section of '- [ ] (P#) title' checkboxes; two-space indent = subtask) to a temp file, then run `bin/worklog plan-capture --slug <kebab-slug> --title '<title>' --file <tempfile>`, then `bin/worklog roadmap-render`, and commit docs/plans/, docs/roadmap.md, and .work/todo.jsonl together. See .claude/skills/plan-capture/SKILL.md."}}
EOF
