---
name: design-docs
description: Generate or sync the design document and code walkthrough under docs/designs/ — frozen dated pairs tied to a release tag, live current pairs regenerated from the actual code. Use when asked for a design doc or code walkthrough, and automatically (background agents) at every release.
---

# Design docs & code walkthroughs

Two artifact kinds, four files, one rule: **generated from the actual repo,
never from memory.** The templates live in `references/`; this skill is the
procedure around them.

## Artifacts

| File | Kind | Rule |
|---|---|---|
| `docs/designs/<DATE>_<NAME>_design_doc.md` | dated | frozen — publish once, never regenerate (same rule as roadmap snapshots) |
| `docs/designs/<DATE>_<NAME>_code_walkthrough.md` | dated | frozen — same |
| `docs/designs/current_design_doc.md` | live | regenerated each release; in-place rewrite is sanctioned (like `docs/roadmap.md`) |
| `docs/designs/current_code_walkthrough.md` | live | same |

`<NAME>` at release time is `vX.Y.Z-release` (matches roadmap-snapshot
naming). Ad-hoc names are fine mid-cycle.

## Frontmatter — how a reader knows what they're looking at

Dated files:

    ---
    date: YYYY-MM-DD
    name: vX.Y.Z-release
    tag: vX.Y.Z
    git_hash: <full sha the doc was generated against>
    branch: <branch at generation>
    roadmap_snapshot: docs/roadmap/<date>_<name>.md
    ---

Current files: same minus `date`/`name`/`roadmap_snapshot`, plus
`generated_at: <UTC ISO date-time>` and `roadmap: docs/roadmap.md`. `tag` is
the latest release tag at generation. Stamp from `git rev-parse HEAD`,
`git branch --show-current`, `git describe --tags --abbrev=0` — never guess.

## 1. Read the config

`release.sync_docs` in `.work/config.yml` lists what regenerates at release
(`design-doc`, `code-walkthrough`, `user-guide`, `readme`). Absent list =
defaults all on. This skill owns the first two entries; the release skill
routes the other two to the user-docs refresh agent.

## 2. Generate

Run `references/design-doc-prompt.md` (or `code-walkthrough-prompt.md`)
against the repository at HEAD. The template's own rules govern content —
sections are a menu, omissions are listed with reasons, every code claim
cites `path — function(), lines N–M`. Fill the template's System Context /
Source Material from the repo itself: README, docs/worklog-spec.md,
docs/plans/, docs/adr/, `.work/config.yml`, the test suites.

## 3. Modes

- **Release mode** (invoked by the release skill after the tag exists):
  regenerate both `current_*` files against the tagged commit, then copy
  each to its dated frozen name with the dated frontmatter. Four files out.
- **Sync mode** (ad-hoc, "update the design doc"): regenerate `current_*`
  only. A dated freeze happens only when explicitly asked.

## 4. Publish

wiki-publish, standard ledger flow (`.work/published.json`):
- `design/current-design-doc` → page `Design-Doc` (live: republish on
  source-hash change), `design/current-code-walkthrough` → `Code-Walkthrough`.
- Dated files → `Design-Doc-<date>_<name>` / `Code-Walkthrough-<date>_<name>`
  (frozen: publish once), linked from Home next to the roadmap snapshots.

## 5. Execution rule: always a background subagent

Generation reads the whole repo — it never blocks the main thread or a
release. Same non-blocking pattern as viz and plan-publish: spawn the agent,
fold the result in when it reports. At release time the release skill spawns
this; the tag never waits for prose.
