#!/usr/bin/env python3
"""worklog#242: warn when an item title cites a ticket number.

A title cannot know its own ticket number — the tracker mints that at the
next sync. So `#123` in a title is either a reference to a DIFFERENT ticket,
which reads as this item's own, or a guess that will be wrong. The case that
actually bites: an item created and closed inside one session never gets an
issue filed, so a commit citing "#254" points at somebody else's ticket.

Advisory, never a refusal — legitimate titles do cite other tickets.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import plan_capture                                             # noqa: E402


class TestTicketRefDetection(unittest.TestCase):

    def test_plain_reference_is_found(self):
        self.assertEqual(plan_capture.ticket_refs("Fix the thing from #98"),
                         ["#98"])

    def test_several_references_are_all_named(self):
        self.assertEqual(
            plan_capture.ticket_refs("Supersede #98 and #125"),
            ["#98", "#125"])

    def test_a_clean_title_is_silent(self):
        self.assertEqual(plan_capture.ticket_refs(
            "Extract the auth middleware"), [])

    def test_none_and_empty_do_not_crash(self):
        self.assertEqual(plan_capture.ticket_refs(None), [])
        self.assertEqual(plan_capture.ticket_refs(""), [])

    def test_a_language_name_is_not_a_ticket(self):
        """`C#` is the obvious false positive; so is a colour."""
        self.assertEqual(plan_capture.ticket_refs("Port the C# adapter"), [])
        self.assertEqual(plan_capture.ticket_refs("Use #ff0000 for errors"), [])

    def test_a_url_fragment_is_not_a_ticket(self):
        self.assertEqual(plan_capture.ticket_refs(
            "See https://example.invalid/docs/#3 for the rationale"), [])

    def test_a_ulid_is_not_flagged(self):
        """ULIDs are the RECOMMENDED alternative — flagging them would tell
        the author to stop doing the right thing."""
        self.assertEqual(plan_capture.ticket_refs(
            "Follow up on 01KYADGT9Q48EKJZVQQSH4HXWZ"), [])


class TestWarningIsAdvisory(unittest.TestCase):
    """The property that matters most: it warns, and the write still lands."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-242-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        os.makedirs(os.path.join(self.dir, ".work"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.dir, ".work", f), "w").close()

    def add(self, title):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "bin", "worklog"),
             "--actor", "t", "add", title, "--level", "task",
             "--kind", "ops", "--priority", "P3"],
            cwd=self.dir, capture_output=True, text=True)

    def test_citing_a_ticket_warns_but_succeeds(self):
        p = self.add("Fix the thing from #98")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("WARNING", p.stderr)
        self.assertIn("#98", p.stderr)
        self.assertTrue(p.stdout.strip(), "the item must still be created")

    def test_the_warning_names_the_alternative(self):
        p = self.add("Fix the thing from #98")
        self.assertIn("ULID", p.stderr)

    def test_a_clean_title_produces_no_warning(self):
        p = self.add("Extract the auth middleware")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("WARNING", p.stderr)

    def test_the_item_lands_in_the_log_either_way(self):
        iid = self.add("Fix the thing from #98").stdout.strip()
        with open(os.path.join(self.dir, ".work", "todo.jsonl")) as fh:
            self.assertIn(iid, fh.read())


class TestPlanCaptureWarns(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-242-pc-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        os.makedirs(os.path.join(self.dir, ".work"))
        os.makedirs(os.path.join(self.dir, "docs", "plans"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.dir, ".work", f), "w").close()

    def capture(self, draft):
        path = os.path.join(self.dir, "draft.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(draft)
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "bin", "worklog"),
             "--actor", "t", "plan-capture", "--slug", "s",
             "--title", "T", "--file", path],
            cwd=self.dir, capture_output=True, text=True)

    def test_a_task_title_citing_a_ticket_warns(self):
        p = self.capture("# P\n\n## Tasks\n\n- [ ] (P2) Revert #98\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("#98", p.stderr)
        self.assertTrue(os.path.exists(
            os.path.join(self.dir, "docs", "plans",
                         sorted(os.listdir(os.path.join(
                             self.dir, "docs", "plans")))[0])),
            "capture must still write the plan")

    def test_clean_tasks_capture_silently(self):
        p = self.capture("# P\n\n## Tasks\n\n- [ ] (P2) Extract the parser\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("WARNING", p.stderr)


if __name__ == "__main__":
    unittest.main()
