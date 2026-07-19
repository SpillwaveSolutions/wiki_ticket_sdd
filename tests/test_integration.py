#!/usr/bin/env python3
"""
Integration tests: simulate pull-request workflows in real throwaway git
repos -- branches, union merges, and the hook gates. WORKLOG-SPEC sections
8, 11, 14, 15.

Each Sandbox is a fresh git repo armed exactly like the real one: the same
bin/, hooks/ (core.hooksPath), tests/ (the pre-commit hook runs the fold
suite), and the union-merge .gitattributes. Everything a PR would exercise.

Not run by the pre-commit hook (too slow); run by CI and by hand:
    python3 tests/test_integration.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cwd, *cmd, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise AssertionError(
            f"$ {' '.join(cmd)}\nexit {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


class Sandbox:
    """A throwaway worklog repo, git-armed like a real checkout."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-it-")
        for d in ("bin", "hooks", "tests"):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(self.dir, d))
        # this file would only slow the sandbox down, and guards against a
        # future "run all tests" hook recursing into itself
        me = os.path.join(self.dir, "tests", "test_integration.py")
        if os.path.exists(me):
            os.remove(me)
        os.makedirs(os.path.join(self.dir, ".work"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.dir, ".work", f), "w").close()
        self.write(".gitattributes",
                   ".work/todo.jsonl merge=union\n.work/done.jsonl merge=union\n")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "it@test.invalid")
        self.git("config", "user.name", "integration-test")
        self.git("config", "core.hooksPath", "hooks")
        self.worklog("roadmap-render")
        self.commit_all("init")

    # -- plumbing ---------------------------------------------------------
    def git(self, *args, **kw):
        return sh(self.dir, "git", *args, **kw)

    def worklog(self, *args, actor="it", **kw):
        return sh(self.dir, sys.executable, "bin/worklog", "--actor", actor,
                  *args, **kw)

    def add(self, title, *args, actor="it"):
        return self.worklog("add", title, *args, actor=actor).stdout.strip()

    def fold(self):
        out = self.worklog("fold").stdout
        return {i["id"]: i for i in json.loads(out)}

    def read(self, rel):
        with open(os.path.join(self.dir, rel), encoding="utf-8") as fh:
            return fh.read()

    def write(self, rel, content):
        path = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def append_raw(self, rel, text):
        """Simulates what the hook exists to catch: a non-worklog writer."""
        with open(os.path.join(self.dir, rel), "a", encoding="utf-8") as fh:
            fh.write(text)

    def commit_all(self, msg, check=True, no_verify=False):
        self.git("add", "-A")
        args = ["commit", "-q", "-m", msg]
        if no_verify:
            args.insert(1, "--no-verify")
        return self.git(*args, check=check)

    def branch(self, name, base="main"):
        self.git("checkout", "-q", base)
        self.git("checkout", "-q", "-b", name)

    def checkout(self, name):
        self.git("checkout", "-q", name)

    def merge(self, branch):
        """Merge like a dev completing a PR: on conflict or a hook-blocked
        auto-commit, regenerate the roadmap and finish the merge. Asserts the
        LOG never conflicts -- that is the union-merge guarantee under test."""
        p = self.git("merge", "--no-edit", branch, check=False)
        if p.returncode == 0:
            return p
        status = self.git("status", "--porcelain").stdout
        conflicted = [l for l in status.splitlines() if l[:2] in ("UU", "AA")]
        for line in conflicted:
            assert ".work/" not in line, f"log conflicted -- union merge broken:\n{status}"
            assert "docs/roadmap.md" in line, f"unexpected conflict:\n{status}"
        self.worklog("roadmap-render")
        self.git("add", "-A")
        self.git("commit", "-q", "--no-edit")
        return p

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def make_sandbox(tc):
    sb = Sandbox()
    tc.addCleanup(sb.cleanup)
    return sb


class TestTwoPRsOneItem(unittest.TestCase):
    """Spec section 8.1: the core promise. Two PRs edit the same item;
    the merge takes both sides and nothing is lost."""

    def test_scalars_lww_labels_union_log_never_conflicts(self):
        sb = make_sandbox(self)
        item = sb.add("Extract auth middleware", "--priority", "P1")
        sb.worklog("roadmap-render")
        sb.commit_all("base item")

        sb.branch("alice")
        sb.worklog("update", item, "--status", "in_progress",
                   "--add-label", "backend", actor="alice")
        sb.worklog("roadmap-render")
        sb.commit_all("alice: start work")

        sb.branch("bob")
        sb.worklog("update", item, "--priority", "P0",
                   "--add-label", "urgent", actor="bob")
        sb.worklog("roadmap-render")
        sb.commit_all("bob: escalate")

        sb.checkout("main")
        sb.merge("alice")
        sb.merge("bob")

        got = sb.fold()[item]
        self.assertEqual(got["status"], "in_progress")   # alice's survives
        self.assertEqual(got["priority"], "P0")          # bob's survives
        self.assertEqual(sorted(got["labels"]), ["backend", "urgent"])  # both

        # and the roadmap on main reflects the merged truth, hook-verified
        roadmap = sb.read("docs/roadmap.md")
        self.assertIn("in progress", roadmap)
        self.assertIn("P0", roadmap)
        sh(sb.dir, "hooks/pre-commit")  # the CI gate passes

    def test_merge_order_does_not_change_the_outcome(self):
        sb = make_sandbox(self)
        item = sb.add("Contested item", "--priority", "P2")
        sb.worklog("roadmap-render")
        sb.commit_all("base")
        base = sb.git("rev-parse", "HEAD").stdout.strip()

        sb.branch("alice")
        sb.worklog("update", item, "--status", "in_progress", actor="alice")
        sb.worklog("roadmap-render")
        sb.commit_all("alice")

        sb.branch("bob")
        sb.worklog("update", item, "--priority", "P0", "--add-label", "hot",
                   actor="bob")
        sb.worklog("roadmap-render")
        sb.commit_all("bob")

        sb.checkout("main")
        sb.merge("alice")
        sb.merge("bob")
        roadmap_ab = sb.read("docs/roadmap.md")
        fold_ab = sb.fold()

        sb.git("reset", "-q", "--hard", base)
        sb.merge("bob")
        sb.merge("alice")
        self.assertEqual(sb.read("docs/roadmap.md"), roadmap_ab)
        self.assertEqual(sb.fold(), fold_ab)


class TestCloseVsUpdateRace(unittest.TestCase):
    def test_newest_event_wins_across_prs(self):
        sb = make_sandbox(self)
        item = sb.add("Racy item", "--priority", "P1")
        sb.worklog("roadmap-render")
        sb.commit_all("base")

        sb.branch("closer")
        sb.worklog("close", item, "--status", "done", actor="closer")
        sb.worklog("roadmap-render")
        sb.commit_all("closer: done")

        time.sleep(0.01)  # guarantee the update's ULID sorts after the close
        sb.branch("worker")
        sb.worklog("update", item, "--status", "in_progress", actor="worker")
        sb.worklog("roadmap-render")
        sb.commit_all("worker: still going")

        sb.checkout("main")
        sb.merge("closer")
        sb.merge("worker")

        # per-field LWW: the chronologically newer event decides
        self.assertEqual(sb.fold()[item]["status"], "in_progress")


class TestHookGates(unittest.TestCase):
    """Spec sections 8.2 and 14: what a PR cannot contain."""

    def _valid_event(self, item="01ORPHANITEM00000000000000"):
        return json.dumps({"ev": "7ZZZZZZZZZZZZZZZZZZZZZZZZZ", "ts": "t",
                           "actor": "vandal", "item": item, "op": "update",
                           "set": {"priority": "P3"}})

    def test_missing_trailing_newline_blocked_then_repair_cascade(self):
        sb = make_sandbox(self)
        sb.append_raw(".work/todo.jsonl", self._valid_event())  # no newline

        p = sb.commit_all("bad newline", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("no trailing newline", p.stdout + p.stderr)

        sb.append_raw(".work/todo.jsonl", "\n")  # repair the newline...
        p = sb.commit_all("still stale", check=False)
        self.assertNotEqual(p.returncode, 0)     # ...next gate: stale roadmap
        self.assertIn("stale or hand-edited", p.stdout + p.stderr)

        sb.worklog("roadmap-render")
        sb.commit_all("fresh and newline-terminated")  # now it lands

    def test_schema_violation_blocked(self):
        sb = make_sandbox(self)
        bad = json.dumps({"ev": "7ZZZZZZZZZZZZZZZZZZZZZZZZZ", "ts": "t",
                          "item": "A", "op": "update"})  # no actor
        sb.append_raw(".work/todo.jsonl", bad + "\n")
        p = sb.commit_all("bad schema", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("missing actor", p.stdout + p.stderr)

    def test_stale_roadmap_cannot_ride_a_merge_commit(self):
        """A --no-verify'd commit leaves main's roadmap stale. The merge
        auto-resolves the roadmap file (only one side changed it) -- without
        hooks/pre-merge-commit the stale result would land silently."""
        sb = make_sandbox(self)
        item = sb.add("Base item", "--priority", "P1")
        sb.worklog("roadmap-render")
        sb.commit_all("base")

        sb.branch("alice")
        sb.worklog("update", item, "--status", "in_progress", actor="alice")
        sb.worklog("roadmap-render")
        sb.commit_all("alice: honest PR")

        sb.checkout("main")
        sb.worklog("update", item, "--add-label", "sneaky")
        sb.commit_all("main: bypassed hook", no_verify=True)  # roadmap now stale

        p = sb.git("merge", "--no-edit", "alice", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("stale or hand-edited", p.stdout + p.stderr)
        # merge is parked, not lost: MERGE_HEAD exists
        self.assertTrue(os.path.exists(os.path.join(sb.dir, ".git", "MERGE_HEAD")))

        sb.worklog("roadmap-render")
        sb.git("add", "-A")
        sb.git("commit", "-q", "--no-edit")
        parents = sb.git("rev-list", "--parents", "-1", "HEAD").stdout.split()
        self.assertEqual(len(parents), 3)  # a real merge commit
        got = sb.fold()[item]
        self.assertEqual(got["status"], "in_progress")
        self.assertIn("sneaky", got["labels"])


class TestNewlineCorruption(unittest.TestCase):
    """Spec section 8.2, revised by evidence. Two findings:

    1. git's ort union driver REPAIRS a missing final newline at merge time
       (verified empirically) -- the spec's fusion scenario does not
       originate in the merge itself.
    2. The real fusion path is local: append() onto a file whose last line
       lost its newline. worklog's append() self-heals that case, so the
       only way to fuse events is to hand-write a fused line and commit it
       with --no-verify. Even then the damage is exactly that line's events.
    """

    def test_append_self_heals_a_missing_trailing_newline(self):
        sb = make_sandbox(self)
        first = sb.add("First", "--priority", "P1")
        log = sb.read(".work/todo.jsonl")
        sb.write(".work/todo.jsonl", log.rstrip("\n"))   # hand-edit damage
        second = sb.add("Second", "--priority", "P1")    # would fuse without the heal
        items = sb.fold()
        self.assertIn(first, items)
        self.assertIn(second, items)
        self.assertTrue(sb.read(".work/todo.jsonl").endswith("\n"))

    def test_a_fused_line_costs_exactly_its_own_events(self):
        sb = make_sandbox(self)
        keep = sb.add("Survivor", "--priority", "P1")
        sb.worklog("roadmap-render")
        sb.commit_all("base")

        sb.branch("vandal")
        fused = (json.dumps({"ev": "7YY1AAAAAAAAAAAAAAAAAAAAAA", "ts": "t",
                             "actor": "vandal", "item": "01FUSEDITEM1", "op":
                             "create", "set": {"type": "task", "title": "F1",
                                               "status": "todo"}})
                 + json.dumps({"ev": "7YY2AAAAAAAAAAAAAAAAAAAAAA", "ts": "t",
                               "actor": "vandal", "item": "01FUSEDITEM2",
                               "op": "update", "set": {"priority": "P0"}}))
        sb.append_raw(".work/todo.jsonl", fused + "\n")
        sb.worklog("roadmap-render")
        sb.commit_all("vandal: fused line", no_verify=True)  # hook rejects it

        sb.branch("victim", base="main")
        sb.worklog("update", keep, "--status", "in_progress", actor="victim")
        sb.worklog("roadmap-render")
        sb.commit_all("victim: honest work")

        sb.checkout("main")
        sb.merge("vandal")  # fast-forward

        # the merge gate catches the corruption a --no-verify smuggled in
        p = sb.git("merge", "--no-edit", "victim", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("schema validation failed", p.stdout + p.stderr)

        # force-land it anyway (what CI would then flag) -- damage must be
        # contained to the fused line's own events
        sb.git("commit", "-q", "--no-edit", "--no-verify")
        r = sh(sb.dir, sys.executable, "bin/fold.py",
               ".work/todo.jsonl", ".work/done.jsonl")
        self.assertIn("unparseable", r.stderr)
        items = {i["id"]: i for i in json.loads(r.stdout)}
        self.assertEqual(items[keep]["status"], "in_progress")  # victim intact
        self.assertNotIn("01FUSEDITEM1", items)
        self.assertNotIn("01FUSEDITEM2", items)
        sb.worklog("list")  # CLI still functions on a damaged log


class TestPlanCapturePR(unittest.TestCase):
    def test_captured_plan_merges_to_main(self):
        sb = make_sandbox(self)
        sb.branch("feature")
        sb.write("draft.md", "\n".join([
            "# Demo plan", "", "Why prose.", "", "## Tasks", "",
            "- [ ] (P1) First task", "  - [ ] A subtask", "- [ ] Second task", "",
        ]))
        out = sb.worklog("plan-capture", "--slug", "demo", "--title",
                         "Demo plan", "--file", "draft.md").stdout.splitlines()
        plan_path, epic = out[0], out[1]
        os.remove(os.path.join(sb.dir, "draft.md"))
        sb.worklog("roadmap-render")
        sb.commit_all("feature: capture plan")

        sb.checkout("main")
        sb.merge("feature")

        self.assertTrue(os.path.exists(os.path.join(sb.dir, plan_path)))
        items = sb.fold()
        self.assertEqual(len(items), 4)  # epic + 2 tasks + 1 subtask
        levels = sorted(i["level"] for i in items.values())
        self.assertEqual(levels, ["epic", "subtask", "task", "task"])
        self.assertIn("### Demo plan", sb.read("docs/roadmap.md"))
        self.assertEqual(items[epic]["level"], "epic")

    def test_two_plan_prs_merge_cleanly(self):
        sb = make_sandbox(self)
        for n, branch in (("one", "feat-one"), ("two", "feat-two")):
            sb.branch(branch)
            sb.write("draft.md",
                     f"# Plan {n}\n\n## Tasks\n\n- [ ] (P2) Task {n}\n")
            sb.worklog("plan-capture", "--slug", n, "--title", f"Plan {n}",
                       "--file", "draft.md")
            os.remove(os.path.join(sb.dir, "draft.md"))
            sb.worklog("roadmap-render")
            sb.commit_all(f"capture plan {n}")

        sb.checkout("main")
        sb.merge("feat-one")
        sb.merge("feat-two")

        items = sb.fold()
        self.assertEqual(len(items), 4)  # 2 epics + 2 tasks
        titles = sorted(i["title"] for i in items.values())
        self.assertEqual(titles, ["Plan one", "Plan two", "Task one", "Task two"])
        sh(sb.dir, "hooks/pre-commit")  # CI gate green on the merged result


if __name__ == "__main__":
    unittest.main()
