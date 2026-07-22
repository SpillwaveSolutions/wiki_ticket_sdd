#!/usr/bin/env python3
"""Tests for `worklog roadmap-snapshot` -- frozen copies of docs/roadmap.md."""
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


class TestRoadmapSnapshot(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-snap-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        os.makedirs(os.path.join(self.dir, "docs"))
        with open(os.path.join(self.dir, "docs", "roadmap.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Roadmap\n\ncontent\n")

    def read(self, rel):
        with open(os.path.join(self.dir, rel), encoding="utf-8") as fh:
            return fh.read()

    def test_named_snapshot_creates_dated_copy_and_prints_path(self):
        date = time.strftime("%Y-%m-%d", time.gmtime())
        p = run(self.dir, "roadmap-snapshot", "--name", "pre-v2")
        self.assertEqual(p.returncode, 0, p.stderr)
        path = f"docs/roadmap/{date}_pre-v2.md"
        self.assertEqual(p.stdout.strip(), path)
        # the copy is restamped with snapshot identity (plan ia-content-model
        # §5.4); the roadmap body itself is carried over verbatim
        text = self.read(path)
        self.assertIn("# Roadmap\n\ncontent\n", text)
        self.assertIn(f"wiki_key: roadmap-snapshot/{date}_pre-v2", text)
        self.assertIn("truth_state: snapshot", text)
        self.assertIn("doc_type: roadmap-snapshot", text)

    def test_no_name_uses_date_only_filename(self):
        date = time.strftime("%Y-%m-%d", time.gmtime())
        p = run(self.dir, "roadmap-snapshot")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), f"docs/roadmap/{date}.md")

    def test_existing_snapshot_is_frozen(self):
        self.assertEqual(run(self.dir, "roadmap-snapshot", "--name", "x").returncode, 0)
        p = run(self.dir, "roadmap-snapshot", "--name", "x")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("frozen", p.stdout + p.stderr)

    def test_missing_roadmap_says_render_first(self):
        os.remove(os.path.join(self.dir, "docs", "roadmap.md"))
        p = run(self.dir, "roadmap-snapshot")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("roadmap-render first", p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
