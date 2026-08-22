"""Claude hooks imply Codex + Cursor-native hooks."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"


def test_three_host_hooks_coexist():
    claude = HOOKS / "hooks.json"
    if not claude.is_file():
        return
    assert (HOOKS / "codex-hooks.json").is_file(), "Codex hooks required when Claude hooks exist"
    assert (HOOKS / "cursor-hooks.json").is_file(), "Cursor-native hooks required when Claude hooks exist"
    for name in ("codex-hooks.json", "cursor-hooks.json"):
        data = json.loads((HOOKS / name).read_text())
        assert "hooks" in data and isinstance(data["hooks"], dict)
        for entries in data["hooks"].values():
            for item in entries if isinstance(entries, list) else []:
                cmd = item.get("command") or ""
                nested = item.get("hooks") or []
                if nested:
                    cmd = nested[0].get("command", cmd)
                assert isinstance(cmd, str) and cmd.strip()
