#!/usr/bin/env python3
"""`worklog pr-sync` (#138): live PR metadata reaches the wiki without the
renderer ever touching the network.

The invariant under test is the split, not the fetch: pr_sync performs the
one `gh` call and writes a committed sidecar; render_pr_page reads that
sidecar off disk. If rendering ever called out, `ia-render --check` would
regenerate-and-diff against mutable remote state and flap forever.
"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import ia                                                       # noqa: E402
import ia_graph                                                 # noqa: E402
import ia_render                                                # noqa: E402

RAW = {
    "title": "plan: close both P1 epics",
    "url": "https://github.com/acme/repo/pull/267",
    "state": "MERGED",
    "mergedAt": "2026-07-31T03:01:02Z",
    "reviewDecision": "APPROVED",
    "files": [{"path": "bin/worklog", "additions": 9},
              {"path": "bin/ia_graph.py", "additions": 70}],
    "statusCheckRollup": [{"conclusion": "SUCCESS", "status": "COMPLETED"},
                          {"conclusion": "SUCCESS", "status": "COMPLETED"}],
}


_DEFAULT = object()   # `{}` is a meaningful payload, so None is not a default


def _with_index_pages(extra):
    """build_manifest indexes every INDEX_PAGES entry; supply stubs so a PR
    assertion is not drowned by unrelated KeyErrors."""
    pages = {fname: "" for _, fname, _, _ in ia_render.INDEX_PAGES}
    pages["_Sidebar.md"] = ""
    pages.update(extra)
    return pages


class _Chdir(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.dir = tempfile.mkdtemp()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)


class TestRollupChecks(unittest.TestCase):
    """One word for many rows, and the worst state has to win."""

    def test_all_success_is_passing(self):
        self.assertEqual(ia_graph.rollup_checks(
            [{"conclusion": "SUCCESS"}, {"conclusion": "SKIPPED"}]), "passing")

    def test_one_failure_beats_many_successes(self):
        rows = [{"conclusion": "SUCCESS"}] * 9 + [{"conclusion": "FAILURE"}]
        self.assertEqual(ia_graph.rollup_checks(rows), "failing")

    def test_failure_beats_pending(self):
        self.assertEqual(ia_graph.rollup_checks(
            [{"status": "IN_PROGRESS"}, {"conclusion": "FAILURE"}]), "failing")

    def test_running_check_has_no_conclusion_yet(self):
        """A live check run carries only `status`; reading `conclusion`
        alone would silently score it as no-checks-at-all."""
        self.assertEqual(ia_graph.rollup_checks(
            [{"conclusion": "", "status": "IN_PROGRESS"}]), "pending")

    def test_commit_status_uses_state(self):
        self.assertEqual(ia_graph.rollup_checks([{"state": "PENDING"}]),
                         "pending")

    def test_no_rows_is_none(self):
        self.assertEqual(ia_graph.rollup_checks([]), "none")
        self.assertEqual(ia_graph.rollup_checks(None), "none")

    def test_unrecognised_state_is_mixed_not_passing(self):
        self.assertEqual(ia_graph.rollup_checks([{"state": "WEIRD"}]), "mixed")


class TestPrSyncSidecar(_Chdir):

    def _sync(self, raw=_DEFAULT, num=267):
        payload = RAW if raw is _DEFAULT else raw
        return ia_graph.pr_sync(num, fetch=lambda n: payload)

    def test_sidecar_round_trips_through_the_yaml_subset(self):
        """write_sidecar/read_sidecar is a hand-rolled YAML subset — the
        point of flattening files to paths is that it survives the trip."""
        written = self._sync()
        read = ia.read_sidecar("pr/267")
        self.assertEqual(read["state"], "merged")
        self.assertEqual(read["review"], "approved")
        self.assertEqual(read["checks"], "passing")
        self.assertEqual(read["number"], 267)
        self.assertEqual(read["merged_at"], "2026-07-31T03:01:02Z")
        self.assertEqual(read["files"], ["bin/ia_graph.py", "bin/worklog"])
        self.assertEqual(read["files"], written["files"])

    def test_files_are_paths_and_sorted(self):
        meta = self._sync()
        self.assertEqual(meta["files"], ["bin/ia_graph.py", "bin/worklog"])

    def test_sidecar_lands_at_the_pr_key(self):
        self._sync()
        self.assertTrue(os.path.exists("docs/.index/pr/267.yml"))

    def test_missing_fields_do_not_crash(self):
        meta = self._sync(raw={}, num=1)
        self.assertEqual(meta["state"], "unknown")
        self.assertEqual(meta["review"], "none")
        self.assertEqual(meta["checks"], "none")
        self.assertEqual(meta["files"], [])
        self.assertIsNone(meta["merged_at"])

    def test_resync_overwrites_rather_than_accumulates(self):
        self._sync()
        later = dict(RAW, state="CLOSED", files=[{"path": "README.md"}])
        meta = self._sync(raw=later)
        self.assertEqual(meta["state"], "closed")
        self.assertEqual(ia.read_sidecar("pr/267")["files"], ["README.md"])

    def test_fetch_failure_surfaces_as_value_error(self):
        def boom(n):
            raise ValueError("gh pr view 9 failed: no such PR")
        with self.assertRaises(ValueError):
            ia_graph.pr_sync(9, fetch=boom)
        self.assertEqual(ia.read_sidecar("pr/9"), {},
                         "a failed fetch must not leave a half-written page")


class TestRenderReadsTheSidecar(_Chdir):

    def _render(self, num=267):
        return ia_render.render_pr_page(num, {}, {}, {})

    def test_unsynced_pr_still_degrades_gracefully(self):
        page = self._render()
        self.assertIn("not tracked", page)
        self.assertIn("worklog pr-sync 267", page)

    def test_synced_pr_renders_live_state(self):
        ia_graph.pr_sync(267, fetch=lambda n: RAW)
        page = self._render()
        self.assertIn("status: **merged**", page)
        self.assertIn("Review: approved", page)
        self.assertIn("Checks: passing", page)
        self.assertIn("plan: close both P1 epics", page)
        self.assertIn("`bin/worklog`", page)
        self.assertNotIn("not tracked", page)

    def test_render_is_deterministic(self):
        """The freshness gate regenerates and byte-diffs; two renders of an
        unchanged sidecar must be identical."""
        ia_graph.pr_sync(267, fetch=lambda n: RAW)
        self.assertEqual(self._render(), self._render())

    def test_render_makes_no_network_call(self):
        """Hard guard on the split: fail loudly if a renderer ever grows a
        subprocess call, rather than discovering it when CI flaps."""
        import subprocess
        real = subprocess.run

        def forbidden(*a, **kw):
            raise AssertionError("render_pr_page shelled out: %r" % (a,))
        subprocess.run = forbidden
        try:
            ia_graph.pr_sync(267, fetch=lambda n: RAW)
            self.assertIn("status: **merged**", self._render())
        finally:
            subprocess.run = real

    def test_manifest_carries_real_state(self):
        ia_graph.pr_sync(267, fetch=lambda n: RAW)
        rendered = _with_index_pages({"prs/267.md": self._render()})
        man = ia_render.build_manifest({}, rendered, items={})
        page = next(p for p in man["pages"] if p["wiki_key"] == "pr/267")
        self.assertEqual(page["truth_state"], "merged")
        self.assertIn("plan: close both P1 epics", page["title"])

    def test_manifest_falls_back_when_unsynced(self):
        rendered = _with_index_pages({"prs/267.md": self._render()})
        man = ia_render.build_manifest({}, rendered, items={})
        page = next(p for p in man["pages"] if p["wiki_key"] == "pr/267")
        self.assertEqual(page["truth_state"], "not tracked")
        self.assertEqual(page["title"], "PR #267")


if __name__ == "__main__":
    unittest.main()
