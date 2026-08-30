#!/usr/bin/env python3
"""Lock tests for truth-hygiene sentences that have already drifted once.

The review (p2-hygiene) found the spec, adapters README, HOSTS.md, and
PORTS.md advertising behavior the code no longer has. These assertions fail
if the stale wording returns.
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class TestSpecFold(unittest.TestCase):
    def test_no_actor_hash_tiebreak(self):
        spec = read("docs/worklog-spec.md")
        self.assertNotIn("Ties broken by", spec)
        self.assertIn("ev` is a total order", spec)

    def test_watermark_is_per_item(self):
        spec = read("docs/worklog-spec.md")
        self.assertNotIn(
            "Discard every event with `ev` <= the highest `compact.through`",
            spec)
        self.assertIn("watermark PER ITEM", spec)
        self.assertIn("Items with no snapshot are never watermarked", spec)

    def test_status_report_is_shipped(self):
        spec = read("docs/worklog-spec.md")
        self.assertNotIn("Still specified, not yet shipped: `status-report`", spec)
        self.assertIn("`status-report` is shipped", spec)
        self.assertIn("| `status-report` |", spec)


class TestAdapterGone(unittest.TestCase):
    def test_exit_3_does_not_auto_clear(self):
        readme = read("adapters/README.md")
        self.assertNotIn("clear `external`, mark for re-push", readme)
        self.assertIn("never auto-clear `external`", readme)
        self.assertIn("worklog unlink", readme)
        self.assertIn("GONE_ABORT", readme)


class TestHostPorts(unittest.TestCase):
    def test_hosts_lists_live_cursor_events(self):
        hosts = read("docs/HOSTS.md")
        self.assertNotIn("postToolUse", hosts)
        self.assertNotIn("afterFileEdit", hosts)
        for ev in ("beforeSubmitPrompt", "stop", "sessionStart", "sessionEnd"):
            self.assertIn(ev, hosts)

    def test_ports_both_manifests_nest(self):
        ports = read("plugin/PORTS.md")
        self.assertNotIn("has it flat", ports)
        self.assertIn("nest", ports)
        self.assertIn("hooks.json", ports)


class TestPlanVsAdr(unittest.TestCase):
    def test_one_sentence_boundary(self):
        guide = read("docs/user_guide/user-guide.md")
        self.assertIn(
            "A plan is the why of a piece of work (written once, superseded not edited); "
            "an ADR is the why of a standing decision (body frozen, status mutates).",
            guide)


class TestFreezeCap(unittest.TestCase):
    def test_design_docs_skill_does_not_copy_full_pair(self):
        skill = read("plugin/skills/design-docs/SKILL.md")
        self.assertNotIn("copy each to its dated frozen name", skill)
        self.assertNotIn("Four files out.", skill)
        self.assertIn("ONE freeze note", skill)
        self.assertIn("Not a copy of the live pair", skill)

    def test_claude_skill_matches_plugin(self):
        plugin = read("plugin/skills/design-docs/SKILL.md")
        claude = read(".claude/skills/design-docs/SKILL.md")
        self.assertEqual(plugin, claude)


if __name__ == "__main__":
    unittest.main()
