#!/usr/bin/env python3
"""Item #136: draft the unreleased CHANGELOG section from git log.

The point is that "we forgot to write it" stops happening, so the tests care
most about two things: real changes must survive into the draft, and dropped
commits must be reported rather than silently vanishing.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
sys.path.insert(0, BIN)
import changelog  # noqa: E402


class TestClassify(unittest.TestCase):
    def test_feat_becomes_new(self):
        self.assertEqual(changelog.classify("feat(ia): add a thing", ["bin/ia.py"]),
                         ("New", "add a thing"))

    def test_fix_keeps_ticket_refs(self):
        label, text = changelog.classify("fix: repair X (#263, #257)", ["bin/x.py"])
        self.assertEqual(label, "Fix")
        self.assertIn("(#263, #257)", text)

    def test_worklog_ids_are_stripped(self):
        """Ticket refs are for readers; ULIDs are internal provenance."""
        _label, text = changelog.classify(
            "fix: something real (01KYTDN3W67ZFFDE1F60M2ST6T)", ["bin/x.py"])
        self.assertEqual(text, "something real")

    def test_unknown_type_still_lands_as_a_change(self):
        label, _ = changelog.classify("wibble: odd one", ["bin/x.py"])
        self.assertEqual(label, "Change")

    def test_subject_without_a_type_prefix_survives(self):
        label, text = changelog.classify("just did a thing", ["bin/x.py"])
        self.assertEqual((label, text), ("Change", "just did a thing"))

    def test_log_only_commit_is_excluded(self):
        label, reason = changelog.classify(
            "chore(worklog): compact through 01KY", [".work/todo.jsonl"])
        self.assertIsNone(label)
        self.assertIn("generated", reason)

    def test_index_and_roadmap_only_commit_is_excluded(self):
        label, _ = changelog.classify(
            "chore: refresh", ["docs/.index/_graph.json", "docs/roadmap.md"])
        self.assertIsNone(label)

    def test_a_code_change_alongside_log_churn_is_kept(self):
        """The trap: most real commits also touch .work/. Only commits that
        touch NOTHING else are housekeeping."""
        label, text = changelog.classify(
            "fix: real fix", [".work/todo.jsonl", "bin/fold.py"])
        self.assertEqual((label, text), ("Fix", "real fix"))

    def test_process_commits_are_excluded(self):
        for subject in ("plan: do a thing", "release: close out v1"):
            label, reason = changelog.classify(subject, ["docs/x.md"])
            self.assertIsNone(label, subject)
            self.assertIn("process", reason)


class TestDraftAgainstRealGit(unittest.TestCase):
    """A throwaway repo with a tag, so the range logic is exercised for real."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-changelog-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.addCleanup(os.chdir, os.getcwd())
        self._sh("git", "init", "-q")
        self._sh("git", "config", "user.email", "t@t")
        self._sh("git", "config", "user.name", "t")
        os.makedirs(os.path.join(self.d, ".work"))
        self._commit("chore: seed", "README.md", "hi")
        self._sh("git", "tag", "v1.0.0")

    def _sh(self, *args):
        return subprocess.run(args, cwd=self.d, capture_output=True, text=True)

    def _commit(self, subject, path, body):
        full = os.path.join(self.d, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "a") as fh:
            fh.write(body + "\n")
        self._sh("git", "add", "-A")
        self._sh("git", "commit", "-q", "-m", subject)

    def _draft(self, **kw):
        cwd = os.getcwd()
        os.chdir(self.d)
        try:
            return changelog.draft(**kw)
        finally:
            os.chdir(cwd)

    def test_only_commits_after_the_tag_appear(self):
        self._commit("feat: after the tag", "bin/a.py", "x")
        text, _ = self._draft(version="1.1.0")
        self.assertIn("after the tag", text)
        self.assertNotIn("seed", text)

    def test_housekeeping_is_excluded_but_reported(self):
        self._commit("feat: real work", "bin/a.py", "x")
        self._commit("chore(worklog): compact", ".work/todo.jsonl", "{}")
        text, excluded = self._draft(version="1.1.0")
        self.assertIn("real work", text)
        self.assertNotIn("compact", text)
        self.assertEqual(len(excluded), 1)
        self.assertIn("compact", excluded[0][0])

    def test_grouping_puts_new_before_fix_before_docs(self):
        self._commit("docs: a doc", "docs/d.md", "x")
        self._commit("fix: a fix", "bin/a.py", "x")
        self._commit("feat: a feature", "bin/b.py", "x")
        text, _ = self._draft(version="1.1.0")
        self.assertLess(text.index("**New**"), text.index("**Fix**"))
        self.assertLess(text.index("**Fix**"), text.index("**Docs**"))

    def test_version_is_never_guessed(self):
        self._commit("feat: x", "bin/a.py", "x")
        text, _ = self._draft()
        self.assertIn("## X.Y.Z — unreleased", text)

    def test_heading_is_the_shape_the_release_skill_requires(self):
        self._commit("feat: x", "bin/a.py", "x")
        text, _ = self._draft(version="1.2.3")
        self.assertTrue(text.startswith("## 1.2.3 — unreleased\n"))

    def test_no_product_changes_says_so_rather_than_emitting_nothing(self):
        self._commit("chore(worklog): compact", ".work/todo.jsonl", "{}")
        text, _ = self._draft(version="1.1.0")
        self.assertIn("No product changes", text)

    def test_cli_writes_markdown_to_stdout_and_report_to_stderr(self):
        self._commit("feat: visible", "bin/a.py", "x")
        self._commit("chore(worklog): hidden", ".work/todo.jsonl", "{}")
        p = subprocess.run(
            [sys.executable, os.path.join(BIN, "worklog"),
             "changelog-draft", "--version", "9.9.9"],
            cwd=self.d, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("## 9.9.9 — unreleased", p.stdout)
        self.assertIn("visible", p.stdout)
        self.assertNotIn("hidden", p.stdout)      # stdout stays pipeable
        self.assertIn("hidden", p.stderr)         # but nothing is silent


if __name__ == "__main__":
    unittest.main(verbosity=2)
