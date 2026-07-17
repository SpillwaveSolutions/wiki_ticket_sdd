#!/usr/bin/env python3
"""Tests for bin/plan_capture.py -- WORKLOG-SPEC sections 12 and 13.2."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from plan_capture import parse_tasks, front_matter  # noqa: E402

DRAFT = """# Auth refactor plan

Prose about why. Not a task:
- [ ] this checkbox is above the Tasks heading and must be ignored

## Tasks

- [ ] (P0) Extract auth middleware
  - [ ] Write failing test
- [x] Session store migration

## Notes

- [ ] this checkbox is after the Tasks section and must be ignored
"""


class TestParseTasks(unittest.TestCase):
    def test_only_the_tasks_section_is_parsed(self):
        self.assertEqual(
            [t["title"] for t in parse_tasks(DRAFT)],
            ["Extract auth middleware", "Write failing test",
             "Session store migration"])

    def test_priority_token_and_default(self):
        tasks = parse_tasks(DRAFT)
        self.assertEqual(tasks[0]["priority"], "P0")
        self.assertEqual(tasks[2]["priority"], "P2")  # no token -> P2

    def test_indent_marks_subtask(self):
        self.assertEqual([t["subtask"] for t in parse_tasks(DRAFT)],
                         [False, True, False])

    def test_no_tasks_section_yields_nothing(self):
        self.assertEqual(parse_tasks("# Plan\n\n- [ ] loose checkbox\n"), [])


class TestFrontMatter(unittest.TestCase):
    def test_shape(self):
        fm = front_matter("2026-07-17", "auth", "Auth refactor",
                          "01EPIC", ["01A", "01B"])
        self.assertTrue(fm.startswith("---\n"))
        self.assertIn("date: 2026-07-17\n", fm)
        self.assertIn("slug: auth\n", fm)
        self.assertIn("epic: 01EPIC\n", fm)
        self.assertIn("items: [01A, 01B]\n", fm)
        self.assertTrue(fm.endswith("---\n\n"))


if __name__ == "__main__":
    unittest.main()
