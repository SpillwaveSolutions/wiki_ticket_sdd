#!/usr/bin/env python3
"""Tests for plugin/scripts/merge-when-green.sh.

A fake `gh` on PATH scripts the check states per invocation; the real script
must merge only on green, refuse on red, and never bypass. Interval 0 keeps
the polls instant.
"""
import os
import stat
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugin", "scripts", "merge-when-green.sh")

FAKE_GH = """#!/usr/bin/env bash
# scripted fake: state file holds one line per `checks` call; merge is recorded
D="$FAKE_DIR"
case "$1" in
  pr)
    case "$2" in
      view)  echo '{"state": "'"$(cat "$D/prstate")"'"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['state'])" ;;
      checks)
        n=$(cat "$D/call" 2>/dev/null || echo 0); echo $((n+1)) > "$D/call"
        sed -n "$((n+1))p" "$D/buckets" | tr -d '\\n'
        ;;
      merge)
        for a in "$@"; do
          if [ "$a" = "--auto" ]; then
            echo "$@" >> "$D/armed"
            exit 0
          fi
        done
        echo "$@" >> "$D/merged"
        exit 0
        ;;
    esac ;;
esac
"""


class Sandbox:
    def __init__(self, tc, buckets, prstate="OPEN", config=None):
        self.dir = tempfile.mkdtemp(prefix="mwg-")
        tc.addCleanup(lambda: subprocess.run(["rm", "-rf", self.dir]))
        gh = os.path.join(self.dir, "gh")
        with open(gh, "w") as fh:
            fh.write(FAKE_GH)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IEXEC)
        with open(os.path.join(self.dir, "buckets"), "w") as fh:
            fh.write("\n".join(buckets) + "\n")
        with open(os.path.join(self.dir, "prstate"), "w") as fh:
            fh.write(prstate)
        if config is not None:
            os.makedirs(os.path.join(self.dir, ".work"))
            with open(os.path.join(self.dir, ".work", "config.yml"), "w") as fh:
                fh.write(config)

    def run(self, max_attempts=5, args=(), env_extra=None):
        env = dict(os.environ, PATH=f"{self.dir}:{os.environ['PATH']}",
                   FAKE_DIR=self.dir)
        if env_extra:
            env.update(env_extra)
        # cwd=self.dir: the script reads ./.work/config.yml relative to cwd
        return subprocess.run(
            ["bash", SCRIPT, *args, "7", "0", str(max_attempts)],
            capture_output=True, text=True, env=env, cwd=self.dir)

    def merged(self):
        return os.path.exists(os.path.join(self.dir, "merged"))

    def armed(self):
        return os.path.exists(os.path.join(self.dir, "armed"))


class TestMergeWhenGreen(unittest.TestCase):
    def test_pending_then_green_merges(self):
        sb = Sandbox(self, ["pending,pass", "pending,pass", "pass,pass"])
        r = sb.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(sb.merged())
        self.assertIn("all checks green", r.stdout)

    def test_failing_check_refuses(self):
        sb = Sandbox(self, ["pass,fail"])
        r = sb.run()
        self.assertEqual(r.returncode, 1)
        self.assertFalse(sb.merged())
        self.assertIn("NOT merging", r.stderr)

    def test_cancelled_counts_as_red(self):
        sb = Sandbox(self, ["cancel,pass"])
        r = sb.run()
        self.assertEqual(r.returncode, 1)
        self.assertFalse(sb.merged())

    def test_already_merged_pr_is_success(self):
        sb = Sandbox(self, ["pass"], prstate="MERGED")
        r = sb.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(sb.merged())
        self.assertIn("already MERGED", r.stderr)

    def test_closed_pr_is_not_merged(self):
        sb = Sandbox(self, ["pass"], prstate="CLOSED")
        r = sb.run()
        self.assertEqual(r.returncode, 3)
        self.assertFalse(sb.merged())

    def test_never_green_times_out(self):
        sb = Sandbox(self, ["pending"] * 10)
        r = sb.run(max_attempts=3)
        self.assertEqual(r.returncode, 4)
        self.assertFalse(sb.merged())
        self.assertIn("timed out", r.stderr)

    def test_advisory_config_green_reports_but_does_not_merge(self):
        sb = Sandbox(self, ["pass,pass"],
                     config="features:\n  auto_merge_on_green: false\n")
        r = sb.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(sb.merged())
        self.assertIn("advisory mode", r.stdout)

    def test_auto_flag_overrides_advisory_config(self):
        sb = Sandbox(self, ["pass"],
                     config="features:\n  auto_merge_on_green: false\n")
        r = sb.run(args=["--auto"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(sb.merged())

    def test_env_override_forces_advisory(self):
        sb = Sandbox(self, ["pass"])   # no config -> default true; env wins
        r = sb.run(env_extra={"WORKLOG_AUTO_MERGE": "0"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(sb.merged())
        self.assertIn("advisory mode", r.stdout)

    def test_no_checks_reported_waits_not_merges(self):
        sb = Sandbox(self, ["", "", ""])
        r = sb.run(max_attempts=2)
        self.assertEqual(r.returncode, 4)   # no gates reporting != gates passing
        self.assertFalse(sb.merged())

    def test_auto_merge_is_armed_before_checks_complete(self):
        sb = Sandbox(self, ["pending,pass", "pass,pass"])
        r = sb.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(sb.armed(), r.stderr)
        self.assertTrue(sb.merged())
        with open(os.path.join(sb.dir, "armed")) as fh:
            armed = fh.read()
        self.assertIn("--auto", armed)
        self.assertIn("--merge", armed)

    def test_advisory_does_not_arm_auto_merge(self):
        sb = Sandbox(self, ["pass,pass"],
                     config="features:\n  auto_merge_on_green: false\n")
        r = sb.run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(sb.armed())
        self.assertFalse(sb.merged())


class TestPostMergeWorkflow(unittest.TestCase):
    """ADR-0010: invariants must listen on the post-merge job name."""

    def test_invariants_listens_on_post_merge_and_compact(self):
        with open(os.path.join(ROOT, ".github", "workflows", "worklog.yml"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('workflows: ["worklog-compact", "worklog-post-merge"]', text)

    def test_post_merge_workflow_contract(self):
        with open(os.path.join(ROOT, ".github", "workflows", "post-merge.yml"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("name: worklog-post-merge", text)
        self.assertIn("types: [closed]", text)
        self.assertIn("triggers pr-merge", text)
        self.assertIn("bin/worklog roadmap-render", text)
        self.assertIn("bin/worklog ia-inventory", text)
        self.assertIn("bin/worklog ia-manifest", text)
        self.assertIn("bin/worklog sync --report", text)
        self.assertIn("--body-file", text)
        self.assertIn("concurrency:", text)
        self.assertIn("--merge-check", text)
        self.assertIn("gh pr merge --auto --merge", text)
        self.assertIn("gh workflow run worklog-invariants", text)
        self.assertIn("actions: write", text)
        self.assertNotIn("--squash", text)
        self.assertNotIn("\\\\n", text)
        # GITHUB_TOKEN cannot push main (GH013 on compact run 33299168867).
        self.assertNotRegex(text, r"(?m)^\s+git push\s*$",
                            "bare git push would target main")

    def test_workflow_run_blocks_do_not_dedent(self):
        """GitHub Actions rejects a run: | body that returns to column 0.
        post-merge.yml L57 on 0295c50 (python heredoc) made the workflow
        invalid, so the PR-closed job never fired."""
        for rel in (".github/workflows/post-merge.yml",
                    ".github/workflows/compact.yml"):
            path = os.path.join(ROOT, rel)
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            in_block = False
            block_indent = 0
            for i, line in enumerate(lines, 1):
                stripped = line.rstrip()
                if stripped.endswith("run: |") or stripped.endswith("run: |-"):
                    in_block = True
                    block_indent = len(line) - len(line.lstrip())
                    continue
                if not in_block or not line.strip():
                    continue
                indent = len(line) - len(line.lstrip())
                if indent > block_indent:
                    continue
                in_block = False
                if indent == 0:
                    self.fail(f"{rel}:{i} dedents to column 0 inside run: |: {line!r}")

    def test_compact_workflow_lands_via_pr(self):
        with open(os.path.join(ROOT, ".github", "workflows", "compact.yml"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("name: worklog-compact", text)
        self.assertIn("gh pr create", text)
        self.assertIn("gh pr merge --auto --merge", text)
        self.assertIn("gh workflow run worklog-invariants", text)
        self.assertIn("actions: write", text)
        self.assertIn("pull-requests: write", text)
        self.assertNotIn("--squash", text)
        self.assertNotRegex(text, r"(?m)^\s+git push\s*$",
                            "bare git push would target main")

    def test_ruleset_is_merge_commit_only(self):
        import json
        path = os.path.join(ROOT, ".github", "merge-when-green-ruleset.json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["name"], "merge-when-green")
        self.assertEqual(data["enforcement"], "active")
        methods = None
        contexts = []
        for rule in data["rules"]:
            if rule["type"] == "pull_request":
                methods = rule["parameters"]["allowed_merge_methods"]
            if rule["type"] == "required_status_checks":
                contexts = [c["context"] for c in rule["parameters"]["required_status_checks"]]
                self.assertTrue(rule["parameters"]["strict_required_status_checks_policy"])
        self.assertEqual(methods, ["merge"])
        self.assertEqual(sorted(contexts), ["coverage", "invariants"])
        actors = {(a["actor_id"], a["actor_type"]) for a in data["bypass_actors"]}
        self.assertIn((41898282, "User"), actors)


if __name__ == "__main__":
    unittest.main()
