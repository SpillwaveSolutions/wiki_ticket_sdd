#!/usr/bin/env bash
# After a github-actions[bot] PR is opened, workflow_dispatch of
# worklog-invariants produces check-runs on the SHA that do NOT appear on
# the PR (statusCheckRollup empty, mergeStateStatus BLOCKED; #408).
# GITHUB_TOKEN pull_request runs sit action_required (#403, #408).
# Commit statuses with contexts `invariants` and `coverage` DO satisfy
# the merge-when-green ruleset (#408 merged that way, MERGE, 2 parents).
# This script waits for the dispatch run, then posts those statuses
# mirroring the job conclusions. Never squash. Never --admin.
set -euo pipefail

SHA="${1:?usage: associate-pr-checks.sh <sha>}"
CONTEXTS="${ASSOCIATE_CONTEXTS:-invariants,coverage}"
WORKFLOW="${ASSOCIATE_WORKFLOW:-worklog-invariants}"
MAX_WAIT="${ASSOCIATE_WAIT:-90}"
POLL="${ASSOCIATE_POLL:-5}"

command -v gh >/dev/null 2>&1 || {
  echo "associate-pr-checks: gh CLI required" >&2
  exit 2
}

repo="${GITHUB_REPOSITORY:-}"
if [ -z "$repo" ]; then
  repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
fi

rid=""
i=0
while [ "$i" -lt "$MAX_WAIT" ]; do
  i=$((i + 1))
  rid=$(gh run list --workflow "$WORKFLOW" --event workflow_dispatch --limit 20 \
          --json databaseId,headSha \
        | python3 -c "
import json, sys
sha = sys.argv[1]
runs = json.load(sys.stdin)
hits = [r for r in runs if r.get('headSha') == sha]
print(hits[0]['databaseId'] if hits else '')
" "$SHA")
  if [ -n "$rid" ]; then
    break
  fi
  echo "associate-pr-checks: waiting for dispatch run on $SHA ($i/$MAX_WAIT)" >&2
  sleep "$POLL"
done

if [ -z "$rid" ]; then
  echo "associate-pr-checks: no workflow_dispatch run for $SHA" >&2
  exit 2
fi

echo "associate-pr-checks: watching run $rid" >&2
gh run watch "$rid" || true

server="${GITHUB_SERVER_URL:-https://github.com}"
fail=0
# bash 3 (macOS) has no mapfile -d ','; keep this portable.
old_ifs=$IFS
IFS=,
# shellcheck disable=SC2086
set -- $CONTEXTS
IFS=$old_ifs
for ctx in "$@"; do
  conc=$(gh run view "$rid" --json jobs \
        | python3 -c "
import json, sys
want = sys.argv[1]
data = json.load(sys.stdin)
jobs = data.get('jobs') or []
hits = [j for j in jobs if j.get('name') == want]
print((hits[0].get('conclusion') or '') if hits else '')
" "$ctx")
  case "$conc" in
    success) state=success ;;
    *) state=failure; fail=1; conc=${conc:-missing} ;;
  esac
  gh api --method POST "repos/${repo}/statuses/${SHA}" \
    -f state="$state" \
    -f context="$ctx" \
    -f target_url="${server}/${repo}/actions/runs/${rid}" \
    -f description="workflow_dispatch ${ctx}: ${conc}"
  echo "associate-pr-checks: posted $ctx=$state ($conc)" >&2
done

exit "$fail"
