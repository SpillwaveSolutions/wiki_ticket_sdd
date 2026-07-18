#!/usr/bin/env python3
"""Tests for `worklog link` (spec 5.3) and `worklog wiki-add` (spec 9.2)."""
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
        self.dir = tempfile.mkdtemp(prefix="worklog-link-")
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


class TestLink(Sandbox):
    def test_link_then_show_has_external(self):
        item = self.wl("add", "Push me")
        self.wl("link", item, "--system", "github", "--key", "123",
                "--url", "https://github.com/o/r/issues/123")
        shown = json.loads(self.wl("show", item))
        ext = shown["external"]
        self.assertEqual(ext["system"], "github")
        self.assertEqual(ext["key"], "123")
        self.assertEqual(ext["url"], "https://github.com/o/r/issues/123")
        self.assertTrue(ext["synced_at"])

    def test_link_survives_fold_with_update(self):
        item = self.wl("add", "Push me")
        self.wl("update", item, "--status", "in_progress")
        self.wl("link", item, "--system", "github", "--key", "7")
        shown = json.loads(self.wl("show", item))
        self.assertEqual(shown["status"], "in_progress")
        self.assertEqual(shown["external"]["key"], "7")

    def test_link_missing_key_exits_nonzero(self):
        item = self.wl("add", "Push me")
        p = self.run_wl("link", item, "--system", "github")
        self.assertNotEqual(p.returncode, 0)


class TestWikiAdd(Sandbox):
    def setUp(self):
        super().setUp()
        self.published = os.path.join(self.dir, ".work", "published.json")
        with open(os.path.join(self.dir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# Plan\n")

    def read_published(self):
        with open(self.published, encoding="utf-8") as fh:
            return json.load(fh)

    def test_creates_entry_with_source_and_null_url(self):
        out = self.wl("wiki-add", "plan.md", "--key", "plan/x", "--title", "Plan X")
        self.assertEqual(out, "plan/x")
        entry = self.read_published()["plan/x"]
        self.assertEqual(entry["source"], "plan.md")
        self.assertEqual(entry["title"], "Plan X")
        self.assertIsNone(entry["url"])
        self.assertIsNone(entry["rev"])
        self.assertIsNone(entry["source_hash"])

    def test_reregister_preserves_publish_state(self):
        with open(self.published, "w", encoding="utf-8") as fh:
            json.dump({"plan/x": {"source": "old.md", "title": "Old",
                                  "url": "https://wiki/x", "rev": "3",
                                  "source_hash": "abc"}}, fh)
        self.wl("wiki-add", "plan.md", "--key", "plan/x", "--title", "New title")
        entry = self.read_published()["plan/x"]
        self.assertEqual(entry["source"], "plan.md")
        self.assertEqual(entry["title"], "New title")
        self.assertEqual(entry["url"], "https://wiki/x")
        self.assertEqual(entry["rev"], "3")
        self.assertEqual(entry["source_hash"], "abc")

    def test_missing_file_exits_nonzero(self):
        p = self.run_wl("wiki-add", "nope.md", "--key", "k", "--title", "T")
        self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
