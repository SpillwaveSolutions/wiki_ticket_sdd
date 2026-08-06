#!/usr/bin/env python3
"""Tests for bin/ulid.py -- WORKLOG-SPEC sections 5.2 and 10.2."""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import ulid  # noqa: E402
from fold import fold  # noqa: E402
from test_fold import write_log  # noqa: E402


class TestFormat(unittest.TestCase):
    def test_length_and_alphabet(self):
        u = ulid.new()
        self.assertEqual(len(u), 26)
        self.assertTrue(all(c in ulid.CROCKFORD for c in u))

    def test_lexicographic_order_matches_time_order(self):
        a = ulid.new(1_700_000_000_000)
        b = ulid.new(1_700_000_001_000)
        self.assertLess(a, b)  # the property the entire fold sort depends on

    def test_timestamp_roundtrip(self):
        ms = 1_752_678_000_123
        self.assertEqual(ulid.timestamp_ms(ulid.new(ms)), ms)

    def test_entropy_must_be_80_bits(self):
        with self.assertRaises(ValueError):
            ulid.encode(0, b"tooshort")


class TestDeterministic(unittest.TestCase):
    def test_same_remote_change_gives_same_ulid(self):
        args = ("jira", "PROJ-412", "2026-07-16T15:39:58Z", 1_752_680_398_000)
        # Two developers, two machines, two clones, one answer.
        self.assertEqual(ulid.deterministic(*args), ulid.deterministic(*args))

    def test_different_rev_gives_different_ulid(self):
        base = ("jira", "PROJ-412", "2026-07-16T15:39:58Z", 1_752_680_398_000)
        other = ("jira", "PROJ-412", "2026-07-16T16:02:11Z", 1_752_680_398_000)
        self.assertNotEqual(ulid.deterministic(*base), ulid.deterministic(*other))

    def test_different_key_gives_different_ulid(self):
        a = ulid.deterministic("jira", "PROJ-412", "r", 1_752_680_398_000)
        b = ulid.deterministic("jira", "PROJ-413", "r", 1_752_680_398_000)
        self.assertNotEqual(a, b)

    def test_timestamp_is_remote_rev_not_now(self):
        ms = 1_752_680_398_000
        u = ulid.deterministic("jira", "PROJ-412", "r", ms)
        self.assertEqual(ulid.timestamp_ms(u), ms)

    def test_local_ulids_are_not_deterministic(self):
        self.assertNotEqual(ulid.new(1_700_000_000_000), ulid.new(1_700_000_000_000))


class TestTheBugThisPrevents(unittest.TestCase):
    """Section 10.2, end to end.

    Two devs poll the same Jira change. Rick edits locally in between. Union
    merge brings both ingests into the log. If ingest `ev` is deterministic,
    dedupe collapses them and Rick's newer edit stands. If `ev` is random --
    e.g. because the remote hash was put in a sidecar field like `ev_remote` --
    the duplicate sorts above Rick's edit and silently reverts him.
    """

    REMOTE = ("jira", "PROJ-412", "2026-07-16T15:39:58Z", 1_752_680_398_000)

    def _log(self, ev_a, ev_b):
        def ingest(ev):
            return {"ev": ev, "ts": "2026-07-16T15:39:58Z", "actor": "jira", "item": "A",
                    "op": "update", "set": {"priority": "P0"},
                    "src": {"system": "jira", "key": "PROJ-412",
                            "rev": "2026-07-16T15:39:58Z"}}
        return write_log([
            {"ev": ulid.new(1_752_680_000_000), "ts": "t", "actor": "rick", "item": "A",
             "op": "create", "set": {"type": "task", "title": "x", "status": "todo",
                                     "priority": "P1"}},
            ingest(ev_a),
            {"ev": ulid.new(1_752_680_500_000), "ts": "t", "actor": "rick", "item": "A",
             "op": "update", "set": {"priority": "P2"}},  # newer than either ingest
            ingest(ev_b),
        ])

    def test_deterministic_ev_preserves_the_local_edit(self):
        ev = ulid.deterministic(*self.REMOTE)
        path = self._log(ev, ev)
        r = fold([path])
        self.assertEqual(r.deduped, 1)
        self.assertEqual(r.items["A"]["priority"], "P2")

    def test_random_ev_silently_reverts_the_local_edit(self):
        # Documents the failure. Dev B's ingest gets a later random ev, so it
        # sorts above Rick's P2 and clobbers it. Nothing errors. Nothing warns.
        path = self._log(ulid.new(1_752_680_398_000), ulid.new(1_752_680_600_000))
        r = fold([path])
        self.assertEqual(r.deduped, 0)
        self.assertEqual(r.items["A"]["priority"], "P0")  # Rick's edit is gone


class TestEntropyIsNeverSpent(unittest.TestCase):
    """01KYZNG520: v0.19.0 overwrote five entropy characters with the short
    git hash. An id is issued once and never changes, and the only thing it
    must guarantee is that it does not clash -- so entropy is not currency to
    spend on metadata. Provenance moved to the event's own `git` field."""

    def test_ids_are_26_characters(self):
        self.assertEqual(len(ulid.new()), 26)

    def test_full_entropy_is_random_across_the_whole_tail(self):
        """Every entropy position must vary. If any five consecutive ones are
        constant across many ids, something is stamping them again."""
        ids = [ulid.new(timestamp_ms=1785000000000) for _ in range(500)]
        for pos in range(10, 26):
            distinct = {i[pos] for i in ids}
            self.assertGreater(len(distinct), 1,
                               "character %d is constant -- entropy is being "
                               "overwritten" % pos)

    def test_no_collisions_in_bulk(self):
        self.assertEqual(len({ulid.new() for _ in range(5000)}), 5000)

    def test_git_commit_is_provenance_not_identity(self):
        """It must not appear in the id at all."""
        sha = ulid.git_commit()
        if not sha:
            self.skipTest("not in a git repo")
        ids = "".join(ulid.new() for _ in range(50))
        self.assertNotIn(sha.upper(), ids)

    def test_deterministic_ids_are_unchanged(self):
        a = ulid.deterministic("jira", "PROJ-1", "rev9", 1785000000000)
        b = ulid.deterministic("jira", "PROJ-1", "rev9", 1785000000000)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 26)


class TestEventProvenance(unittest.TestCase):
    """The git sha rides on the EVENT, so every event names where it came
    from -- not just the one that created the item."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-prov-")
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
        for cmd in (["git", "init", "-q", self.d],
                    ["git", "-C", self.d, "config", "user.email", "t@t"],
                    ["git", "-C", self.d, "config", "user.name", "t"]):
            subprocess.run(cmd, capture_output=True)
        open(os.path.join(self.d, "seed"), "w").close()
        subprocess.run(["git", "-C", self.d, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", self.d, "commit", "-qm", "seed"],
                       capture_output=True)

    def wl(self, *args, env=None):
        return subprocess.run(
            [sys.executable, os.path.join(self.d, "worklog"), *args],
            cwd=self.d, capture_output=True, text=True, env=env)

    def events(self):
        with open(os.path.join(self.d, ".work", "todo.jsonl")) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def head(self):
        return subprocess.run(["git", "-C", self.d, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()

    def test_every_event_carries_the_head_sha(self):
        iid = self.wl("add", "T", "--body", "b").stdout.strip()
        self.wl("update", iid, "--status", "in_progress")
        evs = self.events()
        self.assertEqual(len(evs), 2)
        for e in evs:
            self.assertEqual(e["git"], self.head())

    def test_a_later_event_records_the_commit_it_was_authored_at(self):
        """The reason it is per-event and not baked into the item id."""
        iid = self.wl("add", "T", "--body", "b").stdout.strip()
        first = self.events()[0]["git"]
        open(os.path.join(self.d, "more"), "w").close()
        subprocess.run(["git", "-C", self.d, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", self.d, "commit", "-qm", "second"],
                       capture_output=True)
        self.wl("update", iid, "--status", "in_progress")
        self.assertNotEqual(self.events()[-1]["git"], first,
                            "a later event must name its own commit")

    def test_provenance_never_becomes_item_state(self):
        iid = self.wl("add", "T", "--body", "b").stdout.strip()
        item = json.loads(self.wl("show", iid).stdout)
        self.assertNotIn("git", item)

    def test_outside_a_repo_the_field_is_omitted_not_empty(self):
        env = dict(os.environ, WORKLOG_NO_GIT_PROVENANCE="1")
        self.wl("add", "T", "--body", "b", env=env)
        self.assertNotIn("git", self.events()[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
