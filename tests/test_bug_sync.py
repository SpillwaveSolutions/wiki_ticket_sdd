#!/usr/bin/env python3
"""Regression tests for three bin/sync_dispatch.py tickets:

  #141 -- a cursor-less pull called the adapter with neither --since nor
          --keys, but the adapter contract requires one (the real github
          adapter dies with "pull requires --since <iso> or --keys"). Fixed
          by seeding --since from the earliest local event when no cursor
          exists yet.
  #239 -- `--keys` forces items into scope by matching a ticket number
          against `external.key`. If more than one item claims that number
          (a github#226-style duplicate mid-repair), the old code forced
          every claimant in at once. Fixed by refusing an ambiguous number
          outright, naming every claimant.
  #241 -- a ticket the tracker reports gone (adapter exit 3) kept getting
          re-pushed every run forever, because the old code popped
          last_pushed_hash unconditionally, forcing the item dirty again.
          Fixed by remembering the gone key and skipping the item until a
          human runs `worklog unlink` -- the link is deliberately NOT
          auto-cleared (see TestBug241GoneTicket docstring).

Sandbox is a trimmed copy of tests/test_dispatch.py's fixture, kept
independent since this file may only add tests, never modify that one.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import sync_dispatch as sd  # noqa: E402  (path insert must come first)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-bugsync-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        shutil.copytree(os.path.join(ROOT, "adapters"),
                        os.path.join(self.dir, "adapters"))
        os.makedirs(os.path.join(self.dir, ".work"))
        self.adapter = os.path.join(self.dir, "adapters", "fake", "adapter")
        self.fake_state = os.path.join(self.dir, ".fake-tracker.json")
        self.env = dict(os.environ,
                        WORKLOG_TICKET_ADAPTER=self.adapter,
                        WORKLOG_FAKE_STATE=self.fake_state)

    def run_wl(self, *args, env=None):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True, env=env or self.env)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def sync(self, *args):
        return self.wl("sync", "--retry-base-delay", "0", *args)

    def fake(self, *args):
        p = subprocess.run([sys.executable, self.adapter, *args],
                           cwd=self.dir, capture_output=True, text=True,
                           env=self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def write_event(self, ts, iid):
        ev = {"ev": iid, "ts": ts, "actor": "test", "item": iid, "op": "create",
              "set": {"title": "raw event " + iid, "status": "todo",
                      "priority": "P2"}}
        path = os.path.join(self.dir, ".work", "todo.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev) + "\n")


# --- #141: a spy adapter that only records the argv `pull` was called with ---

SPY_ADAPTER = '''#!/usr/bin/env python3
import json, os, sys
verb = sys.argv[1] if len(sys.argv) > 1 else None
if verb == "capabilities":
    print(json.dumps({
        "system": "spy", "supports": ["pull"], "types": {"task": "ticket"},
        "marker": {"style": "html_comment", "template": "<!-- worklog:{ulid} -->"},
        "fields": {}, "max_title": 256,
    }))
elif verb == "pull":
    with open(os.environ["SPY_RECORD"], "a", encoding="utf-8") as fh:
        fh.write(json.dumps(sys.argv[2:]) + "\\n")
else:
    sys.exit(1)
'''


class TestBug141FirstPullSeedsSince(Sandbox):
    """github#141: pull with no cursor called the adapter with neither
    --since nor --keys, but the contract (see adapters/github/adapter's
    cmd_pull) requires one -- the very first pull always failed."""

    def setUp(self):
        super().setUp()
        self.spy = os.path.join(self.dir, "spy-adapter")
        with open(self.spy, "w", encoding="utf-8") as fh:
            fh.write(SPY_ADAPTER)
        os.chmod(self.spy, 0o755)
        self.record = os.path.join(self.dir, "spy-record.jsonl")
        self.spy_env = dict(self.env, WORKLOG_TICKET_ADAPTER=self.spy,
                            SPY_RECORD=self.record)

    def pull_argv(self):
        with open(self.record, encoding="utf-8") as fh:
            lines = [json.loads(l) for l in fh if l.strip()]
        return lines[-1]

    def since_arg(self):
        argv = self.pull_argv()
        self.assertIn("--since", argv, argv)
        return argv[argv.index("--since") + 1]

    def test_no_cursor_uses_earliest_local_event_ts(self):
        self.write_event("2020-06-01T00:00:00Z", "01AAAAAAAAAAAAAAAAAAAAAAAA")
        self.write_event("2025-01-01T00:00:00Z", "01BBBBBBBBBBBBBBBBBBBBBBBB")
        p = self.run_wl("sync", "--retry-base-delay", "0", "--pull-only",
                        env=self.spy_env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.since_arg(), "2020-06-01T00:00:00Z")

    def test_earliest_not_latest_event_is_chosen(self):
        # Written out of chronological order: the file's SECOND line carries
        # the EARLIER timestamp, proving this isn't "first/last line in the
        # file" but an actual min() over every event's ts.
        self.write_event("2025-01-01T00:00:00Z", "01BBBBBBBBBBBBBBBBBBBBBBBB")
        self.write_event("2020-06-01T00:00:00Z", "01AAAAAAAAAAAAAAAAAAAAAAAA")
        p = self.run_wl("sync", "--retry-base-delay", "0", "--pull-only",
                        env=self.spy_env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.since_arg(), "2020-06-01T00:00:00Z")

    def test_existing_cursor_takes_precedence(self):
        self.write_event("2020-06-01T00:00:00Z", "01AAAAAAAAAAAAAAAAAAAAAAAA")
        cursor = "2099-01-01T00:00:00Z"
        with open(os.path.join(self.dir, ".work", "sync-state.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"cursors": {"spy": cursor}}, fh)
        p = self.run_wl("sync", "--retry-base-delay", "0", "--pull-only",
                        env=self.spy_env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.since_arg(), cursor)

    def test_empty_log_still_yields_a_since(self):
        # No item ever created: nothing to derive "earliest" from, but the
        # adapter's contract still requires --since or --keys.
        p = self.run_wl("sync", "--retry-base-delay", "0", "--pull-only",
                        env=self.spy_env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        since = self.since_arg()
        self.assertTrue(since, "empty log must still produce a usable --since")


class TestBug239AmbiguousKeyRefused(Sandbox):
    """worklog#239: --keys resolves a ticket number to the item(s) that
    claim it. Two claimants (the github#226 shape) must refuse outright,
    naming both -- not drag both into the run."""

    def link_dup(self, item, key, system="fake"):
        self.wl("link", item, "--system", system, "--key", key, "--force")

    def test_ticket_claimed_by_two_items_is_refused_naming_both(self):
        a = self.wl("add", "The real ticket", "--priority", "P1").strip()
        self.sync("--push-only")  # a creates FAKE#1
        b = self.wl("add", "The phantom duplicate", "--priority", "P1").strip()
        self.link_dup(b, "FAKE#1")
        # A third, unrelated healthy item in the same run: the organic
        # collision guard (github#226) would still push this one (skip only
        # the colliders, keep the run going) -- the explicit --keys refusal
        # this ticket asks for is a harder stop than that, so it must NOT.
        self.wl("add", "Unrelated healthy work", "--priority", "P1")
        p = self.run_wl("sync", "--retry-base-delay", "0", "--push-only",
                        "--keys", "FAKE#1")
        self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        out = p.stdout + p.stderr
        self.assertIn(a, out)
        self.assertIn(b, out)
        self.assertIn("FAKE#1", out)
        self.assertEqual(self.fake("_count"), "1", out)

    def test_uniquely_claimed_number_resolves(self):
        self.wl("add", "Solo ticket", "--priority", "P1")
        self.sync("--push-only")  # creates FAKE#1, now hash-clean
        out = self.sync("--push-only", "--keys", "FAKE#1")
        self.assertIn("updated=1", out, out)  # forced despite being clean

    def test_unknown_number_resolves_to_nothing(self):
        self.wl("add", "Clean", "--priority", "P1")
        self.sync("--push-only")  # creates once, now hash-clean
        out = self.sync("--push-only", "--keys", "FAKE#999")
        self.assertIn("created=0", out, out)
        self.assertIn("updated=0", out, out)


# --- #241: unit-level, with run_adapter mocked so exit codes are exact ---

CAPS = {
    "system": "spy",
    "supports": ["push", "pull", "get", "close"],
    "types": {"epic": None, "story": "ticket", "task": "ticket",
              "subtask": "ticket"},
    "marker": {"style": "html_comment", "template": "<!-- worklog:{ulid} -->"},
    "fields": {},
    "max_title": 256,
}


def make_item(iid, key, title="Broken ticket"):
    return {"id": iid, "title": title, "status": "in_progress",
            "priority": "P1", "level": "task",
            "external": {"system": "spy", "key": key}}


class TestBug241GoneTicket(unittest.TestCase):
    """worklog#241: a GONE ticket (adapter exit 3) must stop being retried
    every run and must surface an operator remedy, naming the item.

    Deliberately NOT implemented: automatically running `worklog unlink` for
    the item. The ticket explicitly says auto-clearing on what might be a
    transient error would file a duplicate, so the fix here is conservative:
    remember the gone key, skip pushing it, and tell the operator to run
    `worklog unlink <id>` themselves. Actually clearing the link is left to
    a human decision, not automated by this change.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="worklog-bug241-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self._old_cwd = os.getcwd()
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, self._old_cwd)
        self.calls = []

    def run_adapter_rc(self, rc):
        calls = self.calls

        def fake_run_adapter(self_, *args, stdin=None):
            calls.append(args)
            return subprocess.CompletedProcess(args, rc, stdout="",
                                               stderr="fake exit %d" % rc)
        return fake_run_adapter

    def push_count(self):
        return len([c for c in self.calls if c and c[0] == "push"])

    def test_gone_ticket_is_reported_and_not_retried_next_run(self):
        item = make_item("01GONE0000000000000000000A", "SPY-1")
        with patch.object(sd.Dispatcher, "run_adapter", self.run_adapter_rc(3)):
            d = sd.Dispatcher(adapter="unused", retry_base_delay=0)
            d.push_items([item], CAPS, keys=[])
            self.assertEqual(self.push_count(), 1)
            self.assertTrue(any("worklog unlink %s" % item["id"] in line
                                for line in d.drift), d.drift)
            self.assertTrue(any(item["id"] in line for line in d.drift), d.drift)
            d._save_state()

            # "Next run": a fresh Dispatcher reloading the persisted state.
            d2 = sd.Dispatcher(adapter="unused", retry_base_delay=0)
            d2.push_items([item], CAPS, keys=[])
        self.assertEqual(self.push_count(), 1,
                         "a GONE ticket must not be retried automatically")
        self.assertTrue(any("worklog unlink %s" % item["id"] in line
                            for line in d2.drift), d2.drift)

    def test_transient_failure_is_still_retried_next_run(self):
        item = make_item("01TRANSIENT000000000000001", "SPY-2")
        with patch.object(sd.Dispatcher, "run_adapter", self.run_adapter_rc(4)):
            d = sd.Dispatcher(adapter="unused", retry_base_delay=0)
            d.push_items([item], CAPS, keys=[])
            first_run_calls = self.push_count()
            self.assertGreater(first_run_calls, 0)
            d._save_state()

            d2 = sd.Dispatcher(adapter="unused", retry_base_delay=0)
            d2.push_items([item], CAPS, keys=[])
        self.assertGreater(self.push_count(), first_run_calls,
                           "a transient failure must still be retried on the "
                           "next run, unlike a GONE ticket")


if __name__ == "__main__":
    unittest.main(verbosity=2)
