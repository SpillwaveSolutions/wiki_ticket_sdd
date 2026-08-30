#!/usr/bin/env python3
"""triggers.py: config-driven event → action lists, plus legacy knobs."""
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
import triggers  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class Parse(unittest.TestCase):
    def test_block_list_items(self):
        text = """\
triggers:
  plan-capture:
    - ticket-sync
    - wiki-publish:plans
  pr-open:
    - pr-description
"""
        got = triggers.parse_triggers(text)
        self.assertEqual(got["plan-capture"], ["ticket-sync", "wiki-publish:plans"])
        self.assertEqual(got["pr-open"], ["pr-description"])
        self.assertNotIn("release", got)

    def test_inline_lists(self):
        text = "triggers:\n  pr-merge: [roadmap-render, ticket-sync:close]\n"
        got = triggers.parse_triggers(text)
        self.assertEqual(got["pr-merge"], ["roadmap-render", "ticket-sync:close"])

    def test_empty_event_is_authority(self):
        text = "triggers:\n  plan-capture: []\n"
        got = triggers.parse_triggers(text)
        self.assertEqual(got["plan-capture"], [])

    def test_comments_and_other_blocks_ignored(self):
        text = """\
sync:
  push_on_capture: true
triggers:
  # a comment
  release:
    - design-doc  # docs only
features:
  auto_merge_on_green: true
"""
        got = triggers.parse_triggers(text)
        self.assertEqual(got, {"release": ["design-doc"]})

    def test_missing_block_is_empty(self):
        self.assertEqual(triggers.parse_triggers("sync:\n  x: 1\n"), {})


class Resolve(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-trig-")
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.cfg = os.path.join(self.d, ".work", "config.yml")

    def test_defaults_when_no_file(self):
        missing = os.path.join(self.d, "nope.yml")
        self.assertEqual(
            triggers.resolve("pr-open", missing), ["pr-description"])
        self.assertEqual(
            triggers.resolve("pr-merge", missing),
            ["roadmap-render", "ticket-sync:close"])

    def test_configured_event_wins(self):
        write(self.cfg, "triggers:\n  release:\n    - design-doc\n")
        self.assertEqual(triggers.resolve("release", self.cfg), ["design-doc"])
        # unspecified events still default
        self.assertEqual(
            triggers.resolve("pr-open", self.cfg), ["pr-description"])

    def test_empty_configured_event_disables_the_default(self):
        write(self.cfg, "triggers:\n  plan-capture: []\n")
        self.assertEqual(triggers.resolve("plan-capture", self.cfg), [])

    def test_legacy_release_sync_docs(self):
        write(self.cfg, """\
release:
  sync_docs:
    - design-doc
    - readme
""")
        self.assertEqual(
            triggers.resolve("release", self.cfg),
            ["design-doc", "readme", "wiki-publish", "ticket-sync"])

    def test_triggers_release_beats_sync_docs(self):
        write(self.cfg, """\
release:
  sync_docs:
    - design-doc
triggers:
  release: [user-guide]
""")
        self.assertEqual(triggers.resolve("release", self.cfg), ["user-guide"])

    def test_legacy_push_on_capture_false_drops_ticket_sync(self):
        write(self.cfg, "sync:\n  push_on_capture: false\n")
        self.assertEqual(
            triggers.resolve("plan-capture", self.cfg),
            ["wiki-publish:plans"])

    def test_legacy_status_publish_false_drops_wiki(self):
        write(self.cfg, "status:\n  publish: false\n")
        self.assertEqual(triggers.resolve("status-report", self.cfg), [])

    def test_unknown_event_raises(self):
        with self.assertRaises(KeyError):
            triggers.resolve("nope", self.cfg)

    def test_has_matches_prefix(self):
        write(self.cfg, "triggers:\n  pr-merge: [ticket-sync:close]\n")
        self.assertTrue(triggers.has("pr-merge", "ticket-sync", self.cfg))
        self.assertTrue(triggers.has("pr-merge", "ticket-sync:close", self.cfg))
        self.assertFalse(triggers.has("pr-merge", "roadmap-render", self.cfg))


class Cli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-trig-cli-")
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        shutil.copytree(BIN, os.path.join(self.d, "bin"))
        os.makedirs(os.path.join(self.d, ".work"))
        write(os.path.join(self.d, ".work", "config.yml"), """\
triggers:
  pr-open: [pr-description]
  pr-merge: [roadmap-render]
""")

    def run_wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.d, "bin", "worklog"), *args],
            cwd=self.d, capture_output=True, text=True)

    def test_one_event(self):
        p = self.run_wl("triggers", "pr-open")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["event"], "pr-open")
        self.assertEqual(data["actions"], ["pr-description"])

    def test_all_events(self):
        p = self.run_wl("triggers")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(set(data), set(triggers.EVENTS))
        self.assertEqual(data["pr-merge"], ["roadmap-render"])

    def test_bad_event(self):
        p = self.run_wl("triggers", "nope")
        self.assertNotEqual(p.returncode, 0)


class ThisRepo(unittest.TestCase):
    def test_flagship_config_has_the_block(self):
        path = os.path.join(ROOT, ".work", "config.yml")
        text = open(path, encoding="utf-8").read()
        self.assertIn("\ntriggers:", text)
        self.assertNotIn("push_on_capture:", text)
        self.assertNotIn("publish: true", text)
        # live resolve uses the file
        actions = triggers.resolve("pr-merge", path)
        self.assertIn("roadmap-render", actions)


if __name__ == "__main__":
    unittest.main()
