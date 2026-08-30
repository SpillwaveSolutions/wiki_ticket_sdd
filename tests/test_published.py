#!/usr/bin/env python3
"""published.jsonl: union-merge ledger, fold LWW per key, migrate from JSON.

The leftover P0 from the v0.24.9 review (#392): published.json was a JSON
dict with no merge strategy. Two publishes conflicted. The log is now
append-only jsonl, last-write-wins per key, merge=union.
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
import published  # noqa: E402
import ulid  # noqa: E402


def run(cwd, *args):
    return subprocess.run(
        [sys.executable, os.path.join(cwd, "bin", "worklog"), *args],
        cwd=cwd, capture_output=True, text=True)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-pub-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(BIN, os.path.join(self.dir, "bin"))
        os.makedirs(os.path.join(self.dir, ".work"))
        self._cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self._cwd)

    def write_jsonl(self, lines):
        path = os.path.join(self.dir, ".work", "published.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line if line.endswith("\n") else line + "\n")

    def ev(self, key, op, fields, eid=None, actor="t"):
        return {
            "ev": eid or ulid.new(),
            "ts": "2026-08-30T00:00:00Z",
            "actor": actor,
            "op": op,
            "key": key,
            "set": fields,
        }


class TestFold(Sandbox):
    def test_newest_ev_wins_per_key(self):
        a = self.ev("plan/x", "publish", {"title": "old", "rev": "1"}, eid="01A" + "0" * 23)
        b = self.ev("plan/x", "publish", {"title": "new", "rev": "2"}, eid="01B" + "0" * 23)
        # file order is newest first -- fold must still sort by ev
        self.write_jsonl([json.dumps(b), json.dumps(a)])
        page = published.fold().pages["plan/x"]
        self.assertEqual(page["title"], "new")
        self.assertEqual(page["rev"], "2")

    def test_two_keys_union(self):
        self.write_jsonl([
            json.dumps(self.ev("a", "register", {"source": "a.md", "title": "A"})),
            json.dumps(self.ev("b", "register", {"source": "b.md", "title": "B"})),
        ])
        pages = published.fold().pages
        self.assertEqual(set(pages), {"a", "b"})

    def test_duplicate_ev_dedupes(self):
        e = self.ev("a", "publish", {"rev": "1"}, eid="01D" + "0" * 23)
        self.write_jsonl([json.dumps(e), json.dumps(e)])
        r = published.fold()
        self.assertEqual(r.deduped, 1)
        self.assertEqual(r.pages["a"]["rev"], "1")

    def test_corrupt_line_is_skipped_not_fatal(self):
        good = self.ev("a", "register", {"title": "A"})
        self.write_jsonl(["{not json", json.dumps(good)])
        r = published.fold()
        self.assertEqual(r.skipped, 1)
        self.assertEqual(r.pages["a"]["title"], "A")

    def test_unpublish_drops_the_key(self):
        self.write_jsonl([
            json.dumps(self.ev("a", "publish", {"title": "A"}, eid="01A" + "0" * 23)),
            json.dumps({"ev": "01B" + "0" * 23, "ts": "t", "actor": "t",
                        "op": "unpublish", "key": "a"}),
        ])
        self.assertNotIn("a", published.fold().pages)

    def test_set_merges_fields(self):
        self.write_jsonl([
            json.dumps(self.ev("a", "register",
                               {"source": "a.md", "title": "A", "url": None},
                               eid="01A" + "0" * 23)),
            json.dumps(self.ev("a", "publish",
                               {"url": "https://w/A", "rev": "abc"},
                               eid="01B" + "0" * 23)),
        ])
        page = published.fold().pages["a"]
        self.assertEqual(page["source"], "a.md")
        self.assertEqual(page["url"], "https://w/A")
        self.assertEqual(page["rev"], "abc")


class TestMigrate(Sandbox):
    def test_json_dict_becomes_jsonl_with_deterministic_ids(self):
        blob = {
            "plan/x": {"source": "docs/plans/x.md", "title": "X",
                       "url": "https://w/X", "rev": "aaa"},
            "home": {"source": "docs/wiki-home.md", "title": "Home"},
        }
        with open(".work/published.json", "w") as fh:
            json.dump(blob, fh)
        n = published.migrate_json()
        self.assertEqual(n, 2)
        self.assertTrue(os.path.exists(".work/published.jsonl"))
        pages = published.fold().pages
        self.assertEqual(pages["plan/x"]["url"], "https://w/X")
        self.assertEqual(pages["home"]["title"], "Home")
        # retried migrate is a no-op once jsonl exists
        self.assertEqual(published.migrate_json(), 0)
        # same dict, same events
        os.remove(".work/published.jsonl")
        published.migrate_json()
        first = open(".work/published.jsonl").read()
        os.remove(".work/published.jsonl")
        published.migrate_json()
        self.assertEqual(open(".work/published.jsonl").read(), first)

    def test_register_migrates_then_preserves_url(self):
        with open(".work/published.json", "w") as fh:
            json.dump({"plan/x": {"source": "old.md", "title": "Old",
                                  "url": "https://w/x", "rev": "3",
                                  "source_hash": "abc"}}, fh)
        published.register("plan/x", "plan.md", "New title", "t")
        page = published.load()["plan/x"]
        self.assertEqual(page["source"], "plan.md")
        self.assertEqual(page["title"], "New title")
        self.assertEqual(page["url"], "https://w/x")
        self.assertEqual(page["rev"], "3")
        self.assertEqual(page["source_hash"], "abc")


class TestCli(Sandbox):
    def test_wiki_add_get_record(self):
        open("plan.md", "w").write("# Plan\n")
        p = run(self.dir, "wiki-add", "plan.md", "--key", "plan/x", "--title", "Plan X")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "plan/x")
        got = json.loads(run(self.dir, "wiki-get", "plan/x").stdout)
        self.assertEqual(got["source"], "plan.md")
        self.assertIsNone(got["url"])
        p = run(self.dir, "wiki-record", "--key", "plan/x",
                "--url", "https://w/Plan-X", "--rev", "deadbeef",
                "--source-hash", "abc123abc123")
        self.assertEqual(p.returncode, 0, p.stderr)
        got = json.loads(run(self.dir, "wiki-get", "plan/x").stdout)
        self.assertEqual(got["url"], "https://w/Plan-X")
        self.assertEqual(got["rev"], "deadbeef")
        self.assertEqual(got["source"], "plan.md")  # still there

    def test_wiki_add_missing_file(self):
        p = run(self.dir, "wiki-add", "nope.md", "--key", "k", "--title", "T")
        self.assertNotEqual(p.returncode, 0)

    def test_envelope_rejects_oversize_event(self):
        huge = {"title": "x" * 5000}
        ev = published.event("k", "publish", "t", huge)
        with self.assertRaises(SystemExit):
            published.append(ev)


class TestPlan(unittest.TestCase):
    def page(self, key, **kw):
        p = {"wiki_key": key, "source": key + ".md", "title": key,
             "page_name": key, "render": "doc+banner", "frozen": False}
        p.update(kw)
        return p

    def test_new_page_is_publish(self):
        r = published.plan({"pages": [self.page("a", render_hash="r1")]}, {})
        self.assertEqual([p["wiki_key"] for p in r["publish"]], ["a"])
        self.assertEqual(r["skip"], [])
        self.assertEqual(r["frozen_violations"], [])

    def test_matching_render_hash_skips(self):
        r = published.plan(
            {"pages": [self.page("a", render_hash="r1", source_hash="s1")]},
            {"a": {"render_hash": "r1", "source_hash": "s1"}},
        )
        self.assertEqual(r["publish"], [])
        self.assertEqual(r["skip"], [{"wiki_key": "a", "reason": "render_hash match"}])

    def test_banner_change_publishes_frozen_page(self):
        """Frozen source_hash matches; render_hash moved (banner). Publish."""
        r = published.plan(
            {"pages": [self.page("plan/x", frozen=True, source_hash="s1",
                                 render_hash="r2", banner="> superseded")]},
            {"plan/x": {"source_hash": "s1", "render_hash": "r1"}},
        )
        self.assertEqual(r["frozen_violations"], [])
        self.assertEqual(len(r["publish"]), 1)
        self.assertEqual(r["publish"][0]["render_hash"], "r2")
        self.assertEqual(r["publish"][0]["banner"], "> superseded")

    def test_frozen_source_hash_drift_is_a_stop(self):
        r = published.plan(
            {"pages": [self.page("plan/x", frozen=True, source_hash="NEW",
                                 render_hash="r2")]},
            {"plan/x": {"source_hash": "OLD", "render_hash": "r1"}},
        )
        self.assertEqual(r["publish"], [])
        self.assertEqual(len(r["frozen_violations"]), 1)
        self.assertEqual(r["frozen_violations"][0]["manifest_source_hash"], "NEW")
        self.assertEqual(r["frozen_violations"][0]["ledger_source_hash"], "OLD")

    def test_frozen_first_publish_is_not_a_violation(self):
        r = published.plan(
            {"pages": [self.page("plan/x", frozen=True, source_hash="s1",
                                 render_hash="r1")]},
            {},
        )
        self.assertEqual(r["frozen_violations"], [])
        self.assertEqual([p["wiki_key"] for p in r["publish"]], ["plan/x"])

    def test_sidebar_is_a_page(self):
        r = published.plan(
            {"pages": [], "sidebar": {"source": "docs/.index/rendered/_Sidebar.md",
                                      "render_hash": "abc"}},
            {},
        )
        self.assertEqual(r["publish"][0]["wiki_key"], "sidebar")
        self.assertEqual(r["publish"][0]["page_name"], "_Sidebar")

    def test_cli_exits_1_on_frozen_drift(self):
        d = tempfile.mkdtemp(prefix="worklog-plan-")
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(BIN, os.path.join(d, "bin"))
        os.makedirs(os.path.join(d, ".work"))
        os.makedirs(os.path.join(d, "docs", ".index"))
        manifest = {"version": 1, "pages": [
            {"wiki_key": "plan/x", "source": "p.md", "frozen": True,
             "source_hash": "NEW", "render_hash": "r2", "title": "X",
             "page_name": "X", "render": "doc+banner"},
        ]}
        with open(os.path.join(d, "docs", ".index", "publish-manifest.json"), "w") as fh:
            json.dump(manifest, fh)
        published_path = os.path.join(d, ".work", "published.jsonl")
        ev = {
            "ev": "01A" + "0" * 23, "ts": "2026-08-30T00:00:00Z", "actor": "t",
            "op": "publish", "key": "plan/x",
            "set": {"source_hash": "OLD", "render_hash": "r1"},
        }
        with open(published_path, "w") as fh:
            fh.write(json.dumps(ev) + "\n")
        p = run(d, "wiki-plan")
        self.assertEqual(p.returncode, 1, p.stderr)
        out = json.loads(p.stdout)
        self.assertEqual(len(out["frozen_violations"]), 1)
        self.assertIn("frozen-doc", p.stderr)

    def test_cli_missing_manifest(self):
        d = tempfile.mkdtemp(prefix="worklog-plan-")
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(BIN, os.path.join(d, "bin"))
        os.makedirs(os.path.join(d, ".work"))
        p = run(d, "wiki-plan")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("ia-render", p.stderr)


class TestGitattributes(unittest.TestCase):
    def test_union_is_declared(self):
        text = open(os.path.join(ROOT, ".gitattributes")).read()
        self.assertIn(".work/published.jsonl merge=union", text)


class TestMigrateMs(unittest.TestCase):
    def test_migrate_ms_matches_migrate_ts(self):
        """MIGRATE_MS was 1752883200000 = 2025-07-19 while MIGRATE_TS said 2026."""
        from datetime import datetime, timezone
        ts = published.MIGRATE_TS
        expected = int(
            datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=timezone.utc)
            .timestamp()
            * 1000
        )
        self.assertEqual(published.MIGRATE_MS, expected)
        self.assertEqual(ts, "2026-07-19T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
