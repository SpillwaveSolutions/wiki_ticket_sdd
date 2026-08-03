---
date: 2026-07-25
slug: branch-discipline-hooks
title: Branch-discipline hooks: never commit on main, always reference work
epic: 01KYBD2HYJVNHX698WR1JD96YC
items: [01KYBD2HYKKC2G9NW4VA3RVC6G, 01KYBD2HYKKZM22DFM16ZJXYFG, 01KYBD2HYK1AT1YCN3GW8Q3QQW, 01KYBD2HYK9XY02QHSVF1849BQ, 01KYBD2HYK196RQN7JNCMV6PDS, 01KYBD2HYKYBBNGDMCQSW4VE2T, 01KYBD2HYKET7WJARQFB2NVMFS, 01KYBD2HYKG0DW7QJX7XG561A8, 01KYBD2HYKJHS5M2PFZ78Y585C, 01KYBD2HYKB5E4JXNYYQ9BPDAE]
merged_in: e5cc0f9d621065ef779f32dbdbb3e32295850708
---

# Branch-discipline hooks: never commit on main, always reference work

## Context

This session hit a real incident: local `main` drifted 13 commits ahead of
`origin/main` for hours (every commit landed straight on `main`, never
pushed), while GitHub's nightly compaction bot pushed its own commit
directly to `origin/main` in parallel. The divergence surfaced as a failed
PR merge that took real effort to untangle. Rick's instruction afterward:
commits must always happen on a branch, never on `main`; `main` is
pull-only locally; and work should always be traceable to a plan or
ticket. This ships as part of the plugin (`plugin/scripts/`), not a
local-only fix.

Two new checks, following the existing hook philosophy ("Hooks enforce
invariants, not hope"): a branch guard (new block in the existing
`hooks/pre-commit`) and a new `hooks/commit-msg` that requires every commit
message to reference a worklog item ULID or a ticket number. Both ship
hard-fail immediately. Git's `MERGE_HEAD` file gives a free, correct signal
for "this is a reconciliation merge, not authored work" — both checks
exempt merge commits via its existence, so `git merge origin/main` (the
"pull main" reconciliation this session actually needed) keeps working
while `git commit` authored directly on `main` is blocked.

## Design

### 1. Branch guard — new block in `hooks/pre-commit`

Inserted after `fail()` is defined, before the `.work/*.jsonl` checks:

```bash
if [ -z "${WORKLOG_SKIP_BRANCH_GUARD:-}" ] && \
   [ ! -f "$(git rev-parse --git-path MERGE_HEAD)" ]; then
  branch=$(git symbolic-ref --quiet --short HEAD || true)
  case "$branch" in
    main|master)
      fail "commits go on a branch, not '$branch' (main/master is pull-only). Run: git checkout -b <branch-name>, then commit there."
      ;;
  esac
fi
```

Detached HEAD is allowed (branch=""). `WORKLOG_SKIP_BRANCH_GUARD=1` is
required at three existing bare (non-commit) invocations of this script
that would otherwise false-positive on `main` with no commit in flight:
`plugin/scripts/doctor.sh`'s health check, CI's `--no-verify` backstop
step, and two `tests/test_integration.py` "prove CI would pass" assertions.
`hooks/pre-merge-commit` itself needs zero changes — MERGE_HEAD already
covers it.

### 2. `hooks/commit-msg` — new hook

```bash
#!/usr/bin/env bash
set -euo pipefail
fail() { echo "worklog: $*" >&2; exit 1; }

[ -f "$(git rev-parse --git-path MERGE_HEAD)" ] && exit 0

python3 - "$1" <<'PY' || fail "commit message must reference a worklog item (26-char ULID) or a ticket (#123) -- see: worklog show <id>. Merge commits are exempt."
import re, sys
msg = open(sys.argv[1], encoding="utf-8").read()
sys.exit(0 if (re.search(r'\b[0-9A-HJKMNP-TV-Z]{26}\b', msg) or
               re.search(r'#\d+', msg)) else 1)
PY
```

ULID alphabet matches `bin/ulid.py`'s Crockford set. No exemption beyond
merge commits. Orthogonal to the branch guard — applies on any branch.

### 3. Wiring (mechanical)

- `hooks/commit-msg` (new) + `plugin/scripts/commit-msg` (new, byte-identical)
- `plugin/scripts/init.sh`: hook-copy loop gains `commit-msg`; CI step template prefixed with `WORKLOG_SKIP_BRANCH_GUARD=1`
- `plugin/scripts/uninstall.sh`: symmetric removal
- `plugin/scripts/doctor.sh`: existence/exec check for `commit-msg`; `WORKLOG_SKIP_BRANCH_GUARD=1` on its own pre-commit invocation
- `tests/test_plugin.py` `CANON` list: add `hooks/commit-msg`
- `.github/workflows/worklog.yml` (template + this repo's installed copy): new PR-scoped step walking `git rev-list --no-merges base..HEAD` through `hooks/commit-msg`, needs `fetch-depth: 0`
- `.github/workflows/compact.yml`: no changes needed (fresh checkout never sets `core.hooksPath`)

### 4. Release skill update

`plugin/skills/release/SKILL.md` §3's "Direct-commit repos: commit on the
default branch" mode is removed — dead once the branch guard ships.
Describe branch+PR landing only.

### 5. Test fixture fallout

`tests/test_integration.py` (~23 `commit_all()` calls) and
`tests/test_plugin.py` (3 raw `git commit` calls) mostly commit on `main`
with no-reference messages — pure fixture plumbing. Give them
`no_verify=True` or move onto a branch via `Sandbox.branch()`, following
the precedent already set in the file for "not what this test is about"
commits. The four call sites testing pre-commit's other checks keep
`no_verify=False`.

### 6. New tests

`TestBranchGuard` and `TestCommitMsgReference` in `tests/test_integration.py`
using the existing `Sandbox`/`commit_all`/`branch`/`merge` harness: commit
on main rejected, commit on branch succeeds, merge onto main allowed
(the actual incident scenario), message without reference rejected,
message with ULID/ticket passes, merge commit message exempt.

## Verification

- `python3 -m pytest tests/` green, including new test classes.
- `tests/test_plugin.py::TestCanonSync` passes.
- Manual: commit on main rejected with the "pull-only" message; commit on
  a branch with a ULID-referencing message succeeds; merging that branch
  onto main succeeds (proves the incident scenario now works).
- `worklog doctor` still reports hook health correctly on main.
- CI green on a real PR whose commits reference items/tickets; a
  reference-less commit message fails the new CI step.

## Tasks

- [ ] (P1) Add the branch-guard block to hooks/pre-commit
  Insert the MERGE_HEAD-exempt, WORKLOG_SKIP_BRANCH_GUARD-overridable check
  that fails when HEAD is main/master, right after fail() is defined.
- [ ] (P1) Create hooks/commit-msg requiring a ULID or ticket reference
  New hook: exempt merge commits via MERGE_HEAD, otherwise require a
  26-char Crockford ULID or #123 ticket reference in the message, reusing
  the bin/ulid.py alphabet.
  - [ ] Mirror to plugin/scripts/commit-msg (byte-identical canon copy)
- [ ] (P1) Wire commit-msg into install/uninstall/doctor/CANON
  plugin/scripts/init.sh's hook-copy loop and CI template,
  plugin/scripts/uninstall.sh's removal loop, plugin/scripts/doctor.sh's
  existence check, tests/test_plugin.py's CANON list.
- [ ] (P2) Add WORKLOG_SKIP_BRANCH_GUARD to the three bare pre-commit call sites
  plugin/scripts/doctor.sh's own invocation, plugin/scripts/init.sh's CI
  backstop step, and tests/test_integration.py's two "CI would pass"
  assertions -- these run hooks/pre-commit with no real commit in flight
  and would otherwise false-positive on main.
- [ ] (P2) Add a CI step validating commit messages on PRs
  Walk git rev-list --no-merges base..HEAD through hooks/commit-msg in
  .github/workflows/worklog.yml (template and this repo's installed
  copy); needs fetch-depth 0.
- [ ] (P2) Remove the "direct-commit repos" mode from the release skill
  plugin/skills/release/SKILL.md section 3 currently documents committing
  release stamps directly on the default branch -- dead once the branch
  guard ships; describe branch+PR landing only.
- [ ] (P2) Update test fixtures for the new hooks
  tests/test_integration.py (~23 commit_all calls) and
  tests/test_plugin.py (3 raw git commit calls) mostly commit on main with
  no-reference messages -- give pure setup commits no_verify=True or move
  them onto a branch via Sandbox.branch(), following the file's existing
  precedent; leave the four pre-commit-content-testing call sites alone.
- [ ] (P1) Add TestBranchGuard and TestCommitMsgReference test classes
  New tests in tests/test_integration.py covering: commit on main
  rejected, commit on branch succeeds, merge onto main allowed (the
  incident scenario), message without reference rejected, message with
  ULID/ticket passes, merge commit message exempt.
- [ ] (P2) Full test suite green + manual verification
  Run the full suite, confirm TestCanonSync passes, and manually exercise
  the incident scenario (branch -> commit -> merge onto main) plus
  worklog doctor's health report on main.
