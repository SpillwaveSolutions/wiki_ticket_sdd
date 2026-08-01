#!/usr/bin/env python3
"""Item #236: warn when two assistant sessions share one working directory.

The advisory is only worth having if it is quiet when there is one session and
loud when there are two, so most of these tests are about NOT crying wolf.
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
sys.path.insert(0, BIN)
import session  # noqa: E402


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-session-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.reg = os.path.join(self.d, ".work", ".sessions")

    def touch(self, sid, now, branch="main"):
        session.touch(sid, path=self.reg, now=now, branch_name=branch)

    def test_one_session_is_silent(self):
        self.touch("A", now=1000)
        self.assertIsNone(session.warning(path=self.reg, now=1000))

    def test_two_live_sessions_warn(self):
        self.touch("A", now=1000, branch="feature-a")
        self.touch("B", now=1001, branch="feature-b")
        note = session.warning(path=self.reg, now=1001)
        self.assertIsNotNone(note)
        self.assertIn("worktree", note)
        self.assertIn("feature-a", note)
        self.assertIn("feature-b", note)

    def test_a_stale_session_does_not_warn(self):
        """The one that would make this useless: a session that ended without
        cleanup must not warn the next one forever."""
        self.touch("OLD", now=1000)
        self.touch("NEW", now=1000 + session.WINDOW + 1)
        self.assertIsNone(
            session.warning(path=self.reg, now=1000 + session.WINDOW + 1))

    def test_end_removes_the_session_immediately(self):
        self.touch("A", now=1000)
        self.touch("B", now=1000)
        self.assertIsNotNone(session.warning(path=self.reg, now=1000))
        session.end("A", path=self.reg)
        self.assertIsNone(session.warning(path=self.reg, now=1000))

    def test_touch_prunes_so_the_file_cannot_grow_forever(self):
        for n in range(5):
            self.touch(f"S{n}", now=1000 + n)
        self.touch("LATER", now=1000 + session.WINDOW + 10)
        self.assertEqual(list(json.load(open(self.reg))), ["LATER"])

    def test_same_session_touching_twice_is_still_one_session(self):
        self.touch("A", now=1000)
        self.touch("A", now=1010)
        self.assertIsNone(session.warning(path=self.reg, now=1010))

    def test_corrupt_registry_is_treated_as_empty_never_raises(self):
        os.makedirs(os.path.dirname(self.reg), exist_ok=True)
        with open(self.reg, "w") as fh:
            fh.write("{not json")
        self.assertIsNone(session.warning(path=self.reg))
        self.touch("A", now=1000)          # must still be able to record
        self.assertEqual(list(json.load(open(self.reg))), ["A"])

    def test_missing_registry_is_silent(self):
        self.assertIsNone(session.warning(path=os.path.join(self.d, "nope")))

    def test_empty_session_id_is_ignored(self):
        """A harness that sends no session_id must not create a phantom."""
        session.touch("", path=self.reg, now=1000)
        self.assertEqual(session.live(path=self.reg, now=1000), {})


class TestWorklogIntegration(unittest.TestCase):
    """The warning has to reach a real `worklog add`, on stderr, without
    getting in the way of the write."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-session-cli-")
        self.addCleanup(shutil.rmtree, self.d, True)
        os.makedirs(os.path.join(self.d, ".work"))
        # Whole bin/, not a hand-picked list: worklog imports lazily in
        # several commands and tracking that graph here just breaks later.
        for f in os.listdir(BIN):
            src = os.path.join(BIN, f)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(self.d, f))
        os.chmod(os.path.join(self.d, "worklog"), 0o755)
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.d, ".work", f), "w").close()

    def _add(self, title):
        return subprocess.run(
            [sys.executable, os.path.join(self.d, "worklog"), "add", title,
             "--body", "b", "--level", "task", "--kind", "feature"],
            cwd=self.d, capture_output=True, text=True)

    def _register(self, *sids):
        import time
        now = time.time()
        with open(os.path.join(self.d, ".work", ".sessions"), "w") as fh:
            json.dump({s: {"ts": now, "branch": s} for s in sids}, fh)

    def test_add_warns_when_two_sessions_are_registered(self):
        self._register("A", "B")
        p = self._add("something")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("WARNING", p.stderr)
        self.assertIn("worktree", p.stderr)

    def test_add_is_silent_with_one_session(self):
        self._register("A")
        p = self._add("something")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("WARNING", p.stderr)

    def test_the_write_still_happens_when_warning(self):
        """Advisory means advisory: the event must land regardless."""
        self._register("A", "B")
        self._add("recorded anyway")
        with open(os.path.join(self.d, ".work", "todo.jsonl")) as fh:
            lines = [json.loads(ln) for ln in fh if ln.strip()]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["set"]["title"], "recorded anyway")

    def test_warning_can_be_suppressed(self):
        self._register("A", "B")
        env = dict(os.environ, WORKLOG_NO_SESSION_WARN="1")
        p = subprocess.run(
            [sys.executable, os.path.join(self.d, "worklog"), "add", "x",
             "--body", "b", "--level", "task", "--kind", "feature"],
            cwd=self.d, capture_output=True, text=True, env=env)
        self.assertNotIn("WARNING", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
