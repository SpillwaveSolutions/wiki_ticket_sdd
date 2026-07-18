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
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulid  # noqa: E402
from fold import fold, CLOSED_STATUSES  # noqa: E402
from render_roadmap import max_ev  # noqa: E402


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _public(item):
    """Item state minus private _fields -- what a snapshot carries and what
    verification compares."""
    return {k: v for k, v in item.items() if not k.startswith("_")}


def _snapshot(item):
    # Fresh ULIDs sort after every past ev, so these outsort the watermark.
    return {"ev": ulid.new(), "ts": _now(), "actor": "compactor",
            "item": item["id"], "op": "snapshot",
            "set": {k: v for k, v in _public(item).items() if k != "id"}}


def _compact_line(watermark):
    return {"ev": ulid.new(), "ts": _now(), "actor": "compactor",
            "op": "compact", "through": watermark}


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

    watermark = max_ev([todo_path, done_path])         # step 2: raw max ev
    if watermark is None:
        return None

    raw_todo = _raw_lines(todo_path)
    if all(e is not None and e.get("op") in ("snapshot", "compact")
           for _line, e in raw_todo):
        return watermark  # nothing new since the last run; don't churn files

    before = fold([todo_path, done_path])              # step 1: full history

    open_items, closed_items = [], []                  # step 3: partition
    for item in sorted(before.items.values(), key=lambda i: i["id"]):
        # Anything not positively closed (incl. orphans) stays open: never
        # drop data.
        (closed_items if item.get("status") in CLOSED_STATUSES
         else open_items).append(item)
    open_ids = {i["id"] for i in open_items}

    # step 4: new todo = open snapshots + watermark
    todo_text = _dump([_snapshot(i) for i in open_items]
                      + [_compact_line(watermark)])

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
    fresh = [_snapshot(i) for i in closed_items
             if done_state.get(i["id"]) != _public(i)]
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


def main(argv):
    paths = argv[1:] or [".work/todo.jsonl", ".work/done.jsonl"]
    wm = compact(*paths)
    print(f"compacted through {wm}" if wm else "nothing to compact")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
