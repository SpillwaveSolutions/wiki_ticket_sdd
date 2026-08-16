#!/usr/bin/env python3
"""Wave C: knowledge-tree writes fail-closed without identity.

Worklog --actor still defaults to $USER for local use. Public tests use
only fictional project names.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OKF_WRITE = ROOT / "bin" / "okf_write.py"
WORKLOG = ROOT / "bin" / "worklog"


def run(cmd, *, env=None, cwd=None):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, capture_output=True, text=True, env=merged, cwd=cwd
    )


class TestRequiredIdentity(unittest.TestCase):
    def test_resolve_author_fail_closed(self):
        sys.path.insert(0, str(ROOT / "bin"))
        import okf_write

        prev = os.environ.pop("SECOND_BRAIN_IDENTITY", None)
        try:
            with self.assertRaises(SystemExit):
                okf_write.resolve_author(None)
            self.assertEqual(
                okf_write.resolve_author("grok-bot/northstar-console"),
                "grok-bot/northstar-console",
            )
        finally:
            if prev is not None:
                os.environ["SECOND_BRAIN_IDENTITY"] = prev

    def test_write_without_identity_fails(self):
        env = os.environ.copy()
        env.pop("SECOND_BRAIN_IDENTITY", None)
        with tempfile.TemporaryDirectory(prefix="wiki-noid-") as temp:
            proc = run(
                [
                    sys.executable,
                    str(OKF_WRITE),
                    "write",
                    "--type",
                    "TicketLink",
                    "--title",
                    "Lumenfield scan",
                    "--bundle",
                    temp,
                ],
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("identity", (proc.stdout + proc.stderr).lower())

    def test_write_stamps_author_and_write_event(self):
        env = os.environ.copy()
        env.pop("SECOND_BRAIN_IDENTITY", None)
        with tempfile.TemporaryDirectory(prefix="wiki-id-") as temp:
            proc = run(
                [
                    sys.executable,
                    str(OKF_WRITE),
                    "write",
                    "--type",
                    "TicketLink",
                    "--title",
                    "Lumenfield scan",
                    "--bundle",
                    temp,
                    "--author",
                    "claude-code/lumenfield-detector",
                    "--slug",
                    "lumenfield-scan",
                ],
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            data = json.loads(proc.stdout)
            self.assertEqual(data["author"], "claude-code/lumenfield-detector")
            node = Path(data["path"])
            self.assertTrue(node.is_file())
            text = node.read_text(encoding="utf-8")
            self.assertIn('author: "claude-code/lumenfield-detector"', text)
            self.assertIn("type: TicketLink", text)
            events = list(Path(temp).joinpath("write-events").glob("*.md"))
            self.assertEqual(len(events), 1)
            ev = events[0].read_text(encoding="utf-8")
            self.assertIn("type: WriteEvent", ev)
            self.assertIn('author: "claude-code/lumenfield-detector"', ev)
            self.assertIn("/tickets/lumenfield-scan.md", ev)

    def test_flag_beats_env(self):
        sys.path.insert(0, str(ROOT / "bin"))
        import okf_write

        prev = os.environ.get("SECOND_BRAIN_IDENTITY")
        os.environ["SECOND_BRAIN_IDENTITY"] = "grok-bot/northstar-console"
        try:
            self.assertEqual(
                okf_write.resolve_author(None), "grok-bot/northstar-console"
            )
            self.assertEqual(
                okf_write.resolve_author("claude-code/lumenfield-detector"),
                "claude-code/lumenfield-detector",
            )
        finally:
            if prev is None:
                os.environ.pop("SECOND_BRAIN_IDENTITY", None)
            else:
                os.environ["SECOND_BRAIN_IDENTITY"] = prev

    def test_worklog_actor_reads_second_brain_identity(self):
        with tempfile.TemporaryDirectory(prefix="wiki-actor-") as temp:
            (Path(temp) / ".work").mkdir()
            env = os.environ.copy()
            env["SECOND_BRAIN_IDENTITY"] = "grok-bot/northstar-console"
            proc = run(
                [sys.executable, str(WORKLOG), "add", "Northstar layout", "--body", "demo"],
                env=env,
                cwd=temp,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            lines = (Path(temp) / ".work" / "todo.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            ev = json.loads(lines[0])
            self.assertEqual(ev["actor"], "grok-bot/northstar-console")

    def test_docs_require_author_on_knowledge_writes(self):
        grok = (ROOT / "docs" / "GROK_BOT.md").read_text(encoding="utf-8")
        iso = (ROOT / "docs" / "ISOLATION.md").read_text(encoding="utf-8")
        self.assertIn("okf_write", grok)
        self.assertIn("--author", grok)
        self.assertIn("okf_write", iso)
        self.assertIn("lumenfield-detector", iso)
        self.assertIn("northstar-console", iso)
        self.assertNotIn("ThreatIQ", grok + iso)


if __name__ == "__main__":
    unittest.main()
