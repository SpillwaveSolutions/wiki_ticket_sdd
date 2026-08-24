# Changelog

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

