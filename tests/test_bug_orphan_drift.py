#!/usr/bin/env python3
"""Untitled fold debris is drift only while it is still open (01KYTGNS76).

Debris can never be pushed — an untitled item would file an "(untitled)"
ticket. That skip is correct and stays. What is not correct is repeating it
in the drift report forever: two settled stubs appeared in every sync run for
weeks, which trains an operator to skim the one section they must read.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import sync_dispatch                                          # noqa: E402


class _Probe(sync_dispatch.Dispatcher):
    """Runs push_items far enough to collect drift without an adapter."""

    def __init__(self):
        self.drift = []
        self.state = {"items": {}, "cursors": {}}
        self.pushed = []
        self.adapter_ok = False   # GONE bookkeeping (ADR-0004)
        self.pending_gone = {}

    def run_adapter(self, *a, **kw):
        self.pushed.append(a)
        return 0, "{}", ""


def _drift_for(status):
    d = _Probe()
    items = [{"id": "01KXSP27", "title": None, "status": status}]
    d.push_items(items, {}, [])
    return d.drift, d.pushed


class TestSettledDebrisIsSilent(unittest.TestCase):

    def test_open_untitled_item_is_still_reported(self):
        drift, _ = _drift_for("todo")
        self.assertTrue(any("orphan/untitled" in d for d in drift),
                        "open debris must still be surfaced")

    def test_closed_untitled_item_is_not_reported(self):
        for status in ("done", "cancelled"):
            drift, _ = _drift_for(status)
            self.assertFalse(any("orphan/untitled" in d for d in drift),
                             f"settled debris ({status}) must not repeat")

    def test_debris_is_never_pushed_regardless_of_status(self):
        """The safety property: silencing the report must not start pushing."""
        for status in ("todo", "done", "cancelled"):
            _, pushed = _drift_for(status)
            self.assertEqual(pushed, [],
                             f"untitled item must never be pushed ({status})")


if __name__ == "__main__":
    unittest.main()
