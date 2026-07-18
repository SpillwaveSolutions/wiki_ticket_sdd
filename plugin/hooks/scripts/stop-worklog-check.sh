#!/usr/bin/env bash
# Plugin hooks fire in every session; silence outside worklog repos.
[ -x bin/worklog ] || exit 0

# stop_hook_active means the model is already continuing from a prior Stop
# block — exit 0 or we loop forever.
if python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("stop_hook_active") else 1)' 2>/dev/null; then
  exit 0
fi

# Any git failure (not a repo, etc.) → allow stop silently.
dirty=$(git -C "$PWD" status --porcelain -- . ':!.work' ':!docs/roadmap.md' 2>/dev/null) || exit 0
[ -n "$dirty" ] || exit 0
# Fresh repo with no HEAD yet → nothing to diff against, allow stop.
git -C "$PWD" rev-parse --verify HEAD >/dev/null 2>&1 || exit 0

# Tree changed outside .work/roadmap, but todo.jsonl is untouched vs HEAD:
# work happened with no work item recorded. Block once.
if git -C "$PWD" diff --quiet HEAD -- .work/todo.jsonl 2>/dev/null; then
  cat <<'EOF'
{"decision":"block","reason":"worklog: the working tree changed but no work items were recorded this session. Record them (bin/worklog add/update/close + roadmap-render) or state why no item applies, then finish."}
EOF
fi
exit 0
