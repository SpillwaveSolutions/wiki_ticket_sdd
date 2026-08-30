# Changelog

## Unreleased

- **Wiki ledger is JSONL, union-merge.** `.work/published.json` (a 308KB JSON dict with no merge strategy) is now `.work/published.jsonl`: append-only events, last-write-wins per key, `merge=union`. `worklog wiki-add` / `wiki-record` / `wiki-get` own the file; the wiki-publish skill must not hand-edit it. Leftover JSON migrates on first write with deterministic ULIDs (#392).

- **Compaction preserves open sync conflicts.** Snapshots are built from public fields, which stripped `_conflicts`; the nightly compact then verified the stripped form and silently dropped every open conflict. Compact now re-emits `conflict` events above each snapshot and verifies the private map too.
- **Write envelope, flock, monotonic ULIDs.** `worklog` byte-caps the whole encoded event (PIPE_BUF 4096), checks `os.write`, and holds `.work/.lock` across append so a concurrent compact cannot replace the inode mid-write. `ulid.new()` increments entropy inside the same millisecond so create-then-update cannot fold out of order.
- **Merge bootstrap self-heals.** SessionStart doctor writes `merge.ours.driver` and `core.hooksPath` (absolute in linked worktrees). `doctor --fix-wiring` does the same on demand; `init.sh` is worktree-aware.
- **Sync correctness.** Pull holds the since-cursor when ingest/conflict writes fail; `--keys` is forwarded to the adapter as a point query; `WORKLOG_TICKET_PROJECT` is exported from `ticketing.project` when unset. GitHub `to_line` emits a readable body (so remote body edits conflict instead of being clobbered) and warns at the 1000-issue listing cap.
- **Faster merge.** `merge-when-green` arms `gh pr merge --auto --merge` up front and polls at 60s as fallback. Never squash (ADR-0008).
- **Cursor port.** `cursor-hooks.json` paths resolve against the plugin root (`./hooks/scripts/...`). Host-parity test is a real unittest in CI. `.grok-plugin/marketplace.json` locksteps to 0.24.9.

## 0.24.9 — 2026-08-27

- **Push-only sync absorbs tracker-only tickets and closed-on-remote drift (#385).** `worklog sync` (including `--push-only`) lists remote tickets with no worklog marker as a first-class drift class and prints the `worklog adopt --system … --key …` repair. A linked ticket that is closed remotely while the log item is still open is closed locally (`worklog close`) instead of pushing the open state back over it. `worklog adopt` creates the log item, links it, and stamps the ULID marker so the next push updates. Docs: never `gh issue create` / `gh issue edit` on a worklog-managed tracker — child worktrees add via `worklog` or they do not file tracker issues.
- **Version lockstep 0.24.9.** Plugin manifests, `bin/worklog`, both skill trees, and the README marker all read 0.24.9.

Released with `trace-check --strict` gaps on historical work (none of it from this wave). Reported and accepted rather than skipped silently. `doc-verify --strict` findings on frozen documents do not gate (ADR-0009). Live design docs regenerate after the tag.

## 0.24.8 — 2026-08-26

- **Lost-link sync no longer mints a second ticket (#382).** Create-vs-update now uses `remembered_key`: folded `external.key` if present, otherwise `last_pushed_key` in gitignored `.work/sync-state.json`. A checkout that throws away an uncommitted `link` event updates the original ticket and `record_link` restores the folded pointer. `worklog unlink` clears `last_pushed_*` so a deliberate unlink still files fresh, including for closed items that must not be re-filed.
- **`worklog dedupe` collapses the extras #382 already minted (#383).** Groups by marker ULID, classifies agreed vs mixed-state conflicts, and with `--collapse-agreed` closes extras (pointer in the resolution, never deletes) and re-links the survivor. Default is dry-run. Same-title twins without a shared marker are low-confidence and never auto-collapsed.
- **Generated files stop conflicting on every concurrent branch (#381).** `.gitattributes` marks `docs/roadmap.md` and `docs/.index/**` `merge=ours` (named driver `git config merge.ours.driver true`, installed by `init.sh` and the commit hook). `pre-merge-commit` regenerates from the union-merged log and stages the result before the freshness gate, so the merge commit names both sides' work.
- **Version lockstep 0.24.8.** Plugin manifests, `bin/worklog`, both skill trees, and the README marker all read 0.24.8.

## 0.24.7 — 2026-08-25

- **Prompt companion pins.** `design-doc-prompt.md`, `code-walkthrough-prompt.md`, and `requirements-doc-prompt.md` now name the same versions as the skill table: `document-specialist` v3.2.2, `design-doc-mermaid` v1.1.1, `plantuml` v1.2.2, `google-docs-style` v1.1.4. PlantUML is leftover types only.
- **Design docs under `docs/design/` (singular) are classified.** `ia.py` matched only `docs/designs/` (plural), so consumer repos that follow the singular convention inventoried `design:0` with no warning and never wrote those files to the publish manifest (#377). Both paths now classify as `design`. The sidecar normalizer stamps `git_hash` from the commit that last touched the file when the artifact did not record one, so `ia-inventory --check` no longer blocks on `missing git_hash` after the path fix. `docs/project_notes/` is classified as `guide` so dated cut notes reach the index instead of vanishing.
- **`init.sh` installs `doc_verify.py`, `provenance.py`, and `hooks/session-end.sh`.** All three were present, wired, and dead — the pre-commit citation guard is a file-existence test, so a missing module looked like a pass, and the upgrade notes pointed `SessionEnd` at a path init never created (#344). The plugin manifest (Claude, Codex, Cursor) now wires `SessionEnd` too. `session-end.sh` reads the hook payload from stdin instead of a heredoc, so it actually ends the session.
- **Bot pushes to main now show up in check history.** The compact job already ran the suite before pushing (0.24.3). `worklog-invariants` now also listens on `workflow_run` of `worklog-compact`, which GitHub does fire for `GITHUB_TOKEN` pushes, so a broken compact commit is a red check on main instead of a silent one (#361).
- **Version lockstep 0.24.7.** Plugin manifests, `bin/worklog`, both skill trees, and the README marker all read 0.24.7.

Released with `trace-check --strict` gaps: 50 historical, plus four from this wave (three unplanned items have no plan link; the classify item does not own #377 because the sidecar-stamp item already does). Reported and accepted rather than skipped silently. `doc-verify --strict` findings on frozen documents do not gate (ADR-0009). Two live-doc drifts on `current_design_doc` (`ia.py` `_scalar` / `is_frozen` line numbers from this wave) — the live pair regenerates after the tag.

## 0.24.6 — 2026-08-24

- **Claude Code packaging pins.** Companion skills now point at the GitHub releases that actually install: `spillwave-documentation-marketplace` v0.2.1 (catalog at `.claude-plugin/marketplace.json` with GitHub source objects), `document-specialist` v3.2.2, `design-doc-mermaid` v1.1.1, `plantuml` v1.2.2, `google-docs-style` v1.1.4 (agents is a file array; hooks auto-discover). `ste100` stays v0.1.4. Claude Code can `plugin marketplace add SpillwaveSolutions/spillwave-documentation-marketplace` from GitHub without a local clone.
- **Version lockstep 0.24.6.** Plugin manifests, `bin/worklog`, both skill trees, and the README marker all read 0.24.6.

Released with `trace-check --strict` gaps on historical work (none of it from this wave). Reported and accepted rather than skipped silently. `doc-verify --strict` findings on frozen documents do not gate (ADR-0009); live design docs regenerate after the tag.

## 0.24.5 — 2026-08-24

- **Mermaid-first design docs.** Architecture docs, code walkthroughs, and requirements now require the Spillwave documentation suite: `document-specialist` v3.2.1 writes the prose (STE100 default; Google style only when named) and owns wireframes; `design-doc-mermaid` v1.1.0 is the default for flowchart, sequence, class, ER, state, C4, and component views; `plantuml` v1.2.1 is leftover types only (Salt wireframes, use case, timing, ArchiMate, nwdiag, WBS) and always PNG or SVG. Install from `spillwave-documentation-marketplace` v0.2.0.
- **Wiki vs Confluence diagrams.** GitHub wiki keeps fenced mermaid and uploads PlantUML images with the page. Confluence uploads images for both mermaid and PlantUML. A wiki page that points at a missing `docs/diagrams/*.png` is a publish defect.
- **Requirements prompt.** `design-docs` now ships `requirements-doc-prompt.md` for SRS and PRD, using the same companion skills as the design doc and walkthrough.
- **Hard bans in both voice packs.** No em dash. Do not start a sentence with So, That, Thus, or Hence.

Released with `trace-check --strict` gaps on historical work (none of it from this wave). Reported and accepted rather than skipped silently. `doc-verify --strict` findings on frozen documents do not gate (ADR-0009); live design docs regenerate after the tag.

## 0.24.4

- Three-host hooks: Codex + Cursor-native when Claude hooks exist.


## 0.24.3 — 2026-08-18

- **The Stop hook can see a log you already committed.** Its proof that a session recorded work was an *uncommitted* change to `.work/todo.jsonl`, so the rhythm the policy asks for — record first, then commit — erased the evidence and the session got blocked. `SessionStart` now stamps the commit the session began at into the session registry, and `Stop` diffs the log against that fixed point. The marker never moves on later heartbeats, and a missing or unresolvable marker falls back to `HEAD`, which is the behavior this hook has always had. Trade-off, taken deliberately: a session that pulls someone else's log changes now also reads as having recorded something — a missed nag, where the old direction refused to let a correct session finish its turn.
- **The nightly compaction job checks itself before it pushes.** A push made with the default `GITHUB_TOKEN` triggers no other workflow, so `worklog-invariants` never ran on the commit that job creates. `main` sat red for two days that way. The job now runs `hooks/pre-commit`, the merge-integrity check and the full suite first, so a bad compaction never lands. It still does not produce a run in `main`'s check history — only a credential that is not `GITHUB_TOKEN` can — and that residual gap stays tracked.
- **`--keys` is documented as what it is.** Sync scope is *open* ∪ *hash-dirty* ∪ `--keys`: the flag widens a run and can never narrow one. The help text and `docs/worklog-spec.md` now say so, including why no narrowing flag exists — a sync that skipped dirty items would leave the tracker further from the log, which is the drift `sync` exists to close. No behavior change.
- **Version lockstep repaired.** 0.24.2 bumped two of eight version sources; `plugin/plugin.json`, both plugin manifests, all fourteen skill frontmatters, `bin/worklog` and the README marker were left behind. All eight now agree.

Released with 50 `trace-check --strict` gaps across 29 items — missing PR, ticket and plan links on historical work, none of it from this wave. Reported and accepted rather than skipped silently.

## 0.24.2 — 2026-08-17

- **Cursor host.** `.cursor-plugin/plugin.json` (Cursor Plugins) plus `.cursor/rules/second-brain.mdc`. Docs: `docs/CURSOR.md`. `docs/GROK_BOT.md` now covers Grok Bot spawning Cursor cloud agents.

