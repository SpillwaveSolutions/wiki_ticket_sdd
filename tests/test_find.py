#!/usr/bin/env python3
"""Item #272: search the generated inventory and graph from the CLI.

It is a READER over files that already exist -- no network, no new index, no
writes. The tests build a small graph by hand so they pin behaviour rather
than this repo's current content.
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
import ia_graph  # noqa: E402

GRAPH = {
    "version": 1,
    "nodes": {
        "adr/0005-no-custom-merge-driver": {
            "doc_type": "adr", "truth_state": "current",
            "title": "No custom merge driver for the event log",
            "source": "docs/adr/0005-no-custom-merge-driver.md"},
        "plan/ia-content-model": {
            "doc_type": "plan", "truth_state": "current",
            "title": "IA & content model",
            "source": "docs/plans/ia-content-model.md"},
        "plan/wiki-information-architecture": {
            "doc_type": "plan", "truth_state": "superseded",
            "title": "Wiki information architecture",
            "source": "docs/plans/wiki-ia.md"},
        "item/01KY5G9ZW0": {
            "doc_type": "item", "title": "Phase 0: wiki-key"},
        "ticket/github#98": {"doc_type": "ticket", "title": "IA gates"},
    },
    "edges": [
        {"from": "plan/ia-content-model", "type": "supersedes",
         "to": "plan/wiki-information-architecture"},
        {"from": "plan/ia-content-model", "type": "produces",
         "to": "item/01KY5G9ZW0"},
        {"from": "item/01KY5G9ZW0", "type": "references",
         "to": "ticket/github#98"},
    ],
}


class TestSearch(unittest.TestCase):
    def test_substring_matches_title(self):
        hits = dict(ia_graph.search_nodes(GRAPH, "merge driver"))
        self.assertEqual(list(hits), ["adr/0005-no-custom-merge-driver"])

    def test_substring_matches_the_key_itself(self):
        """Keys are structured, which is why plain substring is enough."""
        hits = dict(ia_graph.search_nodes(GRAPH, "01KY5G9ZW0"))
        self.assertEqual(list(hits), ["item/01KY5G9ZW0"])

    def test_search_is_case_insensitive(self):
        self.assertTrue(ia_graph.search_nodes(GRAPH, "MERGE DRIVER"))

    def test_type_filter(self):
        keys = [k for k, _ in ia_graph.search_nodes(GRAPH, doc_type="plan")]
        self.assertEqual(keys, ["plan/ia-content-model",
                                "plan/wiki-information-architecture"])

    def test_truth_filter_answers_what_is_superseded(self):
        keys = [k for k, _ in ia_graph.search_nodes(GRAPH, truth="superseded")]
        self.assertEqual(keys, ["plan/wiki-information-architecture"])

    def test_filters_combine(self):
        keys = [k for k, _ in ia_graph.search_nodes(
            GRAPH, "content", doc_type="plan", truth="current")]
        self.assertEqual(keys, ["plan/ia-content-model"])

    def test_no_query_returns_everything(self):
        self.assertEqual(len(ia_graph.search_nodes(GRAPH)), len(GRAPH["nodes"]))


class TestTraversal(unittest.TestCase):
    def test_links_are_reported_in_both_directions(self):
        """'which plan decided this' is inbound; 'what did it supersede' is
        outbound. One command has to answer both."""
        out, back = ia_graph.node_links(GRAPH, "item/01KY5G9ZW0")
        self.assertIn(("references", "ticket/github#98"), out)
        self.assertIn(("produced-by", "plan/ia-content-model"), back)

    def test_edges_of_type(self):
        self.assertEqual(
            ia_graph.edges_of_type(GRAPH, "supersedes"),
            [("plan/ia-content-model", "plan/wiki-information-architecture")])

    def test_unknown_edge_type_lists_the_known_ones(self):
        with self.assertRaises(SystemExit) as cm:
            ia_graph.edges_of_type(GRAPH, "nonsense")
        self.assertIn("supersedes", str(cm.exception))

    def test_resolve_accepts_a_unique_substring(self):
        self.assertEqual(ia_graph.resolve_node(GRAPH, "ia-content"),
                         "plan/ia-content-model")

    def test_resolve_prefers_an_exact_key_over_substring(self):
        graph = json.loads(json.dumps(GRAPH))
        graph["nodes"]["plan/ia"] = {"doc_type": "plan", "title": "Short"}
        self.assertEqual(ia_graph.resolve_node(graph, "plan/ia"), "plan/ia")

    def test_ambiguous_resolve_is_an_error_not_a_silent_pick(self):
        with self.assertRaises(SystemExit) as cm:
            ia_graph.resolve_node(GRAPH, "plan/")
        self.assertIn("ambiguous", str(cm.exception))

    def test_unknown_node_is_an_error(self):
        with self.assertRaises(SystemExit):
            ia_graph.resolve_node(GRAPH, "nope/nothing")


class TestCli(unittest.TestCase):
    """Through `worklog find` in a sandbox holding only the generated files —
    proving it needs nothing else, no network and no repo checkout."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-find-")
        self.addCleanup(shutil.rmtree, self.d, True)
        for f in os.listdir(BIN):
            src = os.path.join(BIN, f)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(self.d, f))
        os.makedirs(os.path.join(self.d, "docs", ".index"))
        with open(os.path.join(self.d, "docs", ".index", "_graph.json"),
                  "w") as fh:
            json.dump(GRAPH, fh)

    def find(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.d, "worklog"), "find", *args],
            cwd=self.d, capture_output=True, text=True)

    def test_text_search(self):
        p = self.find("merge driver")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("No custom merge driver", p.stdout)

    def test_no_match_exits_nonzero_like_grep(self):
        p = self.find("nothing matches this")
        self.assertEqual(p.returncode, 1)

    def test_links_shows_both_directions(self):
        p = self.find("--links", "item/01KY5G9ZW0")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("-> references", p.stdout)
        self.assertIn("<- produced-by", p.stdout)

    def test_edge_listing(self):
        p = self.find("--edge", "supersedes")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("plan/wiki-information-architecture", p.stdout)

    def test_json_output_is_machine_readable(self):
        p = self.find("--type", "plan", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = json.loads(p.stdout)
        self.assertEqual({r["key"] for r in rows},
                         {"plan/ia-content-model",
                          "plan/wiki-information-architecture"})

    def test_missing_graph_says_how_to_build_it(self):
        os.remove(os.path.join(self.d, "docs", ".index", "_graph.json"))
        p = self.find("anything")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("worklog ia-graph", p.stdout + p.stderr)

    def test_it_writes_nothing(self):
        """Read-only is the contract; a search that mutates the model would
        be a much bigger promise than this ticket made."""
        before = {}
        for base, _dirs, files in os.walk(os.path.join(self.d, "docs")):
            for name in files:
                path = os.path.join(base, name)
                before[path] = os.stat(path).st_mtime_ns
        self.find("--edge", "produces")
        self.find("merge")
        after = {p: os.stat(p).st_mtime_ns for p in before}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
