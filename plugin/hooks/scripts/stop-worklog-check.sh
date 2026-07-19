#!/usr/bin/env bash
# Plugin hooks fire in every session; silence outside worklog repos.
[ -x bin/worklog ] || exit 0

# stop_hook_active means the model is already continuing from a prior Stop
# block — exit 0 or we loop forever.
if python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("stop_hook_active") else 1)' 2>/dev/null; then
  exit 0
fi

# Any git failure (not a repo, etc.) → allow stop silently.
branch_before=$(git -C "$PWD" rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0
dirty=$(git -C "$PWD" status --porcelain -- . ':!.work' ':!docs/roadmap.md' 2>/dev/null) || exit 0
[ -n "$dirty" ] || exit 0
# Settle-and-recheck: background merge chains flip branches mid-invocation and
# the first status read can see transient checkout state (observed 3x on
# 2026-07-19: false blocks with a clean tree). Re-read after a pause; if the
# tree settled clean or the branch moved under us, allow stop.
sleep "${WORKLOG_STOP_SETTLE:-2}"
dirty=$(git -C "$PWD" status --porcelain -- . ':!.work' ':!docs/roadmap.md' 2>/dev/null) || exit 0
[ -n "$dirty" ] || exit 0
branch_after=$(git -C "$PWD" rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0
[ "$branch_before" = "$branch_after" ] || exit 0
# Fresh repo with no HEAD yet → nothing to diff against, allow stop.
git -C "$PWD" rev-parse --verify HEAD >/dev/null 2>&1 || exit 0

# Tree changed outside .work/roadmap, but todo.jsonl is untouched vs HEAD:
# work happened with no work item recorded.
if git -C "$PWD" diff --quiet HEAD -- .work/todo.jsonl 2>/dev/null; then
  # Flag-gated classifier (spec §6.2): naive-yaml read of classifier.enabled.
  # Absent block, absent file, or anything but "true" → v0.6 behavior unchanged.
  enabled=$(sed -n '/^classifier:/,/^[a-zA-Z]/s/^[[:space:]]*enabled:[[:space:]]*\([a-z]*\).*/\1/p' .work/config.yml 2>/dev/null | head -1)
  if [ "$enabled" = "true" ]; then
    # Cheap no-model gate already passed: tree changed AND no new todo events.
    # A Stop hook cannot spawn subagents itself — emit context instructing the
    # main model to run the classify skill (which spawns the background worker).
    cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"worklog classifier: this exchange may contain untracked work — run the classify skill: spawn ONE background subagent to propose items into .work/suggestions.jsonl (propose-only; never writes the log), then review its suggestions next turn (worklog promote <id> to accept)."}}
EOF
  else
    cat <<'EOF'
{"decision":"block","reason":"worklog: the working tree changed but no work items were recorded this session. Record them (bin/worklog add/update/close + roadmap-render) or state why no item applies, then finish."}
EOF
  fi
fi
exit 0
