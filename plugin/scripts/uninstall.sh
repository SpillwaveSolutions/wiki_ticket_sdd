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

# Stock leftovers from the bin/ install (v0.24.12 and earlier). Only when the
# bytes are still that release, or still identical to the copy we are about
# to remove. A repo's own bin/<name> stays.
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
for f in worklog fold.py ulid.py render_roadmap.py viz_mermaid.py plan_capture.py compact.py adr.py \
         ia.py ia_render.py ia_graph.py canonical.py sync_dispatch.py session.py \
         item_fields.py wiki_flavor.py changelog.py \
         doc_verify.py provenance.py published.py triggers.py; do
  if [ -f "bin/$f" ]; then
    legacy=$(legacy_sha "$f")
    have=$(sha256sum "bin/$f" | awk '{print $1}')
    new="bin/wiki-ticket/$f"
    if [ "$have" = "$legacy" ] || { [ -f "$new" ] && cmp -s "bin/$f" "$new"; }; then
      rm "bin/$f"
      removed+=("bin/$f")
    fi
  fi
done

for f in bin/wiki-ticket/worklog bin/wiki-ticket/fold.py bin/wiki-ticket/ulid.py bin/wiki-ticket/render_roadmap.py bin/wiki-ticket/viz_mermaid.py bin/wiki-ticket/plan_capture.py bin/wiki-ticket/compact.py bin/wiki-ticket/adr.py \
         bin/wiki-ticket/ia.py bin/wiki-ticket/ia_render.py bin/wiki-ticket/ia_graph.py bin/wiki-ticket/canonical.py bin/wiki-ticket/sync_dispatch.py \
         bin/wiki-ticket/item_fields.py bin/wiki-ticket/wiki_flavor.py bin/wiki-ticket/changelog.py \
         bin/wiki-ticket/session.py bin/wiki-ticket/doc_verify.py bin/wiki-ticket/provenance.py bin/wiki-ticket/published.py bin/wiki-ticket/triggers.py; do
  if [ -f "$f" ]; then
    rm "$f"
    removed+=("$f")
  fi
done
rm -rf bin/wiki-ticket/__pycache__ bin/__pycache__
rmdir bin/wiki-ticket 2>/dev/null && removed+=("bin/wiki-ticket/ (empty)") || true
rmdir bin 2>/dev/null && removed+=("bin/ (empty)") || true

for f in hooks/pre-commit hooks/pre-merge-commit hooks/commit-msg hooks/session-end.sh; do
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
ours = {".work/todo.jsonl merge=union", ".work/done.jsonl merge=union", ".work/archive.jsonl merge=union", ".work/published.jsonl merge=union"}
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

if [ -f azure-pipelines.yml ] && grep -q "worklog-invariants" azure-pipelines.yml; then
  rm azure-pipelines.yml
  removed+=("azure-pipelines.yml")
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
