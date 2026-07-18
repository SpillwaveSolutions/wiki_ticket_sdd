---
name: release
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
  as features land, not reconstructed at tag time.

## 2. Stamp

- CHANGELOG: change `— unreleased` to `— YYYY-MM-DD` (UTC, release date).
- `bin/worklog roadmap-snapshot --name vX.Y.Z-release` — the frozen picture
  of open work at release time. Snapshots are frozen; never regenerate.

## 3. Land it

PR-based repos: commit the stamp + snapshot as a release-prep PR and get it
merged. Direct-commit repos: commit on the default branch. Either way the
release tags the commit that carries the dated changelog.

## 4. Tag and platform release

- `git tag vX.Y.Z <commit>` on the landed commit; push the tag.
- Create the platform release with the CHANGELOG section as the notes:
  GitHub — `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <section>`;
  GitLab — `glab release create`; other systems — their CLI or MCP, or
  tag-only when the platform has no release object. Research, don't guess.

## 5. Publish and sync

- wiki-publish: the updated Roadmap and the release snapshot page; link the
  snapshot from Home.
- ticket-sync: close the release work item(s); anything shipped-and-closed
  reconciles with the tracker.

## 6. After

The next feature wave opens a new `## X.Y.Z — unreleased` section and bumps
the version lockstep in the same commit that adds the first feature.
Released changelog sections are frozen — corrections go in the next
release's notes, same rule as status reports.
