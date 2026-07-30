#!/usr/bin/env python3
"""Tests for bug #243 (merge resurrects compacted lines) and bug #237 (merge
creates duplicate external-ticket ownership).

Both bugs only reproduce through git's own merge machinery (the union merge
driver on `.work/*.jsonl`, or a plain content merge on appended lines) -- not
through fold()/compact() called in isolation -- so every test here builds a
REAL throwaway git repo (never the project's own .work/*.jsonl) and runs a
REAL `git merge`.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
HOOKS = os.path.join(ROOT, "hooks")

sys.path.insert(0, BIN)
from compact import compact, check_resurrection, check_duplicate_ownership  # noqa: E402


def sh(cwd, *args, check=True, env=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    if check and p.returncode != 0:
        raise AssertionError(f"{args} in {cwd} failed:\n{p.stdout}\n{p.stderr}")
    return p


def write_jsonl(path, events):
    with open(path, "w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")


def append_jsonl(path, events):
    with open(path, "a", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")


def ev(n, item, op="create", **extra):
    e = {"ev": f"01A{n:04d}", "ts": "t", "actor": "r", "item": item, "op": op}
    e.update(extra)
    return e


class GitRepo(unittest.TestCase):
    """A throwaway repo with a real .git and the union-merge attribute this
    bug depends on. WIRE_HOOKS=True additionally installs the real hooks/ and
    a minimal bin/ so `git merge` itself exercises the guard end to end."""

    WIRE_HOOKS = False

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-mergebug-")
        self.addCleanup(shutil.rmtree, self.d, True)
        sh(self.d, "git", "init", "-q")
        sh(self.d, "git", "config", "user.email", "t@t.com")
        sh(self.d, "git", "config", "user.name", "t")
        os.makedirs(os.path.join(self.d, ".work"))
        with open(os.path.join(self.d, ".gitattributes"), "w") as fh:
            fh.write(".work/todo.jsonl merge=union\n"
                     ".work/done.jsonl merge=union\n")
        self.todo = os.path.join(self.d, ".work", "todo.jsonl")
        self.done = os.path.join(self.d, ".work", "done.jsonl")
        write_jsonl(self.todo, [])
        write_jsonl(self.done, [])
        if self.WIRE_HOOKS:
            # Only the modules compact.py actually needs -- not the whole
            # bin/, so the OTHER guarded checks in pre-commit (roadmap, ADR,
            # IA) stay inert (their trigger files don't exist here) instead
            # of failing on an unrelated, un-configured fixture repo.
            os.makedirs(os.path.join(self.d, "bin"))
            for name in ("compact.py", "fold.py", "ulid.py", "render_roadmap.py"):
                shutil.copy(os.path.join(BIN, name), os.path.join(self.d, "bin", name))
            os.makedirs(os.path.join(self.d, "hooks"))
            for name in ("pre-commit", "pre-merge-commit"):
                shutil.copy(os.path.join(HOOKS, name), os.path.join(self.d, "hooks", name))
                os.chmod(os.path.join(self.d, "hooks", name), 0o755)
            sh(self.d, "git", "config", "core.hooksPath", "hooks")
        self._commit("base")
        self.trunk = sh(self.d, "git", "symbolic-ref", "--short", "HEAD").stdout.strip()

    def _commit(self, msg):
        # Branch-discipline (a different guard, hooks/pre-commit) is out of
        # scope here -- nightly compaction and these fixtures both commit
        # straight to main/a throwaway branch, which is exactly what that
        # guard exists to stop a HUMAN from doing.
        env = dict(os.environ, WORKLOG_SKIP_BRANCH_GUARD="1")
        sh(self.d, "git", "add", "-A", env=env)
        sh(self.d, "git", "commit", "-q", "-m", msg, env=env)

    def _checkout(self, name, new=False):
        sh(self.d, "git", "checkout", "-q", *(["-b", name] if new else [name]))

    def _merge(self, branch):
        return sh(self.d, "git", "merge", "-q", "--no-edit", branch, check=False)


class TestResurrectionDetected(GitRepo):
    """#243: a branch that predates a nightly compaction, pulled after it
    lands, restores every line the compaction removed via the union merge
    driver -- reproduced here with git itself, not a mock."""

    def _seed_and_compact(self, n=49):
        events = [ev(i, f"I{i}", set={"status": "done"}) for i in range(1, n + 1)]
        write_jsonl(self.todo, events)
        self._commit("full log")
        self._checkout("stale", new=True)   # never sees the compaction
        self._checkout(self.trunk)
        compact(self.todo, self.done)       # the nightly job
        self._commit("nightly compaction")
        self._checkout("stale")
        # "plus two new events" -- the near-miss from the ticket.
        append_jsonl(self.todo, [ev(n + 1, "Inew1", set={"status": "todo"}),
                                  ev(n + 2, "Inew2", set={"status": "todo"})])
        self._commit("two new events")

    def test_stale_branch_merge_is_detected(self):
        self._seed_and_compact()
        merged = self._merge(self.trunk)
        self.assertEqual(merged.returncode, 0, merged.stderr)  # union auto-merges cleanly
        problems = check_resurrection(self.todo, self.done)
        self.assertTrue(problems, "expected the resurrection to be flagged")
        self.assertTrue(any("resurrect" in p for p in problems), problems)
        # The size win really was lost, which is the whole bug.
        with open(self.todo) as fh:
            self.assertGreater(sum(1 for _ in fh), 50)

    def test_normal_merge_without_compaction_passes_cleanly(self):
        """No compaction ever ran on either side -- must not cry wolf."""
        write_jsonl(self.todo, [ev(1, "SEED", set={"status": "todo"})])
        self._commit("seed")
        self._checkout("branchA", new=True)
        append_jsonl(self.todo, [ev(2, "A", set={"status": "todo"})])
        self._commit("A change")
        self._checkout(self.trunk)
        self._checkout("branchB", new=True)
        append_jsonl(self.todo, [ev(3, "B", set={"status": "todo"})])
        self._commit("B change")
        merged = self._merge("branchA")
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(check_resurrection(self.todo, self.done), [])

    def test_merge_after_both_sides_saw_the_compaction_passes_cleanly(self):
        """Both branches forked AFTER the compaction and only append fresh
        events -- must not cry wolf either."""
        write_jsonl(self.todo, [ev(1, "I1", set={"status": "done"})])
        self._commit("seed")
        compact(self.todo, self.done)
        self._commit("nightly compaction")
        self._checkout("branchA", new=True)
        append_jsonl(self.todo, [ev(9001, "A", set={"status": "todo"})])
        self._commit("A change")
        self._checkout(self.trunk)
        self._checkout("branchB", new=True)
        append_jsonl(self.todo, [ev(9002, "B", set={"status": "todo"})])
        self._commit("B change")
        merged = self._merge("branchA")
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(check_resurrection(self.todo, self.done), [])


class TestResurrectionHookWiring(TestResurrectionDetected):
    """Same scenarios, but through the actual installed hooks/pre-merge-commit
    and hooks/pre-commit -- proves the guard is really wired, not just that
    the underlying function is correct."""

    WIRE_HOOKS = True

    def test_stale_branch_merge_is_detected(self):
        self._seed_and_compact()
        merged = self._merge(self.trunk)
        self.assertNotEqual(merged.returncode, 0, "hook should have blocked the merge")
        self.assertIn("resurrect", merged.stdout + merged.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.d, ".git", "MERGE_HEAD")),
                         "a blocked merge must be left for the user to resolve, "
                         "not silently discarded")


class TestDuplicateOwnershipMerge(GitRepo):
    """#237: linking refuses a ticket another item already owns, so the only
    remaining way to create a duplicate is a merge of two branches that each
    claimed the same ticket before either saw the other's claim."""

    def _branch_claims(self, branch, item, key, base_ev):
        self._checkout(branch, new=True)
        append_jsonl(self.todo, [ev(base_ev, item, op="create",
                                    set={"status": "todo"}),
                                  ev(base_ev + 1, item, op="link",
                                    set={"external": {"system": "github", "key": key}})])
        self._commit(f"{branch} claims {key}")
        self._checkout(self.trunk)

    def test_same_ticket_claimed_by_both_branches_is_refused(self):
        self._branch_claims("branchA", "A", "42", 1)
        self._checkout("branchB", new=True)
        append_jsonl(self.todo, [ev(101, "B", op="create", set={"status": "todo"}),
                                  ev(102, "B", op="link",
                                     set={"external": {"system": "github", "key": "42"}})])
        self._commit("branchB claims 42")
        merged = self._merge("branchA")
        self.assertEqual(merged.returncode, 0, merged.stderr)  # plain append, no conflict
        problems = check_duplicate_ownership(self.todo, self.done)
        self.assertTrue(problems, "expected the duplicate ticket claim to be flagged")
        joined = " ".join(problems)
        self.assertIn("github:42", joined)
        self.assertIn("A", joined)
        self.assertIn("B", joined)

    def test_different_tickets_claimed_by_each_branch_passes_cleanly(self):
        self._branch_claims("branchA", "A", "42", 1)
        self._checkout("branchB", new=True)
        append_jsonl(self.todo, [ev(101, "B", op="create", set={"status": "todo"}),
                                  ev(102, "B", op="link",
                                     set={"external": {"system": "github", "key": "43"}})])
        self._commit("branchB claims 43")
        merged = self._merge("branchA")
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(check_duplicate_ownership(self.todo, self.done), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
