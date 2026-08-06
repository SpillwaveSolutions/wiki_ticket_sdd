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
from compact import (compact, check_resurrection, check_duplicate_ownership,  # noqa: E402
                     merge_check, merge_rescue)
from fold import fold  # noqa: E402


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


class TestSubWatermarkEventsAreLost(GitRepo):
    """#269 and the data-loss class it uncovered.

    ADR-0005 called check_resurrection a hygiene guard on the grounds that
    "the fold discards resurrected events on read, so no state is ever
    corrupted". That holds only for events the compaction actually folded.
    An event created on a branch BEFORE a compaction ran on main was never
    folded into any snapshot, yet it still sorts below the watermark -- so
    the fold discards it and the work is gone. These tests pin that down and
    prove `merge-rescue` gets it back.

    Hooks are wired because the rescue needs a merge left IN PROGRESS, which
    is exactly what the guard blocking the merge commit produces.
    """

    WIRE_HOOKS = True

    def _fork_compact_merge(self):
        """The live 2026-07-31 sequence: branch forks, does work, nightly
        compaction lands on main while the PR is open, branch pulls main."""
        write_jsonl(self.todo, [ev(i, f"I{i}", set={"status": "todo"})
                                for i in range(1, 6)])
        self._commit("seed")

        self._checkout("feature", new=True)
        # Two events, so ordering between rescued events is testable.
        append_jsonl(self.todo, [
            ev(10, "BRANCHWORK", set={"status": "todo", "title": "branch work"}),
            ev(11, "BRANCHWORK", op="update", set={"status": "in_progress"})])
        self._commit("branch does its own work")

        self._checkout(self.trunk)
        append_jsonl(self.todo, [ev(20, "MAINLATER", set={"status": "todo"})])
        self._commit("unrelated work lands on main")
        compact(self.todo, self.done)          # watermark lands ABOVE ev 10/11
        self._commit("nightly compaction")

        self._checkout("feature")
        return self._merge(self.trunk)

    def test_branch_events_below_the_watermark_survive_the_fold(self):
        """#284: this used to assert the OPPOSITE, and said so -- "if this now
        passes, the watermark rule was fixed and this test should become the
        regression test for that fix". It was, so it is.

        BRANCHWORK is created on the branch and never folded by any
        compaction, so no snapshot carries its state. The old global watermark
        dropped it anyway because it sorted below a mark computed from
        unrelated items. The per-item rule keeps it."""
        merged = self._fork_compact_merge()
        self.assertNotEqual(merged.returncode, 0, "guard should still block")

        items = fold([self.todo, self.done]).items
        self.assertIn("MAINLATER", items)      # main's event survived
        self.assertIn("BRANCHWORK", items,
                      "the branch's own work must survive the merge -- an item "
                      "with no snapshot has nothing that folded its events")
        self.assertEqual(items["BRANCHWORK"].get("status"), "in_progress")
        self.assertEqual(items["BRANCHWORK"].get("title"), "branch work")

    def test_merge_rescue_restores_them_and_clears_the_guard(self):
        merged = self._fork_compact_merge()
        self.assertNotEqual(merged.returncode, 0)

        rescued, dropped = merge_rescue(self.todo, self.done)

        self.assertEqual(len(rescued), 2, f"both branch events re-applied: {rescued}")
        self.assertGreater(dropped, 0, "already-compacted lines should be dropped")

        items = fold([self.todo, self.done]).items
        self.assertIn("BRANCHWORK", items, "the branch's work must come back")
        self.assertIn("MAINLATER", items, "main's work must not be clobbered")
        for n in range(1, 6):
            self.assertIn(f"I{n}", items, "pre-fork history must survive")
        # Order preserved: create then update, so status is the LATER value.
        self.assertEqual(items["BRANCHWORK"].get("status"), "in_progress")
        self.assertEqual(items["BRANCHWORK"].get("title"), "branch work")

        # The whole point: the guard now passes, so the merge can be committed.
        self.assertEqual(check_resurrection(self.todo, self.done), [])
        self.assertTrue(merge_check(self.todo, self.done))

    def test_rescued_events_keep_provenance(self):
        self._fork_compact_merge()
        merge_rescue(self.todo, self.done)
        origins = [json.loads(ln).get("rescued_from")
                   for ln in open(self.todo) if ln.strip()]
        self.assertEqual(sorted(o for o in origins if o), ["01A0010", "01A0011"],
                         "a rescued event must name the id it replaced")

    def test_refuses_when_no_merge_is_in_progress(self):
        write_jsonl(self.todo, [ev(1, "I1", set={"status": "todo"})])
        self._commit("seed")
        with self.assertRaises(SystemExit):
            merge_rescue(self.todo, self.done)


class TestRescueKeepsPerItemOrder(GitRepo):
    """A rescue that loses no events can still return the wrong state.

    Re-issued events are stamped at NOW, so they sort above every event that
    kept its original id -- including LATER events of the same item, which sat
    above the watermark and were therefore left alone. Re-stamp an item's
    create and update but not its close, and the fold reads the pre-close
    state: nothing lost, every existing guard green, wrong answer.

    Seen for real on 2026-08-05 while merging main into the Codex branch --
    an item that read `done` before the merge read `in_progress` after it.
    """

    WIRE_HOOKS = True

    def _fork_compact_merge(self):
        """Same shape as the sub-watermark case, with one difference that is
        the whole point: the branch's LAST event lands after the compaction,
        so it sits above the watermark and the old code left it in place while
        moving the two below it."""
        write_jsonl(self.todo, [ev(i, f"I{i}", set={"status": "todo"})
                                for i in range(1, 6)])
        self._commit("seed")

        self._checkout("feature", new=True)
        append_jsonl(self.todo, [
            ev(10, "SPANNER", set={"status": "todo", "title": "spans the mark"}),
            ev(11, "SPANNER", op="update", set={"status": "in_progress"})])
        self._commit("branch work below the coming watermark")

        self._checkout(self.trunk)
        append_jsonl(self.todo, [ev(20, "MAINLATER", set={"status": "todo"})])
        self._commit("unrelated work lands on main")
        compact(self.todo, self.done)     # watermark lands above ev 10/11
        self._commit("nightly compaction")

        self._checkout("feature")
        # The close happens AFTER the compaction ran on main, so its id sorts
        # above the watermark. This is the ordinary case -- work continues on
        # the branch while the nightly job runs.
        append_jsonl(self.todo, [
            ev(30, "SPANNER", op="close", set={"status": "done"})])
        self._commit("branch finishes the work")
        return self._merge(self.trunk)

    def test_the_close_is_not_undone_by_replaying_earlier_events(self):
        self._fork_compact_merge()
        merge_rescue(self.todo, self.done)

        items = fold([self.todo, self.done]).items
        self.assertEqual(
            items["SPANNER"].get("status"), "done",
            "the branch closed this item and nothing reopened it -- an "
            "earlier event replayed above the close is not a state change")

    def test_every_event_of_a_moved_item_moves_with_it(self):
        """The mechanism, pinned separately from the symptom: re-issuing is
        contagious forward within an item. Partial re-stamping is what
        inverted the order, so no event of a moved item may keep its old id."""
        self._fork_compact_merge()
        merge_rescue(self.todo, self.done)

        evs = [json.loads(ln) for ln in open(self.todo) if ln.strip()]
        spanner = [e for e in evs if e.get("item") == "SPANNER"]
        self.assertEqual(len(spanner), 3, f"all three events present: {spanner}")
        self.assertTrue(all(e.get("rescued_from") for e in spanner),
                        f"every SPANNER event must be re-issued: {spanner}")
        # and they must still fold in the order the branch wrote them
        order = [e["rescued_from"] for e in sorted(spanner, key=lambda x: x["ev"])]
        self.assertEqual(order, ["01A0010", "01A0011", "01A0030"])

    def test_untouched_items_keep_their_original_ids(self):
        """The contagion is scoped to the item, not the file: rewriting ids
        that did not need it would churn provenance for no reason."""
        self._fork_compact_merge()
        merge_rescue(self.todo, self.done)

        evs = [json.loads(ln) for ln in open(self.todo) if ln.strip()]
        others = [e for e in evs
                  if e.get("item") not in (None, "SPANNER") and e.get("ev")]
        self.assertTrue(others, "there are other items in this log")
        self.assertFalse([e for e in others if e.get("rescued_from")],
                         "only the item that had to move should be re-issued")


class TestConflictMarkerGuard(GitRepo):
    """01KYZEC0C1: a merge that left conflict markers in a file committed
    cleanly, because commit-msg exempts merge commits and nothing parsed
    tests/ or plugin/. Found only by running the suite."""

    WIRE_HOOKS = True

    def _stage(self, name, body):
        path = os.path.join(self.d, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(body)
        env = dict(os.environ, WORKLOG_SKIP_BRANCH_GUARD="1")
        sh(self.d, "git", "add", "-A", env=env)
        return env

    def _commit(self, msg="x", env=None):
        env = env or dict(os.environ, WORKLOG_SKIP_BRANCH_GUARD="1")
        return sh(self.d, "git", "commit", "-q", "-m", msg, env=env, check=False)

    def test_conflict_markers_block_the_commit(self):
        env = self._stage("tests/thing.py", "a = 1\n<<<<<<< HEAD\nb = 2\n"
                                            "=======\nb = 3\n>>>>>>> other\n")
        p = self._commit("tracked 01A0001", env)
        self.assertNotEqual(p.returncode, 0, "commit should have been blocked")
        self.assertIn("conflict markers", p.stdout + p.stderr)

    def test_a_resolved_file_commits_normally(self):
        env = self._stage("tests/thing.py", "a = 1\nb = 3\n")
        p = self._commit("tracked 01A0001", env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_prose_about_conflict_markers_is_not_a_conflict(self):
        """Docs explaining the markers must stay committable — the check is
        anchored to line starts and the exact 7-character run."""
        env = self._stage("docs/notes.md",
                          "Resolve a `<<<<<<<` marker by picking a side.\n"
                          "Indented example:\n    <<<<<<< HEAD\n")
        p = self._commit("tracked 01A0001", env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_the_guard_is_not_exempted_for_merges(self):
        """The whole point: the merge path is where this happens, and it is
        the path every other check exempts."""
        env = self._stage("tests/thing.py",
                          "<<<<<<< HEAD\nb = 2\n=======\nb = 3\n>>>>>>> x\n")
        env["WORKLOG_MERGE_COMMIT"] = "1"          # what a real merge sets
        p = self._commit("tracked 01A0001", env)
        self.assertNotEqual(p.returncode, 0,
                            "a merge commit must not be exempt from this")
        self.assertIn("conflict markers", p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
