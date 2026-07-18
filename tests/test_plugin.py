#!/usr/bin/env python3
"""
Plugin tests: canon sync, version sync, and the init/doctor/uninstall
lifecycle in throwaway git repos. Design contract:
docs/plans/2026-07-18-claude-plugin.md.

Not run by the pre-commit hook (spawns real repos); run by CI and by hand:
    python3 tests/test_plugin.py
"""
import filecmp
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugin")

CANON = ["bin/worklog", "bin/fold.py", "bin/ulid.py", "bin/render_roadmap.py",
         "bin/plan_capture.py", "hooks/pre-commit", "hooks/pre-merge-commit"]


def sh(cwd, *cmd, check=True):
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN)
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if check and p.returncode != 0:
        raise AssertionError(
            f"$ {' '.join(cmd)}\nexit {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


def plugin_version():
    with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")) as fh:
        return json.load(fh)["version"]


def make_repo(tc):
    """Fresh empty git repo, cleaned up after the test."""
    d = tempfile.mkdtemp(prefix="worklog-plugin-")
    tc.addCleanup(shutil.rmtree, d, True)
    sh(d, "git", "init", "-q", "-b", "main")
    sh(d, "git", "config", "user.email", "pt@test.invalid")
    sh(d, "git", "config", "user.name", "plugin-test")
    return d


def init_repo(tc):
    d = make_repo(tc)
    sh(d, "bash", os.path.join(PLUGIN, "scripts", "init.sh"))
    return d


def worklog(d, *args):
    return sh(d, sys.executable, "bin/worklog", "--actor", "pt", *args)


def read(d, rel):
    with open(os.path.join(d, rel), encoding="utf-8") as fh:
        return fh.read()


class TestCanonSync(unittest.TestCase):
    def test_repo_files_match_plugin_scripts(self):
        for rel in CANON:
            src = os.path.join(ROOT, rel)
            dst = os.path.join(PLUGIN, "scripts", os.path.basename(rel))
            self.assertTrue(
                filecmp.cmp(src, dst, shallow=False),
                f"{rel} differs from plugin copy — run: cp {rel} plugin/scripts/")


class TestVersionSync(unittest.TestCase):
    def test_cli_manifest_and_skills_agree(self):
        v = plugin_version()
        out = sh(ROOT, sys.executable, "bin/worklog", "--version").stdout
        self.assertEqual(out.strip(), f"worklog {v}")
        skills = sorted(glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md")))
        self.assertGreaterEqual(len(skills), 3)  # every skill dir must carry SKILL.md
        for path in skills:
            with open(path, encoding="utf-8") as fh:
                frontmatter = fh.read().split("---")[1]
            versions = [l.split(":", 1)[1].strip()
                        for l in frontmatter.splitlines()
                        if l.startswith("version:")]
            self.assertEqual(versions, [v], f"{path} version != plugin.json")


class TestPackaging(unittest.TestCase):
    def test_no_repo_docs_inside_plugin(self):
        banned = ("user_guide", "worklog-spec", "docs/")
        for base, _dirs, files in os.walk(PLUGIN):
            for name in files:
                rel = os.path.relpath(os.path.join(base, name), PLUGIN)
                for b in banned:
                    self.assertNotIn(
                        b, rel,
                        f"{rel}: repo docs must not ship inside the plugin")


class TestInit(unittest.TestCase):
    def test_scaffolds_a_usable_repo(self):
        d = init_repo(self)
        worklog(d, "add", "First item", "--priority", "P1")
        worklog(d, "roadmap-render")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "scaffold")  # through the hooks

        ga = read(d, ".gitattributes")
        self.assertIn(".work/todo.jsonl merge=union", ga)
        self.assertIn(".work/done.jsonl merge=union", ga)
        self.assertIn(f"installed: {plugin_version()}", read(d, ".work/config.yml"))
        hookspath = sh(d, "git", "config", "core.hooksPath").stdout.strip()
        self.assertEqual(hookspath, "hooks")

    def test_idempotent_and_lossless(self):
        d = init_repo(self)
        worklog(d, "add", "Survivor", "--priority", "P1")
        sh(d, "bash", os.path.join(PLUGIN, "scripts", "init.sh"))  # again

        items = json.loads(worklog(d, "fold").stdout)
        self.assertEqual([i["title"] for i in items], ["Survivor"])
        ga = read(d, ".gitattributes").splitlines()
        self.assertEqual(ga.count(".work/todo.jsonl merge=union"), 1)
        self.assertEqual(ga.count(".work/done.jsonl merge=union"), 1)
        installed = [l for l in read(d, ".work/config.yml").splitlines()
                     if l.startswith("installed:")]
        self.assertEqual(installed, [f"installed: {plugin_version()}"])


class TestDoctor(unittest.TestCase):
    def test_healthy_then_skew(self):
        d = init_repo(self)
        worklog(d, "add", "Item", "--priority", "P2")
        worklog(d, "roadmap-render")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "base")
        doctor = os.path.join(PLUGIN, "scripts", "doctor.sh")

        before = hashlib.sha256(read(d, ".work/config.yml").encode()).hexdigest()
        p = sh(d, "bash", doctor)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        after = hashlib.sha256(read(d, ".work/config.yml").encode()).hexdigest()
        self.assertEqual(before, after, "doctor modified .work/config.yml")

        cfg = read(d, ".work/config.yml").replace(
            f"installed: {plugin_version()}", "installed: 0.0.9")
        with open(os.path.join(d, ".work", "config.yml"), "w") as fh:
            fh.write(cfg)
        p = sh(d, "bash", doctor, check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("skew", p.stdout + p.stderr)


class TestUninstall(unittest.TestCase):
    def test_preserves_data(self):
        d = init_repo(self)
        worklog(d, "add", "Keep me", "--priority", "P1")
        worklog(d, "roadmap-render")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "tracked")

        sh(d, "bash", os.path.join(PLUGIN, "scripts", "uninstall.sh"))
        for rel in CANON:
            self.assertFalse(os.path.exists(os.path.join(d, rel)), rel)
        p = sh(d, "git", "config", "core.hooksPath", check=False)
        self.assertNotEqual(p.returncode, 0, "core.hooksPath still set")
        self.assertFalse(
            os.path.exists(os.path.join(d, ".github/workflows/worklog.yml")))

        events = [json.loads(l) for l in read(d, ".work/todo.jsonl").splitlines() if l]
        self.assertTrue(any(e.get("set", {}).get("title") == "Keep me"
                            for e in events))
        self.assertTrue(os.path.exists(os.path.join(d, "docs/roadmap.md")))
        self.assertTrue(os.path.isdir(os.path.join(d, "docs/plans")))

        p = sh(d, "bash", os.path.join(PLUGIN, "scripts", "uninstall.sh"))
        self.assertEqual(p.returncode, 0)


class TestGuardedHook(unittest.TestCase):
    HOOK = os.path.join(PLUGIN, "hooks", "scripts", "exit-plan-capture.sh")

    def test_silent_in_uninitialized_repo(self):
        d = tempfile.mkdtemp(prefix="worklog-plugin-bare-")
        self.addCleanup(shutil.rmtree, d, True)
        p = sh(d, "bash", self.HOOK)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")

    def test_emits_context_in_initialized_repo(self):
        d = init_repo(self)
        p = sh(d, "bash", self.HOOK)
        out = json.loads(p.stdout)
        self.assertTrue(out["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
