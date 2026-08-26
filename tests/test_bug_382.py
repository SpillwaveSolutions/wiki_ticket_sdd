#!/usr/bin/env python3
"""Bug #382: sync files a second ticket after git throws away the link.

create-vs-update is decided only by `external.key` in the git-tracked log.
`.work/sync-state.json` (gitignored) already remembers `last_pushed_key`,
but until this fix that field only fed `is_dirty()` — which *forces the
item into scope* and then creates again.

Reproduction in this file is the checkout, not the git command: drop the
`link` event from todo.jsonl after a successful create, leaving
last_pushed_key behind. That is what `git checkout -f` of an older log
does to an uncommitted link.

Unlink must still mint a fresh ticket: it clears last_pushed_* so the
lost-link path and the intentional-unlink path stay distinct.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import sync_dispatch as sd  # noqa: E402


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-382-")
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

    def tickets(self):
        with open(self.fake_state, encoding="utf-8") as fh:
            return json.load(fh)["tickets"]

    def drop_link_events(self, iid):
        """What a checkout of an older todo.jsonl does to an uncommitted link."""
        path = os.path.join(self.dir, ".work", "todo.jsonl")
        kept = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                ev = json.loads(line)
                if ev.get("item") == iid and ev.get("op") == "link":
                    continue
                kept.append(line if line.endswith("\n") else line + "\n")
        with open(path, "w", encoding="utf-8") as fh:
            fh.writelines(kept)

    def sync_state(self):
        path = os.path.join(self.dir, ".work", "sync-state.json")
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def shown_key(self, iid):
        return (json.loads(self.wl("show", iid)).get("external") or {}).get("key")


class TestLostLinkDoesNotCreateASecondTicket(Sandbox):
    def test_dropping_the_link_event_updates_the_original(self):
        iid = self.wl("add", "Do the thing", "--priority", "P1").strip()
        self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "1")
        original = self.shown_key(iid)
        self.assertEqual(original, "FAKE#1")
        self.assertEqual(self.sync_state()["items"][iid]["last_pushed_key"],
                         "FAKE#1")

        self.drop_link_events(iid)
        self.assertIsNone(self.shown_key(iid), "link event still in the fold")

        out = self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "1", out)
        self.assertEqual(json.loads(self.fake("_counters"))["creates"], 1, out)
        self.assertGreaterEqual(json.loads(self.fake("_counters"))["updates"], 1)
        self.assertEqual(self.shown_key(iid), original,
                         "lost link was not repaired")

    def test_dry_run_after_lost_link_does_not_say_create(self):
        iid = self.wl("add", "Do the thing", "--priority", "P1").strip()
        self.sync("--push-only")
        self.drop_link_events(iid)
        p = self.run_wl("sync", "--retry-base-delay", "0", "--push-only",
                        "--dry-run")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("would update", p.stdout)
        self.assertNotIn("would create", p.stdout)
        self.assertEqual(self.fake("_count"), "1")

    def test_closed_item_whose_link_was_lost_closes_the_original(self):
        iid = self.wl("add", "Finish me", "--priority", "P1").strip()
        self.sync("--push-only")
        self.wl("close", iid, "--status", "done", "--resolution", "shipped")
        self.drop_link_events(iid)
        out = self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "1", out)
        self.assertTrue(self.tickets()["FAKE#1"]["closed"], out)
        self.assertEqual(json.loads(self.fake("_counters"))["creates"], 1)


class TestUnlinkStillMintsAFreshTicket(Sandbox):
    def test_unlink_clears_last_pushed_and_the_next_sync_creates(self):
        iid = self.wl("add", "Mislinked", "--priority", "P1").strip()
        self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "1")
        self.wl("unlink", iid)
        st = self.sync_state()["items"][iid]
        self.assertIsNone(st.get("last_pushed_key"))
        self.assertIsNone(st.get("last_pushed_hash"))
        out = self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "2", out)
        self.assertEqual(self.shown_key(iid), "FAKE#2")

    def test_unlink_of_a_closed_item_does_not_file_a_ticket(self):
        iid = self.wl("add", "Done already", "--priority", "P1").strip()
        self.sync("--push-only")
        self.wl("close", iid, "--status", "done", "--resolution", "shipped")
        self.sync("--push-only")
        self.wl("unlink", iid)
        self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "1")


class TestRememberedKeyHelper(unittest.TestCase):
    def test_prefers_external_then_last_pushed(self):
        d = sd.Dispatcher("/dev/null")
        d.state = {"items": {"abc": {"last_pushed_key": "860"}}}
        self.assertEqual(d.remembered_key("abc", {"key": "865"}), "865")
        self.assertEqual(d.remembered_key("abc", {}), "860")
        self.assertIsNone(d.remembered_key("nope", {}))


if __name__ == "__main__":
    unittest.main()
