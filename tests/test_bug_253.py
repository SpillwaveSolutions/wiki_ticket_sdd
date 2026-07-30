#!/usr/bin/env python3
"""Tests for bug #253: priority/level/kind are single-valued, so a push must
REPLACE the label group, not append to it. Reuses the `gh` stub sandbox from
test_github_adapter.py -- see that file for how calls are recorded and
replayed.

Real-world case: issue #243 in this repo was bumped P3 -> P1 and came back
tagged both P1 and P3, because the old push path only ever added labels.
"""
import json
import unittest

from test_github_adapter import AdapterSandbox


class Bug253LabelReplace(AdapterSandbox):
    def _push_update(self, key, item, old_labels):
        self.set_responses({
            "issue edit": {"out": ""},
            "issue view": {"out": json.dumps({
                "updatedAt": "2026-07-30T00:00:00Z",
                "labels": [{"name": n} for n in old_labels],
            })},
        })
        req = {"op": "update", "key": key,
               "marker": "<!-- worklog:01A -->", "item": item}
        p = self.push(req)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def _edit_call(self):
        (edit,) = [c for c in self.gh_calls() if c[:2] == ["issue", "edit"]]
        return edit

    def _flagged(self, edit, flag):
        return {edit[i + 1] for i, a in enumerate(edit) if a == flag}

    def test_priority_bump_removes_old_priority_and_adds_new(self):
        # This is issue #243: P3 -> P1 must not leave both on the ticket.
        item = {"id": "01A", "title": "Bump", "status": "todo",
                "level": "task", "kind": "feature", "priority": "P1"}
        self._push_update("243", item,
                          ("worklog", "level:task", "kind:feature", "P3"))
        edit = self._edit_call()
        self.assertEqual(self._flagged(edit, "--remove-label"), {"P3"})
        self.assertIn("P1", self._flagged(edit, "--add-label"))

    def test_unchanged_priority_removes_nothing(self):
        item = {"id": "01A", "title": "Same", "status": "todo",
                "level": "task", "kind": "feature", "priority": "P1"}
        self._push_update("243", item,
                          ("worklog", "level:task", "kind:feature", "P1"))
        edit = self._edit_call()
        self.assertNotIn("--remove-label", edit)

    def test_level_change_removes_old_level(self):
        item = {"id": "01A", "title": "Promote", "status": "todo",
                "level": "story", "kind": "feature"}
        self._push_update("243", item, ("worklog", "level:task", "kind:feature"))
        edit = self._edit_call()
        self.assertEqual(self._flagged(edit, "--remove-label"), {"level:task"})

    def test_kind_change_removes_old_kind(self):
        item = {"id": "01A", "title": "Reclass", "status": "todo",
                "level": "task", "kind": "ops"}
        self._push_update("243", item, ("worklog", "level:task", "kind:feature"))
        edit = self._edit_call()
        self.assertEqual(self._flagged(edit, "--remove-label"), {"kind:feature"})

    def test_bug_label_removed_when_kind_flips_away_from_bug(self):
        item = {"id": "01A", "title": "Not a bug anymore", "status": "todo",
                "level": "task", "kind": "feature", "priority": "P1"}
        self._push_update("243", item,
                          ("worklog", "level:task", "kind:bug", "bug", "P1"))
        edit = self._edit_call()
        self.assertEqual(self._flagged(edit, "--remove-label"),
                         {"kind:bug", "bug"})

    def test_unowned_labels_are_never_removed(self):
        """The important safety test: labels the tooling didn't apply --
        human-applied or otherwise -- must survive every push, even when
        they look adjacent to an owned group."""
        item = {"id": "01A", "title": "Keep human labels", "status": "todo",
                "level": "task", "kind": "feature", "priority": "P1"}
        self._push_update("243", item,
                          ("worklog", "level:task", "kind:feature", "P1",
                           "needs-design", "customer-escalation"))
        edit = self._edit_call()
        self.assertEqual(self._flagged(edit, "--remove-label"), set())

    def test_bug_label_kept_when_human_applied_without_kind_bug(self):
        # "bug" is on the issue but never paired with kind:bug -- it was
        # applied by a person, not the sync, so it is not tooling-owned.
        item = {"id": "01A", "title": "Feature with bug label", "status": "todo",
                "level": "task", "kind": "feature", "priority": "P1"}
        self._push_update("243", item,
                          ("worklog", "level:task", "kind:feature", "bug", "P1"))
        edit = self._edit_call()
        self.assertEqual(self._flagged(edit, "--remove-label"), set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
