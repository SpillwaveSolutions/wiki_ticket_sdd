#!/usr/bin/env python3
"""Tests for `worklog link` (spec 5.3) and `worklog wiki-add` (spec 9.2)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-link-")
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


class TestLink(Sandbox):
    def test_link_then_show_has_external(self):
        item = self.wl("add", "Push me")
        self.wl("link", item, "--system", "github", "--key", "123",
                "--url", "https://github.com/o/r/issues/123")
        shown = json.loads(self.wl("show", item))
        ext = shown["external"]
        self.assertEqual(ext["system"], "github")
        self.assertEqual(ext["key"], "123")
        self.assertEqual(ext["url"], "https://github.com/o/r/issues/123")
        self.assertTrue(ext["synced_at"])

    def test_link_survives_fold_with_update(self):
        item = self.wl("add", "Push me")
        self.wl("update", item, "--status", "in_progress")
        self.wl("link", item, "--system", "github", "--key", "7")
        shown = json.loads(self.wl("show", item))
        self.assertEqual(shown["status"], "in_progress")
        self.assertEqual(shown["external"]["key"], "7")

    def test_link_missing_key_exits_nonzero(self):
        item = self.wl("add", "Push me")
        p = self.run_wl("link", item, "--system", "github")
        self.assertNotEqual(p.returncode, 0)


class TestOneOwnerPerKey(Sandbox):
    """github#226: `link` accepted a key another item already owned, sync
    pushed both, and a cancelled duplicate marked a live ticket Done."""

    def log(self):
        with open(os.path.join(self.dir, ".work", "todo.jsonl"),
                  encoding="utf-8") as fh:
            return fh.read()

    def test_refuses_a_key_owned_by_another_item(self):
        a = self.wl("add", "The real one")
        b = self.wl("add", "The phantom duplicate")
        self.wl("link", a, "--system", "ado", "--key", "294")
        before = self.log()
        p = self.run_wl("link", b, "--system", "ado", "--key", "294")
        self.assertNotEqual(p.returncode, 0)
        out = p.stdout + p.stderr
        self.assertIn(a, out)                 # names the other owner...
        self.assertIn("The real one", out)    # ...and its title, the tell
        self.assertIn("worklog unlink", out)  # and the repair
        self.assertEqual(self.log(), before, "refused link still wrote an event")
        self.assertNotIn("external", json.loads(self.wl("show", b)))

    def test_refuses_when_the_other_owner_is_closed(self):
        """The repro with the operations reordered. A cancelled owner is the
        MOST dangerous: sync pushes a full update against its key and then
        closes the ticket. An open-items-only guard would wave this through."""
        a = self.wl("add", "Cancelled duplicate")
        b = self.wl("add", "The real one")
        self.wl("link", a, "--system", "ado", "--key", "294")
        self.wl("close", a, "--status", "cancelled")
        p = self.run_wl("link", b, "--system", "ado", "--key", "294")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn(a, p.stdout + p.stderr)

    def test_relinking_the_same_item_is_allowed(self):
        # Refreshing --url/--rev, re-running a partial bulk migration, and
        # sync's own auto-link after a create all depend on this.
        item = self.wl("add", "Push me")
        self.wl("link", item, "--system", "ado", "--key", "294")
        self.wl("link", item, "--system", "ado", "--key", "294",
                "--url", "https://ado/294")
        self.assertEqual(json.loads(self.wl("show", item))["external"]["url"],
                         "https://ado/294")

    def test_same_key_on_a_different_system_is_allowed(self):
        # ado:294 and github:294 are unrelated tickets; a mid-migration repo
        # legitimately holds both.
        a = self.wl("add", "In ADO")
        b = self.wl("add", "In GitHub")
        self.wl("link", a, "--system", "ado", "--key", "294")
        self.wl("link", b, "--system", "github", "--key", "294")
        self.assertEqual(json.loads(self.wl("show", b))["external"]["key"], "294")

    def test_force_bypasses_the_guard(self):
        a = self.wl("add", "First")
        b = self.wl("add", "Second")
        self.wl("link", a, "--system", "ado", "--key", "294")
        self.wl("link", b, "--system", "ado", "--key", "294", "--force")
        self.assertEqual(json.loads(self.wl("show", b))["external"]["key"], "294")


class TestUnlink(Sandbox):
    def test_unlink_clears_external_and_list_still_works(self):
        item = self.wl("add", "Mislinked")
        self.wl("link", item, "--system", "ado", "--key", "294")
        self.wl("unlink", item)
        # {} not null: cmd_list's `.get("external", {})` default never fires
        # when the key exists, so a null would break `list` for the whole repo.
        self.assertEqual(json.loads(self.wl("show", item))["external"], {})
        self.assertIn("-", self.wl("list"))

    def test_unlink_frees_the_key_for_another_item(self):
        a = self.wl("add", "First owner")
        b = self.wl("add", "New owner")
        self.wl("link", a, "--system", "ado", "--key", "294")
        self.assertNotEqual(
            self.run_wl("link", b, "--system", "ado", "--key", "294").returncode, 0)
        self.wl("unlink", a)
        self.wl("link", b, "--system", "ado", "--key", "294")
        self.assertEqual(json.loads(self.wl("show", b))["external"]["key"], "294")

    def test_unlink_warns_the_tracker_may_still_carry_the_marker(self):
        item = self.wl("add", "Mislinked")
        self.wl("link", item, "--system", "ado", "--key", "294")
        p = self.run_wl("unlink", item)
        self.assertIn("marker", p.stderr)
        self.assertIn(item, p.stderr)

    def test_unlink_without_a_link_exits_nonzero(self):
        item = self.wl("add", "Never linked")
        p = self.run_wl("unlink", item)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("nothing to unlink", p.stdout + p.stderr)


class TestWikiAdd(Sandbox):
    def setUp(self):
        super().setUp()
        self.published = os.path.join(self.dir, ".work", "published.json")
        with open(os.path.join(self.dir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# Plan\n")

    def read_published(self):
        with open(self.published, encoding="utf-8") as fh:
            return json.load(fh)

    def test_creates_entry_with_source_and_null_url(self):
        out = self.wl("wiki-add", "plan.md", "--key", "plan/x", "--title", "Plan X")
        self.assertEqual(out, "plan/x")
        entry = self.read_published()["plan/x"]
        self.assertEqual(entry["source"], "plan.md")
        self.assertEqual(entry["title"], "Plan X")
        self.assertIsNone(entry["url"])
        self.assertIsNone(entry["rev"])
        self.assertIsNone(entry["source_hash"])

    def test_reregister_preserves_publish_state(self):
        with open(self.published, "w", encoding="utf-8") as fh:
            json.dump({"plan/x": {"source": "old.md", "title": "Old",
                                  "url": "https://wiki/x", "rev": "3",
                                  "source_hash": "abc"}}, fh)
        self.wl("wiki-add", "plan.md", "--key", "plan/x", "--title", "New title")
        entry = self.read_published()["plan/x"]
        self.assertEqual(entry["source"], "plan.md")
        self.assertEqual(entry["title"], "New title")
        self.assertEqual(entry["url"], "https://wiki/x")
        self.assertEqual(entry["rev"], "3")
        self.assertEqual(entry["source_hash"], "abc")

    def test_missing_file_exits_nonzero(self):
        p = self.run_wl("wiki-add", "nope.md", "--key", "k", "--title", "T")
        self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()


class TestLinkPrResolvesPrefixes(unittest.TestCase):
    """01KYZFMZ5C: link-pr wrote the sidecar under the raw string, so a short
    id filed docs/.index/item/<prefix>.yml, the edge never reached the graph,
    and the release evidence gate still called the item unlinked -- with no
    error, because the write succeeded. Same class already fixed for
    close/update."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-linkpr-")
        self.addCleanup(shutil.rmtree, self.d, True)
        BIN = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "bin")
        for f in os.listdir(BIN):
            src = os.path.join(BIN, f)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(self.d, f))
        os.makedirs(os.path.join(self.d, ".work"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.d, ".work", f), "w").close()

    def wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.d, "worklog"), *args],
            cwd=self.d, capture_output=True, text=True)

    def test_a_prefix_links_the_real_item(self):
        iid = self.wl("add", "T", "--body", "b").stdout.strip()
        p = self.wl("link-pr", iid[:8], "--pr", "42")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(iid, p.stdout, "must report the resolved id, not the prefix")
        self.assertTrue(
            os.path.exists(os.path.join(self.d, "docs", ".index", "item",
                                        iid + ".yml")),
            "the sidecar must be filed under the full ULID")
        self.assertFalse(
            os.path.exists(os.path.join(self.d, "docs", ".index", "item",
                                        iid[:8] + ".yml")),
            "a phantom prefix sidecar must not be created")

    def test_an_unknown_id_is_refused(self):
        p = self.wl("link-pr", "01ZZZZZZZZ", "--pr", "42")
        self.assertNotEqual(p.returncode, 0)
