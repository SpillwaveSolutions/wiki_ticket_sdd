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
      merge) echo "$@" >> "$D/merged"; exit 0 ;;
    esac ;;
esac
"""


class Sandbox:
    def __init__(self, tc, buckets, prstate="OPEN"):
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

    def run(self, max_attempts=5):
        env = dict(os.environ, PATH=f"{self.dir}:{os.environ['PATH']}",
                   FAKE_DIR=self.dir)
        return subprocess.run(["bash", SCRIPT, "7", "0", str(max_attempts)],
                              capture_output=True, text=True, env=env)

    def merged(self):
        return os.path.exists(os.path.join(self.dir, "merged"))


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

    def test_closed_pr_is_not_merged(self):
        sb = Sandbox(self, ["pass"], prstate="MERGED")
        r = sb.run()
        self.assertEqual(r.returncode, 3)
        self.assertFalse(sb.merged())

    def test_never_green_times_out(self):
        sb = Sandbox(self, ["pending"] * 10)
        r = sb.run(max_attempts=3)
        self.assertEqual(r.returncode, 4)
        self.assertFalse(sb.merged())
        self.assertIn("timed out", r.stderr)

    def test_no_checks_reported_waits_not_merges(self):
        sb = Sandbox(self, ["", "", ""])
        r = sb.run(max_attempts=2)
        self.assertEqual(r.returncode, 4)   # no gates reporting != gates passing
        self.assertFalse(sb.merged())


if __name__ == "__main__":
    unittest.main()
