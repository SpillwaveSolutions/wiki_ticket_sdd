#!/usr/bin/env python3
"""
compact.py -- rewrite the event logs into snapshots. WORKLOG-SPEC section 7.

The only code allowed to REWRITE .work/*.jsonl (everything else appends).
Runs in CI on main (nightly); `worklog compact --yes` exists for tests and
emergencies.

Spec 7 algorithm, all eight steps:
  1. fold todo+done together (full history -- a reopen needs its done context)
  2. watermark = max ev over every raw input line of both files
  3. partition open vs closed; orphans count as open -- never drop data
  4. rewrite todo.jsonl: one snapshot per open item + a compact watermark line
  5. append to done.jsonl: snapshot per newly-closed item + a watermark line
  6. prune from done.jsonl anything for a currently-open item (stale reopens)
  7. verify fold(new) == fold(old); on any mismatch leave originals untouched
  8. verify trailing newline and that every written line parses

All writes go to temp copies; the real files are only touched by os.replace
after verification passes. Compaction that loses state is the worst failure
mode in this system.
"""
import json
import os
import fcntl
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulid  # noqa: E402
from fold import fold, CLOSED_STATUSES, external_owners  # noqa: E402
from render_roadmap import max_ev  # noqa: E402


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _public(item):
    """Item state minus private _fields -- what a snapshot carries and what
    verification compares for ordinary fields. `_conflicts` is private but
    must still survive compaction: it is recorded as `conflict` events
    above the snapshot, not stuffed into `set`."""
    return {k: v for k, v in item.items() if not k.startswith("_")}


def _conflicts_map(result):
    """Open conflicts per item. Missing and empty are the same (no conflicts)."""
    out = {}
    for iid, item in result.items.items():
        cs = item.get("_conflicts") or []
        if cs:
            out[iid] = cs
    return out


def _conflict_event(item, conflict):
    """Re-emit one open conflict above a snapshot so the fold restores it."""
    ev = {"ev": ulid.new(), "ts": _now(), "actor": "compactor",
          "item": item["id"], "op": "conflict", "set": conflict}
    sha = ulid.git_commit()
    if sha:
        ev["git"] = sha
    return ev


def _item_events(item, through=None):
    """Snapshot plus any open conflicts, in fold order (snapshot, then conflicts)."""
    events = [_snapshot(item, through)]
    for c in item.get("_conflicts") or []:
        events.append(_conflict_event(item, c))
    return events


def _lock_logs(todo_path):
    """Exclusive lock covering compact vs append. Spec §8.3."""
    lock_path = os.path.join(os.path.dirname(os.path.abspath(todo_path)) or ".",
                             ".lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def _snapshot(item, through=None):
    """A snapshot of one item's folded state.

    `through` is the highest ev this compaction actually folded FOR THIS
    ITEM, and it is what the fold drops against (#284). A global mark cannot
    do that job: it is the max over the whole log, so it also covers events
    from branches this compaction never saw, and dropping those loses work.
    Kept top-level rather than inside `set`, so it never becomes item state
    and never reaches the verify comparison.
    """
    snap = {"ev": ulid.new(), "ts": _now(), "actor": "compactor",
            "item": item["id"], "op": "snapshot",
            "set": {k: v for k, v in _public(item).items() if k != "id"}}
    if through:
        snap["through"] = through
    sha = ulid.git_commit()
    if sha:
        snap["git"] = sha
    return snap


def _compact_line(watermark):
    line = {"ev": ulid.new(), "ts": _now(), "actor": "compactor",
            "op": "compact", "through": watermark}
    sha = ulid.git_commit()
    if sha:
        line["git"] = sha
    return line


def _dump(events):
    return "".join(json.dumps(e, separators=(",", ":"), sort_keys=True) + "\n"
                   for e in events)


def _raw_lines(path):
    """[(line, parsed_or_None)] for every non-blank line. Missing file = []."""
    out = []
    try:
        fh = open(path, encoding="utf-8")
    except FileNotFoundError:
        return out
    with fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                out.append((line.rstrip("\n"), json.loads(line)))
            except json.JSONDecodeError:
                out.append((line.rstrip("\n"), None))
    return out


def _git_refuses(paths):
    """True if the logs have uncommitted changes. Compaction must be its own
    commit (spec 7 rule 2). Not inside a git repo -> no objection (tests)."""
    cwd = os.path.dirname(os.path.abspath(paths[0])) or "."
    probe = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           cwd=cwd, capture_output=True)
    if probe.returncode != 0:
        return False
    for p in paths:
        # ponytail: rc 1 = dirty, refuse; rc 128 (no HEAD yet) = can't diff,
        # let it through -- CI always has a HEAD.
        rc = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", os.path.abspath(p)],
            cwd=cwd, capture_output=True).returncode
        if rc == 1:
            return True
    return False


def _verify(before, tmp_todo, tmp_done):
    """Spec 7 steps 7 and 8. Raises SystemExit(1) on any mismatch."""
    after = fold([tmp_todo, tmp_done])
    old = {iid: _public(i) for iid, i in before.items.items()}
    new = {iid: _public(i) for iid, i in after.items.items()}
    if old != new:
        for iid in sorted(set(old) | set(new)):
            if old.get(iid) != new.get(iid):
                print(f"compact: VERIFY FAILED for {iid}\n"
                      f"  before: {json.dumps(old.get(iid), sort_keys=True)}\n"
                      f"  after:  {json.dumps(new.get(iid), sort_keys=True)}",
                      file=sys.stderr)
        print("compact: aborted; logs untouched", file=sys.stderr)
        raise SystemExit(1)
    old_c, new_c = _conflicts_map(before), _conflicts_map(after)
    if old_c != new_c:
        print("compact: VERIFY FAILED: open conflicts were not preserved\n"
              f"  before: {json.dumps(old_c, sort_keys=True)}\n"
              f"  after:  {json.dumps(new_c, sort_keys=True)}",
              file=sys.stderr)
        print("compact: aborted; logs untouched", file=sys.stderr)
        raise SystemExit(1)
    for path in (tmp_todo, tmp_done):
        with open(path, "rb") as fh:
            data = fh.read()
        if data and not data.endswith(b"\n"):
            print(f"compact: {path} missing trailing newline; aborted",
                  file=sys.stderr)
            raise SystemExit(1)
        for line in data.decode("utf-8").splitlines():
            if line.strip():
                json.loads(line)  # unparseable output -> exception -> abort


def compact(todo_path=".work/todo.jsonl", done_path=".work/done.jsonl"):
    """Run one compaction. Returns the watermark ULID, or None on empty logs.
    Raises SystemExit(1) on refusal or failed verification."""
    if _git_refuses([todo_path, done_path]):
        print("compact: uncommitted changes to the logs; commit first "
              "(compaction must be its own commit, spec 7)", file=sys.stderr)
        raise SystemExit(1)

    lock_fd = _lock_logs(todo_path)
    try:
        return _compact_locked(todo_path, done_path)
    finally:
        os.close(lock_fd)


def _compact_locked(todo_path, done_path):
    watermark = max_ev([todo_path, done_path])         # step 2: raw max ev
    if watermark is None:
        return None

    before = fold([todo_path, done_path])              # step 1: full history
    raw_todo = _raw_lines(todo_path)
    idle_ops = ("snapshot", "compact", "conflict")
    if all(e is not None and e.get("op") in idle_ops
           for _line, e in raw_todo):
        return watermark  # nothing new since the last run; don't churn files

    # Highest ev this run actually folded, PER ITEM (#284). Taken from the raw
    # input lines, not from the fold, because it must describe what was read
    # rather than what survived.
    per_item = {}
    for path in (todo_path, done_path):
        for _line, e in _raw_lines(path):
            if e is None or e.get("op") == "compact":
                continue
            iid, ev = e.get("item"), e.get("ev")
            if iid and ev and ev > per_item.get(iid, ""):
                per_item[iid] = ev

    open_items, closed_items = [], []                  # step 3: partition
    for item in sorted(before.items.values(), key=lambda i: i["id"]):
        # Anything not positively closed (incl. orphans) stays open: never
        # drop data.
        (closed_items if item.get("status") in CLOSED_STATUSES
         else open_items).append(item)
    open_ids = {i["id"] for i in open_items}

    # step 4: new todo = open snapshots + open conflicts + watermark
    todo_events = []
    for i in open_items:
        todo_events.extend(_item_events(i, per_item.get(i["id"])))
    todo_text = _dump(todo_events + [_compact_line(watermark)])

    # steps 5+6: new done = old lines minus open items, plus snapshots for
    # newly-closed items not already there with identical state, plus watermark.
    done_state = {iid: _public(i) for iid, i in fold([done_path]).items.items()}
    kept = []
    for line, parsed in _raw_lines(done_path):
        if parsed is None:
            # Fold already ignores it and step 8 forbids writing it back.
            print(f"compact: dropping unparseable line from {done_path}: "
                  f"{line!r}", file=sys.stderr)
            continue
        if parsed.get("item") in open_ids:
            continue  # stale snapshot/event for a reopened item (step 6)
        kept.append(line + "\n")
    fresh = []
    for i in closed_items:
        if done_state.get(i["id"]) != _public(i) or i.get("_conflicts"):
            fresh.extend(_item_events(i, per_item.get(i["id"])))
    done_text = "".join(kept) + _dump(fresh + [_compact_line(watermark)])

    tmp_todo, tmp_done = todo_path + ".compact", done_path + ".compact"
    with open(tmp_todo, "w", encoding="utf-8") as fh:
        fh.write(todo_text)
    with open(tmp_done, "w", encoding="utf-8") as fh:
        fh.write(done_text)
    try:
        _verify(before, tmp_todo, tmp_done)            # steps 7+8
    except BaseException:
        os.unlink(tmp_todo)
        os.unlink(tmp_done)
        raise
    os.replace(tmp_todo, todo_path)                    # originals untouched
    os.replace(tmp_done, done_path)                    # until verified
    return watermark


def _merge_watermark(raw_by_path):
    """Highest `through` recorded by any compact line across the given raw
    lines -- the same value fold()'s own apply_watermark computes when it
    reads both files together. None if neither file has ever been compacted."""
    marks = [e.get("through") for raw in raw_by_path.values() for _line, e in raw
             if e is not None and e.get("op") == "compact" and e.get("through")]
    return max(marks) if marks else None


def check_resurrection(todo_path, done_path):
    """Bug #243: fold.apply_watermark already drops any raw event at/below a
    compact watermark, so a union merge that resurrects those lines corrupts
    no state the fold reports -- only the file shrinks back to its
    pre-compaction size, silently. Flag any such line instead of losing the
    size win with no warning.

    Since #284 this asks the narrower, truthful question: would the fold
    actually DROP this line? An event is only dropped now if its own item has
    a snapshot claiming to have folded it, so a resurrected line for an item
    with no snapshot is no longer flagged -- it survives, and warning about it
    would be crying wolf. What remains flagged is the real hygiene loss: lines
    a compaction genuinely removed, back in the file, making it grow to its
    pre-compaction size again.

    Returns a list of problem strings; empty means clean."""
    raw = {p: _raw_lines(p) for p in (todo_path, done_path)}
    wm = _merge_watermark(raw)
    if wm is None:
        return []  # never compacted -- nothing to resurrect

    covered = {}
    for lines in raw.values():
        for _line, e in lines:
            if e is None or e.get("op") != "snapshot":
                continue
            through = e.get("through") or wm
            if through > covered.get(e.get("item"), ""):
                covered[e.get("item")] = through

    problems = []
    for path, lines in raw.items():
        bad = [line for line, e in lines
               if e is not None and e.get("op") not in ("compact", "snapshot")
               and e.get("item") in covered
               and e.get("ev", "") <= covered[e.get("item")]]
        if bad:
            problems.append(
                f"{path}: {len(bad)} event(s) at/below their item's compact "
                f"watermark are back (e.g. {bad[0]!r}) -- a union merge "
                f"resurrected lines a compaction already folded into a "
                f"snapshot. Keeping or dropping them changes no state -- the "
                f"snapshot sorts above them and replaces state entirely -- so "
                f"the file has merely grown back to its pre-compaction size. "
                f"That same ordering is why any of these THIS BRANCH authored "
                f"would be overwritten by the snapshot: merge-rescue re-emits "
                f"them above it, which is the only thing that preserves them. "
                f"Run: worklog merge-rescue")
    return problems


def check_duplicate_ownership(todo_path, done_path):
    """Bug #237: `worklog link` already refuses a ticket another item owns
    (fold.external_owners), but a merge of two branches that each claimed the
    same ticket bypasses that check -- sync catches it later, but a merge is
    the earliest point, and it happens on every machine.

    Returns a list of problem strings; empty means clean."""
    r = fold([todo_path, done_path])
    problems = []
    for (system, key), owners in external_owners(r.items.values()).items():
        if len(owners) > 1:
            problems.append(
                f"{system}:{key} is claimed by {len(owners)} items after merge: "
                f"{', '.join(owners)} -- keep one: worklog unlink <id-to-drop>")
    return problems


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _merge_state(cwd):
    """(base, ours, theirs) for the merge in progress, or None if there isn't one."""
    p = _git(cwd, "rev-parse", "-q", "--verify", "MERGE_HEAD")
    if p.returncode != 0 or not p.stdout.strip():
        return None
    theirs = p.stdout.strip()
    ours = _git(cwd, "rev-parse", "-q", "--verify", "HEAD").stdout.strip()
    base = _git(cwd, "merge-base", ours, theirs).stdout.strip()
    return base, ours, theirs


def _events_at(cwd, rev, relpath):
    """Parsed events of `relpath` as of `rev`. Missing file/rev -> []."""
    p = _git(cwd, "show", f"{rev}:{relpath}")
    if p.returncode != 0:
        return []
    out = []
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # fold ignores it too; never fatal
    return out


def _reissue(event, ms):
    """Replay `event` as a fresh event above the watermark.

    The original `ev` is below the watermark, so the fold would drop it -- the
    intent has to be re-emitted under an id that sorts above. Timestamps are
    handed in explicitly and strictly increasing so a batch of reissues keeps
    the branch's order even when they land in one millisecond.
    """
    fresh = {"ev": ulid.new(ms), "ts": _now(), "actor": event.get("actor", "rescue"),
             "item": event["item"], "op": event["op"], "rescued_from": event["ev"]}
    for field in ("set", "add", "del"):
        if event.get(field):
            fresh[field] = event[field]
    return fresh


def merge_rescue(todo_path=".work/todo.jsonl", done_path=".work/done.jsonl"):
    """Resolve a merge that check_resurrection blocked, without losing events.

    Recompacting -- what the guard used to advise -- cannot be done from this
    state and would not be safe if it could: compaction verifies
    fold(new) == fold(old), and the fold has ALREADY discarded this branch's
    sub-watermark events, so the check would pass while making the loss
    permanent. ADR-0005 records the resolution that does work, performed by
    hand once: keep the compacted side's log and re-apply this branch's own
    events on top. This is that procedure, mechanised.

    The merge base is what makes it precise. Compaction ran on a descendant of
    the base, so every event in the base was folded into a snapshot and is safe
    to drop. An event on the other side but NOT in the base was never folded --
    if it sorts below the watermark it is exactly the work that would vanish,
    so it is re-emitted above the watermark instead.

    Returns (rescued, dropped). Raises SystemExit(1) if there is no merge to
    rescue or verification fails.
    """
    cwd = os.path.dirname(os.path.abspath(todo_path)) or "."
    state = _merge_state(cwd)
    if state is None:
        print("merge-rescue: no merge in progress -- run this from the blocked "
              "merge, before `git merge --abort`", file=sys.stderr)
        raise SystemExit(1)
    base, ours, theirs = state

    # realpath both sides: --show-toplevel resolves symlinks and abspath does
    # not, so on macOS (/var -> /private/var) the relative path comes out as
    # garbage and every `git show` silently returns nothing.
    top = _git(cwd, "rev-parse", "--show-toplevel").stdout.strip() or cwd
    paths = (todo_path, done_path)
    rel = {p: os.path.relpath(os.path.realpath(p), os.path.realpath(top))
           for p in paths}
    at = {(rev, p): _events_at(cwd, rev, rel[p])
          for rev in (base, ours, theirs) for p in paths}

    def watermark_of(rev):
        marks = [e.get("through") for p in paths for e in at[(rev, p)]
                 if e.get("op") == "compact" and e.get("through")]
        return max(marks) if marks else None

    wms = {rev: watermark_of(rev) for rev in (ours, theirs)}
    if not any(wms.values()):
        print("merge-rescue: neither side has been compacted; this is not the "
              "situation this command repairs", file=sys.stderr)
        raise SystemExit(1)
    # The compacted side's log is the base to build on; the other side's unique
    # events are what get replayed onto it.
    keep = max((ours, theirs), key=lambda r: wms[r] or "")
    other = theirs if keep == ours else ours
    wm = wms[keep]

    ids_in = lambda rev: {e["ev"] for p in paths for e in at[(rev, p)] if "ev" in e}
    base_ids, keep_ids = ids_in(base), ids_in(keep)

    rescued, dropped, new_text = [], 0, {}
    for p in paths:
        lines = [json.dumps(e, separators=(",", ":"), sort_keys=True)
                 for e in at[(keep, p)]]
        carried = []
        for e in at[(other, p)]:
            if e.get("op") == "compact" or e.get("ev") in keep_ids:
                continue
            if e.get("ev") in base_ids:
                dropped += 1      # already folded into the keep side's snapshot
                continue
            carried.append(e)
        # Replay in the branch's own order; one millisecond apart so the
        # fresh ids sort in that same order.
        #
        # Re-issuing only the sub-watermark events is not enough, and the
        # failure is silent. Fresh ids are stamped at NOW, so they sort above
        # every retained original -- including this item's own LATER events,
        # which were above the watermark and kept their old ids. An item whose
        # create and update were re-issued but whose close was retained folds
        # back to the pre-close state: no event lost, every guard green, wrong
        # answer. Observed 2026-08-05 on the Codex branch, where a `done` item
        # came back as `in_progress`.
        #
        # So re-issuing is contagious forward: once an item has had one event
        # re-issued, every later event of that item must move too, or the
        # partial re-stamp inverts their order.
        start = int(time.time() * 1000)
        moved = set()
        for n, e in enumerate(sorted(carried, key=lambda x: x.get("ev", ""))):
            above = e.get("op") == "snapshot" or e.get("ev", "") > wm
            if above and e.get("item") not in moved:
                lines.append(json.dumps(e, separators=(",", ":"), sort_keys=True))
                continue
            fresh = _reissue(e, start + n)
            moved.add(e.get("item"))
            rescued.append((e["ev"], fresh["ev"], e["item"], e["op"]))
            lines.append(json.dumps(fresh, separators=(",", ":"), sort_keys=True))
        new_text[p] = "".join(ln + "\n" for ln in lines)

    tmp = {p: p + ".rescue" for p in paths}
    for p in paths:
        with open(tmp[p], "w", encoding="utf-8") as fh:
            fh.write(new_text[p])
    try:
        # The merge is only unblocked if the guard now passes...
        left = check_resurrection(tmp[todo_path], tmp[done_path])
        if left:
            for problem in left:
                print(f"merge-rescue: {problem}", file=sys.stderr)
            raise SystemExit(1)
        # ...and nothing may vanish: every item either side knew about must
        # still fold to a state.
        expected = {e["item"] for rev in (keep, other) for p in paths
                    for e in at[(rev, p)] if e.get("op") != "compact" and "item" in e}
        after = set(fold([tmp[todo_path], tmp[done_path]]).items)
        missing = expected - after
        if missing:
            print(f"merge-rescue: would lose {len(missing)} item(s): "
                  f"{sorted(missing)}; aborted, logs untouched", file=sys.stderr)
            raise SystemExit(1)
        # ...and no item's events may change relative order. Losing nothing is
        # necessary and NOT sufficient: state is fold(events sorted by id), so
        # re-stamping ids reorders as surely as deleting them, and the item
        # count check above stays green either way. Sorting by the new ids must
        # give each item the same sequence its original ids did.
        seen = {}
        for p in paths:
            for _line, e in _raw_lines(tmp[p]):
                if not e or "item" not in e or "ev" not in e:
                    continue
                seen.setdefault(e["item"], []).append(
                    (e["ev"], e.get("rescued_from", e["ev"])))
        for item, evs in seen.items():
            was = [orig for _new, orig in sorted(evs)]
            if was != sorted(was):
                print(f"merge-rescue: replay would reorder {item}'s history "
                      f"({' '.join(was)}); aborted, logs untouched",
                      file=sys.stderr)
                raise SystemExit(1)
    except BaseException:
        for p in paths:
            if os.path.exists(tmp[p]):
                os.unlink(tmp[p])
        raise
    for p in paths:
        os.replace(tmp[p], p)
    return rescued, dropped


def report_rescue(rescued, dropped):
    """Print what the rescue did and what the operator still has to run."""
    print(f"merge-rescue: dropped {dropped} already-compacted event(s); "
          f"re-applied {len(rescued)} of this branch's own")
    for old, new, item, op in rescued:
        print(f"  {item} {op}: {old} -> {new}")
    print("\nnow finish the merge:\n"
          "  worklog roadmap-render\n"
          "  git add -A && git commit\n"
          "(undo with: git merge --abort)")


def merge_check(todo_path=".work/todo.jsonl", done_path=".work/done.jsonl"):
    """Run both merge-time integrity guards (#243, #237). Prints and returns
    False on any problem; never raises -- the merge-commit hook decides
    whether that means blocking the commit."""
    problems = (check_resurrection(todo_path, done_path)
                + check_duplicate_ownership(todo_path, done_path))
    if not problems:
        return True
    print("compact: merge integrity check failed", file=sys.stderr)
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    return False


def main(argv):
    if argv[1:2] == ["--merge-check"]:
        paths = argv[2:] or [".work/todo.jsonl", ".work/done.jsonl"]
        return 0 if merge_check(*paths) else 1
    if argv[1:2] == ["--merge-rescue"]:
        paths = argv[2:] or [".work/todo.jsonl", ".work/done.jsonl"]
        report_rescue(*merge_rescue(*paths))
        return 0
    paths = argv[1:] or [".work/todo.jsonl", ".work/done.jsonl"]
    wm = compact(*paths)
    print(f"compacted through {wm}" if wm else "nothing to compact")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
