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
"""

import hashlib
import json
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

SET_VALUED = ("labels", "depends_on")
OPEN_STATUSES = ("todo", "in_progress", "blocked")
CLOSED_STATUSES = ("done", "cancelled")


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
    Ties break on actor then line hash, which makes the result identical on every
    machine -- two devs folding the same log must get the same answer.
    """
    seen: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        key = ev["ev"]
        if key in seen:
            result.deduped += 1
            continue
        seen[key] = ev
    return sorted(
        seen.values(),
        key=lambda e: (
            e["ev"],
            e.get("actor", ""),
            hashlib.sha256(e["_line"].encode()).hexdigest(),
        ),
    )


def apply_watermark(events: List[Dict[str, Any]], result: FoldResult) -> List[Dict[str, Any]]:
    """Step 4: drop everything the compactor already folded into a snapshot.

    Snapshots are exempt -- they carry the state those events produced.
    """
    marks = [e.get("through") for e in events if e["op"] == "compact" and e.get("through")]
    if not marks:
        return [e for e in events if e["op"] != "compact"]
    result.watermark = max(marks)
    return [
        e
        for e in events
        if e["op"] != "compact" and (e["op"] == "snapshot" or e["ev"] > result.watermark)
    ]


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
            result.items[iid] = item
            continue

        if op == "create":
            if known:
                # Duplicate create for one item: keep the earlier, treat as update.
                _apply_mutations(result.items[iid], ev)
                continue
            item = {"id": iid}
            _apply_mutations(item, ev)
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
