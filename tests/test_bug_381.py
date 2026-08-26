#!/usr/bin/env python3
"""Bug #381: generated files conflict on every concurrent branch.

`.work/todo.jsonl` union-merges. docs/roadmap.md does not, and pre-commit
requires every branch to carry a fresh render, so two branches that each
add a work item always conflict on a file nobody edited by hand.

Fix: `merge=ours` on generated paths (built-in, no local git config) plus
regenerate inside pre-merge-commit before the freshness gate runs.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cwd, *cmd, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise AssertionError(
            f"$ {' '.join(cmd)}\nexit {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


class TestGeneratedMergeDriver(unittest.TestCase):
    def test_gitattributes_marks_generated_paths_ours(self):
        text = open(os.path.join(ROOT, ".gitattributes"), encoding="utf-8").read()
        self.assertIn(".work/todo.jsonl merge=union", text)
        self.assertIn("docs/roadmap.md merge=ours", text)
        self.assertIn("docs/.index/** merge=ours", text)

    def test_init_sh_installs_the_generated_merge_lines(self):
        init = open(os.path.join(ROOT, "plugin/scripts/init.sh"),
                    encoding="utf-8").read()
        self.assertIn("docs/roadmap.md merge=ours", init)
        self.assertIn("docs/.index/** merge=ours", init)
        self.assertIn("merge.ours.driver", init)

    def test_pre_merge_commit_regenerates_before_it_validates(self):
        hook = open(os.path.join(ROOT, "hooks/pre-merge-commit"),
                    encoding="utf-8").read()
        self.assertIn("render_roadmap.py", hook)
        self.assertIn("git add", hook)
        self.assertIn("WORKLOG_MERGE_COMMIT=1", hook)
        # Still hands off to pre-commit so the freshness gate actually runs.
        self.assertIn("pre-commit", hook)


class TestConcurrentBranchesDoNotConflictOnRoadmap(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-381-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        for d in ("bin", "hooks", "tests"):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(self.dir, d))
        me = os.path.join(self.dir, "tests", "test_bug_381.py")
        if os.path.exists(me):
            os.remove(me)
        it = os.path.join(self.dir, "tests", "test_integration.py")
        if os.path.exists(it):
            os.remove(it)
        os.makedirs(os.path.join(self.dir, ".work"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.dir, ".work", f), "w").close()
        shutil.copy(os.path.join(ROOT, ".gitattributes"),
                    os.path.join(self.dir, ".gitattributes"))
        with open(os.path.join(self.dir, ".gitignore"), "w") as fh:
            fh.write("__pycache__/\n*.pyc\n")
        sh(self.dir, "git", "init", "-q", "-b", "main")
        sh(self.dir, "git", "config", "user.email", "it@test.invalid")
        sh(self.dir, "git", "config", "user.name", "integration-test")
        sh(self.dir, "git", "config", "core.hooksPath", "hooks")
        # Named driver, not built-in: without this, merge=ours is a missing
        # driver and git falls back to a text merge that conflicts (#381).
        sh(self.dir, "git", "config", "merge.ours.driver", "true")
        sh(self.dir, sys.executable, "bin/worklog", "roadmap-render")
        sh(self.dir, "git", "add", "-A")
        sh(self.dir, "git", "commit", "-q", "--no-verify", "-m", "init")

    def add_on_branch(self, branch, title):
        sh(self.dir, "git", "checkout", "-q", "main")
        sh(self.dir, "git", "checkout", "-q", "-b", branch)
        p = sh(self.dir, sys.executable, "bin/worklog", "--actor", "it",
               "add", title, "--priority", "P1")
        iid = p.stdout.strip()
        sh(self.dir, sys.executable, "bin/worklog", "roadmap-render")
        sh(self.dir, "git", "add", "-A")
        sh(self.dir, "git", "commit", "-q", "-m", f"feat: {iid}")
        return iid

    def test_merge_of_two_item_branches_is_clean_and_names_both(self):
        a = self.add_on_branch("branch-a", "Item A from branch A")
        b = self.add_on_branch("branch-b", "Item B from branch B")
        sh(self.dir, "git", "checkout", "-q", "branch-a")
        merge = sh(self.dir, "git", "merge", "--no-edit", "branch-b", check=False)
        self.assertEqual(merge.returncode, 0,
                         merge.stdout + merge.stderr)
        unmerged = sh(self.dir, "git", "diff", "--name-only", "--diff-filter=U")
        self.assertEqual(unmerged.stdout.strip(), "", unmerged.stdout)
        roadmap = open(os.path.join(self.dir, "docs/roadmap.md"),
                       encoding="utf-8").read()
        self.assertIn("Item A from branch A", roadmap)
        self.assertIn("Item B from branch B", roadmap)
        self.assertIn(a[:8], roadmap)
        self.assertIn(b[:8], roadmap)


if __name__ == "__main__":
    unittest.main()
