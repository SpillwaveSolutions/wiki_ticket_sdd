#!/usr/bin/env bash
# Merge a PR only when every check is green. Polls until then. Never bypasses
# a gate: a failing check is a stop, not an obstacle. GitHub via gh; other
# platforms use their CLI equivalent per the merge-green skill.
#
# Auto-merge is armed up front (`gh pr merge --auto --merge`) so GitHub
# merges server-side the moment checks go green. The poll loop is the
# fallback reporter, not the merge mechanism. Never squash (ADR-0008).
set -euo pipefail

# Optional first arg forces auto-merge on/off for this run only.
FORCE=""
case "${1:-}" in
  --advisory) FORCE=false; shift ;;
  --auto)     FORCE=true;  shift ;;
esac

PR="${1:?usage: merge-when-green.sh [--advisory|--auto] <pr-number> [interval-seconds] [max-attempts]}"
INTERVAL="${2:-60}"    # 1 minute; --auto makes the long poll a fallback
MAX="${3:-120}"        # 120 × 60s = 2 h, then give up loudly

# Resolve auto-merge: --advisory/--auto > WORKLOG_AUTO_MERGE=0|1 > config > true.
# ponytail: naive block scan, same style as _config_system in bin/worklog
AUTO_MERGE=true
cfg=$(awk '/^features:/{f=1;next} f&&/^[^[:space:]]/{exit} f&&/auto_merge_on_green:/{print $2; exit}' \
      ./.work/config.yml 2>/dev/null || true)
[ "$cfg" = "false" ] && AUTO_MERGE=false
case "${WORKLOG_AUTO_MERGE:-}" in
  0) AUTO_MERGE=false ;;
  1) AUTO_MERGE=true ;;
esac
[ -n "$FORCE" ] && AUTO_MERGE=$FORCE

command -v gh >/dev/null 2>&1 || {
  echo "merge-when-green: gh CLI required for GitHub PRs; other platforms: use their CLI with the same rule" >&2
  exit 2
}

state=$(gh pr view "$PR" --json state -q .state)
if [ "$state" != "OPEN" ]; then
  echo "merge-when-green: PR #$PR is $state — nothing to merge" >&2
  exit 3
fi

if [ "$AUTO_MERGE" = true ]; then
  # Arm GitHub auto-merge now so the platform merges when checks go green
  # instead of waiting for our next poll. Non-fatal: we still merge
  # ourselves once green if --auto is unsupported or already pending.
  echo "merge-when-green: arming auto-merge on PR #$PR" >&2
  gh pr merge "$PR" --auto --merge || true
fi

for ((i = 1; i <= MAX; i++)); do
  state=$(gh pr view "$PR" --json state -q .state)
  if [ "$state" != "OPEN" ]; then
    if [ "$state" = "MERGED" ]; then
      echo "merge-when-green: PR #$PR is MERGED"
      exit 0
    fi
    echo "merge-when-green: PR #$PR is $state — nothing to merge" >&2
    exit 3
  fi
  buckets=$(gh pr checks "$PR" --json bucket -q '[.[].bucket] | join(",")' 2>/dev/null || echo "")
  case "$buckets" in
    *fail* | *cancel*)
      echo "merge-when-green: PR #$PR has failing checks — NOT merging" >&2
      gh pr checks "$PR" >&2 || true
      exit 1
      ;;
    "" | *pending*)
      # "" = checks not reported yet; both mean wait. A repo with no CI at
      # all will time out here with exit 4 — that's deliberate: no gates
      # reporting is not the same as gates passing.
      echo "merge-when-green: PR #$PR checks pending ($i/$MAX); sleeping ${INTERVAL}s" >&2
      sleep "$INTERVAL"
      ;;
    *)
      if [ "$AUTO_MERGE" = true ]; then
        echo "merge-when-green: all checks green — merging PR #$PR"
        exec gh pr merge "$PR" --merge
      fi
      echo "merge-when-green: all checks green — advisory mode, NOT merging (features.auto_merge_on_green=false); merge with: gh pr merge $PR --merge"
      exit 0
      ;;
  esac
done

echo "merge-when-green: timed out waiting for PR #$PR checks after $MAX attempts" >&2
exit 4
