#!/usr/bin/env python3
"""
Tests for bin/fold.py -- WORKLOG-SPEC section 6.

The first four cases are regressions against real bugs found in a proposed
implementation. Each one produced plausible-looking output and silently
corrupted state. They are first in the file on purpose.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from fold import fold  # noqa: E402


def write_log(lines):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")  # trailing newline: section 8.2
    return path


class TestOrdering(unittest.TestCase):
    """Union merge scrambles file order. Order is by `ev`, always."""

    def test_newest_ev_wins_regardless_of_file_position(self):
        path = write_log([
            {"ev": "01J8X4RR10", "ts": "t", "actor": "jira", "item": "A", "op": "update",
             "set": {"priority": "P0"},
             "src": {"system": "jira", "key": "PROJ-412", "rev": "r"}},
            {"ev": "01J8X2K4A0", "ts": "t", "actor": "rick", "item": "A", "op": "create",
             "set": {"type": "task", "title": "Extract auth middleware",
                     "status": "todo", "priority": "P1"}},
            {"ev": "01J8X2M900", "ts": "t", "actor": "rick", "item": "A", "op": "update",
             "set": {"status": "in_progress"}},
        ])
        item = fold([path]).items["A"]
        self.assertEqual(item["priority"], "P0")   # file-order fold gives P1
        self.assertEqual(item["status"], "in_progress")
        self.assertEqual(item["id"], "A")          # id survives the fold

    def test_fold_is_deterministic_across_shuffles(self):
        events = [
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo", "priority": "P3"}},
            {"ev": "01B", "ts": "t", "actor": "r", "item": "A", "op": "update",
             "set": {"priority": "P1"}},
            {"ev": "01C", "ts": "t", "actor": "j", "item": "A", "op": "update",
             "set": {"priority": "P0"}},
        ]
        import itertools
        results = {json.dumps(fold([write_log(list(p))]).items["A"], sort_keys=True)
                   for p in itertools.permutations(events)}
        self.assertEqual(len(results), 1, "fold must not depend on line order")


class TestCloseSemantics(unittest.TestCase):
    """`close` takes status from `set`. Assuming 'done' reports abandoned work as shipped."""

    def test_cancelled_stays_cancelled(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "Drop the legacy shim", "status": "todo"}},
            {"ev": "01B", "ts": "t", "actor": "r", "item": "A", "op": "close",
             "set": {"status": "cancelled", "resolution": "wont-do"}},
        ])
        item = fold([path]).items["A"]
        self.assertEqual(item["status"], "cancelled")  # naive fold gives "done"
        self.assertEqual(item["resolution"], "wont-do")

    def test_close_without_explicit_status_defaults_done(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo"}},
            {"ev": "01B", "ts": "t", "actor": "r", "item": "A", "op": "close", "set": {}},
        ])
        self.assertEqual(fold([path]).items["A"]["status"], "done")

    def test_reopen_clears_resolution(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo"}},
            {"ev": "01B", "ts": "t", "actor": "r", "item": "A", "op": "close",
             "set": {"status": "done", "resolution": "shipped"}},
            {"ev": "01C", "ts": "t", "actor": "r", "item": "A", "op": "reopen", "set": {}},
        ])
        item = fold([path]).items["A"]
        self.assertEqual(item["status"], "todo")
        self.assertNotIn("resolution", item)


class TestSetValuedFields(unittest.TestCase):
    """add/del exist so two devs on two branches don't clobber each other."""

    def test_add_and_del_labels(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo", "labels": ["triage"]}},
            {"ev": "01B", "ts": "t", "actor": "r", "item": "A", "op": "update",
             "add": {"labels": ["backend"]}, "del": {"labels": ["triage"]}},
        ])
        self.assertEqual(fold([path]).items["A"]["labels"], ["backend"])  # naive fold drops it

    def test_concurrent_adds_from_two_branches_both_survive(self):
        # The whole point of add/del. Union merge brings both lines in.
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo"}},
            {"ev": "01B", "ts": "t", "actor": "alice", "item": "A", "op": "update",
             "add": {"labels": ["backend"]}},
            {"ev": "01C", "ts": "t", "actor": "bob", "item": "A", "op": "update",
             "add": {"labels": ["urgent"]}},
        ])
        self.assertEqual(sorted(fold([path]).items["A"]["labels"]), ["backend", "urgent"])

    def test_add_is_idempotent(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo"}},
            {"ev": "01B", "ts": "t", "actor": "r", "item": "A", "op": "update",
             "add": {"labels": ["backend"]}},
            {"ev": "01C", "ts": "t", "actor": "r", "item": "A", "op": "update",
             "add": {"labels": ["backend"]}},
        ])
        self.assertEqual(fold([path]).items["A"]["labels"], ["backend"])


class TestCompaction(unittest.TestCase):
    def test_snapshot_replaces_state_entirely(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "old", "status": "todo",
                     "priority": "P3", "labels": ["stale"]}},
            {"ev": "01M", "ts": "t", "actor": "compactor", "item": "A", "op": "snapshot",
             "set": {"type": "task", "title": "new", "status": "in_progress", "priority": "P0"}},
            {"ev": "01Z", "ts": "t", "actor": "compactor", "item": "_", "op": "compact",
             "through": "01M"},
        ])
        item = fold([path]).items["A"]
        self.assertEqual(item["title"], "new")
        self.assertNotIn("labels", item)  # snapshot replaces; it does not merge

    def test_watermark_discards_superseded_events(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo", "priority": "P3"}},
            {"ev": "01M", "ts": "t", "actor": "compactor", "item": "A", "op": "snapshot",
             "set": {"type": "task", "title": "x", "status": "todo", "priority": "P0"}},
            {"ev": "01Z", "ts": "t", "actor": "compactor", "item": "_", "op": "compact",
             "through": "01M"},
        ])
        self.assertEqual(fold([path]).items["A"]["priority"], "P0")

    def test_events_after_watermark_still_apply(self):
        # A branch created before compaction, merged after. Its events sort above
        # the watermark and must survive.
        path = write_log([
            {"ev": "01M", "ts": "t", "actor": "compactor", "item": "A", "op": "snapshot",
             "set": {"type": "task", "title": "x", "status": "todo", "priority": "P2"}},
            {"ev": "01Z", "ts": "t", "actor": "compactor", "item": "_", "op": "compact",
             "through": "01M"},
            {"ev": "02A", "ts": "t", "actor": "r", "item": "A", "op": "update",
             "set": {"priority": "P0"}},
        ])
        self.assertEqual(fold([path]).items["A"]["priority"], "P0")

    def test_compact_event_creates_no_item(self):
        path = write_log([
            {"ev": "01Z", "ts": "t", "actor": "compactor", "item": "_", "op": "compact",
             "through": "01M"},
        ])
        self.assertEqual(fold([path]).items, {})

    def test_reopen_across_files_beats_done_snapshot(self):
        done = write_log([
            {"ev": "01M", "ts": "t", "actor": "compactor", "item": "A", "op": "snapshot",
             "set": {"type": "task", "title": "x", "status": "done", "resolution": "shipped"}},
        ])
        todo = write_log([
            {"ev": "02A", "ts": "t", "actor": "r", "item": "A", "op": "reopen", "set": {}},
        ])
        # ev ordering handles this on its own -- no tombstone needed.
        self.assertEqual(fold([todo, done]).items["A"]["status"], "todo")


class TestDedupe(unittest.TestCase):
    def test_duplicate_ev_counted_once(self):
        line = {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "update",
                "add": {"labels": ["x"]}}
        create = {"ev": "01_", "ts": "t", "actor": "r", "item": "A", "op": "create",
                  "set": {"type": "task", "title": "x", "status": "todo"}}
        path = write_log([create, line, line])
        r = fold([path])
        self.assertEqual(r.deduped, 1)
        self.assertEqual(r.items["A"]["labels"], ["x"])

    def test_ingested_remote_event_dedupes_across_clones(self):
        """Section 10.2: two devs polling Jira produce byte-identical lines.

        This is the test that fails if `ev` is random and the remote hash lives
        in a sidecar field. Order below is the failure order from the spec:
        remote ingest, local edit, duplicate remote ingest.
        """
        remote = {"ev": "01B", "ts": "2026-07-16T15:39:58Z", "actor": "jira", "item": "A",
                  "op": "update", "set": {"priority": "P0"},
                  "src": {"system": "jira", "key": "PROJ-412", "rev": "2026-07-16T15:39:58Z"}}
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo", "priority": "P1"}},
            remote,
            {"ev": "01C", "ts": "t", "actor": "rick", "item": "A", "op": "update",
             "set": {"priority": "P2"}},
            remote,  # dev B's identical ingest, arriving via union merge
        ])
        # Rick's edit is newest and must stand. With a random ev per ingest the
        # duplicate sorts above 01C and silently reverts him to P0.
        self.assertEqual(fold([path]).items["A"]["priority"], "P2")


class TestRobustness(unittest.TestCase):
    def test_corrupt_line_is_skipped_not_fatal(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps({"ev": "01A", "ts": "t", "actor": "r", "item": "A",
                                 "op": "create", "set": {"type": "task", "title": "x",
                                                         "status": "todo"}}) + "\n")
            fh.write('{"ev":"01B","op":"update"}{"ev":"01C"}\n')  # fused by union merge
            fh.write(json.dumps({"ev": "01D", "ts": "t", "actor": "r", "item": "B",
                                 "op": "create", "set": {"type": "bug", "title": "y",
                                                         "status": "todo"}}) + "\n")
        r = fold([path])
        self.assertEqual(r.skipped, 1)
        self.assertEqual(len(r.errors), 1)
        self.assertEqual(sorted(r.items), ["A", "B"])  # one bad line costs one line

    def test_orphan_is_flagged_not_invented(self):
        path = write_log([
            {"ev": "01B", "ts": "t", "actor": "r", "item": "GHOST", "op": "update",
             "set": {"priority": "P0"}},
        ])
        r = fold([path])
        self.assertEqual(r.orphans, ["GHOST"])
        self.assertTrue(r.items["GHOST"]["_orphan"])

    def test_missing_file_is_not_an_error(self):
        self.assertEqual(fold(["/nonexistent/todo.jsonl"]).items, {})

    def test_conflict_records_without_changing_state(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo", "priority": "P1"}},
            {"ev": "01B", "ts": "t", "actor": "sync", "item": "A", "op": "conflict",
             "set": {"field": "priority", "local": "P1", "remote": "P0"}},
        ])
        r = fold([path])
        self.assertEqual(r.items["A"]["priority"], "P1")  # unchanged
        self.assertEqual(len(r.conflicts()), 1)

    def test_link_sets_external_not_ticket(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "x", "status": "todo"}},
            {"ev": "01B", "ts": "t", "actor": "sync", "item": "A", "op": "link",
             "set": {"external": {"system": "jira", "key": "PROJ-412",
                                  "url": "https://x", "synced_at": "t", "hash": "a3f1"}}},
        ])
        item = fold([path]).items["A"]
        self.assertEqual(item["external"]["key"], "PROJ-412")
        self.assertNotIn("ticket", item)  # `src` is provenance; `external` is identity


class TestPartitions(unittest.TestCase):
    def test_open_and_closed_partition(self):
        path = write_log([
            {"ev": "01A", "ts": "t", "actor": "r", "item": "A", "op": "create",
             "set": {"type": "task", "title": "a", "status": "in_progress"}},
            {"ev": "01B", "ts": "t", "actor": "r", "item": "B", "op": "create",
             "set": {"type": "task", "title": "b", "status": "todo"}},
            {"ev": "01C", "ts": "t", "actor": "r", "item": "C", "op": "create",
             "set": {"type": "task", "title": "c", "status": "todo"}},
            {"ev": "01D", "ts": "t", "actor": "r", "item": "C", "op": "close",
             "set": {"status": "cancelled"}},
        ])
        r = fold([path])
        self.assertEqual(sorted(i["id"] for i in r.open_items()), ["A", "B"])
        self.assertEqual([i["id"] for i in r.closed_items()], ["C"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
