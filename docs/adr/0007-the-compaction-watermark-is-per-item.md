---
id: 7
slug: the-compaction-watermark-is-per-item
title: The compaction watermark is per item
date: 2026-08-01
status: accepted
deciders: [rick, claude]
tags: [core, git]
wiki_key: adr/0007-the-compaction-watermark-is-per-item
truth_state: current
---

# ADR-0007: The compaction watermark is per item

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

ADR-0006 established that resurrected events are not always cosmetic, and
left the underlying cause open: the fold dropped every non-snapshot event
sorting at or below **one** watermark, computed as `max_ev` over the whole
log a compaction read. That is a *time* marker doing a *content* marker's
job. An event created on a branch before a compaction ran on main was never
folded into any snapshot, yet still sorted below that global mark, so merging
the branch back discarded it silently.

ADR-0006 deferred the fix on the grounds that it changes what a compaction
records — a WORKLOG-SPEC §7 format change deserving its own decision. This is
that decision.

Implementing it surfaced a second, independent mechanism with the same
symptom. A snapshot's own `ev` is minted at compaction time, so it sorts
above everything that came before it. Because a snapshot *replaces* item
state entirely, a branch event that legitimately survived the watermark could
still be applied first and then immediately overwritten by the snapshot. The
event was in the log, was not dropped, and still had no effect. A test caught
this: fixing only the watermark would have left half the bug in place,
passing its own regression test and looking fixed.

## Decision

**Compaction records a per-item mark, and snapshots sort where their events
were.**

Three changes, all of them required:

1. **`_snapshot` carries `through`** — the highest `ev` this compaction
   actually folded *for that item*. Top-level on the event, never inside
   `set`, so it can never become item state or reach compaction's own
   `fold(new) == fold(old)` verification.

2. **`apply_watermark` drops per item.** An item with **no** snapshot never
   has events dropped: nothing folded them, so nothing carries their state.
   This is compaction's own "never drop data" rule (§7 step 3) applied on the
   read side. An item **with** a snapshot drops only its own events at or
   below that snapshot's `through`.

3. **A snapshot sorts at its `through`, not at its `ev`** (`fold.position`).
   Identity is still `ev` and dedupe is still keyed on it; only ordering
   changes. This puts the snapshot back where it belongs — after the events
   it folded, before anything that happened later on any branch — so a
   branch's later close applies *on top of* the snapshot instead of being
   erased by it.

Legacy logs fold exactly as before: snapshots predating `through` fall back
to the global mark, and to their own `ev` for ordering. The no-snapshot rule
applies to them too, because it can only ever restore data.

## Consequences

- **The class is closed, not narrowed.** Both the reproduced case (an item
  created on a branch vanishing entirely) and the shape of the live
  2026-07-31 incident (closes on items main had snapshotted) now survive a
  merge. The test that pinned the data loss said in its own failure message
  that it should become the regression test for the fix; it now asserts the
  opposite, and says why.

- **`check_resurrection` is a hygiene guard again** — what ADR-0005
  originally claimed and ADR-0006 corrected *for the code as it then stood*.
  Both records were right about their own moment, which is why neither is
  superseded. It now asks the narrower, truthful question — would the fold
  actually drop this line? — so a resurrected event for an unsnapshotted item
  is no longer flagged, because it survives and warning about it would be
  crying wolf.

- **The guard keeps blocking the merge commit anyway**, and not for data
  loss. A branch's edits to an item that main has since snapshotted still
  need re-emitting *above* that snapshot to take effect, and `worklog
  merge-rescue` is the only thing that does it. Blocking is what routes
  people to that command. The printed message now says exactly that, rather
  than implying state is at risk.

- **Compaction stays gated on `fold(new) == fold(old)`.** That equality, not
  any watermark, is still what makes compaction safe, and it now runs against
  the corrected fold.

- **Nothing about the log format is breaking.** `through` is an added field
  on an existing op; an un-upgraded reader ignores it and applies the old
  global rule, which is strictly more conservative and never invents state.

## Alternatives

- **Record the exact set of folded event ids** in the compact line —
  precise, and the first thing considered. Rejected on size: that set is
  every event the compaction just removed, so the record grows to roughly the
  size of the log being compacted, which defeats the operation.

- **Per-item mark only, leaving snapshot ordering alone** — what the first
  implementation did. Rejected once a test proved a branch's close was still
  overwritten by the snapshot.

- **Give a snapshot the `ev` of its `through`**, so ordering falls out
  naturally — rejected: `ev` is identity and dedupe is keyed on it, so the
  snapshot would collide with the very event it replaced. Ordering had to be
  separated from identity instead.

- **Vector clocks or per-item versions** — the general answer to "these two
  events are concurrent, not ordered". Rejected as far larger than the
  problem: ULID ordering plus per-item marks covers every case this system
  has produced, and the merge guard catches the rest.
