#!/usr/bin/env python3
"""Tests for `worklog ingest` / `conflict` / `resolve` -- spec 10.2 and 10.6.

The scenario in TestIngestIdempotence.test_duplicate_ingest_cannot_revert_a_
local_edit is the end-to-end version of tests/test_ulid.py::
TestTheBugThisPrevents, driven through the CLI.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ordering is by `ev` ULID, whose timestamp for an ingest is the REMOTE rev
# time. A rev in the past sorts before the sandbox's just-created item (its
# `create` wins LWW); a rev in the future sorts after everything local. Each
# test picks the side of "now" its scenario needs.
PAST_MS = 1_752_680_398_000
PAST = "2025-07-16T15:39:58Z"
FUT_MS = 1_900_000_000_000
FUT = "2030-03-17T17:46:40Z"


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-ingest-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        os.makedirs(os.path.join(self.dir, ".work"))

    def run_wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def log_lines(self):
        with open(os.path.join(self.dir, ".work", "todo.jsonl"),
                  encoding="utf-8") as fh:
            return [l for l in fh.read().splitlines() if l.strip()]

    def show(self, item):
        return json.loads(self.wl("show", item))

    def ingest(self, item, *extra, rev=FUT, rev_ms=FUT_MS):
        return self.wl("ingest", item, "--system", "github", "--key", "412",
                       "--rev", rev, "--rev-ts-ms", str(rev_ms), *extra)


class TestIngestIdempotence(Sandbox):
    def test_identical_ingests_are_byte_identical_and_dedupe(self):
        item = self.wl("add", "Sync me")
        self.ingest(item, "--set", "priority=P0")
        self.ingest(item, "--set", "priority=P0")
        a, b = self.log_lines()[-2:]
        self.assertEqual(a, b)  # byte-identical: section 10.2's whole point
        self.assertEqual(self.show(item)["priority"], "P0")  # applied once

    def test_duplicate_ingest_cannot_revert_a_local_edit(self):
        # Section 10.2's failure order: remote ingest, local edit, duplicate
        # remote ingest. Deterministic `ev` means the duplicate dedupes away
        # and the local P2 stands.
        item = self.wl("add", "Sync me", "--priority", "P1")
        self.ingest(item, "--set", "priority=P0", rev=PAST, rev_ms=PAST_MS)
        self.wl("update", item, "--priority", "P2")
        # dev B's identical poll of the OLD remote change, via union merge
        self.ingest(item, "--set", "priority=P0", rev=PAST, rev_ms=PAST_MS)
        self.assertEqual(self.show(item)["priority"], "P2")

    def test_ingest_carries_remote_clock_actor_and_provenance(self):
        item = self.wl("add", "Sync me")
        self.ingest(item, "--set", "title=Renamed remotely")
        ev = json.loads(self.log_lines()[-1])
        self.assertEqual(ev["ts"], FUT)  # remote clock, not now()
        self.assertEqual(ev["actor"], "github")
        self.assertEqual(ev["src"],
                         {"system": "github", "key": "412", "rev": FUT})
        self.assertEqual(self.show(item)["title"], "Renamed remotely")

    def test_unknown_set_field_rejected(self):
        item = self.wl("add", "Sync me")
        p = self.run_wl("ingest", item, "--system", "github", "--key", "412",
                        "--rev", PAST, "--rev-ts-ms", str(PAST_MS),
                        "--set", "estimate=XL")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("estimate", p.stderr)

    def test_ingest_with_nothing_to_apply_rejected(self):
        item = self.wl("add", "Sync me")
        p = self.run_wl("ingest", item, "--system", "github", "--key", "412",
                        "--rev", PAST, "--rev-ts-ms", str(PAST_MS))
        self.assertNotEqual(p.returncode, 0)


class TestConflict(Sandbox):
    def test_conflict_shows_and_list_warns(self):
        item = self.wl("add", "Contested", "--priority", "P1")
        self.wl("conflict", item, "--field", "priority",
                "--local", "P1", "--remote", "P0", "--remote-rev", PAST)
        shown = self.show(item)
        self.assertEqual(shown["priority"], "P1")  # state never changes
        self.assertEqual(shown["_conflicts"],
                         [{"field": "priority", "local": "P1", "remote": "P0",
                           "remote_rev": PAST}])
        p = self.run_wl("list")
        self.assertEqual(p.returncode, 0)
        self.assertIn("conflict", p.stderr)


class TestResolve(Sandbox):
    def _conflicted(self):
        item = self.wl("add", "Contested", "--priority", "P1")
        self.wl("conflict", item, "--field", "priority",
                "--local", "P1", "--remote", "P0", "--remote-rev", PAST)
        return item

    def test_take_remote_applies_remote_value_and_clears(self):
        item = self._conflicted()
        out = self.wl("resolve", item, "--field", "priority", "--take", "remote")
        self.assertIn("P1 -> P0", out)
        shown = self.show(item)
        self.assertEqual(shown["priority"], "P0")
        self.assertNotIn("_conflicts", shown)  # the update outsorts and clears

    def test_take_local_reasserts_current_value_and_clears(self):
        item = self._conflicted()
        self.wl("resolve", item, "--field", "priority", "--take", "local")
        shown = self.show(item)
        self.assertEqual(shown["priority"], "P1")
        self.assertNotIn("_conflicts", shown)

    def test_resolve_without_open_conflict_exits_nonzero(self):
        item = self.wl("add", "Calm")
        p = self.run_wl("resolve", item, "--field", "priority",
                        "--take", "local")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("no open conflict", p.stderr)


class TestReopen(Sandbox):
    def _closed(self):
        item = self.wl("add", "Shipped")
        self.wl("close", item, "--resolution", "did the thing")
        return item

    def test_reopen_clears_status_and_stale_resolution(self):
        item = self._closed()
        self.wl("reopen", item)
        shown = self.show(item)
        self.assertEqual(shown["status"], "todo")
        self.assertNotIn("resolution", shown)

    def test_update_status_on_closed_item_refused(self):
        item = self._closed()
        p = self.run_wl("update", item, "--status", "todo")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("reopen", p.stderr)
        self.assertEqual(self.show(item)["status"], "done")  # nothing appended

    def test_reopen_open_item_refused(self):
        item = self.wl("add", "Still going")
        p = self.run_wl("reopen", item)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not closed", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
