#!/usr/bin/env python3
"""Tests for the work taxonomy (docs/plans/2026-07-18-work-taxonomy.md).

Covers spec §8 tests 1-5 and 10: default kind:triage, epic kind rules,
free-floating bugs, leaf-only milestones, legacy `type` migration in the
fold, and suggestion promotion. Sandbox subprocess style (see test_link.py).
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
from canonical import canonical_hash  # noqa: E402


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-taxonomy-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        os.makedirs(os.path.join(self.dir, ".work"))

    def run_wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def show(self, item):
        return json.loads(self.wl("show", item))

    def append_raw(self, event):
        with open(os.path.join(self.dir, ".work", "todo.jsonl"), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")


class TestDefaults(Sandbox):
    def test_add_without_kind_folds_to_triage(self):
        """Spec §8.1: create with no kind -> kind:triage, never feature."""
        item = self.wl("add", "Unclassified thing")
        shown = self.show(item)
        self.assertEqual(shown["kind"], "triage")
        self.assertEqual(shown["level"], "task")

    def test_explicit_kind_is_kept(self):
        item = self.wl("add", "Ops chore", "--kind", "ops")
        self.assertEqual(self.show(item)["kind"], "ops")


class TestEpicRules(Sandbox):
    def test_epic_kind_bug_rejected(self):
        """Spec §8.2: level:epic kind:bug is a category error."""
        p = self.run_wl("add", "Bad epic", "--level", "epic", "--kind", "bug")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("epics are feature or ops", p.stdout + p.stderr)

    def test_epic_kind_triage_rejected(self):
        p = self.run_wl("add", "Vague epic", "--level", "epic",
                        "--kind", "triage")
        self.assertNotEqual(p.returncode, 0)

    def test_epic_milestone_rejected(self):
        """Spec §8.4: milestone lives on leaves; epic milestone is derived."""
        p = self.run_wl("add", "Epic", "--level", "epic", "--kind", "feature",
                        "--milestone", "v1")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("milestone lives on leaves", p.stdout + p.stderr)

    def test_update_epic_to_bad_kind_rejected(self):
        epic = self.wl("add", "Epic", "--level", "epic", "--kind", "feature")
        p = self.run_wl("update", epic, "--kind", "bug")
        self.assertNotEqual(p.returncode, 0)

    def test_leaf_milestone_accepted(self):
        item = self.wl("add", "Ship it", "--kind", "feature",
                       "--milestone", "v0.7.0")
        self.assertEqual(self.show(item)["milestone"], "v0.7.0")


class TestBugs(Sandbox):
    def test_bug_without_parent_is_valid(self):
        """Spec §8.3: bugs may float free of any epic."""
        item = self.wl("add", "Broken thing", "--level", "task", "--kind", "bug")
        shown = self.show(item)
        self.assertEqual(shown["kind"], "bug")
        self.assertNotIn("parent", shown)


class TestLegacyMigration(Sandbox):
    def raw_create(self, ev, item, typ):
        self.append_raw({"ev": ev, "ts": "t", "actor": "r", "item": item,
                         "op": "create",
                         "set": {"type": typ, "title": "legacy",
                                 "status": "todo"}})

    def test_legacy_type_bug_folds_to_task_bug(self):
        """Spec §8.5: old type values map per §3.2."""
        self.raw_create("01A", "LEGACYBUG1", "bug")
        shown = self.show("LEGACYBUG1")
        self.assertEqual(shown["level"], "task")
        self.assertEqual(shown["kind"], "bug")
        self.assertNotIn("type", shown)

    def test_legacy_type_story_folds_to_story_feature(self):
        self.raw_create("01B", "LEGACYSTRY", "story")
        shown = self.show("LEGACYSTRY")
        self.assertEqual(shown["level"], "story")
        self.assertEqual(shown["kind"], "feature")

    def test_legacy_snapshot_is_normalized_too(self):
        self.append_raw({"ev": "01C", "ts": "t", "actor": "compactor",
                         "item": "LEGACYSNAP", "op": "snapshot",
                         "set": {"type": "epic", "title": "old epic",
                                 "status": "todo"}})
        shown = self.show("LEGACYSNAP")
        self.assertEqual(shown["level"], "epic")
        self.assertEqual(shown["kind"], "feature")

    def test_type_flag_alias_warns_but_works(self):
        p = self.run_wl("add", "Aliased", "--type", "task")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("--type is deprecated", p.stderr)
        shown = self.show(p.stdout.strip())
        self.assertEqual(shown["level"], "task")
        self.assertEqual(shown["kind"], "feature")  # legacy type -> feature

    def test_type_flag_bug_maps_to_task_bug(self):
        p = self.run_wl("add", "Aliased bug", "--type", "bug")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        shown = self.show(p.stdout.strip())
        self.assertEqual(shown["level"], "task")
        self.assertEqual(shown["kind"], "bug")


class TestPromote(Sandbox):
    SUGGESTION = {
        "suggestion_id": "01SUGGESTAAAAAAAAAAAAAAAAA",
        "source_span": "turn-12",
        "proposed": {"level": "task", "kind": "triage", "parent": None,
                     "milestone": "v0.7.0", "title": "Fix flaky retry"},
        "confidence": 0.55,
        "open_questions": ["own story or under the sync epic?"],
    }

    def suggestions_path(self):
        return os.path.join(self.dir, ".work", "suggestions.jsonl")

    def write_suggestions(self, records):
        with open(self.suggestions_path(), "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")

    def test_promote_creates_exactly_one_item_and_marks_consumed(self):
        """Spec §8.10: one create event, then a consumed marker."""
        self.write_suggestions([self.SUGGESTION])
        item = self.wl("promote", self.SUGGESTION["suggestion_id"])
        shown = self.show(item)
        self.assertEqual(shown["level"], "task")
        self.assertEqual(shown["kind"], "triage")  # honored, not upgraded
        self.assertEqual(shown["milestone"], "v0.7.0")
        self.assertEqual(shown["title"], "Fix flaky retry")
        with open(os.path.join(self.dir, ".work", "todo.jsonl"),
                  encoding="utf-8") as fh:
            creates = [l for l in fh if '"op": "create"' in l
                       or '"op":"create"' in l]
        self.assertEqual(len(creates), 1)
        with open(self.suggestions_path(), encoding="utf-8") as fh:
            lines = [json.loads(l) for l in fh if l.strip()]
        markers = [l for l in lines if l.get("consumed")]
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["suggestion_id"],
                         self.SUGGESTION["suggestion_id"])

    def test_second_promote_refuses(self):
        self.write_suggestions([self.SUGGESTION])
        self.wl("promote", self.SUGGESTION["suggestion_id"])
        p = self.run_wl("promote", self.SUGGESTION["suggestion_id"])
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("consumed", p.stdout + p.stderr)

    def test_unknown_suggestion_refuses(self):
        self.write_suggestions([self.SUGGESTION])
        p = self.run_wl("promote", "01NOPE")
        self.assertNotEqual(p.returncode, 0)

    def test_missing_suggestions_file_is_a_clear_error(self):
        p = self.run_wl("promote", "01ANYTHING")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("suggestions.jsonl not found", p.stdout + p.stderr)


class TestEmptyItemId(Sandbox):
    def test_update_empty_item_rejected_and_log_untouched(self):
        self.wl("add", "Real thing")
        log = os.path.join(self.dir, ".work", "todo.jsonl")
        with open(log, encoding="utf-8") as fh:
            before = len(fh.readlines())
        p = self.run_wl("update", "", "--status", "in_progress")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("empty item id", p.stdout + p.stderr)
        with open(log, encoding="utf-8") as fh:
            self.assertEqual(len(fh.readlines()), before)


class TestCanonicalHash(unittest.TestCase):
    def test_hash_includes_kind(self):
        a = {"title": "x", "level": "task", "kind": "feature", "status": "todo"}
        b = dict(a, kind="bug")
        self.assertNotEqual(canonical_hash(a), canonical_hash(b))

    def test_hash_ignores_dropped_type_field(self):
        a = {"title": "x", "level": "task", "kind": "bug", "status": "todo"}
        b = dict(a, type="task")  # legacy field must not affect the hash
        self.assertEqual(canonical_hash(a), canonical_hash(b))


if __name__ == "__main__":
    unittest.main(verbosity=2)
