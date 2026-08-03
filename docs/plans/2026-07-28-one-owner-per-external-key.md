---
date: 2026-07-28
slug: one-owner-per-external-key
title: One local owner per remote ticket (#226)
epic: 01KYND4SNNVYRAEQ958HK83W72
items: [01KYND4SNNCPZ7R2NWFD7QXYTJ, 01KYND4SNPF2DYKSMDG4NJ39CF, 01KYND4SNPXVR1W4GQA453VB4G, 01KYND4SNP68XAJ30Q4PY4VV11, 01KYND4SNPH307DFDEE9BJ0ZZ4, 01KYND4SNPG1HFE8E0P7F7K7PF, 01KYND4SNPBAW2A1H0GPHDGT0E]
merged_in: 830c827050171da1eed9fc0497dfb1907f2c0ed4
---

# One local owner per remote ticket (#226)

## Context

Issue #226 reports live data corruption. Two local work items were allowed to own
the same external ticket key (`ado:294`). `worklog sync` pushed both, last writer
won, and a cancelled duplicate marked a live P0 stakeholder-gating ticket **Done**.
Hand-repairing the ticket did not hold — the next sync rewrote the damage, twice.
There is no `worklog unlink`, so the triggering `link` could not be undone through
supported commands; the reporter had to create throwaway ADO items to give the
duplicates somewhere else to point.

The failure is invisible from the log side. `worklog fold` shows two items, each
with a perfectly valid `external` block. Only querying the tracker reveals it.

Root cause: `external.key` is a foreign key into someone else's database and
**nothing ever asserted it was unique**. `cmd_link` has zero validation, and
`.work/sync-state.json` is keyed by ULID only, so two owners get two independent,
both-satisfiable `last_pushed_hash` slots. Neither can ever notice the other. Sync
then pushes per-item deltas: the correctly-linked item is hash-clean so it is
skipped forever and never repairs the ticket, while the wrong one keeps
re-pushing. The system converges on the wrong value.

Three findings from reading the code changed the shape of the fix:

1. **`external` is not in `HASH_FIELDS`** (`bin/canonical.py:17-18`). Unlinking or
   re-linking never makes an item dirty, so repairing the *log* does not repair the
   *tracker* — the good item stays hash-clean and the ticket stays `Done`.
2. **The closed-item branch is separate code** (`sync_dispatch.py:328-384`) from
   the open create/update path (`:386`). A guard placed at the
   `op = "update" if ext.get("key")` discriminator would miss the
   dirty-update-then-close path — the exact one that marked the ticket Done.
3. **Auto-link after a create is `fatal=True`** (`:361`, `:412`). A naive guard
   there aborts sync *between* "remote ticket created" and "link recorded"; on the
   next run the item has no `external.key`, so the discriminator says **create** and
   files a second live ticket. The obvious fix causes a worse bug than the one it
   fixes.

## Decisions

- Sync **skips the colliding items and exits 1** rather than refusing the whole
  run. Corruption requires *both* claimants to be pushed, so skipping removes the
  path entirely; meanwhile the other items still sync and pull still works, which
  is what you want while repairing. The collision prints as its own block, not as a
  `drift:` line — drift is what operators skim, and burying it there would
  reproduce the original silent-failure mode in a new costume.
- Sync tracks **`last_pushed_key`** alongside `last_pushed_hash`, guarded so clones
  that have never stored a key do not see every item go dirty at once.
- The `link` guard is **status-blind**. A cancelled item with a key is one of the
  *most* dangerous owners, because sync pushes a full update against its key and
  then closes the ticket. A guard that only looked at open items would wave through
  the same bug with the two commands reordered.
- Identity is **`(system, key)`**, not bare `key`: `ado:294` and `github:294` are
  unrelated tickets, and a mid-migration repo legitimately holds both.
- **`unlink` writes `external: {}`, never `null`**, and reuses the existing `link`
  op — the fold already applies whole-field last-writer-wins, so no new op is
  needed and an un-upgraded clone folds the retraction correctly too.

On the spec tension: `docs/worklog-spec.md:271` says "never key on `external.key`".
That rule is about *identity* — the ULID stays the primary key and no lookup is
ever done by external key. This is a uniqueness constraint on a nullable secondary
attribute, which is a different thing. Worth saying once in the spec so the next
reader does not "fix" it back.

## Tasks

- [ ] (P1) Add an external-key ownership map to the fold
  One shared helper that answers "which items claim this remote ticket", so the
  link command and the sync dispatcher enforce the same rule from the same place
  instead of each growing its own copy.
- [ ] (P1) Refuse a duplicate external key when linking
  Linking an item to a ticket another item already owns is the mistake that causes
  the corruption. Refuse it, name the other item and its title so the operator can
  see instantly which one is real, and print the two commands that move the ticket
  deliberately.
- [ ] (P1) Add a command to undo a link
  A mistaken link is currently impossible to undo through supported commands, which
  is a sharp edge in a log designed so that mistakes are corrected by appending.
  The new command retracts the link and warns that the ticket itself may still
  carry a marker that has to be cleaned up in the tracker.
- [ ] (P1) Stop sync from pushing a ticket that two items claim
  Skip every item in a contested set, print a prominent block naming all claimants
  and the exact repair, and exit non-zero so the failure cannot be missed. Healthy
  items in the same run still sync.
- [ ] (P1) Make undoing or moving a link actually re-push
  The change detection only looks at an item's content, so unlinking or re-pointing
  it is silently a no-op and the damaged ticket is never repaired. Record which
  ticket was last pushed and treat a change there as a reason to push again.
- [ ] (P1) Keep sync's automatic linking from ever aborting a run
  Sync records the ticket key right after creating the ticket. If that step can
  fail, the run dies with a ticket created but not recorded, and the next run files
  a second one. That step must always succeed and never stop the run.
- [ ] (P2) Update the mirrored copies, the docs and the changelog
  The command scripts ship in two places that must stay byte-identical. Document
  the new command and the one-owner rule, and open the next version's changelog
  section with the version bump in the same commit.

## Testing

Real CLI via subprocess in a throwaway directory, no mocks, matching the existing
suites. The regression test manufactures the duplicate by writing the raw event
into the log, because the new guard makes it unreachable through the CLI — the same
idiom the orphan-item test already uses. Cases that would otherwise be missed:
re-linking the same item to the same key must still succeed (the documented bulk
migration re-runs `link`, and so does sync itself); the same key on a different
system must be allowed; the contested-set skip must cover the closed branch, since
that is the path that marked the ticket Done; and the dry run must also fail, since
"zero creates on a dry run" is the documented migration acceptance gate.

## Out of scope

Filed separately: a merge-time check in the git hooks; the GitHub adapter reading
the issue revision *after* creating the issue (a rate limit there can file up to
four duplicate issues today); `--keys` matching an ambiguous external key;
`conflict`/`resolve` accepting an arbitrary field name; adapter exit 3 not clearing
the external link; the reporter's suggestions 4 and 5 (naming remote overwrites
before they happen, and warning at plan capture when a task title references a
ticket number); and the reporter's contributing factor — two sessions sharing one
working directory.

Not doing at all: a repair or merge command, shared-ownership support, a new fold
op, or a sync-state schema migration.
