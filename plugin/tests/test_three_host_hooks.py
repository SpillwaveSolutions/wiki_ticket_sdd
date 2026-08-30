#!/usr/bin/env python3
"""Claude hooks imply Codex + Cursor-native hooks.

Cursor command paths must resolve against the plugin root (marketplace
source is `./plugin`), not `./plugin/hooks/...` which cannot resolve when
the pack is installed from that source.
"""
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"


class TestThreeHostHooks(unittest.TestCase):
    def test_three_host_hooks_coexist(self):
        claude = HOOKS / "hooks.json"
        if not claude.is_file():
            self.skipTest("no Claude hooks")
        self.assertTrue((HOOKS / "codex-hooks.json").is_file(),
                        "Codex hooks required when Claude hooks exist")
        self.assertTrue((HOOKS / "cursor-hooks.json").is_file(),
                        "Cursor-native hooks required when Claude hooks exist")
        for name in ("codex-hooks.json", "cursor-hooks.json"):
            data = json.loads((HOOKS / name).read_text())
            self.assertIn("hooks", data)
            self.assertIsInstance(data["hooks"], dict)
            for entries in data["hooks"].values():
                for item in entries if isinstance(entries, list) else []:
                    cmd = item.get("command") or ""
                    nested = item.get("hooks") or []
                    if nested:
                        cmd = nested[0].get("command", cmd)
                    self.assertIsInstance(cmd, str)
                    self.assertTrue(cmd.strip())

    def test_cursor_hook_paths_resolve_from_plugin_root(self):
        data = json.loads((HOOKS / "cursor-hooks.json").read_text())
        for ev, entries in data["hooks"].items():
            for item in entries:
                cmd = item.get("command") or ""
                self.assertFalse(
                    cmd.startswith("./plugin/"),
                    "%s: %s cannot resolve when marketplace source is ./plugin"
                    % (ev, cmd))
                rel = cmd[2:] if cmd.startswith("./") else cmd
                path = ROOT / rel
                self.assertTrue(path.is_file(), "%s -> %s" % (cmd, path))
                self.assertTrue(os.access(path, os.X_OK), cmd)


if __name__ == "__main__":
    unittest.main(verbosity=2)
