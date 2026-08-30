#!/usr/bin/env python3
"""
triggers.py -- per-event artifact routing from .work/config.yml.

The when of generation used to live in four skills' prose. Exactly one
binding was config (`release.sync_docs`). This module is the dispatcher:
skills and CI ask `worklog triggers <event>` and run what comes back.

No yaml library (same constraint as item_fields / wiki_flavor). The
`triggers:` block is a flat event → list-of-actions map.

Events: plan-capture, pr-open, pr-merge, release, status-report.

An event key that is present (even as `[]`) is the authority. A missing
key falls back to DEFAULTS, then to the legacy knobs:

- sync.push_on_capture (default true) → ticket-sync on plan-capture
- status.publish (default true) → wiki-publish:status on status-report
- release.sync_docs → the doc subset of the release row
"""
from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Optional, Tuple

CONFIG = ".work/config.yml"

EVENTS = (
    "plan-capture",
    "pr-open",
    "pr-merge",
    "release",
    "status-report",
)

DEFAULTS: Dict[str, Tuple[str, ...]] = {
    "plan-capture": ("ticket-sync", "wiki-publish:plans"),
    "pr-open": ("pr-description",),
    "pr-merge": ("roadmap-render", "ticket-sync:close"),
    "release": (
        "design-doc", "code-walkthrough", "user-guide", "readme",
        "wiki-publish", "ticket-sync",
    ),
    "status-report": ("wiki-publish:status",),
}

RELEASE_DOCS = ("design-doc", "code-walkthrough", "user-guide", "readme")

TRUE = ("true", "yes", "on", "1")
FALSE = ("false", "no", "off", "0")


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _strip(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def _parse_inline_list(rest: str) -> Optional[List[str]]:
    rest = rest.strip()
    if not rest:
        return None
    if rest[0] != "[" or not rest.endswith("]"):
        return None
    inner = rest[1:-1].strip()
    if not inner:
        return []
    return [p.strip().strip("\"'") for p in inner.split(",") if p.strip()]


def parse_triggers(text: str) -> Dict[str, List[str]]:
    """Event → actions for keys that appear under `triggers:`."""
    out: Dict[str, List[str]] = {}
    inside = False
    current: Optional[str] = None
    for raw in text.splitlines():
        line = _strip(raw)
        if not line.strip():
            continue
        if not line[0].isspace():
            if inside and current is not None and current not in out:
                out[current] = []
            inside = line.strip() == "triggers:" or line.strip().startswith("triggers:")
            current = None
            # `triggers: []` / `triggers:` on one line with no mapping
            if inside:
                inline = _parse_inline_list(line.split(":", 1)[1])
                if inline is not None:
                    # `triggers: []` means no overrides, not "disable every event".
                    return out
            continue
        if not inside:
            continue
        # event header at indent 2
        m = re.match(r"^  ([A-Za-z][\w-]*)\s*:\s*(.*)$", line)
        if m:
            if current is not None and current not in out:
                out[current] = []
            current = m.group(1)
            inline = _parse_inline_list(m.group(2))
            if inline is not None:
                out[current] = inline
                current = None
            continue
        # list item at indent 4
        item = re.match(r"^    -\s+(\S.*)$", line)
        if item and current is not None:
            out.setdefault(current, []).append(item.group(1).strip().strip("\"'"))
    if current is not None and current not in out:
        out[current] = []
    return out


def parse_list_under(text: str, block: str, key: str) -> Optional[List[str]]:
    """Parse `block.key` as a YAML list. None if the key is absent."""
    inside_block = False
    inside_key = False
    found = False
    items: List[str] = []
    for raw in text.splitlines():
        line = _strip(raw)
        if not line.strip():
            continue
        if not line[0].isspace():
            if inside_key:
                return items
            inside_block = line.strip().startswith(block + ":")
            inside_key = False
            continue
        if not inside_block:
            continue
        header = re.match(r"^  " + re.escape(key) + r"\s*:\s*(.*)$", line)
        if header:
            found = True
            inline = _parse_inline_list(header.group(1))
            if inline is not None:
                return inline
            inside_key = True
            continue
        if inside_key:
            if re.match(r"^  [A-Za-z]", line):
                return items
            item = re.match(r"^    -\s+(\S.*)$", line)
            if item:
                items.append(item.group(1).strip().strip("\"'"))
    if found:
        return items
    return None


def nested_scalar(text: str, block: str, key: str) -> Optional[str]:
    inside = False
    for raw in text.splitlines():
        line = _strip(raw)
        if not line.strip():
            continue
        if not line[0].isspace():
            inside = line.strip().startswith(block + ":")
            continue
        if inside:
            m = re.match(r"^\s+" + re.escape(key) + r"\s*:\s*(\S+)", line)
            if m:
                return m.group(1).strip("\"'").lower()
    return None


def _flag(text: str, block: str, key: str, default: bool) -> bool:
    raw = nested_scalar(text, block, key)
    if raw is None:
        return default
    if raw in FALSE:
        return False
    if raw in TRUE:
        return True
    return default


def resolve(event: str, path: str = CONFIG) -> List[str]:
    """Actions for one event. Unknown event names are still resolved if
    listed in the file; otherwise KeyError."""
    if event not in EVENTS:
        raise KeyError(event)
    text = _read(path)
    configured = parse_triggers(text)
    if event in configured:
        return list(configured[event])
    if event == "release":
        docs = parse_list_under(text, "release", "sync_docs")
        if docs is not None:
            extra = [a for a in DEFAULTS["release"] if a not in RELEASE_DOCS]
            return list(docs) + extra
    if event == "plan-capture":
        actions = list(DEFAULTS[event])
        if not _flag(text, "sync", "push_on_capture", True):
            actions = [a for a in actions if a != "ticket-sync"]
        return actions
    if event == "status-report":
        actions = list(DEFAULTS[event])
        if not _flag(text, "status", "publish", True):
            actions = [a for a in actions if not a.startswith("wiki-publish")]
        return actions
    return list(DEFAULTS[event])


def resolve_all(path: str = CONFIG) -> Dict[str, List[str]]:
    return {e: resolve(e, path) for e in EVENTS}


def has(event: str, action: str, path: str = CONFIG) -> bool:
    """True if `action` or `action:filter` is listed for the event."""
    for a in resolve(event, path):
        if a == action or a.startswith(action + ":"):
            return True
    return False


def main(argv: Optional[List[str]] = None) -> int:
    """stdlib entry so `python3 bin/triggers.py plan-capture` works in tests."""
    args = list(sys.argv[1:] if argv is None else argv)
    path = CONFIG
    if "--config" in args:
        i = args.index("--config")
        path = args[i + 1]
        del args[i:i + 2]
    import json
    if not args:
        json.dump(resolve_all(path), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    event = args[0]
    if event not in EVENTS:
        sys.stderr.write(
            "worklog: unknown trigger event %r (want %s)\n"
            % (event, ", ".join(EVENTS)))
        return 2
    json.dump(
        {"event": event, "actions": resolve(event, path)},
        sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
