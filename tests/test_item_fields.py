#!/usr/bin/env python3
"""The two item fields the spec declared but the CLI never exposed (#256),
and the fold's unreachable sort tiebreak (#259).

`estimate` and `depends_on` are normative in WORKLOG-SPEC §3.3, the fold has
always treated `depends_on` as set-valued, and five readers already resolve it
— the roadmap even renders a "Blocked by" column from it. Only the write path
was missing, so the fields could be reached by hand-editing the log and no
other way, which invariant 15.4 forbids.
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
from fold import FoldResult, dedupe_and_sort                    # noqa: E402

ULID_A = "01KYWJX3T9CQM15HQNYVHBZE4H"
ULID_B = "01KYWJX47NAVAMEMMQBQMM5HRF"


class _Repo(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-256-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        os.makedirs(os.path.join(self.dir, ".work"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.dir, ".work", f), "w").close()

    def w(self, *args, check=True):
        p = subprocess.run(
            [sys.executable, os.path.join(ROOT, "bin", "worklog"),
             "--actor", "t", *args],
            cwd=self.dir, capture_output=True, text=True)
        if check:
            self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def add(self, title, *args):
        return self.w("add", title, "--level", "task", "--kind", "feature",
                      *args).stdout.strip()

    def item(self, iid):
        return json.loads(self.w("show", iid).stdout)


class TestEstimate(_Repo):

    def test_add_records_it(self):
        iid = self.add("Sized", "--estimate", "M")
        self.assertEqual(self.item(iid)["estimate"], "M")

    def test_update_changes_it(self):
        iid = self.add("Sized", "--estimate", "S")
        self.w("update", iid, "--estimate", "XL")
        self.assertEqual(self.item(iid)["estimate"], "XL")

    def test_omitting_it_leaves_the_field_absent(self):
        """Absent, not a default: an unsized item must look unsized, the same
        reason an unclassified create folds to triage rather than feature."""
        iid = self.add("Unsized")
        self.assertNotIn("estimate", self.item(iid))

    def test_an_invented_size_is_refused(self):
        p = self.w("add", "X", "--estimate", "HUGE", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("invalid choice", p.stderr)


class TestDependsOn(_Repo):

    def test_add_records_a_dependency(self):
        blocker = self.add("Blocker")
        dep = self.add("Dependent", "--depends-on", blocker)
        self.assertEqual(self.item(dep)["depends_on"], [blocker])

    def test_several_dependencies_are_sorted_and_deduped(self):
        a, b = self.add("A"), self.add("B")
        dep = self.add("Dependent", "--depends-on", f"{b},{a},{b}")
        self.assertEqual(self.item(dep)["depends_on"], sorted([a, b]))

    def test_update_adds_and_removes(self):
        a, b = self.add("A"), self.add("B")
        dep = self.add("Dependent", "--depends-on", a)
        self.w("update", dep, "--add-depends-on", b)
        self.assertEqual(self.item(dep)["depends_on"], sorted([a, b]))
        self.w("update", dep, "--del-depends-on", a)
        self.assertEqual(self.item(dep)["depends_on"], [b])

    def test_it_uses_add_del_not_whole_field_replacement(self):
        """depends_on is SET_VALUED in the fold, like labels. Two branches
        each adding a blocker must both survive a union merge, which whole-
        field last-writer-wins would not allow."""
        a, b = self.add("A"), self.add("B")
        dep = self.add("Dependent")
        self.w("update", dep, "--add-depends-on", a)
        self.w("update", dep, "--add-depends-on", b)
        self.assertEqual(self.item(dep)["depends_on"], sorted([a, b]))
        log = open(os.path.join(self.dir, ".work", "todo.jsonl")).read()
        evs = [json.loads(l) for l in log.splitlines() if l.strip()]
        adds = [e for e in evs if "depends_on" in (e.get("add") or {})]
        self.assertEqual(len(adds), 2, "each update must emit an `add` op")

    def test_a_non_ulid_is_refused(self):
        """The shape matters: five readers resolve these to titles, so a typo
        renders as a silently missing blocker rather than an error."""
        p = self.w("add", "X", "--depends-on", "#98", check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not a 26-char ULID", p.stderr)

    def test_self_dependency_is_refused(self):
        """No ordering of the log ever makes this schedulable."""
        iid = self.add("Self")
        p = self.w("update", iid, "--add-depends-on", iid, check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("cannot depend on itself", p.stderr)

    def test_a_dependency_need_not_exist_yet(self):
        """Deliberately unvalidated, matching --parent: an append-only log
        must stay writable when the blocker is filed a minute later."""
        dep = self.add("Dependent", "--depends-on", ULID_A)
        self.assertEqual(self.item(dep)["depends_on"], [ULID_A])

    def test_the_roadmap_counts_it_as_blocked(self):
        """The reader that already existed — this is the point of the ticket."""
        blocker = self.add("Blocker")
        self.add("Dependent", "--depends-on", blocker)
        os.makedirs(os.path.join(self.dir, "docs"), exist_ok=True)
        self.w("roadmap-render")
        with open(os.path.join(self.dir, "docs", "roadmap.md")) as fh:
            self.assertIn("1 blocked", fh.read())


class TestFoldSortIsTotalOnEv(unittest.TestCase):
    """#259: the sort carried an (actor, line-hash) tiebreak that could never
    fire, because dedupe by `ev` runs first. Harmless, but it advertised a
    guarantee that came from somewhere else."""

    def _events(self, evs):
        return [{"ev": e, "op": "update", "item": "A", "actor": "x",
                 "_line": json.dumps({"ev": e})} for e in evs]

    def test_dedupe_leaves_no_duplicate_ev_for_a_tiebreak_to_resolve(self):
        r = FoldResult()
        out = dedupe_and_sort(self._events(["01B", "01A", "01B", "01A"]), r)
        self.assertEqual([e["ev"] for e in out], ["01A", "01B"])
        self.assertEqual(len({e["ev"] for e in out}), len(out))
        self.assertEqual(r.deduped, 2)

    def test_order_is_by_ev_regardless_of_input_order(self):
        r = FoldResult()
        forward = dedupe_and_sort(self._events(["01A", "01B", "01C"]), r)
        backward = dedupe_and_sort(self._events(["01C", "01B", "01A"]),
                                   FoldResult())
        self.assertEqual([e["ev"] for e in forward],
                         [e["ev"] for e in backward])

    def test_actor_and_line_no_longer_affect_the_result(self):
        """Two events with the same ev but different actors: dedupe keeps the
        FIRST, so the tiebreak never saw them — which is exactly why it was
        unreachable."""
        evs = self._events(["01A", "01A"])
        evs[0]["actor"], evs[1]["actor"] = "zeta", "alpha"
        out = dedupe_and_sort(evs, FoldResult())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["actor"], "zeta", "first wins, not lowest")


if __name__ == "__main__":
    unittest.main()
