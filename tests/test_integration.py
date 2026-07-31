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
        # like the real repo: bytecode is never tracked (a committed .pyc on
        # one branch + the same file untracked on another aborts a merge)
        self.write(".gitignore", "__pycache__/\n*.pyc\n")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "it@test.invalid")
        self.git("config", "user.name", "integration-test")
        self.git("config", "core.hooksPath", "hooks")
        self.worklog("roadmap-render")
        self.commit_all("init", no_verify=True)  # bootstrap, not real work

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
        sb.commit_all("base item", no_verify=True)  # pre-PR baseline

        sb.branch("alice")
        sb.worklog("update", item, "--status", "in_progress",
                   "--add-label", "backend", actor="alice")
        sb.worklog("roadmap-render")
        sb.commit_all(f"alice: start work {item}")

        sb.branch("bob")
        sb.worklog("update", item, "--priority", "P0",
                   "--add-label", "urgent", actor="bob")
        sb.worklog("roadmap-render")
        sb.commit_all(f"bob: escalate {item}")

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
        sh(sb.dir, "env", "WORKLOG_SKIP_BRANCH_GUARD=1", "hooks/pre-commit")  # the CI gate passes

    def test_merge_order_does_not_change_the_outcome(self):
        sb = make_sandbox(self)
        item = sb.add("Contested item", "--priority", "P2")
        sb.worklog("roadmap-render")
        sb.commit_all("base", no_verify=True)  # pre-PR baseline
        base = sb.git("rev-parse", "HEAD").stdout.strip()

        sb.branch("alice")
        sb.worklog("update", item, "--status", "in_progress", actor="alice")
        sb.worklog("roadmap-render")
        sb.commit_all(f"alice: {item}")

        sb.branch("bob")
        sb.worklog("update", item, "--priority", "P0", "--add-label", "hot",
                   actor="bob")
        sb.worklog("roadmap-render")
        sb.commit_all(f"bob: {item}")

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
        sb.commit_all("base", no_verify=True)  # pre-PR baseline

        sb.branch("closer")
        sb.worklog("close", item, "--status", "done", actor="closer")
        sb.worklog("roadmap-render")
        sb.commit_all(f"closer: done {item}")

        time.sleep(0.01)  # guarantee the update's ULID sorts after the close
        sb.branch("worker")
        sb.worklog("update", item, "--status", "in_progress", actor="worker")
        sb.worklog("roadmap-render")
        sb.commit_all(f"worker: still going {item}")

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
        sb.branch("work")
        sb.append_raw(".work/todo.jsonl", self._valid_event())  # no newline

        p = sb.commit_all("bad newline", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("no trailing newline", p.stdout + p.stderr)

        sb.append_raw(".work/todo.jsonl", "\n")  # repair the newline...
        p = sb.commit_all("still stale", check=False)
        self.assertNotEqual(p.returncode, 0)     # ...next gate: stale roadmap
        self.assertIn("stale or hand-edited", p.stdout + p.stderr)

        sb.worklog("roadmap-render")
        sb.commit_all("fresh and newline-terminated #1")  # now it lands

    def test_schema_violation_blocked(self):
        sb = make_sandbox(self)
        sb.branch("work")
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
        sb.commit_all("base", no_verify=True)  # pre-PR baseline

        sb.branch("alice")
        sb.worklog("update", item, "--status", "in_progress", actor="alice")
        sb.worklog("roadmap-render")
        sb.commit_all(f"alice: honest PR {item}")

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
        sb.commit_all("base", no_verify=True)  # pre-PR baseline

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
        sb.commit_all(f"victim: honest work {keep}")

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
        sb.commit_all(f"feature: capture plan {epic}")

        sb.checkout("main")
        sb.merge("feature")

        self.assertTrue(os.path.exists(os.path.join(sb.dir, plan_path)))
        items = sb.fold()
        self.assertEqual(len(items), 4)  # epic + 2 tasks + 1 subtask
        levels = sorted(i["level"] for i in items.values())
        self.assertEqual(levels, ["epic", "subtask", "task", "task"])
        self.assertIn("### Demo plan", sb.read("docs/roadmap.md"))
        self.assertEqual(items[epic]["level"], "epic")

    def test_plan_capture_refuses_a_slug_already_captured_on_another_date(self):
        """Invariant 15.8 is slug-scoped, not filename-scoped.

        The guard used to check only `docs/plans/<today-UTC>-<slug>.md`, so it
        enforced the invariant only when the dates happened to match. The date is
        UTC while a plan is authored in local time, so capturing a plan written
        earlier the same local day, from a timezone behind UTC, looked for
        tomorrow's filename, found nothing, and wrote a duplicate. Observed in a
        downstream repo on 2026-07-26: 2026-07-26-<slug>.md was silently
        duplicated as 2026-07-27-<slug>.md.
        """
        sb = make_sandbox(self)
        os.makedirs(os.path.join(sb.dir, "docs/plans"), exist_ok=True)
        sb.write("docs/plans/2020-01-01-demo.md", "# An earlier plan, same slug\n")
        sb.write("draft.md", "# Demo plan\n\n## Tasks\n\n- [ ] (P1) A task\n")

        with self.assertRaises(Exception) as ctx:
            sb.worklog("plan-capture", "--slug", "demo", "--title", "Demo plan",
                       "--file", "draft.md")
        msg = str(ctx.exception)
        self.assertIn("2020-01-01-demo.md", msg)
        self.assertIn("15.8", msg)

        # and nothing was written for today either
        today = time.strftime("%Y-%m-%d", time.gmtime())
        self.assertFalse(
            os.path.exists(os.path.join(sb.dir, f"docs/plans/{today}-demo.md")))

    def test_plan_capture_does_not_false_positive_on_a_suffix_match(self):
        """A raw `*-<slug>.md` glob matches by suffix, not by field boundary:
        searching for slug "migration" would also match an existing
        "database-migration" plan, since that filename also ends in
        "-migration.md". That must NOT refuse a genuinely new, different slug.
        """
        sb = make_sandbox(self)
        os.makedirs(os.path.join(sb.dir, "docs/plans"), exist_ok=True)
        sb.write("docs/plans/2026-07-01-database-migration.md",
                 "# An unrelated plan with a longer slug\n")
        sb.write("draft.md", "# Migration\n\n## Tasks\n\n- [ ] (P1) A task\n")

        sb.worklog("plan-capture", "--slug", "migration", "--title", "Migration",
                   "--file", "draft.md")

        today = time.strftime("%Y-%m-%d", time.gmtime())
        self.assertTrue(
            os.path.exists(os.path.join(sb.dir, f"docs/plans/{today}-migration.md")))

    def test_two_plan_prs_merge_cleanly(self):
        sb = make_sandbox(self)
        for n, branch in (("one", "feat-one"), ("two", "feat-two")):
            sb.branch(branch)
            sb.write("draft.md",
                     f"# Plan {n}\n\n## Tasks\n\n- [ ] (P2) Task {n}\n")
            out = sb.worklog("plan-capture", "--slug", n, "--title", f"Plan {n}",
                             "--file", "draft.md").stdout.splitlines()
            epic = out[1]
            os.remove(os.path.join(sb.dir, "draft.md"))
            sb.worklog("roadmap-render")
            sb.commit_all(f"capture plan {n}: {epic}")

        sb.checkout("main")
        sb.merge("feat-one")
        sb.merge("feat-two")

        items = sb.fold()
        self.assertEqual(len(items), 4)  # 2 epics + 2 tasks
        titles = sorted(i["title"] for i in items.values())
        self.assertEqual(titles, ["Plan one", "Plan two", "Task one", "Task two"])
        sh(sb.dir, "env", "WORKLOG_SKIP_BRANCH_GUARD=1", "hooks/pre-commit")  # CI gate green on the merged result


class TestBranchGuard(unittest.TestCase):
    """The incident this plan exists for: main must stay pull-only."""

    def test_commit_on_main_rejected(self):
        sb = make_sandbox(self)
        item = sb.add("Untracked change", "--priority", "P2")
        sb.write("x.txt", "1")
        p = sb.commit_all(f"no branch: {item}", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("pull-only", p.stdout + p.stderr)

    def test_commit_on_branch_succeeds(self):
        sb = make_sandbox(self)
        item = sb.add("Tracked change", "--priority", "P2")
        sb.branch("feature/x")
        sb.worklog("roadmap-render")
        sb.write("x.txt", "1")
        sb.commit_all(f"feat: {item}")  # must not raise

    def test_merge_onto_main_allowed(self):
        """The exact incident scenario: `git merge origin/main` (here
        simulated as merging a feature branch onto main) must keep working
        even though it's a commit landing directly on main."""
        sb = make_sandbox(self)
        item = sb.add("Reconciled change", "--priority", "P2")
        sb.branch("feature/x")
        sb.worklog("roadmap-render")
        sb.write("x.txt", "1")
        sb.commit_all(f"feat: {item}")
        sb.checkout("main")
        sb.merge("feature/x")  # must not raise


class TestCommitMsgReference(unittest.TestCase):
    """Work must be traceable to a worklog item or ticket."""

    def test_message_without_reference_rejected(self):
        sb = make_sandbox(self)
        sb.branch("feature/x")
        sb.write("x.txt", "1")
        p = sb.commit_all("no reference at all", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("worklog item", p.stdout + p.stderr)

    def test_message_with_ulid_passes(self):
        sb = make_sandbox(self)
        item = sb.add("Referenced change", "--priority", "P2")
        sb.branch("feature/x")
        sb.worklog("roadmap-render")
        sb.write("x.txt", "1")
        sb.commit_all(f"fix: {item}")  # must not raise

    def test_message_with_ticket_passes(self):
        sb = make_sandbox(self)
        sb.branch("feature/x")
        sb.write("x.txt", "1")
        sb.commit_all("fix: closes #42")  # must not raise

    def test_merge_commit_message_exempt(self):
        """git's default "Merge branch 'x'" message carries no ULID/ticket
        -- this is the real-world shape of the incident's reconciliation
        merge, and must not be blocked."""
        sb = make_sandbox(self)
        item = sb.add("Reconciled change", "--priority", "P2")
        sb.branch("feature/x")
        sb.worklog("roadmap-render")
        sb.write("x.txt", "1")
        sb.commit_all(f"feat: {item}")
        sb.checkout("main")
        sb.merge("feature/x")  # default merge message, must not raise


class TestIAGatesAreHard(unittest.TestCase):
    """#98: the IA gates spent a release cycle as warnings; they now fail.

    A promotion is only real if something proves it fails. These build the
    two repos that matter — one that has opted into the IA and one that
    never has — and assert opposite outcomes for each.
    """

    def _armed(self, sb):
        """A sandbox with a generated, committed IA index."""
        sb.branch("feature/ia")
        sb.worklog("ia-inventory")
        sb.worklog("ia-render")
        sb.commit_all("chore: generate the IA index (#98)")
        self.assertTrue(os.path.isdir(os.path.join(sb.dir, "docs/.index")))

    def _hook(self, sb):
        return sh(sb.dir, "env", "WORKLOG_SKIP_BRANCH_GUARD=1",
                  "hooks/pre-commit", check=False)

    def test_scaffolded_repo_without_an_index_is_not_blocked(self):
        """The guard's whole point: a repo that got bin/ from the plugin but
        has never generated an index must still be able to commit."""
        sb = make_sandbox(self)
        self.assertFalse(os.path.isdir(os.path.join(sb.dir, "docs/.index")))
        self.assertEqual(self._hook(sb).returncode, 0)

    def test_armed_repo_passes_when_the_index_is_fresh(self):
        sb = make_sandbox(self)
        self._armed(sb)
        self.assertEqual(self._hook(sb).returncode, 0)

    def test_stale_rendered_page_now_fails_instead_of_warning(self):
        sb = make_sandbox(self)
        self._armed(sb)
        sb.write("docs/.index/rendered/home.md", "# tampered\n")
        r = self._hook(sb)
        self.assertEqual(r.returncode, 1)
        self.assertIn("rendered pages/manifest stale", r.stderr)
        self.assertNotIn("WARNING", r.stderr)

    def test_deleting_one_generated_file_still_fails(self):
        """The guard keys on the directory, not the file — so removing the
        inventory cannot silence the gate that checks it."""
        sb = make_sandbox(self)
        self._armed(sb)
        os.remove(os.path.join(sb.dir, "docs/.index/_inventory.json"))
        r = self._hook(sb)
        self.assertEqual(r.returncode, 1)
        self.assertIn("inventory stale/invalid", r.stderr)

    def test_trace_check_stays_a_warning(self):
        """Deliberately NOT promoted: unlinked evidence is a release-time
        concern, and --strict already covers it there."""
        with open(os.path.join(ROOT, "hooks", "pre-commit")) as fh:
            hook = fh.read()
        self.assertIn("trace-check stays warn-level here forever", hook)
        trace_line = next(ln for ln in hook.splitlines()
                          if "worklog trace-check >/dev/null" in ln)
        self.assertNotIn("fail ", trace_line)


if __name__ == "__main__":
    unittest.main()
