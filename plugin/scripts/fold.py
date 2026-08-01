#!/usr/bin/env python3
"""
fold.py -- derive work item state from the append-only event log.

Reference implementation of WORKLOG-SPEC section 6.

State is a fold over events. Nothing here writes. The log is the truth; this
file is the only thing allowed to decide what it means.

Read section 6 before changing anything in here. In particular:
  - Order is by `ev`, never by file position and never by `ts`.
  - A corrupt line is skipped, never fatal.
  - `close` takes its status from `set`, it does not assume "done".
  - A later write to a field clears earlier recorded conflicts on that field
    (section 10.6); a conflict recorded after the write stays open.

Taxonomy migration (docs/plans/2026-07-18-work-taxonomy.md section 3.2): the
legacy single `type` field is a deprecated alias. On create/snapshot the fold
maps it into (`level`, `kind`) and drops `type` from the ITEM (the event line
is never touched). A create carrying neither type nor kind folds to
kind:triage -- unclassified must look unclassified (section 2.3); that
default is applied on `create` only, never on `snapshot` -- a snapshot must
be a lossless round-trip of the state it was given (WORKLOG-SPEC section 7
step 7), and defaulting there would fabricate taxonomy for items that were
never created in the first place (e.g. a closed orphan). This is LENIENT by
design: the fold never crashes on a bad pair; hard validation lives at write
time (CLI) and in the hook/CI check.
"""

import json
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

SET_VALUED = ("labels", "depends_on")
OPEN_STATUSES = ("todo", "in_progress", "blocked")
CLOSED_STATUSES = ("done", "cancelled")

# Legacy `type` -> (level, kind). Spec 2026-07-18-work-taxonomy section 3.2.
LEGACY_TYPE_MAP = {
    "epic": ("epic", "feature"),
    "story": ("story", "feature"),
    "task": ("task", "feature"),
    "subtask": ("subtask", "feature"),
    "bug": ("task", "bug"),
}


def _normalize_taxonomy(item: Dict[str, Any], defaults: bool = True) -> None:
    """Normalize a freshly created/snapshotted item to the (level, kind) model.

    Lenient: unknown legacy types just fall through. Never raises.

    `defaults` controls whether a MISSING level/kind gets defaulted to
    task/triage (spec 2.3: an unclassified create must still fold to
    something). Only `create` wants that -- it is the one place a genuinely
    new, never-before-seen item enters the fold. `snapshot` must stay a
    lossless round-trip of whatever state it was given (compact.py writes
    the folded state verbatim, WORKLOG-SPEC section 7 step 7): a snapshot of
    an item that was itself never created (e.g. a closed orphan -- link/close
    events for an id with no matching create) has no level/kind to begin
    with, and re-fabricating defaults for it on every re-fold makes
    compaction a non-idempotent transform and fails its own verify step.
    Legacy `type` mapping still runs either way; that's real migrated data,
    not an invented default.
    """
    t = item.pop("type", None)
    if t in LEGACY_TYPE_MAP and "level" not in item and "kind" not in item:
        item["level"], item["kind"] = LEGACY_TYPE_MAP[t]
    if defaults:
        item.setdefault("level", "task")
        item.setdefault("kind", "triage")


class FoldResult:
    def __init__(self) -> None:
        self.items: Dict[str, Dict[str, Any]] = {}
        self.watermark: Optional[str] = None
        self.errors: List[str] = []
        self.orphans: List[str] = []
        self.skipped: int = 0
        self.deduped: int = 0

    def open_items(self) -> List[Dict[str, Any]]:
        return [i for i in self.items.values() if i.get("status") in OPEN_STATUSES]

    def closed_items(self) -> List[Dict[str, Any]]:
        return [i for i in self.items.values() if i.get("status") in CLOSED_STATUSES]

    def conflicts(self) -> List[Tuple[str, Dict[str, Any]]]:
        out = []
        for iid, item in self.items.items():
            for c in item.get("_conflicts", []):
                out.append((iid, c))
        return out


def external_owners(items: Iterable[Dict[str, Any]]) -> Dict[Tuple[Any, str], List[str]]:
    """(system, key) -> sorted ids of every item claiming that remote ticket.

    One remote ticket has exactly one local owner. Two owners and every sync
    overwrites the ticket with whichever item changed last: the correctly
    linked item is hash-clean so it is skipped forever and never repairs the
    damage, while the wrong one keeps re-pushing (github#226).

    Not a violation of spec section 9.2's "never key on external.key" -- that
    rule is about IDENTITY, and the ULID is still the only primary key; no
    lookup here is ever done by external key. This is a uniqueness constraint
    on a nullable secondary attribute.

    (system, key), never key alone: ado:294 and github:294 are unrelated
    tickets, and a mid-migration repo legitimately holds both. str() the key
    because adapters return ints -- 294 must not be a different ticket from
    "294".

    Returns every owner, not just the duplicates: `link` needs "who else owns
    this", `sync` needs "which keys have more than one". One filter each.
    """
    owners: Dict[Tuple[Any, str], List[str]] = {}
    for i in items:
        ext = i.get("external") or {}
        if ext.get("key"):
            owners.setdefault((ext.get("system"), str(ext["key"])), []).append(i["id"])
    return {k: sorted(v) for k, v in owners.items()}


def read_lines(paths: Iterable[str], result: FoldResult) -> List[Dict[str, Any]]:
    """Step 1: parse. A bad line is reported and skipped -- never fatal.

    A single corrupt line must not prevent reading the rest of the log. This is
    not defensive politeness: union merge (section 8.1) plus a missing trailing
    newline can fuse two valid lines into one invalid one, and that must cost
    two events, not the entire history.
    """
    events: List[Dict[str, Any]] = []
    for path in paths:
        try:
            fh = open(path, "r", encoding="utf-8")
        except FileNotFoundError:
            continue
        with fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError as e:
                    result.errors.append(f"{path}:{lineno}: unparseable: {e}")
                    result.skipped += 1
                    continue
                if not isinstance(ev, dict) or "ev" not in ev or "op" not in ev:
                    result.errors.append(f"{path}:{lineno}: missing ev/op")
                    result.skipped += 1
                    continue
                if ev["op"] != "compact" and "item" not in ev:
                    result.errors.append(f"{path}:{lineno}: missing item")
                    result.skipped += 1
                    continue
                ev["_line"] = line.strip()
                events.append(ev)
    return events


def dedupe_and_sort(events: List[Dict[str, Any]], result: FoldResult) -> List[Dict[str, Any]]:
    """Steps 2 and 3: dedupe by `ev`, then sort by `ev`.

    Union merge duplicates lines and scrambles their order, so both of these are
    load-bearing. ULIDs sort lexicographically by time, so this is a string sort.

    `ev` alone is a total order here, and deliberately: dedupe runs FIRST and is
    keyed on `ev`, so no two events reaching the sort can share one. This used
    to carry an (actor, line-hash) tiebreak for determinism across machines --
    unreachable by construction, and worse than silence, because it advertised
    a guarantee that came from the dedupe above it (worklog#259).
    """
    seen: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        key = ev["ev"]
        if key in seen:
            result.deduped += 1
            continue
        seen[key] = ev
    return sorted(seen.values(), key=position)


def position(ev: Dict[str, Any]) -> Tuple[str, int]:
    """Where an event applies in the fold. Identity is still `ev`; this is
    only ordering.

    A snapshot applies where the events it folded were -- at its `through` --
    not at the moment the compactor happened to write it (#284). The
    compactor mints the snapshot's own `ev` at compaction time, so it sorts
    above everything; a branch that closed an item before that compaction ran
    would then have its close applied FIRST and immediately overwritten by
    the snapshot, because a snapshot replaces state entirely. The work
    vanished even though the event was still in the log.

    Ordering by `through` puts the snapshot back where it belongs: after the
    events it folded, before anything that happened later on any branch.

    The second element keeps a snapshot ahead of a same-positioned ordinary
    event, so the later event wins rather than being replaced. Legacy
    snapshots carry no `through` and fall back to their own `ev`, which is
    exactly how they sorted before.
    """
    if ev.get("op") == "snapshot" and ev.get("through"):
        return (ev["through"], 0)
    return (ev["ev"], 1)


def apply_watermark(events: List[Dict[str, Any]], result: FoldResult) -> List[Dict[str, Any]]:
    """Step 4: drop everything the compactor already folded into a snapshot.

    Snapshots are exempt -- they carry the state those events produced.

    The rule is PER ITEM, and that is the whole point (#284). The global
    watermark this used to apply was `max_ev` over the log the compaction
    read -- a TIME marker being used as a CONTENT marker. An event created on
    a branch before a compaction ran on main was never folded into any
    snapshot, yet still sorted below that global mark, so merging the branch
    back silently discarded it. Reproduced deterministically; the live
    2026-07-31 incident carried three such events and they survived only
    because the merge guard blocked and a human re-applied them by hand.

    Two rules replace it:

      - An item with NO snapshot never has events dropped. Nothing folded
        them, so nothing carries their state. This is compaction's own
        "never drop data" principle (spec 7 step 3) applied on the read side.
      - An item WITH a snapshot drops only its own events at/below that
        snapshot's `through` -- the highest ev the compactor actually folded
        for that item.

    Legacy logs whose snapshots predate `through` fall back to the global
    mark, so an un-upgraded log still folds exactly as it did before. The
    no-snapshot rule applies to them too, because it can only ever restore
    data.
    """
    marks = [e.get("through") for e in events if e["op"] == "compact" and e.get("through")]
    result.watermark = max(marks) if marks else None

    # item -> highest ev its snapshots claim to have folded. A union merge can
    # leave two snapshots for one item; the later compaction's is the truth.
    covered: Dict[str, str] = {}
    for e in events:
        if e["op"] != "snapshot":
            continue
        through = e.get("through")
        if through and through > covered.get(e["item"], ""):
            covered[e["item"]] = through
    snapshotted = {e["item"] for e in events if e["op"] == "snapshot"}

    kept = []
    for e in events:
        if e["op"] == "compact":
            continue
        if e["op"] == "snapshot":
            kept.append(e)
            continue
        iid = e.get("item")
        if iid not in snapshotted:
            kept.append(e)          # nothing folded it; never drop it
            continue
        limit = covered.get(iid) or result.watermark
        if limit is None or e["ev"] > limit:
            kept.append(e)
    return kept


def _apply_mutations(item: Dict[str, Any], ev: Dict[str, Any]) -> None:
    """Per-field last-writer-wins. Order is `del` then `add` then `set`.

    Set-valued fields use add/del so two devs adding different labels on
    different branches don't clobber each other (section 5.5).
    """
    for field, values in (ev.get("del") or {}).items():
        current = item.get(field) or []
        item[field] = [v for v in current if v not in values]
    for field, values in (ev.get("add") or {}).items():
        current = list(item.get(field) or [])
        for v in values:
            if v not in current:
                current.append(v)
        item[field] = current
    for field, value in (ev.get("set") or {}).items():
        item[field] = value
    # Section 10.6: writing a field resolves any earlier recorded conflict on
    # it. Events apply in `ev` order, so a conflict recorded AFTER this write
    # stays open. Snapshots start from a fresh dict, which drops conflicts too.
    if item.get("_conflicts"):
        written = {f for k in ("set", "add", "del") for f in (ev.get(k) or {})}
        remaining = [c for c in item["_conflicts"] if c.get("field") not in written]
        if remaining:
            item["_conflicts"] = remaining
        else:
            del item["_conflicts"]


def fold(paths: Iterable[str] = ("todo.jsonl", "done.jsonl")) -> FoldResult:
    result = FoldResult()
    events = apply_watermark(dedupe_and_sort(read_lines(paths, result), result), result)

    for ev in events:
        iid, op = ev["item"], ev["op"]
        known = iid in result.items

        if op == "snapshot":
            # Replaces state entirely -- it IS the fold of everything below the
            # watermark. Never merge into what's already there.
            item = {"id": iid}
            _apply_mutations(item, ev)
            _normalize_taxonomy(item, defaults=False)
            result.items[iid] = item
            continue

        if op == "create":
            if known:
                # Duplicate create for one item: keep the earlier, treat as update.
                _apply_mutations(result.items[iid], ev)
                continue
            item = {"id": iid}
            _apply_mutations(item, ev)
            _normalize_taxonomy(item)
            result.items[iid] = item
            continue

        if not known:
            # Step 6: an event for an item with no create/snapshot. Legitimate
            # mid-rebase. Report it; never crash, never silently invent an item.
            result.orphans.append(iid)
            result.items[iid] = {"id": iid, "_orphan": True}

        item = result.items[iid]

        if op == "conflict":
            item.setdefault("_conflicts", []).append(ev.get("set") or {})
            continue  # records disagreement; changes no state

        if op == "close":
            # Status comes from `set`. A cancelled item is cancelled, not done --
            # assuming "done" here silently reports abandoned work as shipped.
            _apply_mutations(item, ev)
            if item.get("status") not in CLOSED_STATUSES:
                item["status"] = "done"
            continue

        if op == "reopen":
            _apply_mutations(item, ev)
            if item.get("status") in CLOSED_STATUSES or "status" not in item:
                item["status"] = "todo"
            item.pop("resolution", None)
            continue

        # update, link
        _apply_mutations(item, ev)

    return result


def main(argv: List[str]) -> int:
    paths = argv[1:] or [".work/todo.jsonl", ".work/done.jsonl"]
    r = fold(paths)
    for e in r.errors:
        print(f"warn: {e}", file=sys.stderr)
    if r.orphans:
        print(f"warn: {len(r.orphans)} orphan item(s): {sorted(set(r.orphans))}", file=sys.stderr)
    print(json.dumps(sorted(r.items.values(), key=lambda i: i["id"]), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
