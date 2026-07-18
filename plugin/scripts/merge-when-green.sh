#!/usr/bin/env bash
# Merge a PR only when every check is green. Polls until then. Never bypasses
# a gate: a failing check is a stop, not an obstacle. GitHub via gh; other
# platforms use their CLI equivalent per the merge-green skill.
set -euo pipefail

PR="${1:?usage: merge-when-green.sh <pr-number> [interval-seconds] [max-attempts]}"
INTERVAL="${2:-300}"   # 5 minutes
MAX="${3:-24}"         # 24 × 5 min = 2 h, then give up loudly

command -v gh >/dev/null 2>&1 || {
  echo "merge-when-green: gh CLI required for GitHub PRs; other platforms: use their CLI with the same rule" >&2
  exit 2
}

for ((i = 1; i <= MAX; i++)); do
  state=$(gh pr view "$PR" --json state -q .state)
  if [ "$state" != "OPEN" ]; then
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
      echo "merge-when-green: all checks green — merging PR #$PR"
      exec gh pr merge "$PR" --merge
      ;;
  esac
done

echo "merge-when-green: timed out waiting for PR #$PR checks after $MAX attempts" >&2
exit 4
