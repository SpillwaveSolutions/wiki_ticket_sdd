#!/usr/bin/env python3
"""Bug #361: bot pushes to main skip CI.

GitHub does not trigger `on: push` or `on: pull_request` workflows for
commits made with the default GITHUB_TOKEN. Compact used to push that
way, so worklog-invariants never ran on those commits; a workflow_run
listener papered over it, then a commit-status bridge did (v0.24.10).
ADR-0011 closes the gap at the source: bot commits and PRs are made with
a maintainer PAT, so the event-native runs fire and nothing else is
needed. Compact still self-checks before it opens a PR.
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
        with open(os.path.join(ROOT, ".github/workflows/post-merge.yml")) as fh:
            self.post_merge = fh.read()

    def test_bot_commits_carry_a_real_identity(self):
        """A PAT push fires push and pull_request natively (ADR-0011)."""
        for text in (self.compact, self.post_merge):
            self.assertIn("token: ${{ secrets.WORKLOG_BOT_PAT }}", text)
            self.assertIn("GH_TOKEN: ${{ secrets.WORKLOG_BOT_PAT }}", text)
            self.assertNotIn("github.token", text)

    def test_invariants_is_event_native(self):
        """No workflow_run listener and no status bridge: the required
        checks come from the pull_request and push runs themselves."""
        self.assertIn("push:", self.worklog)
        self.assertIn("pull_request:", self.worklog)
        self.assertIn("workflow_dispatch", self.worklog)
        self.assertNotIn("workflow_run", self.worklog.split("jobs:", 1)[1])
        self.assertNotIn("workflows: [", self.worklog)
        self.assertNotIn("ref: main", self.worklog)

    def test_compact_still_self_checks_before_push(self):
        self.assertIn("verify working tree", self.compact)
        self.assertIn("hooks/pre-commit", self.compact)
        compact_body = self.compact.split("name: commit via PR")[0]
        self.assertIn("python3 bin/compact.py --merge-check", compact_body)
        self.assertIn("gh pr merge --auto --merge", self.compact)


if __name__ == "__main__":
    unittest.main()
