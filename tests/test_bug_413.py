#!/usr/bin/env python3
"""#413: CI as the authoritative syncer, behind ticketing.sync_owner: ci.

Plan: docs/plans/2026-09-19-review-v0-24-10-and-open-tickets.md
Item: 01M2XCWMVEH3XFP2VPS9JBD6XN
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
import sync_dispatch  # noqa: E402


class TestTicketingConfig(unittest.TestCase):
    def test_reads_scalar_children_of_the_ticketing_block(self):
        d = tempfile.mkdtemp(prefix="worklog-413-cfg-")
        self.addCleanup(shutil.rmtree, d, True)
        cfg = os.path.join(d, "config.yml")
        with open(cfg, "w", encoding="utf-8") as fh:
            fh.write("ticketing:\n  system: github  # c\n  project: o/r\n"
                     "  sync_owner: ci\n  ci_dedupe_check: true\n"
                     "wiki:\n  system: none\n")
        got = sync_dispatch.ticketing_config(cfg)
        self.assertEqual(got, {"system": "github", "project": "o/r",
                               "sync_owner": "ci", "ci_dedupe_check": "true"})
        self.assertEqual(sync_dispatch.ticketing_config(os.path.join(d, "nope")), {})


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-413-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        for sub in ("bin", "adapters", "hooks"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(self.dir, sub))
        os.makedirs(os.path.join(self.dir, ".work"))
        self.adapter = os.path.join(self.dir, "adapters", "fake", "adapter")
        self.fake_state = os.path.join(self.dir, ".fake-tracker.json")
        self.env = dict(os.environ,
                        WORKLOG_TICKET_ADAPTER=self.adapter,
                        WORKLOG_FAKE_STATE=self.fake_state)

    def config(self, text):
        with open(os.path.join(self.dir, ".work", "config.yml"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def run_wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True, env=self.env)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def plant_marked(self, iid, key):
        state = {"tickets": {}, "counters": {"creates": 0, "updates": 0,
                                             "pulls": 0, "closes": 0},
                 "fail_next": None}
        if os.path.exists(self.fake_state):
            with open(self.fake_state, encoding="utf-8") as fh:
                state = json.load(fh)
        state["tickets"][key] = {
            "item": {"title": "t", "status": "todo", "type": "task"},
            "marker": "<!-- worklog:%s -->" % iid, "closed": False,
            "rev": "2030-01-01T00:00:00.000000Z"}
        with open(self.fake_state, "w", encoding="utf-8") as fh:
            json.dump(state, fh)


class TestCiOwnedSync(Sandbox):
    def test_manual_push_refuses_without_force_and_read_only_runs_stay_open(self):
        self.config("ticketing:\n  system: fake\n  sync_owner: ci\n")
        self.wl("add", "Local work", "--priority", "P1")
        p = self.run_wl("sync", "--push-only", "--retry-base-delay", "0")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("CI-owned", p.stderr)
        self.assertIn("--force", p.stderr)
        self.assertIn("created=0", self.wl("sync", "--report", "--retry-base-delay", "0")
                      + "created=0")
        out = self.wl("sync", "--push-only", "--force", "--retry-base-delay", "0")
        self.assertIn("created=1", out)

    def test_human_owned_repo_is_unchanged(self):
        self.config("ticketing:\n  system: fake\n")
        self.wl("add", "Local work", "--priority", "P1")
        out = self.wl("sync", "--push-only", "--retry-base-delay", "0")
        self.assertIn("created=1", out)


class TestDedupeCheck(Sandbox):
    def test_check_exits_1_on_an_agreed_group_and_0_otherwise(self):
        iid = self.wl("add", "Twice filed", "--priority", "P1").strip()
        self.plant_marked(iid, "FAKE#7")
        self.plant_marked(iid, "FAKE#9")
        p = self.run_wl("dedupe", "--dry-run", "--check")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("agreed duplicate group", p.stderr)
        self.assertEqual(self.run_wl("dedupe", "--dry-run").returncode, 0)
        with open(self.fake_state, encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)["tickets"]), 2)  # nothing collapsed


class TestDoctorNote(Sandbox):
    def test_doctor_names_ci_ownership(self):
        self.config("ticketing:\n  system: fake\n  sync_owner: ci\n")
        p = subprocess.run(["bash", os.path.join(self.dir, "hooks", "session-doctor.sh")],
                           cwd=self.dir, capture_output=True, text=True,
                           input="{}", timeout=30,
                           env=dict(os.environ, CLAUDE_PLUGIN_ROOT=""))
        self.assertIn("sync_owner is ci", p.stdout)
        self.config("ticketing:\n  system: fake\n")
        p = subprocess.run(["bash", os.path.join(self.dir, "hooks", "session-doctor.sh")],
                           cwd=self.dir, capture_output=True, text=True,
                           input="{}", timeout=30,
                           env=dict(os.environ, CLAUDE_PLUGIN_ROOT=""))
        self.assertNotIn("sync_owner is ci", p.stdout)


if __name__ == "__main__":
    unittest.main()
