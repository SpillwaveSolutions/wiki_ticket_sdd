#!/usr/bin/env python3
"""
Tests for `worklog status` -- daily/weekly status reports, WORKLOG-SPEC 13.3.

Sandbox style: every test runs in a tempdir with its own copy of bin/, and
events are written through the worklog CLI so they are genuine (invariant
15.4). The repo's real .work/ is never touched.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestStatus(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-status-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        os.makedirs(os.path.join(self.dir, ".work"))
        self.worklog = os.path.join(self.dir, "bin", "worklog")

    def run_wl(self, *args, stdin=None):
        return subprocess.run(
            [sys.executable, self.worklog, "--actor", "t", *args],
            cwd=self.dir, capture_output=True, text=True, input=stdin)

    def ok(self, *args, stdin=None):
        p = self.run_wl(*args, stdin=stdin)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def facts(self, kind):
        return json.loads(self.ok("status", "--kind", kind, "--emit-facts"))

    def max_ev(self):
        with open(os.path.join(self.dir, ".work", "todo.jsonl"),
                  encoding="utf-8") as fh:
            return max(json.loads(l)["ev"] for l in fh if l.strip())

    def old_ulid(self, days):
        """A ULID timestamped `days` in the past, via the sandbox's bin/ulid."""
        p = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, 'bin'); import time, ulid; "
             f"print(ulid.new(int((time.time() - {days} * 86400) * 1000)))"],
            cwd=self.dir, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def test_emit_facts_daily(self):
        a = self.ok("add", "Fresh task", "--priority", "P1").strip()
        b = self.ok("add", "Quick fix", "--unplanned",
                    "--discovered-during", a).strip()
        self.ok("close", b, "--resolution", "fixed")

        f = self.facts("daily")
        self.assertEqual(f["kind"], "daily")
        self.assertEqual(f["through"], self.max_ev())
        closed = {i["id"]: i for i in f["closed_in_window"]}
        self.assertIn(b, closed)
        self.assertEqual(closed[b]["resolution"], "fixed")
        self.assertTrue(closed[b]["unplanned"])
        self.assertEqual([u["discovered_during"]
                          for u in f["unplanned_in_window"]], ["Fresh task"])
        for edge in ("from", "to"):
            self.assertRegex(f["window"][edge],
                             r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(f["counts"]["closed_in_window"], 1)

    def old_create(self, days, title="Old task"):
        """Append a create event `days` old. Hand-written line, sandbox only
        -- the ev ULID carries the age. Returns the item id."""
        old = self.old_ulid(days)
        line = {"ev": old, "ts": "2026-07-08T00:00:00Z", "actor": "t",
                "item": old, "op": "create",
                "set": {"type": "task", "title": title, "status": "todo"}}
        with open(os.path.join(self.dir, ".work", "todo.jsonl"), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(line) + "\n")
        return old

    def tc_facts(self, *extra):
        return json.loads(self.ok("status", "--kind", "timecard",
                                  "--emit-facts", *extra))

    def test_old_event_outside_both_windows(self):
        fresh = self.ok("add", "Fresh task").strip()
        # A create from 10 days ago: outside daily (24h) AND weekly (7d).
        old = self.old_create(10)

        for kind in ("daily", "weekly"):
            opened = [i["id"] for i in self.facts(kind)["opened_in_window"]]
            self.assertIn(fresh, opened, kind)
            self.assertNotIn(old, opened, kind)

    def test_write_creates_frozen_report(self):
        self.ok("add", "Something")
        prose = "- Shipped: the thing\n- Blocked: nothing\n"
        date = time.strftime("%Y-%m-%d", time.gmtime())
        path = f"docs/status/{date}-daily.md"
        out = self.ok("status", "--kind", "daily", "--write", stdin=prose)
        self.assertEqual(out.strip(), path)

        with open(os.path.join(self.dir, path), encoding="utf-8") as fh:
            doc = fh.read()
        for key in ("kind: daily", f"date: {date}", "window: {from: ",
                    "through: ", "generated_at: "):
            self.assertIn(key, doc)
        self.assertTrue(doc.endswith(prose))

        p = self.run_wl("status", "--kind", "daily", "--write", stdin="v2\n")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("frozen", p.stdout + p.stderr)

        self.ok("status", "--kind", "daily", "--write", "--force", stdin="v2\n")
        with open(os.path.join(self.dir, path), encoding="utf-8") as fh:
            self.assertIn("v2", fh.read())

    def test_timecard_groups_by_day_and_omits_empty_days(self):
        a = self.ok("add", "Fresh task").strip()
        self.ok("add", "Quick fix", "--unplanned", "--discovered-during", a)

        f = self.tc_facts()
        today = time.strftime("%Y-%m-%d", time.gmtime())
        self.assertEqual(f["kind"], "timecard")
        # only today saw activity: the other 7 window days are absent
        self.assertEqual([d["date"] for d in f["days"]], [today])
        day = f["days"][0]
        self.assertEqual([o["title"] for o in day["opened"]],
                         ["Fresh task", "Quick fix"])
        quick = day["opened"][1]
        self.assertTrue(quick["unplanned"])
        self.assertEqual(quick["discovered_during_title"], "Fresh task")
        self.assertNotIn("id", quick)          # no ticket IDs in the facts
        self.assertEqual(day["commits"], [])   # sandbox is not a git repo

    def test_timecard_since_until_bound_the_window(self):
        self.ok("add", "Fresh task")
        self.old_create(10)
        old_date = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 10 * 86400))

        # default window (last 7 days): the 10-day-old create is excluded
        self.assertNotIn(old_date, [d["date"] for d in self.tc_facts()["days"]])

        # explicit window around the old event: it appears; today does not
        since = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 12 * 86400))
        f = self.tc_facts("--since", since, "--until", old_date)
        self.assertEqual([d["date"] for d in f["days"]], [old_date])
        self.assertEqual([o["title"] for o in f["days"][0]["opened"]],
                         ["Old task"])

    def test_timecard_write_is_frozen(self):
        self.ok("add", "Something")
        prose = "## Monday, 14 July\nWrote the thing.\n"
        today = time.strftime("%Y-%m-%d", time.gmtime())
        out = self.ok("status", "--kind", "timecard", "--write", stdin=prose)
        path = f"docs/status/{today}-timecard.md"
        self.assertEqual(out.strip(), path)

        with open(os.path.join(self.dir, path), encoding="utf-8") as fh:
            doc = fh.read()
        for key in ("kind: timecard", f"date: {today}", "window: {from: ",
                    "through: ", "generated_at: "):
            self.assertIn(key, doc)
        self.assertTrue(doc.endswith(prose))

        p = self.run_wl("status", "--kind", "timecard", "--write", stdin="v2\n")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("frozen", p.stdout + p.stderr)

        # an explicit --until names the file, not the day it was run
        y = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400))
        out = self.ok("status", "--kind", "timecard", "--write",
                      "--until", y, stdin=prose)
        self.assertEqual(out.strip(), f"docs/status/{y}-timecard.md")

    def test_timecard_closed_item_lands_on_its_close_day(self):
        a = self.ok("add", "Ship it").strip()
        self.ok("close", a, "--resolution", "shipped")
        today = time.strftime("%Y-%m-%d", time.gmtime())
        day = {d["date"]: d for d in self.tc_facts()["days"]}[today]
        self.assertEqual(day["closed"],
                         [{"title": "Ship it", "resolution": "shipped",
                           "unplanned": False}])

    def test_dry_run_prints_and_writes_nothing(self):
        self.ok("add", "Something")
        out = self.ok("status", "--kind", "weekly", "--dry-run",
                      stdin="- weekly prose\n")
        self.assertIn("kind: weekly", out)
        self.assertIn("- weekly prose", out)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "docs", "status")))


if __name__ == "__main__":
    unittest.main()
