#!/usr/bin/env python3
"""Retention: compact archives old closed items, never deletes.

Plan: docs/plans/2026-08-30-retention.md
Story: 01M19XRRZ2894K7XE59RX1EAY1
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from compact import compact  # noqa: E402
from fold import fold  # noqa: E402


def iso_days_ago(days):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         time.gmtime(time.time() - days * 86400))


def write_log(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")


def read_events(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def snap(paths):
    return {iid: {k: v for k, v in i.items() if not k.startswith("_")}
            for iid, i in fold(paths).items.items()}


class RetentionBase(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp(prefix="worklog-retention-")
        self.addCleanup(shutil.rmtree, d, True)
        self.work = os.path.join(d, ".work")
        os.makedirs(self.work)
        self.todo = os.path.join(self.work, "todo.jsonl")
        self.done = os.path.join(self.work, "done.jsonl")
        self.archive = os.path.join(self.work, "archive.jsonl")
        self.paths = [self.todo, self.done, self.archive]

    def seed_closed_snapshot(self, item, ts, level="task", title=None):
        """A done.jsonl snapshot already carrying the close clock in `ts`."""
        return {"ev": "01A1" + item, "ts": ts, "actor": "compactor",
                "item": item, "op": "snapshot", "through": "01A1" + item,
                "set": {"level": level, "kind": "feature",
                        "title": title or item, "status": "done",
                        "resolution": "shipped"}}

    def seed_open(self, item="OPEN"):
        return {"ev": "01A9" + item, "ts": iso_days_ago(1), "actor": "r",
                "item": item, "op": "create",
                "set": {"level": "task", "kind": "ops",
                        "title": item.lower(), "status": "todo"}}

    def compact(self):
        return compact(self.todo, self.done, self.archive)


class TestAgeEviction(RetentionBase):
    def test_old_task_moves_to_archive_and_fold_is_preserved(self):
        write_log(self.todo, [self.seed_open()])
        write_log(self.done, [
            self.seed_closed_snapshot("OLD", iso_days_ago(400), "task"),
            self.seed_closed_snapshot("NEW", iso_days_ago(10), "task"),
        ])
        before = snap(self.paths)
        self.compact()
        after = snap(self.paths)
        self.assertEqual(before, after)
        done_ids = {e.get("item") for e in read_events(self.done) if e.get("item")}
        arch_ids = {e.get("item") for e in read_events(self.archive) if e.get("item")}
        self.assertIn("OLD", arch_ids)
        self.assertNotIn("OLD", done_ids)
        self.assertIn("NEW", done_ids)
        self.assertNotIn("NEW", arch_ids)
        self.assertIn("OPEN", fold([self.todo]).items)

    def test_epic_200_days_old_stays_in_done(self):
        write_log(self.todo, [self.seed_open()])
        write_log(self.done, [self.seed_closed_snapshot("EP", iso_days_ago(200), "epic")])
        self.compact()
        done_ids = {e.get("item") for e in read_events(self.done) if e.get("item")}
        self.assertIn("EP", done_ids)
        self.assertFalse(os.path.exists(self.archive) and read_events(self.archive))

    def test_unparseable_ts_is_not_evicted(self):
        write_log(self.todo, [self.seed_open()])
        write_log(self.done, [self.seed_closed_snapshot("BAD", "not-a-date", "task")])
        self.compact()
        done_ids = {e.get("item") for e in read_events(self.done) if e.get("item")}
        self.assertIn("BAD", done_ids)


class TestFifoCap(RetentionBase):
    def test_cap_archives_oldest_parseable_first(self):
        cfg = os.path.join(self.work, "config.yml")
        with open(cfg, "w", encoding="utf-8") as fh:
            fh.write("retention:\n  task_days: 36500\n  cap: 2\n")
        events = [
            self.seed_closed_snapshot("A", iso_days_ago(80), "task"),
            self.seed_closed_snapshot("B", iso_days_ago(40), "task"),
            self.seed_closed_snapshot("C", iso_days_ago(10), "task"),
        ]
        write_log(self.todo, [self.seed_open()])
        write_log(self.done, events)
        before = snap(self.paths)
        self.compact()
        self.assertEqual(before, snap(self.paths))
        done_ids = {e.get("item") for e in read_events(self.done) if e.get("item")}
        arch_ids = {e.get("item") for e in read_events(self.archive) if e.get("item")}
        self.assertIn("A", arch_ids)
        self.assertNotIn("A", done_ids)
        self.assertEqual(done_ids & {"B", "C"}, {"B", "C"})


class TestReopenFromArchive(RetentionBase):
    def test_reopen_prunes_archive_and_item_is_open(self):
        write_log(self.todo, [self.seed_open("KEEP")])
        write_log(self.done, [self.seed_closed_snapshot("OLD", iso_days_ago(400), "task")])
        self.compact()
        self.assertIn("OLD", {e.get("item") for e in read_events(self.archive)})
        with open(self.todo, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ev": "01ZREOPENOLD", "ts": iso_days_ago(0),
                "actor": "r", "item": "OLD", "op": "reopen",
                "set": {"status": "todo"},
            }) + "\n")
        self.compact()
        self.assertIn("OLD", fold([self.todo]).items)
        self.assertEqual(fold([self.todo]).items["OLD"]["status"], "todo")
        arch_ids = {e.get("item") for e in read_events(self.archive) if e.get("item")}
        self.assertNotIn("OLD", arch_ids)


class TestNeverDeletes(RetentionBase):
    def test_archive_is_union_merge(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, ".gitattributes"), encoding="utf-8") as fh:
            self.assertIn(".work/archive.jsonl merge=union", fh.read())

    def test_archived_item_still_showable_via_archive_fold(self):
        write_log(self.todo, [self.seed_open()])
        write_log(self.done, [self.seed_closed_snapshot("OLD", iso_days_ago(400), "task")])
        self.compact()
        self.assertIn("OLD", fold(self.paths).items)
        self.assertEqual(fold(self.paths).items["OLD"]["status"], "done")
        self.assertNotIn("OLD", fold([self.todo, self.done]).items)


if __name__ == "__main__":
    unittest.main()
