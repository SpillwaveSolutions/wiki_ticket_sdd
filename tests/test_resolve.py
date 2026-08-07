#!/usr/bin/env python3
"""Tests for item-id prefix resolution (worklog 01KYA99TVC).

`close`/`update`/`link` used to write their event under whatever string the
caller passed. Handed the 8-char prefix that `show`/`list` themselves print,
they appended an event under that short id, which folds into a brand-new
phantom item -- the real item untouched, the log quietly corrupted. `update`
was worse still: its current-state lookup returned {} for a prefix, so the
taxonomy check ran against level=None and the "closed items need reopen"
guard never fired.

Sandbox subprocess style (see test_taxonomy.py).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ResolveTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-resolve-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        os.makedirs(os.path.join(self.dir, ".work"))

    def run_wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def items(self):
        d = json.loads(self.wl("fold"))
        return d if isinstance(d, list) else list(d.get("items", {}).values())

    def add(self, title="Item", **kw):
        args = ["add", title, "--level", kw.get("level", "task"),
                "--kind", kw.get("kind", "feature"),
                "--priority", kw.get("priority", "P2")]
        return self.wl(*args)

    # -- the bug --------------------------------------------------------

    def test_close_by_prefix_closes_the_real_item(self):
        iid = self.add("Close me")
        self.wl("close", iid[:8], "--resolution", "done by prefix")
        items = self.items()
        self.assertEqual(len(items), 1, "prefix close minted a phantom item")
        self.assertEqual(items[0]["id"], iid)
        self.assertEqual(items[0]["status"], "done")
        self.assertEqual(items[0]["resolution"], "done by prefix")

    def test_update_by_prefix_updates_the_real_item(self):
        iid = self.add("Update me")
        self.wl("update", iid[:8], "--priority", "P0")
        items = self.items()
        self.assertEqual(len(items), 1, "prefix update minted a phantom item")
        self.assertEqual(items[0]["priority"], "P0")

    def test_update_status_by_prefix_still_refuses_a_closed_item(self):
        """The guard used to be skipped entirely: .items.get(prefix) -> {},
        so cur['status'] was never a closed status."""
        iid = self.add("Closed already")
        self.wl("close", iid, "--resolution", "fixed")
        p = self.run_wl("update", iid[:8], "--status", "todo")
        self.assertNotEqual(p.returncode, 0, "closed-item guard did not fire")
        self.assertIn("reopen", p.stderr + p.stdout)
        self.assertEqual(len(self.items()), 1)

    def test_update_by_prefix_still_enforces_taxonomy(self):
        """An epic may not be kind:bug (CLAUDE.md §2). The level came back as
        None for a prefix, so the rule silently passed."""
        iid = self.add("Big thing", level="epic")
        p = self.run_wl("update", iid[:8], "--kind", "bug")
        self.assertNotEqual(p.returncode, 0, "taxonomy rule did not fire")
        self.assertEqual(self.items()[0].get("kind"), "feature")

    def test_link_by_prefix_links_the_real_item(self):
        iid = self.add("Link me")
        self.wl("link", iid[:8], "--system", "github", "--key", "42")
        items = self.items()
        self.assertEqual(len(items), 1, "prefix link minted a phantom item")
        self.assertEqual(items[0]["external"]["key"], "42")

    # -- error paths ----------------------------------------------------

    def test_unknown_id_fails_loudly_and_writes_nothing(self):
        self.add("Bystander")
        log = os.path.join(self.dir, ".work", "todo.jsonl")
        with open(log, encoding="utf-8") as fh:
            before = fh.read()
        for cmd in (["close", "01NOSUCH"], ["update", "01NOSUCH", "--priority", "P0"],
                    ["link", "01NOSUCH", "--system", "github", "--key", "1"]):
            p = self.run_wl(*cmd)
            self.assertNotEqual(p.returncode, 0, f"{cmd[0]} accepted an unknown id")
            self.assertIn("no item matching", p.stderr + p.stdout)
        with open(log, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before)

    def test_ambiguous_prefix_names_the_candidates(self):
        """Two ids sharing a prefix used to take match[0] arbitrarily."""
        a = self.add("First")
        b = self.add("Second")
        shared = os.path.commonprefix([a, b])
        self.assertTrue(shared, "ULIDs share no prefix; test cannot run")
        p = self.run_wl("close", shared)
        self.assertNotEqual(p.returncode, 0, "ambiguous prefix was accepted")
        out = p.stderr + p.stdout
        self.assertIn("ambiguous", out)
        self.assertIn(a, out)
        self.assertIn(b, out)
        self.assertEqual(len(self.items()), 2)

    def test_empty_id_still_rejected(self):
        p = self.run_wl("close", "")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("empty item id", p.stderr + p.stdout)

    def test_composite_id_on_close_names_the_real_mistake(self):
        """`close "$id1 $id2"` puts both ids in one positional.

        `_resolve` already refuses to act on the composite key, so no event is
        written here — but it reports "no item matching <two ULIDs>", which
        reads as a missing item rather than as a quoting mistake. Name the
        actual fault instead.
        """
        a = self.add("First")
        b = self.add("Second")
        before = self.items()
        p = self.run_wl("close", f"{a} {b}")
        self.assertNotEqual(p.returncode, 0, "a composite id was accepted")
        self.assertIn("whitespace", p.stderr + p.stdout)
        self.assertEqual(self.items(), before)

    def test_composite_id_on_a_non_resolving_command_writes_nothing(self):
        """`conflict` and `ingest` append without resolving — the real hole.

        Both call `_require_item` and then `append()` directly, so before this
        guard a whitespace-bearing id wrote an event against a composite key
        matching no item: a silent no-op whose rendered sidecar path grows with
        every id. One downstream log carried a 10-ULID key whose 273-byte
        filename exceeded the filesystem limit and crashed `ia-render`. These
        are sync-path commands, so the id can arrive from a remote system.
        """
        a = self.add("First")
        b = self.add("Second")
        log = os.path.join(self.dir, ".work", "todo.jsonl")
        with open(log, encoding="utf-8") as fh:
            before = fh.read()
        p = self.run_wl("conflict", f"{a} {b}", "--field", "title",
                        "--local", "x", "--remote", "y", "--remote-rev", "1")
        self.assertNotEqual(p.returncode, 0, "a composite id was accepted")
        self.assertIn("whitespace", p.stderr + p.stdout)
        with open(log, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before, "a rejected id still wrote an event")

    # -- commands that already resolved keep working --------------------

    def test_show_and_reopen_by_prefix(self):
        iid = self.add("Round trip")
        self.wl("close", iid, "--resolution", "fixed")
        self.assertEqual(json.loads(self.wl("show", iid[:8]))["id"], iid)
        self.wl("reopen", iid[:8])
        items = self.items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "todo")
        self.assertIsNone(items[0].get("resolution"))


if __name__ == "__main__":
    unittest.main()
