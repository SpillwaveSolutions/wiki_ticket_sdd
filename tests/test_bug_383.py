#!/usr/bin/env python3
"""Bug #383: no way to reconcile the duplicate tickets #382 mints.

Once two remote tickets carry the same worklog marker, fold LWW keeps only
the last local key, so `external_owners` (many items, one key) cannot see
the inverse (one item, many keys). `worklog dedupe` groups by marker,
classifies agreed vs conflicting state, and collapses only the agreed ones.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-383-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        shutil.copytree(os.path.join(ROOT, "adapters"),
                        os.path.join(self.dir, "adapters"))
        os.makedirs(os.path.join(self.dir, ".work"))
        self.adapter = os.path.join(self.dir, "adapters", "fake", "adapter")
        self.fake_state = os.path.join(self.dir, ".fake-tracker.json")
        self.env = dict(os.environ,
                        WORKLOG_TICKET_ADAPTER=self.adapter,
                        WORKLOG_FAKE_STATE=self.fake_state)

    def run_wl(self, *args, env=None):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True, env=env or self.env)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def sync(self, *args):
        return self.wl("sync", "--retry-base-delay", "0", *args)

    def fake(self, *args):
        p = subprocess.run([sys.executable, self.adapter, *args],
                           cwd=self.dir, capture_output=True, text=True,
                           env=self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def tickets(self):
        with open(self.fake_state, encoding="utf-8") as fh:
            return json.load(fh)["tickets"]

    def plant_duplicate(self, title="Same work", close_first=False,
                        close_second=False):
        """Create one local item, then a second remote ticket with the same
        marker — the shape #382 leaves on the board."""
        iid = self.wl("add", title, "--priority", "P1").strip()
        self.sync("--push-only")
        first = "FAKE#1"
        if close_first:
            p = subprocess.run(
                [sys.executable, self.adapter, "close", first, "done"],
                cwd=self.dir, capture_output=True, text=True, env=self.env)
            self.assertEqual(p.returncode, 0, p.stderr)
        # Second create with the same marker, as a lost-link sync would.
        marker = "<!-- worklog:%s -->" % iid
        payload = json.dumps({
            "op": "create", "key": None, "marker": marker,
            "item": {"id": iid, "type": "task", "title": title,
                     "status": "todo"}})
        p = subprocess.run([self.adapter, "push"], input=payload,
                           cwd=self.dir, capture_output=True, text=True,
                           env=self.env)
        self.assertEqual(p.returncode, 0, p.stderr)
        second = json.loads(p.stdout)["key"]
        if close_second:
            p = subprocess.run(
                [sys.executable, self.adapter, "close", second, "done"],
                cwd=self.dir, capture_output=True, text=True, env=self.env)
            self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.fake("_count"), "2")
        return iid, first, second


class TestDedupeDetectsMarkerCopies(Sandbox):
    def test_dry_run_reports_an_agreed_open_pair(self):
        iid, first, second = self.plant_duplicate()
        out = self.wl("dedupe", "--dry-run")
        self.assertIn(iid, out)
        self.assertIn(first, out)
        self.assertIn(second, out)
        self.assertIn("agreed", out)
        self.assertEqual(self.fake("_count"), "2", "dry-run closed a ticket")

    def test_default_is_dry_run(self):
        self.plant_duplicate()
        out = self.wl("dedupe")
        self.assertIn("agreed", out)
        self.assertEqual(self.fake("_count"), "2")

    def test_conflict_when_one_copy_is_done_and_one_is_open(self):
        iid, first, second = self.plant_duplicate(close_first=True)
        out = self.wl("dedupe", "--show-conflicts")
        self.assertIn("conflict", out)
        self.assertIn(iid, out)
        collapse = self.run_wl("dedupe", "--collapse-agreed")
        self.assertEqual(collapse.returncode, 0, collapse.stderr)
        # Conflict group is not collapsed.
        self.assertEqual(self.fake("_count"), "2")
        self.assertFalse(self.tickets()[second]["closed"])

    def test_collapse_agreed_closes_the_later_copy_and_keeps_the_original(self):
        iid, first, second = self.plant_duplicate()
        out = self.wl("dedupe", "--collapse-agreed")
        self.assertIn(first, out)
        self.assertTrue(self.tickets()[second]["closed"], out)
        self.assertFalse(self.tickets()[first]["closed"], out)
        self.assertIn(first, self.tickets()[second]["resolution"])
        shown = json.loads(self.wl("show", iid))
        self.assertEqual(shown["external"]["key"], first)

    def test_both_done_is_agreed_and_collapses(self):
        iid, first, second = self.plant_duplicate(close_first=True,
                                                 close_second=True)
        out = self.wl("dedupe")
        self.assertIn("agreed", out)
        self.wl("dedupe", "--collapse-agreed")
        shown = json.loads(self.wl("show", iid))
        self.assertEqual(shown["external"]["key"], first)

    def test_title_twins_without_a_shared_marker_are_low_confidence(self):
        a = self.wl("add", "Popular title", "--priority", "P1").strip()
        self.sync("--push-only")
        b = self.wl("add", "Popular title", "--priority", "P1").strip()
        self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "2")
        out = self.wl("dedupe")
        self.assertIn("low-confidence", out)
        self.wl("dedupe", "--collapse-agreed")
        # Distinct items, same title: never auto-collapsed.
        self.assertFalse(self.tickets()["FAKE#1"]["closed"])
        self.assertFalse(self.tickets()["FAKE#2"]["closed"])
        self.assertEqual(
            json.loads(self.wl("show", a))["external"]["key"], "FAKE#1")
        self.assertEqual(
            json.loads(self.wl("show", b))["external"]["key"], "FAKE#2")


if __name__ == "__main__":
    unittest.main()
