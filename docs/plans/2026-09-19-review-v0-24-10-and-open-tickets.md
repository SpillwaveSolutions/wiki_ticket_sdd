---
date: 2026-09-19
slug: review-v0-24-10-and-open-tickets
title: Fix the v0.24.10 review findings and close #412 and #413
epic: 01M2XCWMV0QYM4ZRBWN1V1327B
items: [01M2XCWMVD7KJ01FCNEV1X822S, 01M2XCWMVD7KJ01FCNEV1X822V, 01M2XCWMVD7KJ01FCNEV1X822X, 01M2XCWMVD7KJ01FCNEV1X822Z, 01M2XCWMVD7KJ01FCNEV1X8231, 01M2XCWMVD7KJ01FCNEV1X8233, 01M2XCWMVD7KJ01FCNEV1X8235, 01M2XCWMVD7KJ01FCNEV1X8237, 01M2XCWMVEH3XFP2VPS9JBD6X7, 01M2XCWMVEH3XFP2VPS9JBD6X9, 01M2XCWMVEH3XFP2VPS9JBD6XB, 01M2XCWMVEH3XFP2VPS9JBD6XD, 01M2XCWMVEH3XFP2VPS9JBD6XF, 01M2XCWMVEH3XFP2VPS9JBD6XH, 01M2XCWMVEH3XFP2VPS9JBD6XK, 01M2XCWMVEH3XFP2VPS9JBD6XN, 01M2XCWMVEH3XFP2VPS9JBD6XQ, 01M2XCWMVEH3XFP2VPS9JBD6XS, 01M2XCWMVEH3XFP2VPS9JBD6XV, 01M2XCWMVEH3XFP2VPS9JBD6XX]
git_hash: "0c94b2154610ca9b3c4aff22295efc56cadfd601"
---

# Fix the v0.24.10 review findings and close #412 and #413

Slug: `review-v0-24-10-and-open-tickets`. Date: 2026-09-19.

## Context

The v0.24.10 change review (artifact `SDWhX9np6JgPErn8z5nvyP`) found one P0 and six P1 defects under green suites. Two open GitHub issues (#412, #413) from the NDQR deployment add a duplicate-ticket bug and a CI-ownership request. The worklog has zero open items, so nothing is tracked yet.

Every finding below was re-verified in code by three Explore passes and a three-reviewer council. Two review claims were corrected:

- Unparseable `ts` is not evicted by the cap in the normal case. `compact.py:218-223` sorts it last. The residual defect is that unparseable items still occupy cap slots, and `cap: 0` evicts them. The fix is one line.
- Pinning `integration_id` 15368 on the required checks is not available. `CHANGELOG.md:17` records that GitHub returned 422 for it.

Deadline: the first archive evictions come due about 2026-10-17 (`task_days: 90` from the 2026-07-19 snapshots). Workstream A must land before then. Missing the date starts churn (re-snapshot and re-evict every night), not data loss: `_verify` guarantees fold equality on every run. The date is a hygiene deadline, not a reason to skip review.

## Decisions

- Bot PRs use a fine-grained PAT stored as `WORKLOG_BOT_PAT`, not a GitHub App. One secret, one identity. Scopes: contents rw, pull-requests rw, issues rw (the same token serves the ticket adapter in Workstream D). The PAT belongs to a maintainer account, not a new machine user: a new account hits the same first-time-contributor gate that stalls `github-actions[bot]` today (#403). Expiry is one year; the expiry date goes in the CHANGELOG entry.
- The draft plan lives in the session scratchpad during the council review. `plan-capture` refuses a slug that already exists in `docs/plans/`, so capture writes the permanent record exactly once, after the single edit pass.
- Workstreams A through F all belong to this plan. E shrinks to a static Azure Pipelines template emitted by `init.sh` plus a mapping table. No renderer, no forge module, no GitLab or Bitbucket. Build a renderer when a third forge is real.
- For #412, ship the marker probe, `sync --explain`, and the report hints. Skip the sibling-worktree pre-flight and the doctor check. The probe removes the common cause (a clone with no link memory), not every cause: a failed or capped listing, a search index that lags a create by seconds, or two syncers that both observe absence can still mint a duplicate. The `remembered_key` docstring says so, and the #412 close comment says that existing duplicates are not collapsed (that stays `dedupe --collapse-agreed`).
- ADR-0010 is not rewritten. ADR-0011 supersedes it. ADR-0010 gets only the front-matter change that `bin/adr.py:142-145` needs (`status: superseded`, `superseded_by: 11`).
- Every PR that touches `bin/*.py`, `hooks/*`, or a harness hook copies the file to its plugin mirror in the same PR. `tests/test_plugin.py:25-38` (`CANON`, `HOOK_CANON`) fails parity otherwise, and installed repos never see the fix.

## Order

0. Council review and single edit pass, then `plan-capture`.
1. A retention correctness (P0, before 2026-10-17).
2. B #412 marker probe. A and B are independent in code. Both edit `docs/worklog-spec.md` §10.5 and `cli-reference.md`, so B rebases onto A before its docs commit, or A lands first.
3. C1 interim gate hardening and ADR-0011.
4. C2 PAT identity for bot PRs. Needs the `WORKLOG_BOT_PAT` secret before merge. All `compact.yml` edits live here, none in A.
5. D #413 CI as the authoritative syncer. Needs B and C2.
6. F release hygiene.
7. E #413 Azure Pipelines template.

One PR per workstream. Each PR merges with `gh pr merge --auto --merge` per policy.

## Step 0: council review, edit once, capture

1. Copy this plan verbatim to `<scratchpad>/2026-09-19-review-v0-24-10-and-open-tickets.md`.
2. Write the shared review prompt from the `planner-council` skill to `<scratchpad>/review-prompt.txt`, pointing at the draft path.
3. In one message, run all three reviewers:
   - `grok --prompt-file review-prompt.txt --reasoning-effort high --always-approve --output-format json --cwd <repo> -s "$(uuidgen)" > grok-review.json`
   - `codex exec -s read-only -c model_reasoning_effort=high --skip-git-repo-check -C <repo> -o codex-review.txt - < review-prompt.txt`
   - An `Agent` call with `model: "fable"`, `subagent_type: "general-purpose"`, read-only instructions, the same prompt, output to `fable-review.md`.
4. Spawn one `Agent` with `model: "fable"` as the editor. Its prompt: read the draft and the three reviews, decide which concerns are worthy (agreement across reviewers ranks highest, then project fit), apply those edits to the draft file once, append a short `## Council notes` section that lists accepted and rejected concerns with one reason each. Do not re-run any reviewer. Do not edit any other file.
5. Run `bin/worklog plan-capture --slug review-v0-24-10-and-open-tickets --title "Fix the v0.24.10 review findings and close #412 and #413" --body "<epic body>" --file <draft>`. Then `bin/worklog roadmap-render`, `bin/worklog ia-index`, and commit `docs/plans/`, `docs/roadmap.md`, `docs/.index/`, `.work/todo.jsonl` together.
6. Spawn the background publish subagent that the `plan-capture` skill describes. Do not wait for it.
7. Retag defect tasks after capture: `bin/worklog update <ulid> --kind bug` for the A, B, C1, and F(gate) tasks. C2, D, and E stay `feature`.
8. Start Workstream A. The plan is not edited again. A changed design gets a new plan with `supersedes:`.

## Workstream A: retention correctness

File: `bin/compact.py`. Tests: `tests/test_retention.py` (helpers `seed_closed_snapshot:54`, `seed_open:63`, `RetentionBase.compact:69`).

Changes in `_compact_locked` (`:340-445`):

1. `done_state` folds `[done_path, archive_path]` (`:382`). An archived item with identical state no longer looks changed.
2. Prune refreshed ids from the archive. Compute `fresh_ids = {e["item"] for e in fresh}`. Replace `_prune_open_from_text(existing_archive, open_ids)` (`:411`) with a prune on `open_ids | fresh_ids`. An item updated after archival keeps one snapshot, in `done.jsonl`.
3. Dedupe on append by `item`, not by `ev`. `_snapshot` (`:99`) mints a new `ulid.new()` for every snapshot, so an `ev` match never happens. Drop existing archive lines whose `item` appears in `newly_archived`, then concatenate. Newest snapshot wins. This also repairs a consumer repo that already accumulated ping-pong duplicates.
4. Early return (`:414`) triggers when nothing changed: `todo_text is None and done_text == original_done and archive_text == original_archive`. Read `original_done` once next to `original_archive`.
5. Delete the dead `archive_changed` at `:419`.
6. Pass `before.items` to `_evict_done` instead of `closed_map` (`:404-405`). `_evict_done` already filters on `CLOSED_STATUSES` and needs open items for the parent veto.

Changes in `_evict_done` (`:189-232`):

1. Build `done_ids = {e.get("item") for e in events}`. `continue` for any folded item not in `done_ids`. The cap counts items in `done.jsonl` only.
2. `if epoch is None: continue` before `remaining.append`. Drop the boolean from the tuple and the sort key. Unparseable ts never occupies a cap slot.
3. Parent veto after the cap. Live children are the items in `done_ids` plus the open items in `folded_items`; an already archived child does not count. Loop `evict -= {folded_items[i].get("parent") for i in live_children if i not in evict}` until the set stops changing. A parent is never archived while a child stays in `done.jsonl` or `todo.jsonl`, and a parent becomes eligible on the compaction after its last live child leaves.
4. Update the docstring to match.

Changes in `_prune_open_from_text` (`:235-246`): drop the `not open_ids` half of the early-return guard so the function always walks the text. Wrap `json.loads` in `try/except json.JSONDecodeError`, print the same `compact: dropping unparseable line from <path>` warning that `:384-389` prints, and drop the line. Pass the path in for the message. Without this, an all-closed repo with no refreshed ids keeps the garbage line and `_verify` (`:317-319`) aborts.

Changes in `_retention_config` (`:139-172`):

1. Match only keys whose indent equals the indent of the first non-blank line after `retention:`. Skip deeper lines.
2. Print a warning to stderr for any ignored value (negative, non-integer, unknown key). Keep the default.
3. `cap: 0` is already accepted (`:166`, `n >= 0`). Document it in `cli-reference.md` as "archive every closed item with a parseable timestamp and no child still in done or todo".

Changes in `bin/worklog` and `compact.py`:

1. `check_duplicate_ownership` (`compact.py:507`) folds the archive too, so a branch linking a ticket that an archived item owns fails merge-check. Infer the archive path from the todo path inside `merge_check` (`:735`) so `worklog.yml:46`, `hooks/pre-commit:134`, and the `--merge-check` flag keep their two-path call.
2. `_git_refuses` (`:268-283`) treats an untracked `.work/archive.jsonl` as dirty. `git diff --quiet HEAD -- <path>` returns 0 for an untracked file, so use `git status --porcelain -- <path>` instead. A missing file is not dirty, or the first eviction never runs. Note the reason in a comment.

`worklog.yml:57-73`: add `tests/test_retention.py` and `tests/test_watermark.py` to the explicit list. No other workflow edits in A; `compact.yml` changes belong to C2.

Tests to add in `tests/test_retention.py`:

- `TestArchiveStability`: evict, `seed_open`, compact, assert the item has zero lines in done and exactly one in archive. Repeat twice. Assert the archive bytes are unchanged.
- `TestCapCountsDoneOnly`: cap 3, 2 items in done, 5 in archive. Assert done keeps both.
- `TestUnparseableNeverCapped`: `cap: 0` with one unparseable ts. Assert it stays.
- `TestParentVeto`: `task_days: 0` and `epic_days: 0`, closed epic with one closed story in done. Assert the epic stays while the story stays. Archive the story, compact again, assert the epic is now archived. Without the veto the first compaction evicts both, so the test fails against today's code.
- `TestUpdateAfterArchive`: archived item reopened and closed again. Assert one snapshot total, in done, and the archive line is pruned.
- `TestArchiveDedupeByItem`: two archive lines for one item. Compact. Assert one line, the newest.
- `TestCorruptArchiveLine`: one garbage line in archive, no open items and no refreshed ids. Assert compaction succeeds and warns.
- `TestConfigWarnings`: negative, float, nested, `cap: 0`.
- Fixtures must use `through != ev` so the ordering tie is real.

Docs: renumber the `compact.py` header (evict is step 7, verify steps 8 and 9, "nine steps"); same in `docs/worklog-spec.md:370-375`; `cli-reference.md:623-633` gains `archive.jsonl` and the `retention:` block; `README.md:296` lists `archive.jsonl`; spec §14 says merge-time, not nightly; spec §10.5 says `--report` is an alias of `--dry-run`; note that closed orphans without `level` age as tasks.

## Workstream B: #412 stop minting duplicates

File: `bin/sync_dispatch.py`. Pattern for tests: `tests/test_bug_385.py:53-74` (`fake_state_obj`, `write_fake`).

1. `observe_remote` (`:1165`) makes two passes over `tickets`. Pass one stores `self.remote_keys[iid] = key` and `self.remote_closed_keys[iid] = self._ticket_closed(t)` for every ticket that carries a marker id. When two tickets carry the same marker, pick the survivor with `_key_sort` (`:1010-1019`), the rule `dedupe` already uses, so a probe hit and a later `dedupe --collapse-agreed` agree. Pass two builds `owned` as today. Ordering matters: `owned` calls `remembered_key`, so the probe map must exist first, or a probe hit never reaches `remote_closed` and `skip_push_ids` and `push_items` updates a closed ticket from open local state (the #385 regression).
2. `remembered_key` (`:262`) gains a third source after `last_pushed_key`: `self.remote_keys.get(iid)`, a key string, never a tuple. Update the docstring to name all three sources, the survivor rule, and why the worktree scan and doctor check are not implemented.
3. In `push_items` the existing `relink` flag (`:642`) already fires `record_link` after an update when `ext.key` is empty, so a probe hit self-heals the log with zero extra API calls. A probe hit that is closed on the remote takes the `apply_remote_closes` path, which records the link the same way. Add `relinked` to `COUNT_KEYS` (`:204`) and count probe hits there. Update the existing report tests for the new column.
4. `report()` prints `N items already had tickets (marker probe); link events recorded` when `relinked > 0`, and `hint: worklog dedupe --dry-run` when `created > 0`.
5. `worklog sync --explain <ULID>`: one dispatcher method `explain(iid)` that prints the three sources and each value, after `observe_remote`, and returns without pushing or pulling. Parser flag in `bin/worklog` next to `--report`, and forwarded in the argv that `cmd_sync` rebuilds (`bin/worklog:1261-1264`), or the flag never reaches the dispatcher.
6. Probe guard: when the adapter supports pull, `fetch_remote_tickets` returns nothing (`:939-957`: auth failure, non-zero exit), and `self.state` has no `items`, skip creates for this run and print `sync: marker probe failed and this clone has no push memory; not creating tickets`. A fresh CI clone with a transient listing failure is the #412 scenario. Adapters without pull keep today's behavior.
7. `worklog adapter check`: when `sync-state.json` has no `items`, print `no push memory in this clone yet; first sync relies on the log and the marker probe`.
8. Caveat in the docstring: the GitHub adapter lists marked tickets with `--state all` (`adapters/github/adapter:316-319`), capped at 1000 (`:321-322`), through `gh issue list -S`, which is search-backed and eventually consistent. A ticket created seconds earlier can be invisible to the probe.

Tests: `tests/test_bug_412.py`. Seed a remote ticket with marker `worklog:<ULID>` for a local item with no link event and no state file. Run a real sync, not a dry run: the dry-run path prints `would update` and `continue`s before `updated` increments (`:772`). Assert `created == 0`, `updated == 1`, a `link` event exists in the log, and the report line appears. Second test: two remote tickets with the same marker; assert the `_key_sort` survivor wins. Third: the probe hit is closed on the remote; assert no update and a `remote_closed` entry. Fourth: `--explain` output names all three sources and writes no event. Fifth: `created > 0` prints the dedupe hint. Sixth: listing failure with no state file skips creates.

Docs: `cli-reference.md` sync section (`--explain`, the probe), spec §10.5 idempotency paragraph (now marker-based, with the caveats above stated).

## Workstream C1: interim gate hardening and ADR-0011

1. `.github/workflows/worklog.yml`: add `permissions: contents: read` at the top. Check during implementation that no job posts anything. Leave the `workflow_run` comment at `:6-9` alone; it is still true until C2 removes the trigger.
2. `.github/merge-when-green-ruleset.json:5-11`: remove the dead `User 41898282` bypass actor. Update `tests/test_merge_green.py:247-264` to assert an empty `bypass_actors` list. The JSON is a mirror, not the live rule: apply it with `gh api -X PUT /repos/SpillwaveSolutions/wiki_ticket_sdd/rulesets/<id> --input .github/merge-when-green-ruleset.json` and read it back with `gh api .../rulesets/<id>` in the PR description.
3. ADR-0011 via `bin/adr.py`, `supersedes: 10`, title "Bot PRs land through the merge gate with a PAT identity". Record: the GH013 failure, the status bridge as the interim path, the PAT decision, and the deletion of the bridge in C2. ADR-0010 front matter only: `status: superseded`, `superseded_by: 11`.
4. Fix stale prose: `.claude/skills/merge-green/SKILL.md:23-25`, `plugin/commands/merge.md:20-22`, `.claude/skills/release/SKILL.md` if it names the push path.

## Workstream C2: PAT identity for bot PRs

Prerequisite (user action): create a fine-grained PAT on `SpillwaveSolutions/wiki_ticket_sdd` from a maintainer account with contents rw, pull-requests rw, issues rw, one-year expiry. Store it as repo secret `WORKLOG_BOT_PAT`. The PR for C2 stays open until the secret exists.

`.github/workflows/compact.yml` and `post-merge.yml`:

1. `GH_TOKEN: ${{ secrets.WORKLOG_BOT_PAT }}` for `git push`, `gh pr create`, and `gh pr merge --auto --merge --delete-branch`. Checkout with `token: ${{ secrets.WORKLOG_BOT_PAT }}` and `fetch-depth: 0` so the push carries the PAT and the branch starts from current `main`.
2. Fail loudly when the secret is empty: first step `test -n "$GH_TOKEN" || { echo "WORKLOG_BOT_PAT missing"; exit 1; }`. No silent fallback to the bridge.
3. Delete the `gh workflow run` and `associate-pr-checks.sh` steps, `actions: write`, and `statuses: write`. Delete `plugin/scripts/associate-pr-checks.sh` and `TestAssociatePrChecks` (`test_merge_green.py:269-381`).
4. Supersede, do not rebase. The ruleset sets `strict_required_status_checks_policy: true` (`merge-when-green-ruleset.json:33`), GitHub never updates a PR branch on its own, and a bot PR armed for auto-merge outlives its job, so a second bot PR goes stale the moment the first merges. At the top of each bot job, before regenerating, close every open `chore/compact-*` and `chore/post-merge-*` PR with `gh pr close --delete-branch`. Each bot PR regenerates from `main` and supersedes the last, so nothing is lost. No shared concurrency group, no rebase loop, no ERR trap: an aborted job leaves at most one stray branch, and the next run deletes it.
5. `post-merge.yml:33` explicit loop guard: skip when `head.ref` starts with `chore/compact-` or `chore/post-merge-`. With the PAT, bot merges now fire `pull_request: closed`, so this guard is required, not accidental. Add a comment that idempotent rendering from the log's `git` field is the real terminator.
6. `post-merge.yml:51-65`: `bin/worklog sync --report > f 2>&1 || true`, then post the comment. Skip the comment when the output contains `no adapter configured` or `LOCAL_ONLY`. Remove `continue-on-error`.
7. `worklog.yml:10-12`: remove the `workflow_run` trigger, the conditionals at `:16`, `:20`, `:27`, and `:90`, the second checkout block at `:26-30`, and the stale comment at `:6-9`. Bot merge commits now get a native `push` run.
8. `compact.yml` nits: replace `[ -f … ] && git add …` with `if/fi` and update the assertion at `test_merge_green.py:236-240` in the same PR. When todo is idle no compact line lands in done either (`compact.py:398-399`), so an eviction-only run has no new watermark; use the message `chore(worklog): compact: evict to archive` for that case.

Tests: extend `TestPostMergeWorkflow` and `test_compact_workflow_lands_via_pr` (`test_merge_green.py:167-245`) to assert the PAT token reference, the guard expression, the supersede step, `--delete-branch`, and the absence of `statuses: write`. Delete `test_invariants_listens_on_post_merge_and_compact` (`:170-173`), which asserts the `workflow_run` list. Keep `test_workflow_run_blocks_do_not_dedent` (`:199-223`); it checks `run: |` indentation and is unrelated to the trigger.

Docs: CHANGELOG entry for the next release with the PAT expiry date, `docs/user_guide` merge section, spec §14.

## Workstream D: #413 CI as the authoritative syncer

Config: `ticketing.sync_owner: human | ci` (default `human`) and `ticketing.ci_dedupe_check: true | false` (default `false`) in `.work/config.yml`. Parse where the ticketing block is read in `bin/worklog`.

1. `post-merge.yml`: when `sync_owner == ci` and the `WORKLOG_BOT_PAT` secret exists, run `bin/worklog sync --push-only` before the render step. `resolve_adapter()` (`sync_dispatch.py:154-162`) reads only `WORKLOG_TICKET_ADAPTER` or the gitignored `.work/sync-state.json`, so the job sets `WORKLOG_TICKET_ADAPTER: adapters/github/adapter` and `GH_TOKEN` from the secret, or the step prints `LOCAL_ONLY` and exits 0 as it does today. `--push-only` is explicit because bare `sync` also pulls the whole board from EPOCH on every run (`:1426-1427`). Cache `.work/sync-state.json` with `actions/cache` (`key: sync-state-${{ github.run_id }}`, `restore-keys: sync-state-`) so `is_dirty` (`:287-292`) does not re-push every open item on every merge.
2. The commit step stages `.work/todo.jsonl` as well as `docs`, and the porcelain check names both (`post-merge.yml:71`, `:79`). Sync runs before `roadmap-render` so the new ticket keys land on the roadmap and pre-commit freshness passes. The link events ride the same derived-docs PR.
3. `bin/worklog sync` in push mode refuses when `sync_owner == ci` unless `--force`: `this repo is CI-owned; a manual sync can race the post-merge job. Pass --force to push anyway.` Exit 1. `--report`, `--explain`, and `--pull-only` stay allowed. A warning alone leaves the second-checkout race open, which is the class #413 asks to close.
4. `hooks/session-doctor.sh`: one warn line (not `fails+=`) when `sync_owner == ci`.
5. `worklog.yml`: when `ci_dedupe_check` is true and the secret exists, run `bin/worklog dedupe --dry-run --check` with the same adapter env and fail on any agreed duplicate group. `Dispatcher.dedupe()` (`:1113`) returns 0 even when agreed groups exist, so `--check` is new: exit 1 when `agreed` is non-empty. Print `skipped: no token` otherwise.
6. Prose fix from #413 ask 1: `check_duplicate_ownership` already runs in `worklog.yml:46` and `hooks/pre-commit:134`. Say so in the issue close comment. The A change to fold the archive there covers the rest. The close comment also says that this repo keeps `sync_owner: human`; NDQR opts in.

Tests: config parsing for both keys, workflow structural asserts (adapter env, `--push-only`, staged log, sync before render), refusal and `--force` in `sync`, `dedupe --check` exit code with a seeded agreed group, doctor warn line.

Docs: config reference, `cli-reference.md`, spec §10, user guide section "Let CI own ticket sync".

## Workstream F: release hygiene

1. `bin/doc_verify.py --strict` gains two checks; no new module. `doc_verify.py` already names the live pair (`LIVE_DOCS`, `:55`) and reads `git_hash` per document (`:239`). For each live doc: the hash must resolve, and the previous tag must be an ancestor of it or equal to it (`git merge-base --is-ancestor <prev tag> <hash>`). An unresolvable hash fails. A freeze record for the previous tag must exist as either `<date>_<tag>-release.md` (the skill's form, `.claude/skills/release/SKILL.md:85`) or the historical dated pair `<date>_<tag>-release_design_doc.md` and `_code_walkthrough.md`; its front matter must name that tag. Test with a fixture repo like `tests/test_watermark.py`'s real-git class.
2. `.claude/skills/release/SKILL.md` §5: replace the prose-only spawn with an explicit `Agent` call and a completion check: the release is not done until the freeze note exists and `doc-verify --strict` passes. Mirror in `plugin/skills/release/SKILL.md`. §2 needs no new step; `doc-verify --strict` already runs there (`:43`).
3. Regenerate the live pair for v0.24.10 with the `design-docs` skill in release mode and write the freeze note inside the F PR, in the foreground, so the PR that adds the gate also passes it. Publish afterwards.
4. CHANGELOG: correct the "Live design docs regenerate after the tag" boilerplate at `:41` and `:48` in the next entry, not by editing old entries.

## Workstream E: #413 Azure Pipelines template

`plugin/scripts/init.sh:229-262` already writes a hook-only `.github/workflows/worklog.yml` into installed projects. Installed projects have no Worklog `tests/`, so this repo's test and coverage jobs are the wrong source; the installed workflow is.

1. In `init.sh`, read `git remote get-url origin`. When it matches `dev.azure.com` or `visualstudio.com`, write `azure-pipelines.yml` instead of the GitHub workflow, from a second heredoc with the same steps: checkout, `WORKLOG_SKIP_BRANCH_GUARD=1 hooks/pre-commit`, `hooks/commit-msg` over PR commits, `python3 bin/compact.py --merge-check`. Skip when the file exists, the same rule the GitHub branch uses. Any other remote keeps today's GitHub output. No `ci.forge:` override key; a user on another forge copies the template by hand.
2. Contract test in `tests/test_plugin.py`: the Azure heredoc parses as YAML and its step `script:` bodies equal the GitHub `run:` bodies. This repo has no ADO test project; NDQR verifies the template live and reports back on #413.
3. Docs: user guide "CI wiring" section with the GitHub Actions to Azure Pipelines mapping table (trigger, checkout, PR head and base, secret injection, shell failure propagation) and a note on which steps the post-merge job needs when NDQR wants that too.

## Tasks

- [ ] (P0) Council review, single edit pass, and plan capture
  Copy the plan to the scratchpad, run grok, codex, and a Fable 5.1 subagent as reviewers, let one Fable 5.1 editor subagent apply the worthy edits once, then capture the plan with plan-capture. The plan is not edited after capture.
- [ ] (P0) Retention: stop re-snapshotting archived items into done.jsonl
  done_state folds done and archive together, refreshed ids are pruned from the archive, and archive appends dedupe by item with the newest snapshot winning. Without this the archive ping-pongs forever and done.jsonl never shrinks. Must land before 2026-10-17.
  - [ ] Cap counts only items present in done.jsonl and unparseable ts never occupies a cap slot
    The FIFO cap currently counts archived items and evicts real ones once the archive exceeds the cap.
  - [ ] Parent veto in eviction, live children only
    A parent is never archived while a child remains in done or todo, and an already archived child does not hold its parent back. The roadmap and status reports keep the epic column.
  - [ ] Tolerate a corrupt archive line and warn on ignored retention config values
    A garbage line in archive.jsonl must not crash the nightly job, even when no item is open. Negative, float, and nested config values print a warning instead of vanishing.
  - [ ] Archive-aware duplicate ownership check and untracked-archive guard
    Merge-check folds the archive so an archived owner still blocks a duplicate link, with the archive path inferred so callers do not change. An untracked archive.jsonl counts as dirty.
  - [ ] Retention tests and doc renumbering
    Add the eight test classes listed in the plan, add test_retention and test_watermark to the explicit CI list, and fix the step order in the compact.py header, the spec, the CLI reference, and the README.
- [ ] (P1) #412: consult the remote marker map before creating a ticket
  observe_remote already fetches every remote ticket. Keep the marker to key map, populate it before the owned pass, pick the dedupe survivor when markers collide, and make it the third source of remembered_key so a clone without link events updates the existing ticket and records the link. Closes #412.
  - [ ] Probe guard when the listing fails and the clone has no push memory
    A transient listing failure on a fresh clone is the #412 scenario. Skip creates for that run and say why.
  - [ ] sync --explain and report hints
    Print which key source answered for one item without mutating anything, forward the flag through cmd_sync, report probe hits in a new relinked count, and suggest dedupe --dry-run when the sync created tickets.
  - [ ] adapter check says when the clone has no push memory
    A fresh clone must not see output that claims it has push memory.
- [ ] (P1) Interim merge-gate hardening and ADR-0011
  Read-only permissions in worklog.yml, remove the dead bypass actor from the ruleset and apply the ruleset live with gh api, and write ADR-0011 that supersedes ADR-0010 with the PR-landing path and the PAT decision.
- [ ] (P1) Bot PRs use the WORKLOG_BOT_PAT identity
  Open and merge compact and post-merge PRs with a maintainer's fine-grained PAT so pull_request CI runs natively, then delete the status bridge, actions: write, statuses: write, and the workflow_run trigger. Requires the secret before merge.
  - [ ] Pipeline hygiene: supersede open bot PRs, delete-branch, explicit loop guard
    Each bot job closes the previous open bot PR before regenerating from main, so a stale PR never blocks under the strict checks policy. post-merge skips its own PRs by branch prefix.
  - [ ] sync --report drift is never masked and the local-only comment is suppressed
    A real drift finding must reach the PR comment. A repo with no adapter gets no noise comment.
- [ ] (P2) #413: CI as the authoritative syncer behind ticketing.sync_owner: ci
  post-merge sets the adapter env, runs a push-only sync with the bot token before rendering, stages the log with the docs, and caches sync-state. Manual push sync refuses without --force in a CI-owned repo and session-doctor warns. Optional dedupe --check PR gate behind ticketing.ci_dedupe_check.
- [ ] (P2) Release gate for design-doc freshness in doc-verify --strict
  A release fails when a live doc's git_hash does not descend from the previous tag or the freeze record for that tag is missing. The release skill spawns the design-docs agent explicitly and checks that it finished.
  - [ ] Regenerate the live design docs for v0.24.10
    The wiki still describes published.json. Run design-docs in release mode and write the freeze note in the same PR as the gate.
- [ ] (P2) #413: Azure Pipelines template from init.sh
  init.sh writes azure-pipelines.yml with the same hook-only steps as the installed GitHub workflow when the origin remote is Azure DevOps. A contract test keeps the two heredocs in step. NDQR verifies live.
  - [ ] CI wiring docs and the GitHub Actions to Azure Pipelines mapping table
    A user guide section that explains the template, the mapping, and how to wire another forge by hand.

## Verification

- Local: `for t in tests/test_*.py; do python3 "$t" || exit 1; done` after each workstream. Coverage stays at or above 80 percent on `bin/*.py`. Every PR that touches `bin/` or `hooks/` passes `tests/test_plugin.py` parity.
- A: reproduce the ping-pong in a scratch `.work/` with `task_days: 0` before the fix, then confirm three compaction cycles leave done at zero lines and the archive at one line. Confirm an archived story no longer pins its epic on the following compaction.
- B: run a real `bin/worklog sync` against the fake adapter with a seeded marker ticket and confirm `created 0, updated 1, relinked 1` and a `link` event in the log. Run `bin/worklog sync --explain <ULID>` and confirm the log is unchanged.
- C1: `gh api .../rulesets/<id>` shows an empty `bypass_actors`.
- C2: after the secret exists, trigger `compact.yml` by `workflow_dispatch` twice and confirm the second run closes the first PR, the surviving PR shows native `pull_request` check runs, and it merges by auto-merge with the branch deleted.
- D: set `sync_owner: ci` in a scratch config and confirm `sync` refuses without `--force`, `--report` still runs, and `session-doctor` warns. In a scratch workflow run, confirm the post-merge PR diff includes a `link` event in `.work/todo.jsonl`.
- F: run `bin/worklog doc-verify --strict` at HEAD and confirm it fails today and passes after regeneration.
- E: run `init.sh` in a scratch repo whose origin is `https://dev.azure.com/x/y/_git/z` and confirm that `init.sh` writes `azure-pipelines.yml` and skips `.github/workflows/worklog.yml`.
- Every PR: `bin/worklog roadmap-render` before commit, items moved `in_progress` to `done` as work lands, `worklog sync` when the plan completes.

## Council notes

All three reviewers responded: grok (has-blocking-issues), codex (has-blocking-issues), fable (needs-changes).

Accepted:

- A: parent veto over `before.items` lets archived children pin their parents forever; veto now counts live children only, and `TestParentVeto` uses ages that evict without the veto (grok, codex).
- A: dedupe-by-`ev` is dead code because `_snapshot` mints a fresh ulid; dedupe by item, newest wins (fable, confirmed at `compact.py:99`).
- A: `_prune_open_from_text` short-circuits on empty `open_ids`, so a garbage line survives in an all-closed repo (codex, fable).
- A: `_git_refuses` uses `git diff --quiet HEAD`, which ignores untracked files; use `git status --porcelain` and never refuse a missing file (grok, fable).
- A: lazy `_resolve` fold changes ambiguity semantics and no archive exists yet; dropped (codex, fable).
- A: `merge_check` infers the archive path so CI and hooks keep their two-path call (grok).
- A: `cap: 0` is already accepted; only docs change, and the doc line names the two exceptions (grok, codex, fable).
- A and C2: all `compact.yml` edits move to C2, including the `[ -f archive.jsonl ]` test update and the eviction-only watermark message (grok, fable).
- A: deadline framed as churn, not data loss (fable).
- A and B: doc file collision noted in Order (grok).
- B: probe map stored a tuple; store the key string only (grok).
- B: populate the probe map before the `owned` pass or probe hits skip the closed-on-remote check (grok, fable).
- B: duplicate markers resolve last-wins; use `_key_sort` (grok, codex, fable).
- B: probe failure on a fresh clone is the original hazard; one guard when pull is supported, listing failed, and no state exists (codex, fable).
- B: caveat 7 was wrong; the adapter lists `--state all`, capped at 1000, through eventually consistent search (grok, codex, fable).
- B: `cmd_sync` must forward `--explain`; `COUNT_KEYS` must gain `relinked`; verification needs a real sync because dry-run does not increment `updated` (grok, codex).
- B: the "can no longer cause harm" claim was false; Decisions now names the residual causes and the close comment says existing duplicates stay (grok, codex).
- C1: the ruleset JSON is a mirror; apply and read back with `gh api` (codex, fable).
- C1 and C2: the `workflow_run` comment stays until C2 removes the trigger; C2 removes the conditionals and the second checkout too; the test that dies is `test_invariants_listens_on_post_merge_and_compact`, not `test_workflow_run_blocks_do_not_dedent` (grok, fable).
- C2: rebase-before-arm and the ERR trap can destroy a valid bot PR under the strict checks policy; replaced by close-and-supersede at job start, no shared concurrency group (grok, codex, fable).
- C2: PAT identity under-specified; maintainer account, one-year expiry, expiry recorded (grok).
- D: `resolve_adapter()` finds no adapter on a runner; set `WORKLOG_TICKET_ADAPTER` (grok, codex, fable).
- D: post-merge stages only `docs` and renders before sync; stage the log and sync first (grok, codex, fable).
- D: bare `sync` pulls the whole board and re-pushes everything without cached state; `--push-only` plus `actions/cache` (fable).
- D: `dedupe` returns 0 with agreed groups; add `--check` (codex).
- D: warning-only manual sync leaves the race open; refuse without `--force` and say in the close comment that this repo stays human-owned (grok).
- E: four renderers, a new module, and byte-for-byte parity are more than #413 asked and the installed workflow, not this repo's, is the right source; shrunk to an Azure template in `init.sh` plus a contract test and mapping table (grok, codex, fable).
- F: `bin/doc_freshness.py` does not exist; the checks go into `doc_verify.py --strict`, the predicate is stated positively, both freeze-record forms are accepted, and the regeneration runs inside the F PR (grok, codex, fable).
- All: plugin mirrors must ship in the same PR (codex).

Rejected:

- A: healing pass for done snapshots already re-copied by an earlier ping-pong (grok). No archive exists in this repo, fold equality holds, and the archive-side dedupe by item covers the consumer case; the residual is a 90-day delay, not a defect.
- A: derive config indent from full YAML structure (codex). The first-child-indent rule covers the nested case the review found, and a YAML parser is scope the plan did not ask for.
- B: contract test that ADO `pull` lines carry the marker id (grok). No ADO adapter lives in this repo; NDQR verifies live.
- B: define behavior for two concurrent syncers that both observe absence (codex). D's refusal in CI-owned repos is the structural answer; a lock across checkouts is scope the user did not ask for. The residual is stated in Decisions.
- C2 and D: coalescing semantics for a shared concurrency group (codex). The shared group is gone; each workflow keeps its own group and supersede handles the rest.
- E: keep a renderer with executable per-forge contract tests (codex). The renderer is gone; the template plus NDQR's live run is the acceptance test.
- Step 0: retag is easy to skip (grok). Already step 0.7; no change.
