#!/usr/bin/env python3
"""Tests for bug #222 -- a finished-but-unclosed epic must not rot invisibly.

The renderer only put an epic on the roadmap when one of its children landed
in a Now/Next/Later bucket. The moment the last open child closed, the epic
vanished from the roadmap entirely even though it was still open work.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
sys.path.insert(0, os.path.dirname(__file__))
from render_roadmap import render  # noqa: E402
from test_fold import write_log  # noqa: E402


def ev(n, item, op, **kw):
    e = {"ev": f"01J8X{n:04d}A0", "ts": "t", "actor": "t", "item": item, "op": op}
    e.update(kw)
    return e


class TestStaleEpicSurfaced(unittest.TestCase):
    def test_open_epic_with_all_children_closed_is_shown(self):
        out = render([write_log([
            ev(1, "E1", "create", set={"level": "epic", "kind": "feature",
                                       "title": "Finished Epic", "status": "todo",
                                       "priority": "P1"}),
            ev(2, "T1", "create", set={"level": "task", "kind": "feature",
                                       "title": "Last child", "status": "todo",
                                       "priority": "P1", "parent": "E1"}),
            ev(3, "T1", "close", set={"status": "done"}),
        ])])
        self.assertIn("## Needs attention", out)
        self.assertIn("Finished Epic", out.split("## Needs attention")[1])

    def test_closed_epic_with_all_children_closed_is_not_shown(self):
        out = render([write_log([
            ev(1, "E1", "create", set={"level": "epic", "kind": "feature",
                                       "title": "Done Epic", "status": "todo",
                                       "priority": "P1"}),
            ev(2, "T1", "create", set={"level": "task", "kind": "feature",
                                       "title": "Last child", "status": "todo",
                                       "priority": "P1", "parent": "E1"}),
            ev(3, "T1", "close", set={"status": "done"}),
            ev(4, "E1", "close", set={"status": "done"}),
        ])])
        self.assertNotIn("Done Epic", out)

    def test_open_epic_with_open_child_still_shown_no_regression(self):
        out = render([write_log([
            ev(1, "E1", "create", set={"level": "epic", "kind": "feature",
                                       "title": "Active Epic", "status": "todo",
                                       "priority": "P1"}),
            ev(2, "T1", "create", set={"level": "task", "kind": "feature",
                                       "title": "Still open", "status": "todo",
                                       "priority": "P1", "parent": "E1"}),
        ])])
        self.assertIn("### Active Epic", out)
        # not flagged as stale -- it still has an open child
        if "## Needs attention" in out:
            self.assertNotIn("Active Epic", out.split("## Needs attention")[1])

    def test_open_epic_with_no_children_at_all_is_shown(self):
        out = render([write_log([
            ev(1, "E1", "create", set={"level": "epic", "kind": "feature",
                                       "title": "Childless Epic", "status": "todo",
                                       "priority": "P1"}),
        ])])
        self.assertIn("## Needs attention", out)
        self.assertIn("Childless Epic", out.split("## Needs attention")[1])


if __name__ == "__main__":
    unittest.main()
