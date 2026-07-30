#!/usr/bin/env python3
"""Bug #137: banner() called every frozen+current doc a "report" — plans,
roadmap snapshots, and dated designs are frozen (ia.is_frozen()) but are not
status reports. Pins banner() to branch on doc_type specifically."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import ia_render


class TestBug137FrozenCurrentBanners(unittest.TestCase):
    def test_status_report_still_reads_as_its_kind(self):
        rec = {"doc_type": "status", "truth_state": "current",
               "source": "docs/status/2026-01-01-daily.md", "kind": "daily"}
        self.assertIn("daily report", ia_render.banner(rec, {}))

    def test_frozen_current_plan_is_not_called_a_report(self):
        rec = {"doc_type": "plan", "truth_state": "current",
               "source": "docs/plans/2026-01-01-foo.md"}
        b = ia_render.banner(rec, {})
        self.assertNotIn("report", b)
        self.assertIn("plan", b.lower())

    def test_frozen_current_roadmap_snapshot_is_not_called_a_report(self):
        rec = {"doc_type": "roadmap-snapshot", "truth_state": "current",
               "source": "docs/roadmap-snapshots/2026-01-01_v1.0.0.md"}
        b = ia_render.banner(rec, {})
        self.assertNotIn("report", b)

    def test_frozen_current_dated_design_is_not_called_a_report(self):
        rec = {"doc_type": "design", "truth_state": "current",
               "source": "docs/designs/2026-01-01_foo_design_doc.md"}
        b = ia_render.banner(rec, {})
        self.assertNotIn("report", b)

    def test_every_frozen_current_doc_type_yields_a_banner(self):
        recs = [
            {"doc_type": "status", "truth_state": "current",
             "source": "docs/status/2026-01-01-daily.md", "kind": "daily"},
            {"doc_type": "plan", "truth_state": "current",
             "source": "docs/plans/2026-01-01-foo.md"},
            {"doc_type": "roadmap-snapshot", "truth_state": "current",
             "source": "docs/roadmap-snapshots/2026-01-01_v1.0.0.md"},
            {"doc_type": "design", "truth_state": "current",
             "source": "docs/designs/2026-01-01_foo_design_doc.md"},
        ]
        for rec in recs:
            b = ia_render.banner(rec, {})
            self.assertTrue(b.startswith("> **"), rec["doc_type"])
            self.assertGreater(len(b), 0)


if __name__ == "__main__":
    unittest.main()
