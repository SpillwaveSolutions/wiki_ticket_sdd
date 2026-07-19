#!/usr/bin/env bash
# worklog repo uninstall: remove exactly what init.sh added. Idempotent.
# NEVER touches .work/, docs/plans/, docs/status/, docs/roadmap.md.
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "worklog uninstall: not inside a git work tree." >&2
  exit 1
fi
cd "$(git rev-parse --show-toplevel)"

removed=()

for f in bin/worklog bin/fold.py bin/ulid.py bin/render_roadmap.py bin/viz_mermaid.py bin/plan_capture.py bin/compact.py bin/adr.py; do
  if [ -f "$f" ]; then
    rm "$f"
    removed+=("$f")
  fi
done
rm -rf bin/__pycache__   # byproduct of running the scripts init installed
rmdir bin 2>/dev/null && removed+=("bin/ (empty)") || true

for f in hooks/pre-commit hooks/pre-merge-commit; do
  if [ -f "$f" ]; then
    rm "$f"
    removed+=("$f")
  fi
done
rmdir hooks 2>/dev/null && removed+=("hooks/ (empty)") || true
git config --unset core.hooksPath 2>/dev/null && removed+=("git config core.hooksPath") || true

# .gitattributes: strip the two union-merge lines; delete the file if nothing else remains.
if [ -f .gitattributes ]; then
  before=$(cat .gitattributes)
  python3 - .gitattributes <<'PY'
import sys
p = sys.argv[1]
ours = {".work/todo.jsonl merge=union", ".work/done.jsonl merge=union"}
lines = [l for l in open(p).read().splitlines() if l.strip() not in ours]
if any(l.strip() for l in lines):
    open(p, "w").write("\n".join(lines) + "\n")
else:
    import os
    os.remove(p)
PY
  if [ ! -f .gitattributes ]; then
    removed+=(".gitattributes (only worklog lines remained)")
  elif [ "$before" != "$(cat .gitattributes)" ]; then
    removed+=(".gitattributes union-merge lines")
  fi
fi

# AGENTS.md: remove only the symlink init created; a real file is not ours.
if [ -L AGENTS.md ] && [ "$(readlink AGENTS.md)" = "CLAUDE.md" ]; then
  rm AGENTS.md
  removed+=("AGENTS.md (symlink to CLAUDE.md)")
fi

# CLAUDE.md: strip the marker block; delete the file if effectively empty after.
if [ -f CLAUDE.md ] && grep -qF '<!-- worklog:policy:start -->' CLAUDE.md; then
  python3 - CLAUDE.md <<'PY'
import os, re, sys
p = sys.argv[1]
s = open(p).read()
s = re.sub(r"\n?<!-- worklog:policy:start -->.*?<!-- worklog:policy:end -->\n?",
           "", s, flags=re.S)
if s.strip():
    open(p, "w").write(s)
else:
    os.remove(p)
PY
  if [ -f CLAUDE.md ]; then
    removed+=("CLAUDE.md policy block")
  else
    removed+=("CLAUDE.md (contained only the policy block)")
  fi
fi

if [ -f .github/workflows/worklog.yml ]; then
  rm .github/workflows/worklog.yml
  removed+=(".github/workflows/worklog.yml")
fi
rmdir .github/workflows .github 2>/dev/null || true

if [ ${#removed[@]} -gt 0 ]; then
  echo "removed:"
  printf '  %s\n' "${removed[@]}"
else
  echo "nothing to remove (already uninstalled)."
fi
echo
echo "preserved (data outlives tooling):"
echo "  .work/          — event logs and config: the work record, not the tooling"
echo "  docs/plans/     — the permanent design record; plans are never rewritten"
echo "  docs/status/    — published status reports; frozen once read"
echo "  docs/roadmap.md — generated view of the logs, kept with them"
