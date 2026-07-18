#!/usr/bin/env bash
# worklog repo install: scaffold or upgrade the CURRENT repo. Idempotent.
# Design contract: docs/plans/2026-07-18-claude-plugin.md (install semantics, versioning).
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "worklog init: not inside a git work tree. cd into the repo you want to scaffold and re-run." >&2
  exit 1
fi
cd "$(git rev-parse --show-toplevel)"

PLUGIN_VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
  "$PLUGIN_ROOT/.claude-plugin/plugin.json")

prev=""
if [ -f .work/config.yml ]; then
  prev=$(awk '/^installed:/ {print $2; exit}' .work/config.yml)
fi

wrote=()
skipped=()

# --- bin/ and hooks/: always re-copied (init on an installed repo IS the upgrade path) ---
mkdir -p bin hooks
for f in worklog fold.py ulid.py render_roadmap.py plan_capture.py compact.py; do
  cp -p "$PLUGIN_ROOT/scripts/$f" "bin/$f"
  chmod +x "bin/$f"
  wrote+=("bin/$f")
done
for f in pre-commit pre-merge-commit; do
  cp -p "$PLUGIN_ROOT/scripts/$f" "hooks/$f"
  chmod +x "hooks/$f"
  wrote+=("hooks/$f")
done
git config core.hooksPath hooks

# --- .gitattributes: union merge for the event logs, append only if absent ---
for line in ".work/todo.jsonl merge=union" ".work/done.jsonl merge=union"; do
  if [ -f .gitattributes ] && grep -qxF "$line" .gitattributes; then
    skipped+=(".gitattributes: $line")
  else
    echo "$line" >> .gitattributes
    wrote+=(".gitattributes: $line")
  fi
done

# --- .work/: NEVER truncate or overwrite existing logs. Data outlives tooling. ---
mkdir -p .work
for f in .work/todo.jsonl .work/done.jsonl; do
  if [ -f "$f" ]; then
    skipped+=("$f (existing log preserved)")
  else
    : > "$f"
    wrote+=("$f")
  fi
done

if [ -f .work/config.yml ]; then
  skipped+=(".work/config.yml (existing)")
else
  cat > .work/config.yml <<'EOF'
# Machine-readable settings. The agent file (CLAUDE.md / AGENTS.md) carries
# policy only. Scripts read THIS file.
version: 1

project:
  key: PROJ
  name: "My Project"

ticketing:
  system: none                 # jira | ado | github | none

wiki:
  system: none                 # confluence | github-wiki | ado-wiki | none

paths:
  plans: docs/plans
  status: docs/status
  roadmap: docs/roadmap.md
EOF
  wrote+=(".work/config.yml")
fi
# Record the installed plugin version (replace existing installed: line, else append).
python3 - .work/config.yml "$PLUGIN_VERSION" <<'PY'
import sys
p, v = sys.argv[1], sys.argv[2]
lines = open(p).read().splitlines()
hit = False
for i, l in enumerate(lines):
    if l.startswith("installed:"):
        lines[i] = f"installed: {v}"
        hit = True
if not hit:
    lines.append(f"installed: {v}")
open(p, "w").write("\n".join(lines) + "\n")
PY

# --- docs dirs ---
for d in docs/plans docs/status; do
  if [ -d "$d" ]; then
    skipped+=("$d/")
  else
    mkdir -p "$d"
    touch "$d/.gitkeep"
    wrote+=("$d/")
  fi
done

# --- CI workflow: hook checks only (target repos have no tests/) ---
if [ -f .github/workflows/worklog.yml ]; then
  skipped+=(".github/workflows/worklog.yml")
else
  mkdir -p .github/workflows
  cat > .github/workflows/worklog.yml <<'EOF'
name: worklog-invariants
on: [push, pull_request]

jobs:
  invariants:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Same script as the local hook: trailing newline, event schema,
      # roadmap freshness. A dev can --no-verify past the local hook; not this.
      - name: log invariants
        run: hooks/pre-commit
EOF
  wrote+=(".github/workflows/worklog.yml")
fi

# --- CLAUDE.md policy block ---
if [ -f CLAUDE.md ] && grep -qF '<!-- worklog:policy:start -->' CLAUDE.md; then
  skipped+=("CLAUDE.md policy block")
else
  [ -f CLAUDE.md ] && printf '\n' >> CLAUDE.md
  cat >> CLAUDE.md <<'EOF'
<!-- worklog:policy:start -->
## Work tracking policy

- Every plan MUST end by running `worklog plan-capture` — it writes
  `docs/plans/<date>-<slug>.md` and appends the plan's steps as work items.
- Work discovered mid-flight that wasn't in the plan: run
  `worklog add --unplanned --discovered-during <item>` BEFORE doing the work.
- Never hand-edit `.work/*.jsonl` (use `worklog`) or `docs/roadmap.md`
  (it is generated; change the work items instead).
- After changing work items, run `worklog roadmap-render` and commit the log
  and roadmap together.
<!-- worklog:policy:end -->
EOF
  wrote+=("CLAUDE.md policy block")
fi

# --- summary ---
echo "worklog $PLUGIN_VERSION installed."
if [ -n "$prev" ] && [ "$prev" != "$PLUGIN_VERSION" ]; then
  echo "upgraded from: $prev"
fi
echo "written:"
printf '  %s\n' "${wrote[@]}"
echo "skipped (already present):"
if [ ${#skipped[@]} -gt 0 ]; then printf '  %s\n' "${skipped[@]}"; else echo "  (none)"; fi
