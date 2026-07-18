#!/usr/bin/env bash
# worklog doctor: read-only health report. Exit 0 healthy, 1 if any check failed.
set -uo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "FAIL not inside a git work tree"
  exit 1
fi
cd "$(git rev-parse --show-toplevel)"

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
for f in pre-commit pre-merge-commit; do
  if [ ! -f "hooks/$f" ]; then
    bad "hooks/$f missing"
  elif [ ! -x "hooks/$f" ]; then
    bad "hooks/$f not executable"
  else
    ok "hooks/$f present and executable"
  fi
done

# hook wiring
hookspath=$(git config core.hooksPath 2>/dev/null || true)
if [ "$hookspath" = "hooks" ]; then
  ok "core.hooksPath = hooks"
else
  bad "core.hooksPath is '${hookspath:-unset}', expected 'hooks'"
fi

# invariants: run the pre-commit checks (newline, schema, roadmap freshness)
if [ -x hooks/pre-commit ]; then
  out=$(hooks/pre-commit 2>&1)
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
