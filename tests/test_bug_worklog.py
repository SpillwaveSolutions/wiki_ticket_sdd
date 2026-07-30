#!/usr/bin/env python3
"""Tests for two bug tickets in bin/worklog.

#221 -- `roadmap-snapshot` used to copy docs/roadmap.md as-is, so a snapshot
could freeze a picture that predated the last log write.

#240 -- `conflict`/`resolve` took any field name, including `external` (a
structured link, not a string) and `id` (identity, not data), so a later
sync crashed reading the corrupted value.

Sandbox subprocess style (see tests/test_snapshot.py, tests/test_resolve.py):
every test runs `bin/worklog` against a scratch tempdir, never the real log.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKLOG = os.path.join(ROOT, "bin", "worklog")


def run(cwd, *args):
    return subprocess.run([sys.executable, WORKLOG, *args],
                          cwd=cwd, capture_output=True, text=True)


class Bug221RoadmapSnapshotFreshness(unittest.TestCase):
    """A snapshot must not freeze a docs/roadmap.md that predates the log."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-bug221-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        os.makedirs(os.path.join(self.dir, ".work"))

    def add(self, title):
        p = run(self.dir, "add", title, "--level", "task", "--kind", "feature")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def read(self, rel):
        with open(os.path.join(self.dir, rel), encoding="utf-8") as fh:
            return fh.read()

    def test_stale_roadmap_is_regenerated_before_snapshot(self):
        """Two releases in a row froze a snapshot missing the release's own
        work item (the ticket, verbatim). Add an item, render, THEN add a
        second item without re-rendering -- roadmap.md is now stale."""
        self.add("Item One")
        p = run(self.dir, "roadmap-render")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("Item Two", self.read("docs/roadmap.md"))

        self.add("Item Two")  # log moved on; docs/roadmap.md did not

        date = time.strftime("%Y-%m-%d", time.gmtime())
        p = run(self.dir, "roadmap-snapshot", "--name", "stale")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        snapshot = self.read(f"docs/roadmap/{date}_stale.md")
        self.assertIn("Item Two", snapshot,
                      "snapshot froze a picture missing the newly-added item")
        # self-healing: the live roadmap was brought current too, not just
        # the frozen copy.
        self.assertIn("Item Two", self.read("docs/roadmap.md"))

    def test_fresh_roadmap_snapshot_still_works_unchanged(self):
        """No log change since the last render -- regenerating is a no-op
        (render() is a pure function of the log), so the snapshot must still
        succeed and carry the same content it always did."""
        self.add("Solo Item")
        p = run(self.dir, "roadmap-render")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        before = self.read("docs/roadmap.md")

        date = time.strftime("%Y-%m-%d", time.gmtime())
        p = run(self.dir, "roadmap-snapshot", "--name", "fresh")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        snapshot = self.read(f"docs/roadmap/{date}_fresh.md")
        self.assertIn("Solo Item", snapshot)
        # body (everything after the frontmatter) is untouched when already fresh
        self.assertEqual(before.split("<!-- GENERATED", 1)[1],
                         snapshot.split("<!-- GENERATED", 1)[1])
        # live roadmap.md was not perturbed either
        self.assertEqual(before, self.read("docs/roadmap.md"))


class Bug240ConflictResolveFieldAllowlist(unittest.TestCase):
    """conflict/resolve must refuse `external` and `id`, and name the
    allowed fields so an operator can recover."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-bug240-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        os.makedirs(os.path.join(self.dir, ".work"))
        p = run(self.dir, "add", "Conflicted Item", "--level", "task",
               "--kind", "feature", "--priority", "P2")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.iid = p.stdout.strip()

    def conflict(self, *args):
        return run(self.dir, "conflict", self.iid, *args,
                   "--local", "local-val", "--remote", "remote-val",
                   "--remote-rev", "r1")

    def resolve(self, field, take="remote"):
        return run(self.dir, "resolve", self.iid, "--field", field, "--take", take)

    # -- rejected fields --------------------------------------------------

    def test_conflict_refuses_external(self):
        p = self.conflict("--field", "external")
        self.assertNotEqual(p.returncode, 0, "conflict accepted the external-identity field")
        out = p.stdout + p.stderr
        self.assertIn("external", out)
        self.assertIn("title", out, "rejection must name what IS allowed")

    def test_conflict_refuses_id(self):
        p = self.conflict("--field", "id")
        self.assertNotEqual(p.returncode, 0, "conflict accepted id")
        self.assertIn("title", p.stdout + p.stderr)

    def test_resolve_refuses_external(self):
        p = self.resolve("external")
        self.assertNotEqual(p.returncode, 0, "resolve accepted the external-identity field")
        out = p.stdout + p.stderr
        self.assertIn("external", out)
        self.assertIn("title", out)

    def test_resolve_refuses_id(self):
        p = self.resolve("id")
        self.assertNotEqual(p.returncode, 0, "resolve accepted id")
        self.assertIn("title", p.stdout + p.stderr)

    # -- ordinary fields still work, end to end ---------------------------

    def test_conflict_and_resolve_still_accept_ordinary_fields(self):
        for field, local, remote in (
            ("title", "Local Title", "Remote Title"),
            ("body", "local body", "remote body"),
            ("status", "in_progress", "blocked"),
            ("priority", "P2", "P0"),
            ("milestone", "v0.1.0", "v0.2.0"),
        ):
            with self.subTest(field=field):
                p = run(self.dir, "conflict", self.iid, "--field", field,
                        "--local", local, "--remote", remote, "--remote-rev", "r1")
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                p = run(self.dir, "resolve", self.iid, "--field", field, "--take", "remote")
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertIn(remote, p.stdout)


if __name__ == "__main__":
    unittest.main()
