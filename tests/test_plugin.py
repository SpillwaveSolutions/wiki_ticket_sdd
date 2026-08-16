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
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugin")

CANON = ["bin/worklog", "bin/fold.py", "bin/ulid.py", "bin/render_roadmap.py",
         "bin/viz_mermaid.py",
         "bin/plan_capture.py", "bin/compact.py", "bin/adr.py",
         "bin/sync_dispatch.py", "bin/canonical.py", "bin/ia.py",
         "bin/ia_render.py", "bin/ia_graph.py", "bin/item_fields.py",
         "bin/wiki_flavor.py", "bin/session.py", "bin/changelog.py",
         "bin/okf_write.py",
         "hooks/pre-commit", "hooks/pre-merge-commit", "hooks/commit-msg"]

# Hooks the harness runs (not git hooks) live in a second directory and are
# mirrored the same way. #236 added two more, and nothing was checking them.
HOOK_CANON = ["prompt-reminder.sh", "session-doctor.sh", "session-end.sh",
              "stop-worklog-check.sh", "exit-plan-capture.sh"]


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


def codex_plugin_version():
    with open(os.path.join(PLUGIN, ".codex-plugin", "plugin.json")) as fh:
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


def front_matter(path):
    """The frontmatter block, parsed the way a real consumer parses it.

    Deliberately NOT `text.split("---")[1]`, which is what this file used to
    do: splitting on the SUBSTRING happily swallows a malformed
    `version: 0.18.0---` fence, so twelve shipped skills carried broken
    frontmatter for a release cycle while the test stayed green (#263). Every
    real reader scans for a LINE that is exactly `---`; so does this.
    """
    lines = open(path, encoding="utf-8").read().split("\n")
    if not lines or lines[0].strip() != "---":
        raise AssertionError(f"{path}: no opening frontmatter fence")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise AssertionError(
            f"{path}: frontmatter is never closed by a line that is exactly "
            f"'---' — check for a value fused to the fence, e.g. "
            f"'version: 1.2.3---'")
    return lines[1:end]


class TestCanonSync(unittest.TestCase):
    def test_repo_files_match_plugin_scripts(self):
        for rel in CANON:
            src = os.path.join(ROOT, rel)
            dst = os.path.join(PLUGIN, "scripts", os.path.basename(rel))
            self.assertTrue(
                filecmp.cmp(src, dst, shallow=False),
                f"{rel} differs from plugin copy — run: cp {rel} plugin/scripts/")

    def test_repo_hooks_match_plugin_hooks(self):
        for name in HOOK_CANON:
            src = os.path.join(ROOT, "hooks", name)
            dst = os.path.join(PLUGIN, "hooks", "scripts", name)
            self.assertTrue(
                filecmp.cmp(src, dst, shallow=False),
                f"hooks/{name} differs from plugin copy — "
                f"run: cp hooks/{name} plugin/hooks/scripts/")

    def test_skill_trees_match(self):
        """#257: skills existed as two unlinked copies and had drifted in both
        directions — one carried a pre-release gate the other lacked, the
        other a release note the first lacked. CANON covered scripts and
        hooks but not skills, so nothing failed while they diverged."""
        shipped = os.path.join(PLUGIN, "skills")
        local = os.path.join(ROOT, ".claude", "skills")
        names = sorted(os.listdir(shipped))
        self.assertGreaterEqual(len(names), 3)
        self.assertEqual(names, sorted(os.listdir(local)),
                         "a skill exists in one tree but not the other")
        for rel in sorted(glob.glob(os.path.join(shipped, "**", "*.md"),
                                    recursive=True)):
            other = rel.replace(shipped, local, 1)
            self.assertTrue(
                os.path.exists(other), f"{other} is missing")
            self.assertTrue(
                filecmp.cmp(rel, other, shallow=False),
                f"{os.path.relpath(rel, ROOT)} differs from the .claude copy "
                f"— skills ship from plugin/skills; copy that side over")


class TestCodexHookParity(unittest.TestCase):
    """The Codex plugin must ship the enforcement hooks, not just the skills.

    The first cut of the Codex package shipped skills alone, reasoning that the
    hosts use incompatible hook schemas. They do not: Codex reads the same
    hookSpecificOutput/additionalContext output our scripts already emit and
    sets CLAUDE_PLUGIN_ROOT for plugin-sourced hooks, so the scripts are shared
    verbatim and only the wrapper differs. These tests pin that, because a
    Codex package with no hooks is the exact failure this project exists to
    prevent -- policy that holds only because someone remembers it.
    """

    def codex_hooks(self):
        with open(os.path.join(PLUGIN, "hooks", "codex-hooks.json")) as fh:
            return json.load(fh)

    def claude_hooks(self):
        with open(os.path.join(PLUGIN, "hooks", "hooks.json")) as fh:
            return json.load(fh)["hooks"]

    def test_the_manifest_points_at_the_hooks_file(self):
        with open(os.path.join(PLUGIN, ".codex-plugin", "plugin.json")) as fh:
            rel = json.load(fh)["hooks"]
        # paths in the manifest resolve against the PLUGIN ROOT (the directory
        # holding .codex-plugin/), not against the manifest's own directory
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, rel.lstrip("./"))),
                        f"manifest hooks path {rel} resolves to nothing")

    def test_BOTH_hosts_wrap_the_event_map_under_a_hooks_key(self):
        """This test used to assert the OPPOSITE for Claude, and was wrong.

        Shipping the Codex manifest, the wrapper was read as a Codex quirk and
        this test pinned Claude's file as flat. It never was: `plugin/` had
        declared its events at the top level since the hooks were written, the
        loader read no events, and EVERY plugin hook silently did nothing for
        anyone who installed it -- including the plan-capture hook this plugin
        is partly built around. The file is valid JSON, so nothing complained.

        Four of four other installed plugins (superpowers, i-have-adhd,
        okf-graph-eng, explanatory-output-style) use the wrapper. Found
        against a real installation in #329; the repo's own sessions never
        caught it because they wire these scripts through settings, not
        through the plugin loader.
        """
        for name in ("hooks.json", "codex-hooks.json"):
            with open(os.path.join(PLUGIN, "hooks", name)) as fh:
                top = json.load(fh)
            self.assertIn("hooks", top,
                          f"{name}: the loader reads events from under a "
                          f"top-level 'hooks' key; a flat map parses fine and "
                          f"loads nothing")
            self.assertNotIn("PostToolUse", top,
                             f"{name}: events must be nested, not top-level")

    def test_every_hook_command_points_at_an_executable_script(self):
        """A path typo fails the same way a missing wrapper does: quietly.
        Both manifests, every event, every command."""
        for name in ("hooks.json", "codex-hooks.json"):
            with open(os.path.join(PLUGIN, "hooks", name)) as fh:
                events = json.load(fh)["hooks"]
            for ev, groups in events.items():
                for entry in groups:
                    for h in entry["hooks"]:
                        rel = h["command"].split("}\"/", 1)[1]
                        path = os.path.join(PLUGIN, rel)
                        self.assertTrue(os.path.isfile(path),
                                        f"{name} {ev}: {rel} does not exist")
                        self.assertTrue(os.access(path, os.X_OK),
                                        f"{name} {ev}: {rel} is not executable")

    def test_the_enforcement_hooks_reach_codex(self):
        """UserPromptSubmit and Stop are the two the policy file names as the
        work-tracking enforcement mechanism. Losing either is the regression."""
        events = self.codex_hooks()["hooks"]
        for ev in ("UserPromptSubmit", "Stop", "SessionStart"):
            self.assertIn(ev, events, f"{ev} missing from the Codex hooks")

    def test_both_hosts_run_the_same_scripts(self):
        def commands(event_map):
            return {h["command"] for group in event_map.values()
                    for entry in group for h in entry["hooks"]}
        codex = commands(self.codex_hooks()["hooks"])
        claude = commands(self.claude_hooks())
        # every Codex command is a Claude command -- no forked copies
        self.assertTrue(codex <= claude, f"Codex-only commands: {codex - claude}")
        for cmd in codex:
            rel = cmd.split("}\"/", 1)[1]
            self.assertTrue(os.access(os.path.join(PLUGIN, rel), os.X_OK),
                            f"{rel} is not executable")

    def test_plan_capture_is_the_only_hook_left_behind(self):
        """It matches the ExitPlanMode TOOL, which Codex does not have, so the
        matcher could never fire. Shipping it would be dead config that reads
        like coverage. If Codex ever grows the tool, this test fails and tells
        you to ship it."""
        missing = set(self.claude_hooks()) - set(self.codex_hooks()["hooks"])
        self.assertEqual(missing, {"PostToolUse"})
        matchers = [g.get("matcher") for g in self.claude_hooks()["PostToolUse"]]
        self.assertEqual(matchers, ["ExitPlanMode"])


class TestSkillFrontmatterLoads(unittest.TestCase):
    """From #329: a skill whose frontmatter fails to parse is not rejected --
    it loads with EMPTY metadata. `name` and `description` vanish, so the
    skill can never be matched, and nothing reports an error. Installed and
    invisible is the worst failure mode available, so it gets its own checks
    rather than riding on the version assertion.
    """

    def skills(self):
        return sorted(glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md")))

    def test_every_skill_declares_name_and_description(self):
        """The two fields a host reads to decide whether to invoke. These are
        exactly what an unparseable block silently drops."""
        for path in self.skills():
            keys = {l.split(":", 1)[0].strip()
                    for l in front_matter(path) if ":" in l}
            for field in ("name", "description"):
                self.assertIn(field, keys,
                              f"{os.path.relpath(path, ROOT)} has no {field}")

    def test_no_unquoted_frontmatter_value_contains_a_colon_space(self):
        """YAML forbids ': ' inside a plain scalar, and `classify` shipped one
        ("Propose-only: writes ...") that broke the parse even after the fence
        it was blamed on had been repaired. Quoting is the fix; this is the
        check that keeps the next one from shipping."""
        for path in self.skills():
            for line in front_matter(path):
                if line.startswith(" ") or ":" not in line:
                    continue          # nested value, handled by its parent
                value = line.split(":", 1)[1].strip()
                if value[:1] in ("'", '"') or not value:
                    continue          # quoted, or a block opener
                self.assertNotIn(
                    ": ", value,
                    f"{os.path.relpath(path, ROOT)}: {line[:40]}... contains "
                    f"': ' unquoted, so the whole block fails to parse and "
                    f"the skill loads with no name or description")


class TestVersionSync(unittest.TestCase):
    def test_cli_manifest_and_skills_agree(self):
        v = plugin_version()
        self.assertEqual(codex_plugin_version(), v)
        out = sh(ROOT, sys.executable, "bin/worklog", "--version").stdout
        self.assertEqual(out.strip(), f"worklog {v}")
        skills = sorted(glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md")))
        self.assertGreaterEqual(len(skills), 3)  # every skill dir must carry SKILL.md
        for path in skills:
            versions = [l.split(":", 1)[1].strip().strip('"\'')
                        for l in front_matter(path)
                        if l.strip().startswith("version:")]
            self.assertEqual(versions, [v], f"{path} version != plugin.json")

    def test_readme_version_marker_agrees(self):
        """#223: the README carries the shipped version too, and nothing
        checked it — so a release could bump the manifest, the CLI and every
        skill and still leave the front door advertising the old one."""
        v = plugin_version()
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            readme = fh.read()
        found = re.findall(r"\*\*v(\d+\.\d+\.\d+)\*\*", readme)
        self.assertTrue(found, "README.md has no **vX.Y.Z** version marker")
        self.assertEqual(set(found), {v},
                         f"README.md advertises {sorted(set(found))}, "
                         f"plugin.json says {v}")


class TestSuiteHygiene(unittest.TestCase):
    """No test file may define a class below its `if __name__` block.

    Running a file as a script executes that block, which calls
    `unittest.main()` and exits -- so every class defined below it is never
    registered and never runs. Nothing warns. pytest imports the module and
    sees all of them, so the two runners disagree in silence, and CI runs
    files as scripts.

    v0.22.0 found this in `test_dispatch.py` (20 of 27 running) and fixed
    that one file without sweeping the rest. Three more were still hiding 15
    tests, among them the whole conflict-marker guard suite -- a regression
    test for a guard the design docs cite as enforcement. Fixing the instance
    and not the class is what made a second discovery necessary, so this
    checks the class.
    """

    def test_no_test_class_is_defined_below_the_runner_block(self):
        root = os.path.join(ROOT, "tests")
        files = sorted(glob.glob(os.path.join(root, "test_*.py")))
        self.assertGreater(len(files), 10, "found suspiciously few test files")
        for path in files:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
            guard = next((i for i, l in enumerate(lines)
                          if l.startswith("if __name__")), None)
            if guard is None:
                continue
            orphans = [l.split("(")[0].removeprefix("class ")
                       for l in lines[guard:] if l.startswith("class ")]
            self.assertEqual(
                orphans, [],
                f"{os.path.relpath(path, ROOT)}: {orphans} defined below the "
                f"`if __name__` block at line {guard + 1}, so they never run "
                f"as a script -- move that block to the end of the file")


class TestPackaging(unittest.TestCase):
    def test_no_repo_docs_inside_plugin(self):
        # match whole path segments: skills/design-docs/ is fine, docs/ is not
        banned_dirs = {"user_guide", "docs"}
        for base, _dirs, files in os.walk(PLUGIN):
            for name in files:
                rel = os.path.relpath(os.path.join(base, name), PLUGIN)
                segs = rel.split(os.sep)
                self.assertFalse(
                    banned_dirs & set(segs[:-1]),
                    f"{rel}: repo docs must not ship inside the plugin")
                self.assertNotIn("worklog-spec", segs[-1],
                                 f"{rel}: spec must not ship inside the plugin")


class TestInit(unittest.TestCase):
    def test_scaffolds_a_usable_repo(self):
        d = init_repo(self)
        iid = worklog(d, "add", "First item", "--priority", "P1").stdout.strip()
        worklog(d, "roadmap-render")
        sh(d, "git", "checkout", "-q", "-b", "work")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", f"scaffold: {iid}")  # through the hooks

        ga = read(d, ".gitattributes")
        self.assertIn(".work/todo.jsonl merge=union", ga)
        self.assertIn(".work/done.jsonl merge=union", ga)
        self.assertIn(f"installed: {plugin_version()}", read(d, ".work/config.yml"))
        hookspath = sh(d, "git", "config", "core.hooksPath").stdout.strip()
        self.assertEqual(hookspath, "hooks")
        agents = os.path.join(d, "AGENTS.md")
        self.assertTrue(os.path.exists(agents))
        self.assertTrue(os.path.islink(agents))
        self.assertEqual(os.readlink(agents), "CLAUDE.md")

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
        agents = os.path.join(d, "AGENTS.md")
        self.assertTrue(os.path.islink(agents))  # still the one symlink
        self.assertEqual(os.readlink(agents), "CLAUDE.md")


class TestDoctor(unittest.TestCase):
    def test_healthy_then_skew(self):
        d = init_repo(self)
        iid = worklog(d, "add", "Item", "--priority", "P2").stdout.strip()
        worklog(d, "roadmap-render")
        sh(d, "git", "checkout", "-q", "-b", "work")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", f"base: {iid}")
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
        iid = worklog(d, "add", "Keep me", "--priority", "P1").stdout.strip()
        worklog(d, "roadmap-render")
        sh(d, "git", "checkout", "-q", "-b", "work")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", f"tracked: {iid}")

        sh(d, "bash", os.path.join(PLUGIN, "scripts", "uninstall.sh"))
        for rel in CANON:
            self.assertFalse(os.path.exists(os.path.join(d, rel)), rel)
        p = sh(d, "git", "config", "core.hooksPath", check=False)
        self.assertNotEqual(p.returncode, 0, "core.hooksPath still set")
        self.assertFalse(
            os.path.exists(os.path.join(d, ".github/workflows/worklog.yml")))
        self.assertFalse(
            os.path.lexists(os.path.join(d, "AGENTS.md")),
            "uninstall must remove the AGENTS.md -> CLAUDE.md symlink")

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
