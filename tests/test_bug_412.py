#!/usr/bin/env python3
"""Bug #412: sync mints duplicate tickets when link events have not reached
the shared log.

A clone with no link event and no per-clone state file used to create a
second ticket for an item whose marker already sits on the remote.
`observe_remote` lists every remote ticket anyway; it now keeps the marker
map and `remembered_key` consults it as its third source, so the push is an
update and the relink path records the missing link event.

Plan: docs/plans/2026-09-19-review-v0-24-10-and-open-tickets.md
Item: 01M2XCWMVD7KJ01FCNEV1X8237
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-412-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        shutil.copytree(os.path.join(ROOT, "adapters"),
                        os.path.join(self.dir, "adapters"))
        os.makedirs(os.path.join(self.dir, ".work"))
        self.adapter = os.path.join(self.dir, "adapters", "fake", "adapter")
        self.fake_state = os.path.join(self.dir, ".fake-tracker.json")
        self.sync_state = os.path.join(self.dir, ".work", "sync-state.json")
        self.env = dict(os.environ,
                        WORKLOG_TICKET_ADAPTER=self.adapter,
                        WORKLOG_FAKE_STATE=self.fake_state)

    def run_wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True, env=self.env)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def sync(self, *args):
        return self.wl("sync", "--retry-base-delay", "0", *args)

    def fake_state_obj(self):
        with open(self.fake_state, encoding="utf-8") as fh:
            return json.load(fh)

    def write_fake(self, state):
        with open(self.fake_state, "w", encoding="utf-8") as fh:
            json.dump(state, fh)

    def plant_marked(self, iid, key, title="Filed by another clone",
                     closed=False):
        """A remote ticket that already carries this item's marker."""
        state = {"tickets": {},
                 "counters": {"creates": 0, "updates": 0, "pulls": 0,
                              "closes": 0},
                 "fail_next": None}
        if os.path.exists(self.fake_state):
            state = self.fake_state_obj()
        state["tickets"][key] = {
            "item": {"title": title, "status": "todo", "type": "task"},
            "marker": "<!-- worklog:%s -->" % iid, "closed": closed,
            "rev": "2030-01-01T00:00:00.000000Z"}
        self.write_fake(state)
        return key

    def show(self, item):
        return json.loads(self.wl("show", item))

    def log_bytes(self):
        with open(os.path.join(self.dir, ".work", "todo.jsonl"), "rb") as fh:
            return fh.read()


class TestProbeTurnsCreateIntoUpdate(Sandbox):
    def test_fresh_clone_updates_the_marked_ticket_and_records_the_link(self):
        iid = self.wl("add", "Local work", "--priority", "P1").strip()
        self.plant_marked(iid, "FAKE#7")
        self.assertFalse(os.path.exists(self.sync_state))
        out = self.sync("--push-only")
        self.assertIn("created=0", out)
        self.assertIn("updated=1", out)
        self.assertIn("relinked=1", out)
        self.assertIn("already had tickets (marker probe)", out)
        self.assertEqual(self.show(iid)["external"]["key"], "FAKE#7")
        self.assertEqual(self.fake_state_obj()["counters"]["creates"], 0)
        with open(os.path.join(self.dir, ".work", "todo.jsonl"),
                  encoding="utf-8") as fh:
            events = [json.loads(l) for l in fh if l.strip()]
        self.assertTrue(any(e.get("op") == "link" and e.get("item") == iid
                            for e in events))

    def test_colliding_markers_resolve_to_the_dedupe_survivor(self):
        iid = self.wl("add", "Local work", "--priority", "P1").strip()
        self.plant_marked(iid, "FAKE#9")
        self.plant_marked(iid, "FAKE#7")
        self.sync("--push-only")
        self.assertEqual(self.show(iid)["external"]["key"], "FAKE#7")

    def test_probe_hit_closed_on_remote_closes_locally_and_does_not_push(self):
        iid = self.wl("add", "Done elsewhere", "--priority", "P1").strip()
        self.plant_marked(iid, "FAKE#7", closed=True)
        out = self.sync("--push-only")
        self.assertIn("closed on remote, still open in the log", out)
        self.assertIn("updated=0", out)
        self.assertEqual(self.show(iid)["status"], "done")
        self.assertEqual(self.fake_state_obj()["counters"]["updates"], 0)


class TestDeliberateUnlink(Sandbox):
    def test_probe_does_not_undo_an_unlink(self):
        iid = self.wl("add", "Mislinked", "--priority", "P1").strip()
        self.sync("--push-only")
        self.wl("unlink", iid)
        out = self.sync("--push-only")
        self.assertIn("created=1", out)
        self.assertIn("relinked=0", out)
        self.assertEqual(len(self.fake_state_obj()["tickets"]), 2)


class TestExplain(Sandbox):
    def test_explain_names_three_sources_and_changes_nothing(self):
        iid = self.wl("add", "Local work", "--priority", "P1").strip()
        self.plant_marked(iid, "FAKE#7")
        before = self.log_bytes()
        out = self.sync("--explain", iid[:8])
        self.assertIn("1. external.key (log):       -", out)
        self.assertIn("2. last_pushed_key (state):  -", out)
        self.assertIn("3. marker probe (remote):    FAKE#7", out)
        self.assertIn("remembered_key: FAKE#7", out)
        self.assertEqual(self.log_bytes(), before)
        self.assertFalse(os.path.exists(self.sync_state))
        self.assertEqual(self.fake_state_obj()["counters"]["updates"], 0)


class TestHints(Sandbox):
    def test_created_prints_the_dedupe_hint(self):
        self.wl("add", "Brand new", "--priority", "P1")
        out = self.sync("--push-only")
        self.assertIn("created=1", out)
        self.assertIn("worklog dedupe --dry-run", out)

    def test_adapter_check_says_no_push_memory(self):
        out = self.wl("adapter", "check", self.adapter)
        self.assertIn("no push memory in this clone yet", out)


class TestProbeGuard(Sandbox):
    def test_listing_failure_with_no_state_skips_creates(self):
        self.wl("add", "Would be a duplicate", "--priority", "P1")
        self.plant_marked("01UNRELATED", "FAKE#1")
        subprocess.run([sys.executable, self.adapter, "_fail_next_pull", "1"],
                       env=self.env, check=True)
        out = self.sync("--push-only")
        self.assertIn("marker probe failed and this clone has no push memory", out)
        self.assertIn("created=0", out)
        self.assertEqual(self.fake_state_obj()["counters"]["creates"], 0)
        # With push memory the guard stays out of the way.
        self.sync("--push-only")
        self.assertTrue(os.path.exists(self.sync_state))
        subprocess.run([sys.executable, self.adapter, "_fail_next_pull", "1"],
                       env=self.env, check=True)
        self.wl("add", "Second item", "--priority", "P1")
        out = self.sync("--push-only")
        self.assertNotIn("not creating tickets", out)
        self.assertIn("created=1", out)


if __name__ == "__main__":
    unittest.main()
