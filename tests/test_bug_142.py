#!/usr/bin/env python3
"""Bug #142: a commit-only code entry ({'commit': sha}, written by
`worklog link-pr --commit` with no --pr) created no lands-in edge in
build_graph(), so trace-check --strict kept reporting "no PR/commit link"
even after linking a real commit."""
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import ia_graph


def graph_for(code_entries):
    """build_graph for one item "01ABC" whose sidecar has the given code
    list, with ia.read_sidecar mocked out so no real file touches disk."""
    items = {"01ABC": {"title": "Item", "status": "done"}}
    with patch.object(ia_graph, "item_sidecar",
                       lambda iid: {"code": code_entries}):
        return ia_graph.build_graph(records={}, items=items)


def item_edges(graph):
    return [(e["type"], e["to"]) for e in graph["edges"]
            if e["from"] == "item/01ABC"]


class TestLandsInEdges(unittest.TestCase):
    def test_commit_only_entry_produces_one_edge_naming_the_sha(self):
        edges = item_edges(graph_for([{"commit": "deadbeef"}]))
        self.assertEqual(edges, [("lands-in", "commit/deadbeef")])

    def test_pr_only_entry_still_produces_its_pr_edge(self):
        edges = item_edges(graph_for([{"pr": 42}]))
        self.assertEqual(edges, [("lands-in", "pr/42")])

    def test_entry_with_both_pr_and_commit_produces_exactly_one_edge(self):
        # PR wins: it's the richer artifact (review, CI, description).
        edges = item_edges(graph_for([{"pr": 42, "commit": "deadbeef"}]))
        self.assertEqual(edges, [("lands-in", "pr/42")])

    def test_empty_entry_produces_no_edge(self):
        self.assertEqual(item_edges(graph_for([{}])), [])

    def test_trace_check_strict_no_longer_flags_a_commit_only_link(self):
        items = {"01ABC": {"title": "Item", "status": "done"}}
        with patch.object(ia_graph, "item_sidecar",
                          lambda iid: {"code": [{"commit": "deadbeef"}]}):
            graph = ia_graph.build_graph(records={}, items=items)
            gaps = ia_graph.trace_check(graph=graph, items=items, strict=True)
        self.assertFalse(any("no PR/commit link" in g for g in gaps), gaps)


if __name__ == "__main__":
    unittest.main()
