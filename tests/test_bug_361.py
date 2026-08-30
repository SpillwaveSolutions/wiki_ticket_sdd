#!/usr/bin/env python3
"""Bug #361: bot pushes to main skip CI.

GitHub does not trigger `on: push` workflows for commits made with the
default GITHUB_TOKEN. Compact used to push that way, so worklog-invariants
never ran on those commits. Compact already self-checks before it opens a
PR. The remaining gap is main's check history, closed by listening
on workflow_run of worklog-compact — an event GitHub does fire for
GITHUB_TOKEN pushes. Compact now lands via PR (ADR-0010) because the
merge-when-green ruleset rejects GITHUB_TOKEN pushes to main.
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCompactCannotSkipInvariants(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, ".github/workflows/worklog.yml")) as fh:
            self.worklog = fh.read()
        with open(os.path.join(ROOT, ".github/workflows/compact.yml")) as fh:
            self.compact = fh.read()

    def test_invariants_listen_on_compact_workflow_run(self):
        self.assertIn("workflow_run", self.worklog)
        self.assertIn("worklog-compact", self.worklog)
        self.assertIn("workflow_dispatch", self.worklog)

    def test_workflow_run_checks_out_main_not_the_pre_compact_sha(self):
        """workflow_run.head_sha is the commit that *started* compact, not
        the commit compact pushed. Checking that out would miss the break."""
        self.assertIn("ref: main", self.worklog)
        self.assertNotRegex(
            self.worklog,
            r"ref:\s*\$\{\{\s*github\.event\.workflow_run\.head_sha")

    def test_compact_still_self_checks_before_push(self):
        # Self-check still happens before the bot PR is opened. Step names
        # changed when compact stopped pushing main (GH013 on run 33299168867).
        self.assertIn("verify working tree", self.compact)
        self.assertIn("hooks/pre-commit", self.compact)
        compact_body = self.compact.split("name: commit via PR")[0]
        self.assertIn("python3 bin/compact.py --merge-check", compact_body)
        self.assertIn("gh pr merge --auto --merge", self.compact)


if __name__ == "__main__":
    unittest.main()
