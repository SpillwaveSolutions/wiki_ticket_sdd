---
date: 2026-07-30
slug: close-p1-epics-and-settle-merge-and-gone-questions
title: Close both P1 epics, settle the merge-strategy and GONE questions
epic: 01KYTJGK2WMX6PNMYQDFFFPGTP
items: [01KYTJGK2XJD516RXMZ52PDZP1, 01KYTJGK2XDTKNHGH8QTHBHCTY, 01KYTJGK2X7FFZC5BCYF2BPSSF, 01KYTJGK2XSA2C4H72SKP8F34D, 01KYTJGK2XMY73EJMZ026Q573G, 01KYTJGK2XYHW1BT3Y1XH1YNP7, 01KYTJGK2XDQVAZ85ZEH92NGGW, 01KYTJGK2XJSCMJ9K16YDXXMD2, 01KYTJGK2X7FC4PTAMH60ECY36, 01KYTJGK2X700NYTZHB0JDE6Q1, 01KYTJGK2X98H9T7VVR879B0XC]
---

# Close both P1 epics, settle the merge-strategy and GONE questions

## Context

The 2026-07-30 bug sweep cleared every defect in the tracker: twelve fixed, backlog 22
open items down to 11, zero bugs remaining. What survived is eleven feature and ops items
plus two design questions that were left open deliberately, because answering them needed
research rather than a guess.

That research is done, and it moved three decisions.

**An event-aware merge driver is not worth building.** The work log is declared
`merge=union` in `.gitattributes`, and git's union driver keeps every line from both
sides, so a branch spanning a compaction resurrects the removed events. The obvious fix is
a purpose-built driver that dedupes by event id and honors compaction watermarks. It does
not survive contact with how merges actually happen here. Hosted platforms run no merge
driver server-side, which the spec already records as a known consequence and which was
discovered the hard way merging an earlier pull request. A driver would therefore leave
the most common merge path — the button on the pull request — exactly as exposed as it is
today. It is also silently optional: the attribute travels in the repository but the
driver registration is per-clone configuration, so a developer who has not run the
installer gets git's default text merge, which is worse than union because it writes
conflict markers into a file that must stay machine-readable. Finally, the reader already
provides the guarantee the driver would add. Folding deduplicates by event id before
sorting, and every operation is idempotent under duplication.

**The real exposure is that the guard shipped for the resurrection bug only runs on a
developer's machine.** It is gated on a merge being in progress, which is never true in a
continuous-integration checkout, and its test file was never added to the integration test
list. So the protection that was just built has no automated coverage at all. Closing that
gap is cheap and is worth more than the driver would have been.

**Clearing a dead ticket link cannot be automated.** When the tracker reports a ticket
gone, the adapter contract says to clear the item's link so it can be filed afresh. The
signal that says "gone" is a substring match against the command-line tool's error text,
matching not-found, 404, and could-not-resolve. The hosting platform returns 404 rather
than 403 for a repository you are not allowed to see, so that one signal conflates a
deleted ticket, a permissions failure, a renamed repository, and some name-resolution
failures. A single mistyped project setting would mark every linked item in the repository
as gone in one run. No confirmation count makes that safe, because the failure repeats
identically on every attempt. A second hazard confirms it: clearing a link does not touch
the remote side, so the marker that ties a ticket to an item survives, and a later pull can
re-attribute the old ticket to the same item — which is the duplicate-filing path the
original report warned about.

**The information-architecture phase-five item is a container, not a task.** Its own plan
decomposed every earlier phase into two or three children; this one stayed single only
because it was last. It bundles a six-line promotion of three warning gates to hard
failures, which the design documents rank first on the extension roadmap, with a
speculative rendering port to three wiki platforms that no one uses — the configuration
names the hosted wiki this project actually publishes to. Splitting it lets the parent epic
close on the value that shipped, instead of being held open by work nobody has planned.

## Approach

Two epics are each blocked on exactly one open leaf, so each closes for the price of one
item. Do those first, because they convert the largest amount of open bookkeeping into
closed bookkeeping.

The pull-request metadata command comes first. Pull request pages currently render their
state and changed files as not tracked, because nothing in the repository fetches that
data. The fix must not break the invariant that rendering is a pure function of committed
files, since a freshness check regenerates and compares bytes; a network call inside
rendering would make that check depend on mutable remote state. The split that preserves
it is the same shape the existing link command already uses: a new command performs the
network call and writes a sidecar file, and the renderer reads that committed sidecar off
disk.

The gate promotion comes second. Three of the four warnings become hard failures; the
fourth is deliberately excluded, because its own comment says it stays advisory forever and
runs strictly only at release. Continuous integration runs the same hook script, so
promotion takes effect there with no workflow change. The sandbox repositories built by two
integration tests assert that the hook exits cleanly, so they must be verified clean before
promotion rather than after.

The two decisions are then recorded as architecture decision records, which this repository
already has tooling and enforced structure for. The merge-strategy record supersedes rather
than edits the existing one, because an accepted record's body is written once. Alongside
each record goes the small amount of code that actually reduces risk: running the merge
guard in continuous integration, and making a repository-level failure abort the run
instead of condemning every item in it.

Everything else is either cheap enough to fold in if time allows, or deferred with a stated
reason. The configurable field model is deferred hardest: it would make the canonical item
hash depend on configuration, which breaks change detection across clones that disagree,
and it needs a nested configuration block in a project that has no configuration parser and
a documented aversion to knobs.

## Verification

The suite must stay green at 355 or more tests, and coverage must hold above the 80 percent
floor measured the way continuous integration measures it, which is subprocess-aware and
combined across runs rather than a single naive run. The promoted gates must pass cleanly
when the hook is run directly. A sync dry run should report no drift beyond the structural
note that dependencies have no field on the tracker. Re-rendering the roadmap should produce
no diff, proving it was already current. Finally the item list should show both epics gone
and no open bugs.

## Tasks

- [ ] (P2) Run the log merge guard in continuous integration
      The guard added for the resurrection bug is gated on a merge being in progress, which
      is never true in a continuous-integration checkout, so it protects only developer
      machines today. Give the workflow a path that exercises it, so a branch that would
      resurrect compacted-away events fails the build rather than depending on whoever
      happens to merge locally.
- [ ] (P2) Add the merge-guard tests to the integration test list
      The test file that covers both merge guards was never added to the workflow's test
      list, so the protection built for them has no automated coverage. It builds real
      throwaway repositories and runs real merges, so it belongs in the integration step
      rather than the fast one.
- [ ] (P1) Record the decision that clearing a dead ticket link stays manual
      Write the architecture decision record explaining why automation is unsafe: the gone
      signal is a substring match that cannot separate a deleted ticket from one you lack
      permission to read, and clearing a link leaves the remote marker in place so a later
      pull can re-attribute the old ticket. State plainly in the consequences if the two
      cases cannot be told apart, rather than implying a precision the signal does not have.
- [ ] (P2) Abort the run when the whole project is unreachable
      A failure to resolve the project itself produces the same gone signal as a single
      missing ticket, once per item, so one mistyped project setting would mark every linked
      item gone in a single run. Detect the project-level case and stop the run the way an
      authentication failure already does.
- [ ] (P3) Forget the gone marker once a ticket answers again
      The marker recording that a ticket was reported missing is written but never cleared;
      it is only outgrown when the key itself changes. A ticket restored from the trash stays
      skipped forever. Clear it when a later push to the same key succeeds.
- [ ] (P2) Record the decision not to build a custom merge driver
      Supersede the existing record rather than editing it, since an accepted record's body
      is written once. Capture the three findings: hosted merges run no driver, an
      unconfigured driver is silently ignored and falls back to something worse than union,
      and the reader already deduplicates by event id. Note which of the two merge guards
      protects correctness and which only protects file size, so nobody mistakes the second
      for data protection.
- [ ] (P3) Split the phase-five container into a new epic
      Close the container on the gate promotion and refile what remains: the rendering
      adapter seam, one item per wiki platform to be filed only when that platform has a
      user, the document search command, and the optional glossary. Prefer dropping the
      glossary as speculative; its own plan marks it optional.
- [ ] (P2) Fix the fused version fence in every shipped skill
      Each shipped skill's front matter runs the version straight into the closing fence with
      no newline between them, so the block is malformed. The lockstep test passes only
      because it splits on the fence marker and never notices. Whatever stamps the version is
      doing a naive rewrite; fix the stamping, not just the files.
- [ ] (P2) Bring skill copies under the byte-for-byte sync check
      Skills exist as two unlinked copies, shipped and development-local, and they have
      already drifted in both directions: one carries a pre-release gate the other lacks, the
      other carries a release note the first lacks. The sync check covers scripts and hooks
      but not skills, so nothing fails when they diverge.
- [ ] (P3) Expose the two item fields the specification already declares
      Estimate and dependencies are normative in the specification, and the roadmap renderer
      already reads dependencies to compute blockers, but neither can be set from the command
      line. This is the small, uncontroversial part of the configurable field model and should
      be split out of it rather than waiting on that design.
- [ ] (P3) Remove the unreachable sort tiebreak in the fold
      Deduplication by event id happens before the sort, so the secondary sort key can never
      be reached. It is harmless but advertises a guarantee that is not doing anything, which
      is worse than silence in code this load-bearing.
