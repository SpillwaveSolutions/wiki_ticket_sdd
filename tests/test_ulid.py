#!/usr/bin/env python3
"""Tests for bin/ulid.py -- WORKLOG-SPEC sections 5.2 and 10.2."""

import os
import sys
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


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestGitStamp(unittest.TestCase):
    """The short git hash is stamped into locally-minted ids so two agents in
    different worktrees or branches mint visibly different ones (01KYZER08G)."""

    def test_stamp_replaces_entropy_and_keeps_the_width(self):
        out = ulid.new(git="ABCDE")
        self.assertEqual(len(out), 26)
        self.assertEqual(out[10:15], "ABCDE")

    def test_time_prefix_is_untouched(self):
        stamped = ulid.new(timestamp_ms=1785000000000, git="ABCDE")
        self.assertEqual(ulid.timestamp_ms(stamped), 1785000000000)

    def test_sort_is_still_time_sort(self):
        early = ulid.new(timestamp_ms=1785000000000, git="ZZZZZ")
        late = ulid.new(timestamp_ms=1785000001000, git="00000")
        self.assertLess(early, late,
                        "the stamp must never outrank the timestamp")

    def test_different_branches_produce_different_ids(self):
        a = ulid.new(timestamp_ms=1785000000000, git="AAAAA")
        b = ulid.new(timestamp_ms=1785000000000, git="BBBBB")
        self.assertNotEqual(a[10:15], b[10:15])

    def test_entropy_still_varies_within_one_branch(self):
        """55 bits remain; two ids in the same ms must not collide."""
        ids = {ulid.new(timestamp_ms=1785000000000, git="AAAAA")
               for _ in range(200)}
        self.assertEqual(len(ids), 200)

    def test_no_stamp_leaves_a_plain_ulid(self):
        out = ulid.new(git="")
        self.assertEqual(len(out), 26)

    def test_stamp_is_valid_crockford(self):
        """Git hashes are hex; 0-9 and A-F are all Crockford, so uppercasing
        is the whole conversion. A stamp that wasn't would make ids
        unparseable."""
        for ch in ulid.git_stamp():
            self.assertIn(ch, ulid.CROCKFORD)

    def test_deterministic_ids_are_never_stamped(self):
        """Spec §10.2: two machines ingesting the same remote change must
        produce byte-identical ids, and a per-clone git hash is the one thing
        guaranteed to differ."""
        a = ulid.deterministic("jira", "PROJ-1", "rev9", 1785000000000)
        b = ulid.deterministic("jira", "PROJ-1", "rev9", 1785000000000)
        self.assertEqual(a, b)
        self.assertNotEqual(a[10:15], ulid.git_stamp() or None)
