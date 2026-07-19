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

# --- work-taxonomy block (spec: docs/plans/2026-07-18-work-taxonomy.md §4) ---
# Written between markers so re-running updates in place, never duplicates.
# Only `init.sh taxonomy` touches it — the default flow never writes it; the
# /worklog:init command asks the user first (CLAUDE.md is not silently rewritten).
install_taxonomy_block() {
  # Block text lives in the python heredoc (not $(cat <<EOF)): macOS bash 3.2
  # mis-parses apostrophes inside heredocs within command substitution.
  python3 - CLAUDE.md <<'PYEOF'
import os, re, sys
p = sys.argv[1]
block = """<!-- worklog:taxonomy:start -->
## Work taxonomy

Every work item sits on four independent axes:

| Axis | Field | Values | Answers |
|---|---|---|---|
| Level | `level` | epic / story / task / subtask | size & place in the parent tree |
| Kind | `kind` | feature / bug / ops / triage | nature of the work |
| Milestone | `milestone` | free string (e.g. v0.6.0) or null | what ships together |
| Planned | `unplanned` + `discovered_during` | bool + ULID | deliberate vs discovered |

Rules (the validator enforces these; apply them when proposing items):
1. Kind is free at story/task/subtask.
2. Epics are `feature` or `ops` only — a bug is never epic-sized.
3. `kind` defaults to `triage` when omitted — never silently default to feature.
4. `bug.parent` is optional; bugs may float free of any epic.
5. `milestone` lives on leaves (story and below); an epic's milestone derives from its children.
6. `triage` and `ops` both trend down: triage shrinks by classifying, ops by automating.

When trackable work surfaces in conversation, propose an item inline as part of
the normal response — "want me to file this? `level:story kind:feature
parent:<ulid> milestone:v0.6.0`" — and create it only on assent, via the
work-track or plan-capture skill. When unsure of the kind, propose `kind:triage`
with the open question stated — triage is the honest default, never a confident
guess. This inline path is the default; the flag-gated classifier (`classifier:`
in `.work/config.yml`, off by default) is the escape hatch for teams where work
keeps escaping the log.
<!-- worklog:taxonomy:end -->"""
text = open(p).read() if os.path.exists(p) else ""
pat = re.compile(r"<!-- worklog:taxonomy:start -->.*?<!-- worklog:taxonomy:end -->", re.S)
if pat.search(text):
    text = pat.sub(lambda m: block, text, count=1)
else:
    if text and not text.endswith("\n"):
        text += "\n"
    text += ("\n" if text else "") + block + "\n"
open(p, "w").write(text)
PYEOF
  echo "CLAUDE.md taxonomy block installed (between worklog:taxonomy markers)."
}

if [ "${1:-}" = "taxonomy" ]; then
  install_taxonomy_block
  exit 0
fi

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
for f in worklog fold.py ulid.py render_roadmap.py viz_mermaid.py plan_capture.py compact.py adr.py; do
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
  system: none                 # github | gitlab | jira | ado | linear | codecatalyst | other | none

wiki:
  system: none                 # github-wiki | gitlab-wiki | ado-wiki | confluence | other | none

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

# --- AGENTS.md: symlink to CLAUDE.md so Codex/OpenCode read the same policy ---
if [ -L AGENTS.md ]; then
  skipped+=("AGENTS.md (existing symlink)")
elif [ -e AGENTS.md ]; then
  skipped+=("AGENTS.md (regular file left alone)")
  echo "note: AGENTS.md exists; add the worklog policy manually or symlink to CLAUDE.md"
else
  ln -s CLAUDE.md AGENTS.md
  wrote+=("AGENTS.md -> CLAUDE.md")
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
