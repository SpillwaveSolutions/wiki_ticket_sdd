---
id: 6
slug: resurrected-events-are-not-always-cosmet
title: Resurrected events are not always cosmetic
date: 2026-08-01
status: accepted
deciders: [rick, claude]
tags: [core, git]
wiki_key: adr/0006-resurrected-events-are-not-always-cosmet
truth_state: current
---

# ADR-0006: Resurrected events are not always cosmetic

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

ADR-0005 settled the merge-driver question and, in doing so, classified the
two merge guards by severity. It called `check_resurrection` a **hygiene**
guard on this reasoning: "the fold discards resurrected events on read, so no
state is ever corrupted — only the size win from compaction is lost."

That claim is true for the events it was reasoned about, and false in general.
It holds for an event the compaction actually folded: the snapshot carries the
state that event produced, so discarding the raw line loses nothing. It does
not hold for an event the compaction never saw.

`fold.apply_watermark` drops every non-snapshot event whose `ev` sorts at or
below the watermark. The watermark is `max_ev` over the log the compaction
read — a **time** marker being used as a **content** marker. An event created
on a branch before a compaction ran on main is not in that log, so no snapshot
carries its state, yet it still sorts below the watermark. Merging the branch
back makes the fold discard it. The work is gone, with no error.

This was reproduced deterministically while fixing #269: an item created on a
branch is absent from the fold entirely after the merge. It is not
hypothetical history either. The live 2026-07-31 incident that prompted
ADR-0005 carried exactly three such events (an `in_progress`, and two closes,
including an epic). They survived only because the guard blocked the merge and
the resolution was done by hand.

## Decision

`check_resurrection` is a **correctness** guard, not a hygiene guard, and it
keeps blocking the merge commit.

The severity classification in ADR-0005's first consequence is superseded by
this record. Nothing else in ADR-0005 changes: union merge stays, no custom
merge driver, and its three findings all still hold.

Two things follow directly, and both shipped with #269:

**The guard may not be demoted to a warning.** It is the only thing standing
between this class and silent data loss. Demoting it — which the "hygiene"
label invites, and which was actively considered — would let the loss through
on exactly the path the guard was built for.

**Recompaction is not a valid remedy and was never a safe one.** The advice
the guard used to print could not be run from the state it created, which is
what #269 reported. The deeper problem is that it would have been wrong even
if it had run: compaction verifies `fold(new) == fold(old)`, and the fold has
already discarded the branch's sub-watermark events by the time that check
runs. It would have passed, and made the loss permanent. The guard is replaced
by `worklog merge-rescue`, which keeps the compacted side's log and re-emits
this branch's own events above the watermark — the manual 2026-07-31
resolution, mechanised, with a verification step that refuses to write if any
item would disappear.

## Consequences

- The distinction ADR-0005 drew between the two guards is real but was drawn
  in the wrong place. Both are correctness guards. They differ in what they
  protect: `check_duplicate_ownership` protects a remote ticket from
  divergent local owners, `check_resurrection` protects unmerged branch work
  from the watermark rule.

- The watermark rule itself is still unsound, and `merge-rescue` is a repair
  at merge time rather than a fix. The guard catches every instance today, so
  nothing is lost in practice, but correctness depends on a hook that the
  ADR-0005 consequences already note never fires in CI. Tracked as its own
  item; the real fix changes what a compaction records about the events it
  folded, which is a spec change to section 7 and deliberately not made here.

- Anything that reasons about "is this event already represented" needs the
  merge base, not the watermark. `merge-rescue` uses it: compaction ran on a
  descendant of the base, so every event in the base was folded and is safe
  to drop, and anything on the other side but absent from the base was not.
  That test is precise where the watermark comparison is merely a heuristic.

- `ulid.new()` has no intra-millisecond counter, so ULIDs minted in the same
  millisecond sort by their random bytes. Any code re-emitting a sequence of
  events must hand in explicit increasing timestamps or it will scramble their
  order. `merge-rescue` does; this bit the reproduction harness first.

## Alternatives

- **Leave the classification alone and only fix the printed message** — what
  #269 literally asked for. Rejected: the message was a symptom. The label is
  what would have caused the next person to remove the guard, and the same
  reasoning had already been written down as settled.

- **Fix the watermark rule now** (record the folded event ids, or make the
  watermark per-item) — the actual fix, and deliberately deferred rather than
  rejected. It changes the compaction record format, which is a spec change
  to section 7 and wants its own decision. The guard plus `merge-rescue`
  closes the operational hole in the meantime.

- **Teach compaction to run during a merge**, the other option #269 offered —
  rejected outright now that the mechanism is understood. It would verify
  against an already-lossy fold and cement the loss.
