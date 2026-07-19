#!/usr/bin/env python3
"""Tests for bin/viz_mermaid.py -- Mermaid roadmap diagrams.

Plan: docs/plans/2026-07-19-grok-compat-and-mermaid-viz.md. Everything here
must be byte-deterministic (the pre-commit freshness gate diffs regenerated
output) and gantt dates must come from event ULID timestamps, never invented.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
sys.path.insert(0, os.path.dirname(__file__))
import ulid  # noqa: E402
import viz_mermaid  # noqa: E402
from fold import fold  # noqa: E402
from render_roadmap import render  # noqa: E402
from test_fold import write_log  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ev(n, item, op, **kw):
    e = {"ev": f"01J8X{n:04d}A0", "ts": "t", "actor": "t", "item": item, "op": op}
    e.update(kw)
    return e


def ev_at(ms, item, op, **kw):
    """Event whose ULID carries a known millisecond timestamp."""
    e = {"ev": ulid.encode(ms, bytes(10)), "ts": "t", "actor": "t",
         "item": item, "op": op}
    e.update(kw)
    return e


GRAPH_EVENTS = [
    ev(1, "E1", "create", set={"level": "epic", "kind": "feature",
                               "title": "Auth epic", "status": "todo",
                               "priority": "P0"}),
    ev(2, "T1", "create", set={"level": "task", "kind": "feature",
                               "title": "Extract middleware",
                               "status": "in_progress", "priority": "P0",
                               "parent": "E1"}),
    ev(3, "T2", "create", set={"level": "task", "kind": "bug",
                               "title": "Session migration", "status": "todo",
                               "priority": "P1", "parent": "E1",
                               "depends_on": ["T1"]}),
]


class TestDepsGraph(unittest.TestCase):
    def test_parent_solid_and_depends_on_dashed_edges(self):
        items = fold([write_log(GRAPH_EVENTS)]).items
        out = viz_mermaid.deps_graph(items)
        self.assertIn("graph TD", out)
        self.assertIn("E1 --> T1", out)        # parent: solid
        self.assertIn("T1 -.-> T2", out)       # depends_on: dashed
        self.assertIn("\U0001F41B", out)       # bug emoji in T2's label
        self.assertIn("classDef in_progress", out)

    def test_cap_at_40_with_more_note(self):
        events = [ev(i, f"I{i:03d}", "create",
                     set={"level": "task", "kind": "feature",
                          "title": f"Item {i}", "status": "todo",
                          "priority": "P2"}) for i in range(1, 46)]
        items = fold([write_log(events)]).items
        out = viz_mermaid.deps_graph(items)
        self.assertIn("_+5 more items not shown_", out)
        self.assertEqual(sum(1 for l in out.splitlines() if '["' in l), 40)

    def test_escaping_strips_mermaid_breaking_chars(self):
        events = [ev(1, "X1", "create",
                     set={"level": "task", "kind": "feature",
                          "title": 'Fix [the] {bad} "quote" <tag>|`x`',
                          "status": "todo"})]
        items = fold([write_log(events)]).items
        out = viz_mermaid.deps_graph(items)
        for ch in '[]{}"`<>|':
            self.assertNotIn(f"Fix {ch}", out)
        self.assertIn("Fix the bad quote", out)


class TestHierarchy(unittest.TestCase):
    def test_epic_to_task_edge(self):
        items = fold([write_log(GRAPH_EVENTS)]).items
        out = viz_mermaid.hierarchy(items)
        self.assertIn("E1 --> T1", out)
        self.assertNotIn("-.->", out)  # hierarchy has no dep edges


class TestGantt(unittest.TestCase):
    START = 1752900000000   # 2025-07-19T05:20:00Z
    CLOSE = 1753100000000   # 2025-07-21T12:53:20Z

    def events(self):
        return [
            ev_at(self.START - 86400000, "G1", "create",
                  set={"level": "task", "kind": "feature", "title": "Ship viz",
                       "status": "todo", "milestone": "v0.9.0"}),
            ev_at(self.START, "G1", "update", set={"status": "in_progress"}),
            ev_at(self.CLOSE, "G1", "close", set={"status": "done"}),
            # milestone-less item with dates: must NOT appear in the gantt
            ev_at(self.START, "G2", "create",
                  set={"level": "task", "kind": "ops", "title": "No milestone",
                       "status": "in_progress"}),
        ]

    def test_bar_uses_event_dates_and_omits_milestone_less(self):
        paths = [write_log(self.events())]
        items = fold(paths).items
        dates, now = viz_mermaid.item_dates(paths)
        out = viz_mermaid.gantt(items, dates, now)
        self.assertIn("section v0.9.0", out)
        self.assertIn("2025-07-19", out)   # started, not created
        self.assertIn("2025-07-21", out)   # closed
        self.assertIn("done, ", out)
        self.assertNotIn("No milestone", out)

    def test_omitted_when_no_eligible_items(self):
        paths = [write_log(GRAPH_EVENTS)]  # nothing carries a milestone
        items = fold(paths).items
        dates, now = viz_mermaid.item_dates(paths)
        self.assertEqual(viz_mermaid.gantt(items, dates, now), "")


class TestRenderIntegration(unittest.TestCase):
    def test_determinism_including_viz(self):
        a = render([write_log(GRAPH_EVENTS)], viz="all")
        b = render([write_log(list(reversed(GRAPH_EVENTS)))], viz="all")
        self.assertEqual(a, b)
        self.assertIn("## Visual roadmap", a)

    def test_viz_none_omits_section(self):
        out = render([write_log(GRAPH_EVENTS)], viz="none")
        self.assertNotIn("## Visual roadmap", out)

    def test_mermaid_fences_balanced(self):
        out = render([write_log(GRAPH_EVENTS)], viz="all")
        self.assertEqual(out.count("```") % 2, 0)
        self.assertEqual(out.count("```mermaid"), 2)  # no gantt: no milestones

    def test_empty_log_has_no_viz_section(self):
        self.assertNotIn("## Visual roadmap", render([write_log([])], viz="all"))


class TestCli(unittest.TestCase):
    """Sandbox convention: copy bin/ into a tempdir, run subprocesses with
    cwd=sandbox (the coverage gate depends on this layout)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-viz-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        os.makedirs(os.path.join(self.dir, ".work"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.dir, ".work", f), "w").close()

    def wl(self, *args):
        p = subprocess.run([sys.executable, "bin/worklog", *args],
                           cwd=self.dir, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def roadmap(self):
        with open(os.path.join(self.dir, "docs", "roadmap.md")) as fh:
            return fh.read()

    def test_no_viz_flag_and_default(self):
        self.wl("add", "One item", "--kind", "feature")
        self.wl("roadmap-render", "--no-viz")
        self.assertNotIn("## Visual roadmap", self.roadmap())
        self.wl("roadmap-render")  # default: deps,hierarchy
        out = self.roadmap()
        self.assertIn("## Visual roadmap", out)
        self.assertIn("### Dependency graph", out)


if __name__ == "__main__":
    unittest.main()
