#!/usr/bin/env python3
"""Bug #385: push-only sync cannot absorb tracker-only tickets, and a
GitHub close stays open in the log.

Two agents, two worktrees, one tracker. Session A files issues with
`gh issue create` (no worklog marker). Session B's --push-only run
treats the log as source of truth: the orphans are invisible, and a
later dirty push can rewrite tickets GitHub already closed.

Push-only stays. This file pins the three gaps the ticket asked for:
unmarked remotes as a first-class drift class, `worklog adopt`, and
closed-on-remote detection that closes the log item instead of pushing
the open state back.
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
        self.dir = tempfile.mkdtemp(prefix="worklog-385-")
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

    def fake_state_obj(self):
        with open(self.fake_state, encoding="utf-8") as fh:
            return json.load(fh)

    def write_fake(self, state):
        with open(self.fake_state, "w", encoding="utf-8") as fh:
            json.dump(state, fh)

    def plant_unmarked(self, key="FAKE#93", title="Filed with gh issue create",
                       **item):
        state = {"tickets": {},
                 "counters": {"creates": 0, "updates": 0, "pulls": 0,
                              "closes": 0},
                 "fail_next": None}
        if os.path.exists(self.fake_state):
            state = self.fake_state_obj()
        ticket_item = {"title": title, "status": "todo"}
        ticket_item.update(item)
        state["tickets"][key] = {
            "item": ticket_item, "marker": None, "closed": False,
            "rev": "2030-01-01T00:00:00.000000Z"}
        self.write_fake(state)
        return key

    def show(self, item):
        return json.loads(self.wl("show", item))


class TestUnmarkedReportedOnPushOnly(Sandbox):
    def test_unmarked_remote_is_a_first_class_drift_class(self):
        self.wl("add", "Local work", "--priority", "P1")
        self.sync("--push-only")
        self.plant_unmarked(title="Session A filed this")
        out = self.sync("--push-only")
        self.assertIn("unmarked remote tickets (no worklog marker)", out)
        self.assertIn("FAKE#93", out)
        self.assertIn("Session A filed this", out)
        self.assertIn("worklog adopt --system fake --key FAKE#93", out)
        self.assertNotIn("no local item created", out)

    def test_dry_run_reports_unmarked_without_adopting(self):
        self.plant_unmarked()
        out = self.sync("--push-only", "--dry-run")
        self.assertIn("unmarked remote tickets (no worklog marker)", out)
        self.assertEqual(self.run_wl("fold").returncode, 0)
        folded = json.loads(self.wl("fold"))
        self.assertFalse(any((i.get("external") or {}).get("key") == "FAKE#93"
                             for i in folded))


class TestClosedOnRemote(Sandbox):
    def test_push_only_closes_local_instead_of_rewriting_the_ticket(self):
        iid = self.wl("add", "Already done on GitHub", "--priority", "P1").strip()
        self.sync("--push-only")
        shown = self.show(iid)
        key = shown["external"]["key"]
        state = self.fake_state_obj()
        state["tickets"][key]["closed"] = True
        state["tickets"][key]["rev"] = "2031-01-01T00:00:00.000000Z"
        self.write_fake(state)

        out = self.sync("--push-only")
        self.assertIn("closed on remote, still open in the log", out)
        self.assertIn("closed locally", out)
        self.assertEqual(self.show(iid)["status"], "done")
        # Did not reopen.
        self.assertTrue(self.fake_state_obj()["tickets"][key]["closed"])
        # A later push-only must not treat the status change as dirty and
        # rewrite the closed ticket.
        out2 = self.sync("--push-only")
        self.assertNotIn("would update", out2)
        self.assertNotIn("closed on remote, still open in the log", out2)
        self.assertTrue(self.fake_state_obj()["tickets"][key]["closed"])

    def test_dry_run_does_not_close_and_names_the_repair(self):
        iid = self.wl("add", "Still open here", "--priority", "P1").strip()
        self.sync("--push-only")
        key = self.show(iid)["external"]["key"]
        state = self.fake_state_obj()
        state["tickets"][key]["closed"] = True
        state["tickets"][key]["rev"] = "2031-01-01T00:00:00.000000Z"
        self.write_fake(state)

        out = self.sync("--push-only", "--dry-run")
        self.assertIn("run `worklog close %s`" % iid, out)
        self.assertEqual(self.show(iid)["status"], "todo")

    def test_dirty_local_is_not_pushed_over_a_closed_remote(self):
        iid = self.wl("add", "Original title", "--priority", "P1").strip()
        self.sync("--push-only")
        key = self.show(iid)["external"]["key"]
        self.wl("update", iid, "--title", "Local edit after they closed it")
        state = self.fake_state_obj()
        state["tickets"][key]["closed"] = True
        state["tickets"][key]["rev"] = "2031-01-01T00:00:00.000000Z"
        self.write_fake(state)

        self.sync("--push-only")
        remote = self.fake_state_obj()["tickets"][key]
        self.assertTrue(remote["closed"])
        self.assertEqual(remote["item"]["title"], "Original title")
        self.assertEqual(self.show(iid)["status"], "done")
        self.assertEqual(self.show(iid)["title"],
                         "Local edit after they closed it")


class TestAdopt(Sandbox):
    def test_adopt_creates_links_and_stamps_the_marker(self):
        self.plant_unmarked(key="FAKE#93", title="Outside ticket",
                            body="what and why", priority="P1")
        out = self.wl("adopt", "--system", "fake", "--key", "FAKE#93")
        iid = out.strip().splitlines()[-1]
        shown = self.show(iid)
        self.assertEqual(shown["title"], "Outside ticket")
        self.assertEqual(shown["external"]["system"], "fake")
        self.assertEqual(shown["external"]["key"], "FAKE#93")
        self.assertIn("01", self.fake_state_obj()["tickets"]["FAKE#93"]["marker"])
        # Next push-only updates, does not create a second ticket.
        n_before = len(self.fake_state_obj()["tickets"])
        self.sync("--push-only")
        self.assertEqual(len(self.fake_state_obj()["tickets"]), n_before)
        self.assertNotIn("unmarked remote tickets", self.sync("--push-only"))

    def test_adopt_refuses_a_key_another_item_owns(self):
        iid = self.wl("add", "Mine", "--priority", "P1").strip()
        self.sync("--push-only")
        key = self.show(iid)["external"]["key"]
        p = self.run_wl("adopt", "--system", "fake", "--key", key)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("already belongs", p.stderr)

    def test_adopt_dry_run_writes_nothing(self):
        self.plant_unmarked(key="FAKE#93", title="Leave it")
        out = self.wl("adopt", "--system", "fake", "--key", "FAKE#93",
                      "--dry-run")
        self.assertIn("would create", out)
        folded = json.loads(self.wl("fold"))
        self.assertEqual(folded, [])
        self.assertIsNone(
            self.fake_state_obj()["tickets"]["FAKE#93"]["marker"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
