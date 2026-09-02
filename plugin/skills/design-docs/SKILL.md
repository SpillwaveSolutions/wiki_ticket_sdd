---
name: design-docs
metadata:
  version: "0.24.10"
description: Generate or sync the design document or code walkthrough. Live current pair regenerated from the actual code; a release freeze is a short tag+hash+delta note, not a full dated copy. Uses document-specialist v3.2.2, design-doc-mermaid v1.1.1, plantuml v1.2.2. Use when asked for a design doc, architecture doc, code walkthrough, or requirements doc, and automatically (background agents) at every release.
---

# Design docs and code walkthroughs

Two live files, one freeze note per release, one rule: **generated from the
actual repo, never from memory.** The templates live in `references/`; this
skill is the procedure around them.

## Companion skills (required)

When this skill writes an architecture doc, a code walkthrough, or a requirements doc, invoke the
Spillwave documentation suite. Install from
`SpillwaveSolutions/spillwave-documentation-marketplace` **v0.2.1**.
Load `references/companion-skills.md` before either prompt.

| Role | Skill | Version | Rule |
|------|--------|---------|------|
| Prose | `document-specialist` | v3.2.2 | Default voice is STE100. Switch to `google-docs-style` v1.1.4 only when the user names Google style. Never mix packs. Wireframes belong in this skill's diagram pass. |
| GitHub-safe diagrams | `design-doc-mermaid` | v1.1.1 | Default for flowchart, sequence, class, ER, state, C4, and component views. Fenced `mermaid` in the Markdown. Validate before publish. |
| Leftover UML and wireframes | `plantuml` | v1.2.2 | Use case, timing, ArchiMate, Salt wireframes, nwdiag, WBS. Always render PNG or SVG. GitHub wiki does not render PlantUML source. |

Hard bans for prose in both voice packs:

- No em dash.
- Do not start a sentence with So, That, Thus, or Hence.

## Artifacts

| File | Kind | Rule |
|---|---|---|
| `docs/designs/current_design_doc.md` | live | regenerated each release; in-place rewrite is sanctioned (like `docs/roadmap.md`) |
| `docs/designs/current_code_walkthrough.md` | live | same |
| `docs/designs/<DATE>_vX.Y.Z-release.md` | freeze note | tag + git_hash + pointers at the live pair + a short delta from the previous freeze. Frozen. Not a copy of the live pair. |
| `docs/designs/<DATE>_<NAME>_design_doc.md` | legacy dated | full copies written before the freeze cap. Frozen forever. Never regenerate, never edit. |
| `docs/designs/<DATE>_<NAME>_code_walkthrough.md` | legacy dated | same |
| `docs/requirements/<NAME>_srs.md` or `_prd.md` | ad-hoc | generated on request from `requirements-doc-prompt.md`. Register with `worklog wiki-add`. |

`<NAME>` on a freeze note is `vX.Y.Z-release` (matches roadmap-snapshot
naming). Ad-hoc names are fine mid-cycle. Legacy full copies keep the
names they already have.

## Frontmatter: how a reader knows what they are looking at

Legacy dated files (do not write new ones):

    ---
    wiki_key: design/<date>_<name>-design-doc   # or -code-walkthrough
    doc_type: design
    truth_state: snapshot
    date: YYYY-MM-DD
    name: vX.Y.Z-release
    tag: vX.Y.Z
    git_hash: <full sha the doc was generated against>
    branch: <branch at generation>
    roadmap_snapshot: docs/roadmap/<date>_<name>.md
    ---

Current files: same minus `date`/`name`/`roadmap_snapshot`, plus
`generated_at: <UTC ISO date-time>` and `roadmap: docs/roadmap.md`, with
`wiki_key: design/current-design-doc` (or `-code-walkthrough`) and
`truth_state: current`. `tag` is
the latest release tag at generation. Stamp from `git rev-parse HEAD`,
`git branch --show-current`, `git describe --tags --abbrev=0`. Never guess.
The identity trio (`wiki_key`, `doc_type`, `truth_state`) is required by the
IA gates (plan ia-content-model §5.4). Regenerating without it trips
`worklog ia-normalize --check`.

## 1. Read the config

Run `bin/worklog triggers release`. This skill owns `design-doc` and
`code-walkthrough`. The release skill routes `user-guide` / `readme` to
the user-docs refresh agent. `release.sync_docs` is the legacy fallback.
Absent list = defaults all on.

## 2. Generate

Load `references/companion-skills.md`, then run
`references/design-doc-prompt.md` (architecture / design),
`references/code-walkthrough-prompt.md` (walkthrough), or
`references/requirements-doc-prompt.md` (SRS / PRD)
against the repository at HEAD. The template's own rules govern content.

Sections are a menu. Omissions are listed with reasons. Every code claim
cites `path, function(), lines N-M`. Fill System Context and Source Material
from the repo itself: README, docs/worklog-spec.md,
docs/plans/, docs/adr/, `.work/config.yml`, the test suites.

## 2b. Verify before you report done. Not optional

Run `bin/worklog doc-verify` and fix every **FABRICATED** finding in the
files you just wrote, then re-run until they are gone. Do this before
publishing and before reporting completion.

This is the step whose absence caused #294. Line citations were checked by
nobody, and a measured **12 of 26 were wrong**, pointing at offsets from
several releases earlier. Every one was written by an agent that had the
file open and copied the previous edition's number forward. One wrong claim
was even introduced while hand-fixing the previous wrong claim, which is
what a regeneration without a check does: it moves the error rather than
removing it.

Reading the verdicts:

- **FABRICATED**: the citation is wrong at the commit you generated
  against. Your bug, in the file you just wrote. Fix it.
- **DRIFT**: right when written, moved since. Expected in the frozen dated
  copies; in a `current_*` file it means you cited an older tree than the
  one you generated against, so treat it as yours too.
- **UNSTAMPED / UNRESOLVABLE**: no `git_hash`, or a commit not in this
  clone (see ADR-0008). Report it; never re-check against HEAD.

Do not hand-edit a frozen dated copy or freeze note to silence a finding. Frozen means
frozen: the correction belongs in the next edition, and the current pair
should say so in prose where a reader would be misled.

## 3. Modes

- **Release mode** (invoked by the release skill after the tag exists):
  regenerate both `current_*` files against the tagged commit, then write
  ONE freeze note `docs/designs/<DATE>_vX.Y.Z-release.md`. Do not copy the
  live pair into two dated files. Existing full dated copies stay as they
  are.
- **Sync mode** (ad-hoc, "update the design doc"): regenerate `current_*`
  only. A freeze note happens only when explicitly asked.

### Freeze note shape

    ---
    wiki_key: design/<date>_vX.Y.Z-release
    doc_type: design
    truth_state: snapshot
    date: YYYY-MM-DD
    name: vX.Y.Z-release
    tag: vX.Y.Z
    git_hash: <full sha the live pair was generated against>
    branch: <branch at generation>
    roadmap_snapshot: docs/roadmap/<date>_vX.Y.Z-release.md
    live_design: docs/designs/current_design_doc.md
    live_walkthrough: docs/designs/current_code_walkthrough.md
    ---

Body is a short delta from the previous freeze: what landed in the
architecture, what was removed, which ADRs shipped. Do not paste the live
pair. Stamp `git_hash` from `git rev-parse HEAD` at the tagged commit.

## 4. Publish

wiki-publish, standard ledger flow (`.work/published.jsonl`):
- `design/current-design-doc` to page `Design-Doc` (live: republish on
  source-hash change), `design/current-code-walkthrough` to `Code-Walkthrough`.
- Freeze notes to `Design-Freeze-<date>_vX.Y.Z-release` (frozen: publish
  once), linked from Home next to the roadmap snapshots.
- Legacy full dated copies already on the wiki stay; do not republish
  them and do not add new full-copy pages.

## 5. Execution rule: always a background subagent

Generation reads the whole repo. It never blocks the main thread or a
release. Same non-blocking pattern as viz and plan-publish: spawn the agent,
fold the result in when it reports. At release time the release skill spawns
this; the tag never waits for prose.
