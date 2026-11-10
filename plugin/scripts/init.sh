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


# sha256 of each script as shipped in bin/ at v0.24.12. init removes that
# exact file on upgrade and will not touch any other bytes.
legacy_sha() {
  case "$1" in
    worklog) echo "6e2722e167ff45df1c633138bda084df3663e4e9d842527ff77a7af5ead483a4" ;;
    fold.py) echo "8096b7a1dcdd2728bb7530bb1a3c6e7d8461e7152a613bf28b972bdcbe5bd99a" ;;
    ulid.py) echo "e26fb58e0d063d568eb117d494a04646010a11da66290131f33256d101f0d4e6" ;;
    render_roadmap.py) echo "c9b89d6d73bfb2d39c91c2578b5ebc1fe29f81663ec257da5de9d59dc6c30dd5" ;;
    viz_mermaid.py) echo "1e926ef333b392e99d673879fd97617fb5347f7e445536296f6ffa07039593d7" ;;
    plan_capture.py) echo "b03d8e49c7bc4bd1ea7457c37f832c3120f9a074de507fd0d763fb81c2d68209" ;;
    compact.py) echo "7ea62cd44c81d985b64446b54f10fc00c9e8f8cef77f2539c14594cd567088c0" ;;
    adr.py) echo "251a0eef5a2add6ae6fdf8e7d960a549655a66632ff331a77a262019de723f4d" ;;
    ia.py) echo "a8f360e1499ee517ad625102bf82ffb8626c5f0719b6ac581d8c75a688b6af6f" ;;
    ia_render.py) echo "2363f89f9fe4d5abe8338e34c11768806750569b92c318bd3ce16a410b36fbe1" ;;
    ia_graph.py) echo "39e3637d341d81c09327f017b30de25f22ea824a82702e4a33677762b7f73e26" ;;
    canonical.py) echo "2d05ccf79ff862684312b8a16cfba98e0d9c9b270127c62ad37ae6b4df9aceda" ;;
    sync_dispatch.py) echo "453fde400f10c8a2e6f51edc51d5feac4d0c1617655bc7181cd8d59c1c9a679d" ;;
    session.py) echo "6e715bfae7e02a65d78bc93bf657823f1275cc7b02f436dfc85ad3df8c9536d9" ;;
    item_fields.py) echo "be7796bd8958595aea1a16f0fadb8858fd32b483e5297a8b72e347c5d96929d6" ;;
    wiki_flavor.py) echo "f7e148ce1b591201fb3909a336c5db5eb349f90543fd1c1197930f6b00e6d82f" ;;
    changelog.py) echo "fc427bba6c9ae0021f132f8603a32d81ffb4b0e4a5f3bee06318ac88dc312b33" ;;
    doc_verify.py) echo "e4bb7de6bd5bf6a7777a94f8fbc412ff70b02a6bd7060d4bf1cd6b45555edfb2" ;;
    provenance.py) echo "3fd95f2e0b4a65900cb1080fd7784619dc5c2a4d12ad6b05d47cafbec5ad6d73" ;;
    published.py) echo "552db668c3bce34cf54176fb405b6c1b8b5a82e40cd55980e9a51a76e5ae39bf" ;;
    triggers.py) echo "1e854e4b37bba0b33f309e4aa48d0361286d97acef323ddcbfb2a16f14c16b40" ;;
    *) echo "" ;;
  esac
}

# --- bin/wiki-ticket/ and hooks/: always re-copied (init on an installed repo IS the upgrade path) ---
# Scripts used to land in bin/ itself. That collided with the repo's own tools
# and put fold.py, ulid.py, ia.py, ... on PATH. They now live in one directory.
mkdir -p bin/wiki-ticket hooks
for f in worklog fold.py ulid.py render_roadmap.py viz_mermaid.py plan_capture.py compact.py adr.py \
         ia.py ia_render.py ia_graph.py canonical.py sync_dispatch.py session.py \
         item_fields.py wiki_flavor.py changelog.py \
         doc_verify.py provenance.py published.py triggers.py; do
  cp -p "$PLUGIN_ROOT/scripts/$f" "bin/wiki-ticket/$f"
  chmod +x "bin/wiki-ticket/$f"
  wrote+=("bin/wiki-ticket/$f")
  # Retire the pre-0.24.13 copy only when it is still the stock script.
  # A foreign bin/$f (the repo's own tool) is left alone.
  if [ -f "bin/$f" ]; then
    legacy=$(legacy_sha "$f")
    have=$(sha256sum "bin/$f" | awk '{print $1}')
    if [ "$have" = "$legacy" ] || cmp -s "bin/$f" "bin/wiki-ticket/$f"; then
      rm "bin/$f"
      wrote+=("removed legacy bin/$f")
    fi
  fi
done
rm -rf bin/__pycache__
rmdir bin 2>/dev/null || true
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
    ".work/archive.jsonl merge=union" \
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
for f in .work/todo.jsonl .work/done.jsonl .work/archive.jsonl .work/published.jsonl; do
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
# Forge is read from the origin remote (#413). Azure DevOps gets
# azure-pipelines.yml with the same steps; every other host gets the GitHub
# Actions file. Adapter (ticketing.system) and CI host are separate axes: an
# ADO-hosted repo can track tickets anywhere. Another forge copies the
# closest template by hand (user guide, "CI wiring").
origin_url="$(git remote get-url origin 2>/dev/null || true)"
case "$origin_url" in
  *dev.azure.com*|*visualstudio.com*) ci_forge=azure ;;
  *) ci_forge=github ;;
esac

if [ "$ci_forge" = "azure" ]; then
if [ -f azure-pipelines.yml ]; then
  skipped+=("azure-pipelines.yml")
else
  cat > azure-pipelines.yml <<'EOF'
# worklog-invariants: the same hook checks the GitHub workflow runs.
# Rendered by worklog init for an Azure DevOps origin (#413).
trigger:
  branches:
    include: ['*']
pr:
  branches:
    include: ['*']

pool:
  vmImage: ubuntu-latest

steps:
  - checkout: self
    fetchDepth: 0
  # Same script as the local hook: trailing newline, event schema,
  # roadmap freshness. A dev can --no-verify past the local hook; not
  # this. WORKLOG_SKIP_BRANCH_GUARD: this step runs on whatever ref was
  # checked out with no commit in flight -- the branch guard only makes
  # sense for an actual `git commit`.
  - script: WORKLOG_SKIP_BRANCH_GUARD=1 hooks/pre-commit
    displayName: log invariants
  # commit-msg's own MERGE_HEAD check doesn't exist post-hoc in a CI
  # checkout, so re-derive "was this a merge" via --no-merges instead.
  # System.PullRequest.TargetBranch is refs/heads/<name>; the PR build
  # checks out the merge commit, so its first parent is the target.
  - script: |
      base="origin/${SYSTEM_PULLREQUEST_TARGETBRANCH#refs/heads/}"
      for sha in $(git rev-list --no-merges "$base..HEAD"); do
        git log -1 --format=%B "$sha" > /tmp/msg
        hooks/commit-msg /tmp/msg || { echo "commit $sha:"; cat /tmp/msg; exit 1; }
      done
    displayName: commit messages reference a worklog item or ticket
    condition: eq(variables['Build.Reason'], 'PullRequest')
EOF
  wrote+=("azure-pipelines.yml")
fi
else
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
