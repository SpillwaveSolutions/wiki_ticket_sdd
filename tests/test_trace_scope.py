#!/usr/bin/env python3
"""The traceability gate is scoped to the released-milestone set (#291).

`trace_check()` computed a released/closed scope label, interpolated it into
every message, and filtered on nothing -- so the gate swept all 267 closed
items instead of the 39 its own docstring claimed. 401 gaps, 323 of them on
items the docstring excludes, and the count rose with every item closed.

These tests assert the boundary in BOTH directions. An item just inside the
scope must be reported; an otherwise identical item just outside it must not.
A one-directional test is what let the original mismatch through: the old
suite asserted only that gaps appeared, which stayed true no matter how far
the sweep widened.

Design record: docs/plans/2026-08-02-trace-check-scope.md
"""
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import ia_graph  # noqa: E402


def item(**over):
    """A closed, milestoned feature with no evidence links of any kind --
    the maximally-reported item. Each test moves ONE field off this base so
    a failure names exactly which condition broke."""
    it = {"title": "Item", "status": "done", "kind": "feature",
          "milestone": "v1"}
    it.update(over)
    return it


def gaps_for(it, strict=True, code=None):
    items = {"01ABC": it}
    with patch.object(ia_graph, "item_sidecar",
                      lambda iid: {"code": code or []}):
        graph = ia_graph.build_graph(records={}, items=items)
        return ia_graph.trace_check(graph=graph, items=items, strict=strict)


class TestScopeBoundary(unittest.TestCase):
    def test_a_milestoned_item_with_no_links_reports_all_three(self):
        self.assertEqual(len(gaps_for(item())), 3)

    def test_the_same_item_without_a_milestone_reports_nothing(self):
        """The bug, at its smallest: 323 of the 401 gaps were these."""
        self.assertEqual(gaps_for(item(milestone=None)), [])

    def test_an_open_item_is_never_in_scope(self):
        self.assertEqual(gaps_for(item(status="todo")), [])

    def test_a_cancelled_item_is_never_in_scope(self):
        """Cancelled work shipped nothing, so it is evidence of nothing."""
        self.assertEqual(gaps_for(item(status="cancelled")), [])


class TestOpsIsExempt(unittest.TestCase):
    """Release cuts, status reports, compactions and worktree cleanup have no
    plan, ticket or PR by design -- the release skill states release items are
    deliberately never given an external ticket. Flagging them forever is how
    a gate teaches people to ignore it."""

    def test_a_milestoned_ops_item_reports_nothing(self):
        self.assertEqual(gaps_for(item(kind="ops")), [])

    def test_but_a_milestoned_bug_is_still_in_scope(self):
        """Exempting ops must not exempt the neighbouring kinds."""
        self.assertEqual(len(gaps_for(item(kind="bug"))), 3)


class TestUnplannedIsExemptFromThePlanCheckOnly(unittest.TestCase):
    """The taxonomy defines unplanned work as arriving without a plan, so
    demanding a plan link from it is a contradiction. It still owes evidence."""

    def test_unplanned_work_is_not_asked_for_a_plan(self):
        gaps = gaps_for(item(unplanned=True, discovered_during="01XYZ"))
        self.assertFalse(any("no plan link" in g for g in gaps), gaps)

    def test_unplanned_work_still_owes_a_ticket_and_a_pr(self):
        gaps = gaps_for(item(unplanned=True, discovered_during="01XYZ"))
        self.assertTrue(any("no external ticket" in g for g in gaps), gaps)
        self.assertTrue(any("no PR/commit link" in g for g in gaps), gaps)


class TestTheThreeChecksAreSatisfiable(unittest.TestCase):
    """Each gap must be closable, or the gate is unactionable by construction."""

    def test_a_plan_attribute_closes_the_plan_gap(self):
        gaps = gaps_for(item(plan="docs/plans/2026-08-02-x.md"))
        self.assertFalse(any("no plan link" in g for g in gaps), gaps)

    def test_an_external_key_closes_the_ticket_gap(self):
        gaps = gaps_for(item(external={"system": "github", "key": "291"}))
        self.assertFalse(any("no external ticket" in g for g in gaps), gaps)

    def test_a_pr_link_closes_the_pr_gap(self):
        gaps = gaps_for(item(), code=[{"pr": 291}])
        self.assertFalse(any("no PR/commit link" in g for g in gaps), gaps)

    def test_a_fully_linked_item_reports_nothing(self):
        gaps = gaps_for(item(plan="docs/plans/2026-08-02-x.md",
                             external={"system": "github", "key": "291"}),
                        code=[{"pr": 291}])
        self.assertEqual(gaps, [])


class TestStrictIsTheOnlyThingThatAsksForCode(unittest.TestCase):
    def test_warn_level_omits_the_pr_check(self):
        gaps = gaps_for(item(), strict=False)
        self.assertFalse(any("no PR/commit link" in g for g in gaps), gaps)

    def test_warn_level_still_asks_for_plan_and_ticket(self):
        self.assertEqual(len(gaps_for(item(), strict=False)), 2)


class TestMixedLog(unittest.TestCase):
    """End to end on a log shaped like the real one: mostly out-of-scope work
    with a few genuinely unlinked items in it."""

    def test_only_the_in_scope_item_is_reported(self):
        items = {
            "01IN": item(title="shipped feature, no evidence"),
            "01OPS": item(title="Cut v1", kind="ops"),
            "01OLD": item(title="closed, never released", milestone=None),
            "01OPEN": item(title="still going", status="todo"),
            "01DONE": item(title="fully linked",
                           plan="docs/plans/2026-08-02-x.md",
                           external={"system": "github", "key": "1"}),
        }
        with patch.object(ia_graph, "item_sidecar",
                          lambda iid: {"code": [{"pr": 1}]} if iid == "01DONE"
                          else {"code": []}):
            graph = ia_graph.build_graph(records={}, items=items)
            gaps = ia_graph.trace_check(graph=graph, items=items, strict=True)
        self.assertTrue(all(g.startswith("01IN") for g in gaps), gaps)
        self.assertEqual(len(gaps), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
