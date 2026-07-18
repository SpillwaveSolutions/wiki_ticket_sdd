#!/usr/bin/env python3
"""
Tests for bin/compact.py -- WORKLOG-SPEC section 7.

Every test runs against a throwaway .work/ in a tempdir (never the repo's
real log) and calls compact() as a module import with explicit paths.
The tempdir is not a git repo, so the dirty-tree check is skipped.
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import ulid  # noqa: E402
from compact import compact  # noqa: E402
from fold import fold, OPEN_STATUSES  # noqa: E402


def write_log(path, lines):
    with open(path, "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")  # trailing newline: section 8.2


def read_events(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def strip(item):
    return {k: v for k, v in item.items() if not k.startswith("_")}


def snap(result):
    return {iid: strip(i) for iid, i in result.items.items()}


# Fixture evs sort BELOW any fresh ULID ('01A' < '01K...' == 2026 timestamps).
EVENTS = [
    {"ev": "01A1", "ts": "t", "actor": "r", "item": "A", "op": "create",
     "set": {"type": "task", "title": "a title", "status": "todo",
             "priority": "P2", "labels": ["triage"]}},
    {"ev": "01A2", "ts": "t", "actor": "r", "item": "B", "op": "create",
     "set": {"type": "bug", "title": "b title", "status": "todo"}},
    {"ev": "01A3", "ts": "t", "actor": "r", "item": "C", "op": "create",
     "set": {"type": "task", "title": "c title", "status": "todo",
             "priority": "P1"}},
    {"ev": "01A4", "ts": "t", "actor": "r", "item": "D", "op": "create",
     "set": {"type": "task", "title": "d title", "status": "todo"}},
    {"ev": "01A5", "ts": "t", "actor": "r", "item": "A", "op": "update",
     "set": {"status": "in_progress"},
     "add": {"labels": ["backend"]}, "del": {"labels": ["triage"]}},
    {"ev": "01A6", "ts": "t", "actor": "r", "item": "A", "op": "update",
     "set": {"priority": "P0"}},
    {"ev": "01A7", "ts": "t", "actor": "r", "item": "C", "op": "close",
     "set": {"status": "done", "resolution": "shipped"}},
    {"ev": "01A8", "ts": "t", "actor": "r", "item": "D", "op": "close",
     "set": {"status": "cancelled", "resolution": "wont-do"}},
]
MAX_EV = "01A8"


class CompactBase(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp(prefix="worklog-compact-")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, ".work"))
        self.todo = os.path.join(d, ".work", "todo.jsonl")
        self.done = os.path.join(d, ".work", "done.jsonl")
        write_log(self.todo, EVENTS)
        write_log(self.done, [])


class TestFoldEquality(CompactBase):
    def test_fold_is_preserved(self):
        before = snap(fold([self.todo, self.done]))
        compact(self.todo, self.done)
        after = snap(fold([self.todo, self.done]))
        self.assertEqual(before, after)


class TestTodoRewrite(CompactBase):
    def test_open_items_become_single_snapshots(self):
        compact(self.todo, self.done)
        events = read_events(self.todo)
        open_ids = {i["id"] for i in fold([self.todo, self.done]).open_items()}
        self.assertEqual(open_ids, {"A", "B"})
        self.assertEqual(len(events), len(open_ids) + 1)  # + compact line
        ops = sorted(e["op"] for e in events)
        self.assertEqual(ops, ["compact", "snapshot", "snapshot"])
        # Old events are gone; the folded state survives in the snapshots.
        a = fold([self.todo]).items["A"]
        self.assertEqual(a["priority"], "P0")
        self.assertEqual(a["status"], "in_progress")
        self.assertEqual(a["labels"], ["backend"])

    def test_snapshot_evs_sort_after_watermark(self):
        compact(self.todo, self.done)
        for e in read_events(self.todo):
            self.assertGreater(e["ev"], MAX_EV)


class TestDoneRewrite(CompactBase):
    def test_closed_items_land_in_done(self):
        compact(self.todo, self.done)
        done_items = fold([self.done]).items
        self.assertEqual(sorted(done_items), ["C", "D"])
        self.assertEqual(done_items["C"]["resolution"], "shipped")
        self.assertEqual(done_items["D"]["status"], "cancelled")
        # ...and are absent from a fold of todo alone.
        self.assertEqual(sorted(fold([self.todo]).items), ["A", "B"])


class TestReopen(CompactBase):
    def reopen_c(self):
        compact(self.todo, self.done)
        # A second later than the compactor's snapshots: real reopens come long
        # after the nightly run; same-millisecond ULIDs would tie-break randomly.
        ev = ulid.new(int(time.time() * 1000) + 1000)
        with open(self.todo, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ev": ev, "ts": "t", "actor": "r",
                                 "item": "C", "op": "reopen", "set": {}}) + "\n")

    def test_reopen_after_compact_restores_pre_close_fields(self):
        self.reopen_c()
        c = fold([self.todo, self.done]).items["C"]
        self.assertEqual(c["status"], "todo")
        self.assertIn(c["status"], OPEN_STATUSES)
        self.assertEqual(c["title"], "c title")      # from the done snapshot
        self.assertEqual(c["priority"], "P1")
        self.assertNotIn("resolution", c)

    def test_recompact_prunes_stale_done_snapshot(self):
        self.reopen_c()
        before = snap(fold([self.todo, self.done]))
        compact(self.todo, self.done)
        self.assertEqual(before, snap(fold([self.todo, self.done])))
        # C is open again: no trace of it may remain in done.jsonl.
        self.assertNotIn("C", [e.get("item") for e in read_events(self.done)])
        # Its state now lives in a todo snapshot.
        c = fold([self.todo]).items["C"]
        self.assertEqual(c["title"], "c title")
        self.assertEqual(c["status"], "todo")


class TestFileInvariants(CompactBase):
    def test_every_line_parses_and_ends_with_newline(self):
        compact(self.todo, self.done)
        for path in (self.todo, self.done):
            with open(path, "rb") as fh:
                data = fh.read()
            self.assertTrue(data.endswith(b"\n"), path)
            for line in data.decode().splitlines():
                json.loads(line)  # every written line parses

    def test_watermark_line_present(self):
        wm = compact(self.todo, self.done)
        self.assertEqual(wm, MAX_EV)
        for path in (self.todo, self.done):
            marks = [e["through"] for e in read_events(path)
                     if e["op"] == "compact"]
            self.assertEqual(marks, [MAX_EV], path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
