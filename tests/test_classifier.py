#!/usr/bin/env python3
"""Tests for the work-taxonomy always-on + flag-gated classifier plumbing.

Spec: docs/plans/2026-07-18-work-taxonomy.md §8 tests 7-9.

7  - `init.sh taxonomy` writes the block between markers, idempotently.
8  - classifier off (or config absent): Stop hook keeps exact v0.6 block behavior.
9  - classifier on: hook emits additionalContext naming the classify skill,
     never blocks, never creates suggestions.jsonl itself.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "hooks", "stop-worklog-check.sh")
PLUGIN_HOOK = os.path.join(ROOT, "plugin", "hooks", "scripts", "stop-worklog-check.sh")
INIT = os.path.join(ROOT, "plugin", "scripts", "init.sh")

MARK_START = "<!-- worklog:taxonomy:start -->"
MARK_END = "<!-- worklog:taxonomy:end -->"

CLASSIFIER_ON = """\
version: 1

classifier:
  enabled: true
  min_confidence: 0.7
  debounce: stop
"""

CLASSIFIER_OFF = CLASSIFIER_ON.replace("enabled: true", "enabled: false")


def make_repo(tc):
    """Sandbox git repo: committed base, bin/worklog present, dirty file."""
    d = tempfile.mkdtemp(prefix="clsf-")
    tc.addCleanup(shutil.rmtree, d)
    subprocess.run(["git", "init", "-q", d], check=True)
    subprocess.run(["git", "-C", d, "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", d, "config", "user.name", "t"], check=True)
    os.makedirs(os.path.join(d, ".work"))
    os.makedirs(os.path.join(d, "bin"))
    shutil.copy2(os.path.join(ROOT, "bin", "worklog"), os.path.join(d, "bin", "worklog"))
    open(os.path.join(d, ".work", "todo.jsonl"), "w").close()
    open(os.path.join(d, "base.txt"), "w").write("base\n")
    subprocess.run(["git", "-C", d, "add", "-A"], check=True)
    subprocess.run(["git", "-C", d, "commit", "-qm", "base"], check=True)
    # Dirty the tree outside .work so the hook's gate fires.
    open(os.path.join(d, "src.txt"), "w").write("work happened\n")
    return d


def run_hook(cwd):
    return subprocess.run(
        ["bash", HOOK], cwd=cwd, capture_output=True, text=True,
        input='{"stop_hook_active": false}',
    )


class TestStopHookClassifierGate(unittest.TestCase):
    def test_copies_byte_identical(self):
        with open(HOOK, "rb") as a, open(PLUGIN_HOOK, "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_8_classifier_off_blocks_as_v06(self):
        d = make_repo(self)
        with open(os.path.join(d, ".work", "config.yml"), "w") as fh:
            fh.write(CLASSIFIER_OFF)
        r = run_hook(d)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block")
        self.assertNotIn("classif", r.stdout)  # no classifier leakage when off

    def test_9b_config_absent_blocks_as_v06(self):
        d = make_repo(self)  # no .work/config.yml at all
        r = run_hook(d)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block")
        self.assertNotIn("classif", r.stdout)

    def test_9_classifier_on_emits_context_not_block(self):
        d = make_repo(self)
        with open(os.path.join(d, ".work", "config.yml"), "w") as fh:
            fh.write(CLASSIFIER_ON)
        r = run_hook(d)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)  # must be valid single-JSON output
        self.assertNotIn("decision", out)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("classify skill", ctx)
        self.assertIn(".work/suggestions.jsonl", ctx)
        # The hook itself never writes suggestions; it only instructs the model.
        self.assertFalse(os.path.exists(os.path.join(d, ".work", "suggestions.jsonl")))

    def test_clean_tree_stays_silent_in_both_modes(self):
        for cfg in (CLASSIFIER_ON, CLASSIFIER_OFF):
            d = make_repo(self)
            os.remove(os.path.join(d, "src.txt"))  # clean tree
            with open(os.path.join(d, ".work", "config.yml"), "w") as fh:
                fh.write(cfg)
            r = run_hook(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "")


class TestTaxonomyBlockInstall(unittest.TestCase):
    def _install(self, cwd):
        r = subprocess.run(["bash", INIT, "taxonomy"], cwd=cwd,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return open(os.path.join(cwd, "CLAUDE.md")).read()

    def test_7_writes_between_markers_idempotently(self):
        d = make_repo(self)
        with open(os.path.join(d, "CLAUDE.md"), "w") as fh:
            fh.write("# My Project\n\nExisting policy.\n")

        text = self._install(d)
        self.assertEqual(text.count(MARK_START), 1)
        self.assertEqual(text.count(MARK_END), 1)
        self.assertTrue(text.startswith("# My Project"))  # existing content kept
        canonical = re.search(
            re.escape(MARK_START) + r".*?" + re.escape(MARK_END), text, re.S
        ).group(0)
        self.assertIn("level", canonical)
        self.assertIn("kind:triage", canonical)

        # Mutate the inner text, re-run: canonical restored, still one block.
        mutated = text.replace("Work taxonomy", "MUTATED HEADING")
        with open(os.path.join(d, "CLAUDE.md"), "w") as fh:
            fh.write(mutated)
        text2 = self._install(d)
        self.assertEqual(text2.count(MARK_START), 1)
        self.assertIn(canonical, text2)
        self.assertNotIn("MUTATED HEADING", text2)

    def test_7_creates_claude_md_when_absent(self):
        d = make_repo(self)
        text = self._install(d)
        self.assertEqual(text.count(MARK_START), 1)

    def test_taxonomy_arg_touches_nothing_else(self):
        d = make_repo(self)
        self._install(d)
        # taxonomy-only run must not scaffold bin/hooks/config.
        self.assertFalse(os.path.exists(os.path.join(d, ".work", "config.yml")))
        self.assertFalse(os.path.exists(os.path.join(d, "hooks")))


if __name__ == "__main__":
    unittest.main()
