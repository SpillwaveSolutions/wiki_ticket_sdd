#!/usr/bin/env python3
"""Tests for `worklog adr new|list|check` -- schema-validated ADRs."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cwd, *args):
    # sandbox convention: run the sandbox's own bin/ copy so subprocess
    # coverage (relative source=bin) attributes lines correctly
    return subprocess.run([sys.executable, os.path.join(cwd, "bin", "worklog"), *args],
                          cwd=cwd, capture_output=True, text=True)


class TestAdr(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-adr-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        shutil.copytree(os.path.join(ROOT, "schema"), os.path.join(self.dir, "schema"))

    def path(self, rel):
        return os.path.join(self.dir, rel)

    def read(self, rel):
        with open(self.path(rel), encoding="utf-8") as fh:
            return fh.read()

    def write(self, rel, text):
        with open(self.path(rel), "w", encoding="utf-8") as fh:
            fh.write(text)

    def check(self):
        return run(self.dir, "adr", "check")

    def test_new_round_trips_check_and_registers_ledger(self):
        p = run(self.dir, "adr", "new", "Use event log")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "docs/adr/0001-use-event-log.md")
        c = self.check()
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        self.assertIn("1 records ok", c.stdout)
        pub = json.loads(self.read(".work/published.json"))
        entry = pub["adr/0001-use-event-log"]
        self.assertEqual(entry["source"], "docs/adr/0001-use-event-log.md")
        self.assertEqual(entry["title"], "ADR-0001-use-event-log")

    def test_existing_target_is_refused(self):
        self.assertEqual(run(self.dir, "adr", "new", "First").returncode, 0)
        os.rename(self.path("docs/adr/0001-first.md"),
                  self.path("docs/adr/0002-first.md"))
        p = run(self.dir, "adr", "new", "First")  # next id 3, distinct name ok
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "docs/adr/0003-first.md")

    def test_bad_status_named(self):
        run(self.dir, "adr", "new", "First")
        self.write("docs/adr/0001-first.md",
                   self.read("docs/adr/0001-first.md")
                   .replace("status: proposed", "status: bogus"))
        c = self.check()
        self.assertEqual(c.returncode, 1)
        self.assertIn("status", c.stdout)

    def test_duplicate_id_named(self):
        run(self.dir, "adr", "new", "First")
        shutil.copyfile(self.path("docs/adr/0001-first.md"),
                        self.path("docs/adr/0001-zzz.md"))
        c = self.check()
        self.assertEqual(c.returncode, 1)
        self.assertIn("duplicate id", c.stdout)

    def test_filename_id_mismatch_named(self):
        run(self.dir, "adr", "new", "First")
        os.rename(self.path("docs/adr/0001-first.md"),
                  self.path("docs/adr/0002-first.md"))
        c = self.check()
        self.assertEqual(c.returncode, 1)
        self.assertIn("filename", c.stdout)

    def test_missing_context_section_named(self):
        run(self.dir, "adr", "new", "First")
        self.write("docs/adr/0001-first.md",
                   self.read("docs/adr/0001-first.md")
                   .replace("## Context", "## Backdrop"))
        c = self.check()
        self.assertEqual(c.returncode, 1)
        self.assertIn("## Context", c.stdout)

    def test_supersede_flow_mutates_old_status_and_superseded_by(self):
        run(self.dir, "adr", "new", "Old way")
        p = run(self.dir, "adr", "new", "New way", "--supersedes", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        old = self.read("docs/adr/0001-old-way.md")
        self.assertIn("status: superseded", old)
        self.assertIn("superseded_by: 2", old)
        self.assertIn("supersedes: 1", self.read("docs/adr/0002-new-way.md"))
        c = self.check()
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)

    def test_superseded_without_superseded_by_named(self):
        run(self.dir, "adr", "new", "First")
        self.write("docs/adr/0001-first.md",
                   self.read("docs/adr/0001-first.md")
                   .replace("status: proposed", "status: superseded"))
        c = self.check()
        self.assertEqual(c.returncode, 1)
        self.assertIn("superseded_by", c.stdout)

    def test_list_sorted_by_id(self):
        run(self.dir, "adr", "new", "First")
        run(self.dir, "adr", "new", "Second", "--status", "accepted")
        p = run(self.dir, "adr", "list")
        self.assertEqual(p.returncode, 0, p.stderr)
        lines = p.stdout.strip().split("\n")
        self.assertTrue(lines[0].startswith("0001"))
        self.assertIn("accepted", lines[1])
        self.assertIn("Second", lines[1])


if __name__ == "__main__":
    unittest.main()
