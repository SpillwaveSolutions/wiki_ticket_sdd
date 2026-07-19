---
date: 2026-07-19
slug: design-docs-release-sync
title: Design docs + code walkthroughs with release-time doc sync
epic: 01KXY7X0QH47Z6B5QZD5G052FJ
items: [01KXY7X0QJCEHRDABCXF6QKXF7, 01KXY7X0QJAE0QH2W30JKK39TA, 01KXY7X0QJ2SBY6KTQ30AKASP7, 01KXY7X0QJQHZBCSCR438RFFMM, 01KXY7X0QJY4JZWYYF2CA46B9G, 01KXY7X0QJ79852RFK5Q8F6FZM]
---

# Design docs + code walkthroughs, release-time doc sync (background agents)

## Context

The repo has frozen plans (the *why*), a generated roadmap (the *what's next*), and
status reports (the *what happened*) — but no living description of the *what is*:
architecture, data flow, and a guided tour of the code. Rick wants two new artifact
kinds under `docs/designs/`, tied to releases, regenerated automatically at release
time by background agents, plus release-time refresh of the user guide and README so
shipped docs never drift from the shipped code. All of it publishes to the wiki via
the existing ledger.

## Artifact model (mirrors the roadmap-snapshot pattern)

**Dated (frozen, publish-once — same rules as roadmap snapshots):**
- `docs/designs/<DATE>_<NAME>_design_doc.md`
- `docs/designs/<DATE>_<NAME>_code_walkthrough.md`
- `<NAME>` at release time is `vX.Y.Z-release` (matches snapshot naming); ad-hoc
  names allowed mid-cycle.
- Frontmatter: `date`, `name`, `tag: vX.Y.Z` (git tag), `roadmap_snapshot:
  docs/roadmap/<date>_<name>.md`, `git_hash`, `branch`.

**Current (live, regenerated each release — same rules as the live Roadmap page):**
- `docs/designs/current_design_doc.md`, `docs/designs/current_code_walkthrough.md`
- Frontmatter: `generated_at` (UTC date-time), `git_hash`, `branch`,
  `roadmap: docs/roadmap.md`, `tag` (latest release tag when generated at release).
- Frozen-artifact exception documented: these two are the only docs besides
  `docs/roadmap.md` that get rewritten in place.

**Content templates** live in the skill dir as references:
- `references/design-doc-prompt.md` — Rick's full 35-section Design Document
  Prompt (supplied in-session), stored with these improvements:
  1. **Sections are a menu, not a quota.** New preamble: include only sections
     whose subject exists in the analyzed system; close the doc with an "Omitted
     sections" list, one line of reason each. (35 enterprise sections against a
     stdlib-only CLI would be mostly "N/A" padding — omission-with-reason keeps
     the doc honest AND short.)
  2. **Vendor sections genericized.** §16 Redis / §19 Bedrock become "for each
     cache/AI-provider dependency actually present…", keeping Rick's detailed
     checklists as the per-dependency template. §17 MCP / §18 AI endpoints keep
     their checklists, gated the same way.
  3. **Source material auto-filled, not `[insert]`ed.** The skill fills System
     Context/Source Material from the repo itself: README, spec, docs/plans/,
     docs/adr/, `.work/config.yml`, test suites — the analyzed repo is the
     source of truth, placeholders deleted.
  4. **Source-reference + accuracy rules merged in** from Rick's companion
     walkthrough prompt: every code claim cites `path — function(), lines N–M`;
     quote exactly; never invent; distinguish production/test/deprecated code;
     no secrets. Labels Confirmed/Assumption/Recommendation/Open Question kept.
  5. **Frontmatter block required** (this plan's artifact model: generated_at /
     git_hash / branch / tag / roadmap ref) — the prompt's own "store under
     docs/design/<DATE>_design_doc_<NAME>.md" line is replaced by our layout:
     `docs/designs/<DATE>_<NAME>_design_doc.md` (Rick's stated convention; the
     prompt's path/name-order variant normalized to it).
  6. **Mermaid rules kept**, plus our house constraint: node cap with "+K more"
     (no silent truncation), diagrams derived from actual code/events only.
  7. Quality-controls and Output-Rules sections kept verbatim (they're good);
     "Validate the Mermaid syntax" stays — we render Mermaid in the roadmap
     already, so broken syntax is visible immediately.
- `references/code-walkthrough-prompt.md` — walkthrough variant built from the
  same accuracy/source-reference rules: guided tour of bin/ + hooks/ + plugin/
  in execution order, tests as executable spec, junior-engineer orientation
  (where to start, what's risky, which invariants must hold), gaps-and-drift
  section comparing walkthrough against the design doc — design doc as context,
  never as proof.

## New skill: `design-docs` (repo `.claude/skills/` + plugin copy, canon versioning)

Instructions, no shipped code (consistent with skill-based edges):
1. Read `.work/config.yml` `release.sync_docs` list (see below).
2. Generate = run the reference prompt against the ACTUAL repo at HEAD; stamp
   frontmatter from `git rev-parse` / `git describe --tags` / current roadmap.
3. Release mode: regenerate both `current_*` files, then freeze dated copies
   `<DATE>_<vX.Y.Z-release>_*.md` with tag + snapshot frontmatter.
4. Sync mode (ad-hoc): regenerate `current_*` only; dated copy only when asked.
5. Publish via wiki-publish: `Design-Doc` / `Code-Walkthrough` live pages
   (republish on hash change) + frozen dated pages linked from Home — ledger keys
   `design/current-design-doc`, `design/<date>_<name>-design-doc`, etc.
6. **Always executed in a background subagent** — same non-blocking rule as viz.

## Config: the release-sync list (Rick: "a list … updated on release")

`.work/config.yml` gains:

```yaml
release:
  sync_docs:            # regenerated by background agents at every release
    - design-doc        # docs/designs/current_design_doc.md + dated freeze
    - code-walkthrough  # docs/designs/current_code_walkthrough.md + dated freeze
    - user-guide        # docs/user_guide/*.md reviewed against diff since last tag
    - readme            # README.md same
```

Remove an entry to opt a doc out of release sync. `plugin/scripts/init.sh` scaffold
gains the same block (commented defaults).

## Release skill integration (the automation)

`release` skill (both copies) gains a step between "Tag and platform release" and
"Publish and sync": **spawn background agents, never block the tag**:
- Agent A — design-docs skill in release mode (current + dated + wiki).
- Agent B — user-docs refresh: diff `vPREV..vX.Y.Z`, update `docs/user_guide/*` and
  `README.md` where the diff made them stale (guided by `release.sync_docs`),
  commit on main after the release lands, republish changed wiki pages via ledger.
- The release itself completes without waiting; agents report when done. Doc
  commits land AFTER the tag (docs describe the release; the tag doesn't wait for
  prose).

## Files

- `.claude/skills/design-docs/SKILL.md` + `references/{design-doc-prompt,code-walkthrough-prompt}.md`
- `plugin/skills/design-docs/` mirror (with `version:` frontmatter — lockstep test
  picks it up automatically)
- `.claude/skills/release/SKILL.md` + `plugin/skills/release/SKILL.md` — new
  background-agents step
- `.work/config.yml` + `plugin/scripts/init.sh` — `release.sync_docs` block
- `docs/designs/` — first generation: `current_*` pair + dated `v0.11.0-release`
  pair against the just-cut tag (dogfood proof)
- `.claude/skills/wiki-publish/SKILL.md` (+ plugin) — one line adding designs to
  the default publish set; frozen/live rules already cover the rest
- `docs/user_guide/user-guide.md`, `plugin-guide.md`, `README.md` — document the
  new artifacts + release sync
- `tests/test_plugin.py` — skill count/version lockstep covers the new skill
  automatically (assertGreaterEqual); packaging guard unchanged (docs/ never ships)
- `CLAUDE.md` — one policy bullet: designs regenerate on release via background
  agents; `current_*` are the sanctioned rewrite-in-place exception; dated ones
  frozen

## Execution shape

Wave 1 (parallel subagents): skill + references | release-skill step + config |
docs updates. Wave 2 (background agent, dogfood): generate the four artifacts
against v0.11.0 and publish to wiki. PR → green-gates loop → merge. Version stays
0.11.0 (content change post-release; next release picks it up — same pattern as
the ADO-caveats PR).

## Verification

- `tests/test_plugin.py` green (canon + lockstep + packaging).
- `docs/designs/` holds 4 files; frontmatter carries tag/hash/branch/roadmap refs
  that match `git rev-parse v0.11.0` and the v0.11.0 snapshot path.
- Wiki shows Design-Doc + Code-Walkthrough live pages + dated pages linked from
  Home; `.work/published.json` has the new keys.
- A re-run of the design-docs skill with unchanged sources publishes nothing
  (hash-skip proof).
- Release skill text: next release spawns the agents (proven live at v0.12.0).
- Plan captured via `worklog plan-capture` to `docs/plans/` at execution start.

## Tasks

- [ ] (P1) design-docs skill: SKILL.md + references/design-doc-prompt.md (Rick's 35-section prompt, improved) + references/code-walkthrough-prompt.md; plugin mirror with version frontmatter
- [ ] (P1) release skill gains background-agents doc-sync step (both copies); release.sync_docs list in .work/config.yml + init.sh scaffold
- [ ] (P1) docs: user guide + plugin guide + README document design artifacts; CLAUDE.md policy bullet; wiki-publish default set gains designs
- [ ] (P1) dogfood generation: current_design_doc + current_code_walkthrough + dated v0.11.0-release pair under docs/designs/ (background agent, grounded in actual repo, frontmatter tag/hash/branch/roadmap)
- [ ] (P1) wiki: Design-Doc + Code-Walkthrough live pages, frozen dated pages, Home links, published.json ledger keys
- [ ] (P2) suites green; PR; green-gates merge; item closeout
