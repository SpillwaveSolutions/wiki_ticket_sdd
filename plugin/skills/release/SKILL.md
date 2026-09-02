---
name: release
metadata:
  version: "0.24.10"
description: Cut a versioned release — stamp the changelog, snapshot the roadmap, tag, create the platform release, publish, and sync. Use when asked to "cut a release", "ship vX.Y.Z", "tag a version", or when an unreleased changelog section is ready to go out.
---

# Release

A release is worklog work: record a release task first (work-track), and the
release leaves frozen artifacts behind — a dated changelog section, a roadmap
snapshot, a tag, and a platform release. No per-system code ships with this
skill; use the platform's own release tooling.

## 1. Preconditions

- Clean working tree on the default branch (or a release-prep branch about
  to merge into it).
- All test suites green locally; CI green on the tip.
- Version lockstep holds: the plugin manifest, `bin/worklog --version`, and
  every plugin skill's frontmatter agree (`tests/test_plugin.py` enforces it).
- The top CHANGELOG section reads `## X.Y.Z — unreleased` and describes what
  actually ships. If it doesn't, fix that first — release notes are written
  as features land, not reconstructed at tag time. When the section is missing
  or thin, `bin/worklog changelog-draft --version X.Y.Z` writes a starting
  draft from git log since the last tag (markdown on stdout, the commits it
  excluded on stderr). It is bullets, not release notes: edit the prose before
  stamping, and read the exclusion list to confirm nothing real was dropped.

## 2. Stamp

- CHANGELOG: change `— unreleased` to `— YYYY-MM-DD` (UTC, release date).
- `bin/worklog roadmap-snapshot --name vX.Y.Z-release` — the frozen picture
  of open work at release time. Snapshots are frozen; never regenerate.
- `bin/worklog ia-index` — sidecars the new snapshot (stamping its
  `release` and supersede chain), refreshes the inventory, and re-renders
  Home/Sidebar/Releases-index + publish manifest so the release is
  navigable. Commit `docs/.index/` with the snapshot.
- `bin/worklog trace-check --strict` — the pre-release evidence gate: every
  closed item must trace to a plan, ticket, and PR. Failures block the
  release; fix the links (`worklog link-pr`, sidecar `relates_to`) or
  consciously report the gaps to the human — never skip silently.
- `bin/worklog doc-verify --strict` — the pre-release citation gate: every
  document's code citations must resolve at the commit that document was
  written against. FABRICATED means wrong even in the tree the author had
  open — a real defect, fix it. DRIFT on a frozen document is expected and
  does not block; drift on `current_design_doc` / `current_code_walkthrough`
  does, because those claim to describe HEAD. `unresolvable` means the
  stamped commit is not in this clone (see ADR-0008) — report it, never
  re-check against HEAD.

## 3. Land it

Commit the stamp + snapshot on a release-prep branch and land it as a PR
(the branch guard hook refuses commits directly on the default branch --
main is pull-only). The release tags the commit that carries the dated
changelog.

**Batch ceremony.** Stamp, `provenance-backfill`, and item-close are one
PR, not three. Each extra PR pays a full CI cycle (history: #386→#389 in
one afternoon). If backfill needs the merge commit of the stamp, put it
in the same PR after the stamp commit — do not open a follow-up PR that
only closes an item or restamps `merged_in`.

## 4. Tag and platform release

- `git tag vX.Y.Z <commit>` on the landed commit; push the tag.
- Create the platform release with the CHANGELOG section as the notes:
  GitHub — `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <section>`;
  GitLab — `glab release create`; other systems — their CLI or MCP, or
  tag-only when the platform has no release object. Research, don't guess.

## 5. Doc sync — background agents

The moment the tag exists, spawn background subagents — the release NEVER
waits on prose. Run `bin/worklog triggers release`; each listed target
gets regenerated and republished. Doc commits land via a PR AFTER the tag:
docs describe the release, the tag does not wait for them. (Main is
pull-only — §3. Do not commit these onto the default branch directly.)

- **Agent A — design-docs skill, release mode**: if `design-doc` and/or
  `code-walkthrough` are listed, regenerates
  `docs/designs/current_design_doc.md` + `current_code_walkthrough.md`
  against the tagged commit, writes one freeze note
  (`<DATE>_vX.Y.Z-release.md`: tag + git_hash + delta — not a copy of the
  live pair), publishes the live pair plus the freeze note via wiki-publish
  when `wiki-publish` is also listed. Existing full dated copies stay frozen;
  do not write new ones.
- **Agent B — user-docs refresh**: if `user-guide` and/or `readme` are
  listed, diffs `vPREV..vX.Y.Z`, updates `docs/user_guide/*.md` and
  `README.md` wherever that diff made them stale, then republishes
  changed wiki pages through the ledger when `wiki-publish` is listed.

Agents report when done; their commits reference the release work item.
The list is the contract, not this prose. `release.sync_docs` is the
legacy fallback — `worklog triggers` already folds it in.

## 6. Publish and sync

- wiki-publish: the updated Roadmap and the release snapshot page; link the
  snapshot from Home.
- ticket-sync: close the release work item(s); anything shipped-and-closed
  reconciles with the tracker. Release items are local-only by convention —
  no external ticket is filed for them, so this step is a no-op for the
  release item itself. That's intentional, not a gap: the tag and platform
  release already give the release public visibility; don't file a
  redundant issue just to have something for ticket-sync to close.
- **Re-index after publishing, and commit the result.** Publishing writes the
  page's live wiki location back into the ledger, so the generated inventory
  is stale the moment the last page lands. Run `bin/worklog ia-index` and
  commit `docs/.index/` — the IA gates are hard now, and the next commit fails
  otherwise. One pass is enough: publishing adds only the wiki location to a
  record, which is not part of the render hash, so re-indexing never makes
  another page need republishing.

## 7. After

- `bin/worklog provenance-backfill` — stamps `merged_in` on frozen documents
  that have now landed on the default branch. A document cannot know the
  merge that will carry it, so this is the step that fills it in; run it on
  the post-release branch (this step already lands a commit) and run
  `worklog ia-index` alongside it in the SAME commit, or the freshness gate
  rejects the result. Frozen documents only, by design — a live document has
  been edited since it landed, so the merge that first carried it would name
  a version that no longer exists. Safe to re-run: it skips anything already
  stamped. Do not open a separate PR for this step — see §3 batch ceremony.

The next feature wave opens a new `## X.Y.Z — unreleased` section and bumps
the version lockstep in the same commit that adds the first feature.
Released changelog sections are frozen — corrections go in the next
release's notes, same rule as status reports.
