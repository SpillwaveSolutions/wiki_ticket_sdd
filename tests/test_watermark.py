#!/usr/bin/env python3
"""#284: the compaction watermark is per item, not global.

The old rule dropped every non-snapshot event sorting at or below ONE mark
computed as `max_ev` over the whole log -- a time marker used as a content
marker. An event created on a branch before a compaction ran on main was
never folded into any snapshot, yet still sorted below that mark, so merging
the branch back discarded it silently.

Two rules replace it, and the tests below are organised around them:
  1. an item with NO snapshot never has events dropped;
  2. an item WITH a snapshot drops only its own events at/below that
     snapshot's `through`.

Legacy logs (snapshots written before `through` existed) must keep folding
exactly as they did, except where the new rule can only restore data.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
sys.path.insert(0, BIN)
from fold import fold  # noqa: E402
from compact import compact, check_resurrection  # noqa: E402


def ev(n, item, op="create", **extra):
    e = {"ev": "01A%04d" % n, "ts": "t", "actor": "r", "item": item, "op": op}
    e.update(extra)
    return e


class LogFixture(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-watermark-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.todo = os.path.join(self.d, "todo.jsonl")
        self.done = os.path.join(self.d, "done.jsonl")
        open(self.done, "w").close()

    def write(self, path, events):
        with open(path, "w") as fh:
            for e in events:
                fh.write(json.dumps(e) + "\n")

    def append(self, path, events):
        with open(path, "a") as fh:
            for e in events:
                fh.write(json.dumps(e) + "\n")

    def items(self):
        return fold([self.todo, self.done]).items


class TestNoSnapshotMeansNeverDropped(LogFixture):
    def test_event_for_an_unsnapshotted_item_survives_a_low_ev(self):
        """The bug, at its smallest: a global mark from OTHER items must not
        reach an item nothing ever folded."""
        self.write(self.todo, [
            ev(50, "SNAPPED", op="snapshot", through="01A0050",
               set={"title": "folded", "status": "todo"}),
            {"ev": "01A0090", "ts": "t", "actor": "c", "op": "compact",
             "through": "01A0090"},
            ev(10, "BRANCHNEW", set={"title": "branch work", "status": "todo"}),
        ])
        self.assertIn("BRANCHNEW", self.items())

    def test_the_snapshotted_item_still_drops_its_own_folded_events(self):
        self.write(self.todo, [
            ev(20, "SNAPPED", set={"title": "old", "status": "todo"}),
            ev(50, "SNAPPED", op="snapshot", through="01A0050",
               set={"title": "new", "status": "todo"}),
            {"ev": "01A0090", "ts": "t", "actor": "c", "op": "compact",
             "through": "01A0090"},
        ])
        self.assertEqual(self.items()["SNAPPED"]["title"], "new")

    def test_an_event_above_its_items_own_mark_is_kept(self):
        self.write(self.todo, [
            ev(50, "X", op="snapshot", through="01A0050",
               set={"title": "snapped", "status": "todo"}),
            {"ev": "01A0090", "ts": "t", "actor": "c", "op": "compact",
             "through": "01A0090"},
            ev(60, "X", op="update", set={"status": "blocked"}),
        ])
        self.assertEqual(self.items()["X"]["status"], "blocked")


class TestLegacyLogsStillFold(LogFixture):
    """Snapshots written before `through` existed carry no per-item mark."""

    def test_legacy_snapshot_falls_back_to_the_global_mark(self):
        self.write(self.todo, [
            ev(20, "X", set={"title": "old", "status": "todo"}),
            ev(50, "X", op="snapshot", set={"title": "new", "status": "todo"}),
            {"ev": "01A0090", "ts": "t", "actor": "c", "op": "compact",
             "through": "01A0090"},
        ])
        self.assertEqual(self.items()["X"]["title"], "new")

    def test_legacy_log_still_protects_unsnapshotted_items(self):
        """The new rule applied to an old log can only restore data."""
        self.write(self.todo, [
            ev(50, "X", op="snapshot", set={"title": "new", "status": "todo"}),
            {"ev": "01A0090", "ts": "t", "actor": "c", "op": "compact",
             "through": "01A0090"},
            ev(10, "NEVERFOLDED", set={"title": "kept", "status": "todo"}),
        ])
        self.assertIn("NEVERFOLDED", self.items())

    def test_a_log_that_was_never_compacted_is_untouched(self):
        self.write(self.todo, [ev(1, "A", set={"title": "a", "status": "todo"}),
                               ev(2, "B", set={"title": "b", "status": "todo"})])
        self.assertEqual(sorted(self.items()), ["A", "B"])


class TestCompactionRecordsPerItemMarks(LogFixture):
    def setUp(self):
        super().setUp()
        subprocess.run(["git", "init", "-q", self.d], check=True)
        subprocess.run(["git", "-C", self.d, "config", "user.email", "t@t"])
        subprocess.run(["git", "-C", self.d, "config", "user.name", "t"])

    def _commit(self):
        subprocess.run(["git", "-C", self.d, "add", "-A"], check=True)
        subprocess.run(["git", "-C", self.d, "commit", "-qm", "x"], check=True)

    def snapshots(self):
        out = []
        for path in (self.todo, self.done):
            with open(path) as fh:
                out += [json.loads(l) for l in fh
                        if l.strip() and json.loads(l).get("op") == "snapshot"]
        return {s["item"]: s for s in out}

    def test_each_snapshot_carries_its_own_items_highest_ev(self):
        self.write(self.todo, [
            ev(10, "A", set={"title": "a", "status": "todo"}),
            ev(11, "A", op="update", set={"status": "blocked"}),
            ev(40, "B", set={"title": "b", "status": "todo"}),
        ])
        self._commit()
        compact(self.todo, self.done)
        snaps = self.snapshots()
        self.assertEqual(snaps["A"]["through"], "01A0011")
        self.assertEqual(snaps["B"]["through"], "01A0040")

    def test_through_never_leaks_into_item_state(self):
        """It is a property of the compaction, not of the work item."""
        self.write(self.todo, [ev(10, "A", set={"title": "a", "status": "todo"})])
        self._commit()
        compact(self.todo, self.done)
        self.assertNotIn("through", self.items()["A"])

    def test_compaction_is_still_idempotent(self):
        self.write(self.todo, [
            ev(10, "A", set={"title": "a", "status": "todo"}),
            ev(20, "B", set={"title": "b", "status": "done"}),
        ])
        self._commit()
        compact(self.todo, self.done)
        before = {k: dict(v) for k, v in self.items().items()}
        self._commit()
        compact(self.todo, self.done)
        self.assertEqual(self.items(), before)

    def test_a_later_branch_event_survives_compaction_and_remerge(self):
        """End to end: the shape of the live 2026-07-31 incident."""
        self.write(self.todo, [
            ev(10, "MAINITEM", set={"title": "m", "status": "todo"}),
            ev(40, "OTHER", set={"title": "o", "status": "todo"}),
        ])
        self._commit()
        compact(self.todo, self.done)          # global mark would be 01A0040
        self._commit()
        # A branch closed MAINITEM at ev 20 -- below the old global mark, but
        # above MAINITEM's own mark of 01A0010.
        self.append(self.todo, [ev(20, "MAINITEM", op="close",
                                   set={"status": "done"})])
        self.assertEqual(self.items()["MAINITEM"]["status"], "done")


class TestGuardStopsCryingWolf(LogFixture):
    def test_a_resurrected_event_for_an_unsnapshotted_item_is_not_flagged(self):
        """It now survives, so warning about it would be crying wolf."""
        self.write(self.todo, [
            ev(50, "X", op="snapshot", through="01A0050",
               set={"title": "x", "status": "todo"}),
            {"ev": "01A0090", "ts": "t", "actor": "c", "op": "compact",
             "through": "01A0090"},
            ev(10, "BRANCHNEW", set={"title": "n", "status": "todo"}),
        ])
        self.assertEqual(check_resurrection(self.todo, self.done), [])

    def test_a_genuinely_refolded_event_is_still_flagged(self):
        self.write(self.todo, [
            ev(20, "X", set={"title": "old", "status": "todo"}),
            ev(50, "X", op="snapshot", through="01A0050",
               set={"title": "x", "status": "todo"}),
            {"ev": "01A0090", "ts": "t", "actor": "c", "op": "compact",
             "through": "01A0090"},
        ])
        self.assertTrue(check_resurrection(self.todo, self.done))


if __name__ == "__main__":
    unittest.main(verbosity=2)
