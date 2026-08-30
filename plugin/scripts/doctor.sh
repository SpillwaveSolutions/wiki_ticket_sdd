#!/usr/bin/env bash
# worklog doctor: read-only health report. Exit 0 healthy, 1 if any check failed.
# --fix-wiring: also write the two per-clone git config lines (hooksPath,
# merge.ours.driver) so a fresh clone is not a silent hook-floor outage.
set -uo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
FIX_WIRING=0
for arg in "$@"; do
  [ "$arg" = "--fix-wiring" ] && FIX_WIRING=1
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "FAIL not inside a git work tree"
  exit 1
fi
cd "$(git rev-parse --show-toplevel)"

if [ "$FIX_WIRING" -eq 1 ]; then
  git config merge.ours.driver true
  git_dir=$(cd "$(git rev-parse --git-dir)" && pwd -P)
  common=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
  if [ "$git_dir" != "$common" ]; then
    git config core.hooksPath "$(pwd -P)/hooks"
  else
    git config core.hooksPath hooks
  fi
  echo "ok    wiring repaired (core.hooksPath, merge.ours.driver)"
fi

fail=0
ok()  { echo "ok    $*"; }
bad() { echo "FAIL  $*"; fail=1; }

PLUGIN_VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
  "$PLUGIN_ROOT/.claude-plugin/plugin.json")

# version
installed=""
if [ -f .work/config.yml ]; then
  installed=$(awk '/^installed:/ {print $2; exit}' .work/config.yml)
fi
if [ -z "$installed" ]; then
  bad "not installed: no 'installed:' in .work/config.yml — run /worklog:init"
elif [ "$installed" = "$PLUGIN_VERSION" ]; then
  ok "version: installed $installed matches plugin $PLUGIN_VERSION"
else
  bad "version skew: repo has $installed, plugin is $PLUGIN_VERSION — run /worklog:init to upgrade"
fi

# features (read-only report; same naive scan as merge-when-green.sh)
am=$(awk '/^features:/{f=1;next} f&&/^[^[:space:]]/{exit} f&&/auto_merge_on_green:/{print $2; exit}' \
     .work/config.yml 2>/dev/null || true)
echo "features.auto_merge_on_green: ${am:-true}"

# GitHub arm (informational). Missing protection is not a FAIL: consumer
# repos may not want a ruleset. ADR-0010 is this flagship's setting. Skip
# when there is no github origin so sandboxed doctor tests stay offline.
origin=$(git remote get-url origin 2>/dev/null || true)
case "$origin" in
  *github.com*)
    if command -v gh >/dev/null 2>&1; then
      owner_repo=$(printf '%s' "$origin" | sed -E 's#.*github.com[:/]##' | sed 's/\.git$//')
      repo_json=$(gh api "repos/$owner_repo" --jq '{a:.allow_auto_merge,s:.allow_squash_merge}' 2>/dev/null || true)
      if [ -n "$repo_json" ]; then
        echo "$repo_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("github.allow_auto_merge:", d["a"]); print("github.allow_squash_merge:", d["s"])'
      fi
    fi
    ;;
esac

# files: present + executable; bin files byte-identical to canonical copies
for f in worklog fold.py ulid.py render_roadmap.py plan_capture.py; do
  if [ ! -f "bin/$f" ]; then
    bad "bin/$f missing"
  elif [ ! -x "bin/$f" ]; then
    bad "bin/$f not executable"
  elif ! cmp -s "bin/$f" "$PLUGIN_ROOT/scripts/$f"; then
    bad "bin/$f stale: differs from plugin copy — run /worklog:init to upgrade"
  else
    ok "bin/$f present, executable, matches plugin"
  fi
done
for f in pre-commit pre-merge-commit commit-msg; do
  if [ ! -f "hooks/$f" ]; then
    bad "hooks/$f missing"
  elif [ ! -x "hooks/$f" ]; then
    bad "hooks/$f not executable"
  else
    ok "hooks/$f present and executable"
  fi
done

# hook wiring
# An absolute path to this repo's hooks/ is as wired as the relative "hooks"
# init writes — and is the form that survives a git worktree checkout.
hookspath=$(git config core.hooksPath 2>/dev/null || true)
if [ "$hookspath" = "hooks" ] ||
   [ "$(cd "${hookspath:-/nonexistent}" 2>/dev/null && pwd -P)" = "$(pwd -P)/hooks" ]; then
  ok "core.hooksPath = ${hookspath}"
else
  bad "core.hooksPath is '${hookspath:-unset}', expected this repo's hooks/"
fi

# invariants: run the pre-commit checks (newline, schema, roadmap freshness)
# WORKLOG_SKIP_BRANCH_GUARD: this is a standalone health check, not a real
# commit -- doctor is usually run on main, which the branch guard would
# otherwise always fail.
if [ -x hooks/pre-commit ]; then
  out=$(WORKLOG_SKIP_BRANCH_GUARD=1 hooks/pre-commit 2>&1)
  if [ $? -eq 0 ]; then
    ok "hooks/pre-commit invariant checks pass"
  else
    bad "hooks/pre-commit failed:"
    printf '      %s\n' "$out"
  fi
else
  bad "cannot run invariant checks: hooks/pre-commit missing"
fi

if [ "$fail" -eq 0 ]; then
  echo "healthy."
else
  echo "problems found."
fi
exit "$fail"
