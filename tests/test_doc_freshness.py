#!/usr/bin/env python3
"""Release gate: the live design pair must descend from the latest tag and
the tag must have a freeze record (v0.24.10 review, P1 process).

Plan: docs/plans/2026-09-19-review-v0-24-10-and-open-tickets.md
Item: 01M2XCWMVEH3XFP2VPS9JBD6XQ
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import doc_verify  # noqa: E402


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout.strip()


class TestFreshness(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-fresh-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.prev = os.getcwd()
        self.addCleanup(os.chdir, self.prev)
        os.chdir(self.dir)
        git(self.dir, "init", "-q")
        git(self.dir, "config", "user.email", "t@t")
        git(self.dir, "config", "user.name", "t")
        os.makedirs("docs/designs")
        self.live = "docs/designs/current_design_doc.md"
        self.stamp("0000000")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "a")
        self.a = git(self.dir, "rev-parse", "HEAD")
        with open("code.txt", "w") as fh:
            fh.write("x")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "b")
        self.b = git(self.dir, "rev-parse", "HEAD")
        git(self.dir, "tag", "v0.1.0")

    def stamp(self, sha):
        with open(self.live, "w") as fh:
            fh.write("---\ngit_hash: \"%s\"\ntag: v0.1.0\n---\n# live\n" % sha)

    def records(self, sha):
        return {"design-doc": {"source": self.live, "git_hash": sha}}

    def test_no_tag_means_nothing_to_compare(self):
        git(self.dir, "tag", "-d", "v0.1.0")
        self.assertEqual(doc_verify.freshness(self.records(self.a)), [])

    def test_stale_hash_and_missing_freeze_record_both_fail(self):
        f = doc_verify.freshness(self.records(self.a))
        verdicts = sorted((x["doc"], x["verdict"]) for x in f)
        self.assertEqual(verdicts, [("design-doc", "stale"), ("design-freeze", "stale")])
        self.assertIn("predates tag v0.1.0", f[0]["detail"])
        self.assertTrue(doc_verify.failing(f))

    def test_unresolvable_hash_is_stale(self):
        f = doc_verify.freshness(self.records("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"))
        self.assertEqual(f[0]["verdict"], "stale")
        self.assertIn("not in this clone", f[0]["detail"])

    def test_fresh_hash_with_freeze_note_passes(self):
        with open("docs/designs/2026-01-01_v0.1.0-release.md", "w") as fh:
            fh.write("---\ntag: v0.1.0\n---\n")
        self.assertEqual(doc_verify.freshness(self.records(self.b)), [])
        # A commit after the tag is fine too: the tag is an ancestor.
        with open("code.txt", "a") as fh:
            fh.write("y")
        git(self.dir, "commit", "-q", "-am", "c")
        c = git(self.dir, "rev-parse", "HEAD")
        self.assertEqual(doc_verify.freshness(self.records(c)), [])

    def test_historical_dated_pair_counts_as_the_freeze_record(self):
        with open("docs/designs/2026-01-01_v0.1.0-release_design_doc.md", "w") as fh:
            fh.write("---\ntag: v0.1.0\n---\n")
        self.assertEqual(doc_verify.freshness(self.records(self.b)), [])

    def test_freeze_record_must_name_the_tag(self):
        with open("docs/designs/2026-01-01_v0.1.0-release.md", "w") as fh:
            fh.write("---\ntag: v0.0.9\n---\n")
        f = doc_verify.freshness(self.records(self.b))
        self.assertEqual([x["doc"] for x in f], ["design-freeze"])

    def test_staged_scope_skips_freshness(self):
        """A commit hook scoped with `only` must not fail every commit
        between a tag and the doc PR that follows it."""
        f, s = doc_verify.verify(records=self.records(self.a), only={self.live})
        self.assertEqual(s.get("stale", 0), 0)
        f, s = doc_verify.verify(records=self.records(self.a))
        self.assertEqual(s["stale"], 2)


if __name__ == "__main__":
    unittest.main()
