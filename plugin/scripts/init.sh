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
for f in worklog fold.py ulid.py render_roadmap.py viz_mermaid.py plan_capture.py compact.py adr.py \
         ia.py ia_render.py ia_graph.py canonical.py sync_dispatch.py session.py \
         item_fields.py wiki_flavor.py changelog.py \
         doc_verify.py provenance.py published.py triggers.py; do
  cp -p "$PLUGIN_ROOT/scripts/$f" "bin/$f"
  chmod +x "bin/$f"
  wrote+=("bin/$f")
done
for f in pre-commit pre-merge-commit commit-msg; do
  cp -p "$PLUGIN_ROOT/scripts/$f" "hooks/$f"
  chmod +x "hooks/$f"
  wrote+=("hooks/$f")
done
# SessionEnd is not a git hook. The plugin used to tell consumers to wire
# $CLAUDE_PROJECT_DIR/hooks/session-end.sh by hand after init, then never
# created the file (#344). Copy it next to the git hooks so that path
# exists; the plugin manifest now wires SessionEnd too.
if [ -f "$PLUGIN_ROOT/hooks/scripts/session-end.sh" ]; then
  cp -p "$PLUGIN_ROOT/hooks/scripts/session-end.sh" "hooks/session-end.sh"
  chmod +x "hooks/session-end.sh"
  wrote+=("hooks/session-end.sh")
fi
git_dir=$(cd "$(git rev-parse --git-dir)" && pwd -P)
common=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
if [ "$git_dir" != "$common" ]; then
  # Linked worktree: relative hooksPath resolves against the wrong CWD.
  git config core.hooksPath "$(pwd -P)/hooks"
else
  git config core.hooksPath hooks
fi
# Built-in `union` needs no config. `ours` is a named driver, not a built-in:
# `driver = true` is a no-op that succeeds and leaves the file as ours, which
# is what pre-merge-commit then regenerates (#381).
git config merge.ours.driver true

# --- .gitattributes: union merge for the event logs, ours for generated ---
for line in \
    ".work/todo.jsonl merge=union" \
    ".work/done.jsonl merge=union" \
    ".work/published.jsonl merge=union" \
    "docs/roadmap.md merge=ours" \
    "docs/.index/** merge=ours"
do
  if [ -f .gitattributes ] && grep -qxF "$line" .gitattributes; then
    skipped+=(".gitattributes: $line")
  else
    echo "$line" >> .gitattributes
    wrote+=(".gitattributes: $line")
  fi
done

# --- .work/: NEVER truncate or overwrite existing logs. Data outlives tooling. ---
mkdir -p .work
for f in .work/todo.jsonl .work/done.jsonl .work/published.jsonl; do
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

# Per-event artifact routing. `worklog triggers <event>` is the reader.
# Drop an action (or set the event to []) to opt that generation out.
triggers:
  plan-capture:
    - ticket-sync
    - wiki-publish:plans
  pr-open:
    - pr-description
  pr-merge:
    - roadmap-render
    - ticket-sync:close
  release:
    - design-doc        # docs/designs/current_design_doc.md + dated freeze
    - code-walkthrough  # docs/designs/current_code_walkthrough.md + dated freeze
    - user-guide        # docs/user_guide/*.md refreshed against diff since last tag
    - readme            # README.md same
    - wiki-publish
    - ticket-sync
  status-report:
    - wiki-publish:status

paths:
  plans: docs/plans
  status: docs/status
  roadmap: docs/roadmap.md

# Optional item fields (`worklog fields` lists them with what each means).
# The core -- id/title/status/level/kind/priority/milestone/labels/parent/
# body/plan/depends_on -- is fixed and deliberately not listed here.
# Defaults: estimate, owner, risk, acceptance_criteria on; value, confidence,
# due_date, severity off. Uncomment to change.
# work_item_fields:
#   severity: on
#   risk: off
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
        with:
          fetch-depth: 0
      # Same script as the local hook: trailing newline, event schema,
      # roadmap freshness. A dev can --no-verify past the local hook; not
      # this. WORKLOG_SKIP_BRANCH_GUARD: this step runs on whatever ref was
      # checked out (including main on push) with no commit in flight --
      # the branch guard only makes sense for an actual `git commit`.
      - name: log invariants
        run: WORKLOG_SKIP_BRANCH_GUARD=1 hooks/pre-commit
      # commit-msg's own MERGE_HEAD check doesn't exist post-hoc in a CI
      # checkout, so re-derive "was this a merge" via --no-merges instead.
      - name: commit messages reference a worklog item or ticket
        if: github.event_name == 'pull_request'
        run: |
          base="${{ github.event.pull_request.base.sha }}"
          for sha in $(git rev-list --no-merges "$base..HEAD"); do
            git log -1 --format=%B "$sha" > /tmp/msg
            hooks/commit-msg /tmp/msg || { echo "commit $sha:"; cat /tmp/msg; exit 1; }
          done
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
- One session per working directory. Two assistant sessions sharing a checkout
  switch branches under each other and solve the same problem twice; give each
  its own `git worktree`. `worklog` warns when it sees more than one, but the
  warning is advisory and arrives after the fact.
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
