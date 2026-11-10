#!/usr/bin/env python3
"""
published.py -- append-only wiki ledger, folded like the work log.

.work/published.json was a 308KB JSON dict with no merge strategy. Two
branches that each published produced a classic 3-way conflict in a file
policy said must never be hand-edited. The ledger is now `.work/published.jsonl`:
append-only events, last-write-wins per logical key, `merge=union`.

The fold is the only reader. `append()` is the only writer. Same envelope
as the work log (PIPE_BUF, flock, trailing newline). Nothing else in the
repo may write this file (invariant 15.4).

Event shape (spec §9.3):

    {"ev": ULID, "ts": RFC3339, "actor": str,
     "op": "register"|"publish"|"unpublish",
     "key": "<logical-key>",
     "set": {source, title, url, rev, source_hash, render_hash, ...}}

`register` is wiki-add (source + title; publish fields stay).
`publish` is wiki-record after a successful page push.
`unpublish` drops the key.

A leftover `.work/published.json` is migrated on first write with
deterministic ULIDs (same dict -> same events, so a retried migrate
dedupes). After this repo's one-shot conversion the JSON file is gone.
"""
from __future__ import annotations

import fcntl
import json
import os
import sys
import time
from typing import Any, Dict, Iterable, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulid  # noqa: E402

JSONL = ".work/published.jsonl"
JSON = ".work/published.json"
LOCK = ".work/.lock"
MAX_LINE = 4096  # POSIX PIPE_BUF; same envelope as the work log.
OPS = ("register", "publish", "unpublish")

# First wiki-publish in this repo (docs/plans/2026-07-18-docs-wiki-dogfood.md).
# Migration events sort before any live write.
# 1784419200000 = 2026-07-19T00:00:00Z. This repo's already-migrated events
# were minted with 1752883200000 (2025-07-19); those ULIDs stay. Migrate
# is one-shot and .work/published.json is gone.
MIGRATE_TS = "2026-07-19T00:00:00Z"
MIGRATE_MS = 1784419200000


class FoldResult:
    def __init__(self) -> None:
        self.pages: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        self.skipped: int = 0
        self.deduped: int = 0


def _canon(entry: Dict[str, Any]) -> str:
    return json.dumps(entry, separators=(",", ":"), sort_keys=True)


def read_lines(paths: Iterable[str], result: FoldResult) -> List[Dict[str, Any]]:
    """Parse. A bad line is reported and skipped -- never fatal."""
    events: List[Dict[str, Any]] = []
    for path in paths:
        try:
            fh = open(path, "r", encoding="utf-8")
        except FileNotFoundError:
            continue
        with fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError as e:
                    result.errors.append(f"{path}:{lineno}: unparseable: {e}")
                    result.skipped += 1
                    continue
                if not isinstance(ev, dict) or "ev" not in ev or "op" not in ev:
                    result.errors.append(f"{path}:{lineno}: missing ev/op")
                    result.skipped += 1
                    continue
                if ev["op"] != "unpublish" and "key" not in ev:
                    result.errors.append(f"{path}:{lineno}: missing key")
                    result.skipped += 1
                    continue
                events.append(ev)
    return events


def dedupe_and_sort(events: List[Dict[str, Any]], result: FoldResult) -> List[Dict[str, Any]]:
    """Dedupe by `ev` (first wins), then sort by `ev`. Union merge depends on both."""
    seen = {}
    ordered: List[Dict[str, Any]] = []
    for ev in events:
        eid = ev["ev"]
        if eid in seen:
            result.deduped += 1
            continue
        seen[eid] = True
        ordered.append(ev)
    ordered.sort(key=lambda e: (e["ev"], e.get("actor", ""), _canon(e)))
    return ordered


def fold(paths: Iterable[str] = (JSONL,)) -> FoldResult:
    """Last-write-wins per key. `set` merges into the existing page dict."""
    result = FoldResult()
    for ev in dedupe_and_sort(read_lines(paths, result), result):
        op = ev.get("op")
        key = ev.get("key")
        if op == "unpublish":
            if key:
                result.pages.pop(key, None)
            continue
        if op not in OPS or not key:
            result.errors.append(f"skip op={op!r} key={key!r}")
            result.skipped += 1
            continue
        page = result.pages.setdefault(key, {})
        for field, value in (ev.get("set") or {}).items():
            page[field] = value
        page.setdefault("wiki_key", key)
    return result


def load() -> Dict[str, Dict[str, Any]]:
    """Folded ledger. jsonl wins; leftover JSON is a read-only fallback."""
    if os.path.exists(JSONL):
        return fold().pages
    if os.path.exists(JSON):
        try:
            with open(JSON, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def migrate_json(json_path: str = JSON, jsonl_path: str = JSONL) -> int:
    """One-shot: leftover dict -> jsonl with deterministic ULIDs.

    Idempotent: if jsonl already exists, do nothing. Same dict produces the
    same events, so a retried migrate that somehow races still dedupes.
    Does not delete the JSON file -- callers that own the conversion do.
    """
    if os.path.exists(jsonl_path) or not os.path.exists(json_path):
        return 0
    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return 0
    lines = []
    for key, entry in sorted(data.items()):
        if not isinstance(entry, dict):
            entry = {"value": entry}
        ev = {
            "actor": "migrator",
            "ev": ulid.deterministic("published-json", key, _canon(entry), MIGRATE_MS),
            "key": key,
            "op": "publish",
            "set": entry,
            "ts": MIGRATE_TS,
        }
        lines.append(json.dumps(ev, separators=(",", ":"), sort_keys=True) + "\n")
    os.makedirs(os.path.dirname(jsonl_path) or ".", exist_ok=True)
    raw = "".join(lines).encode("utf-8")
    tmp = jsonl_path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        n = os.write(fd, raw)
        if n != len(raw):
            os.close(fd)
            os.unlink(tmp)
            sys.exit("worklog: short write migrating published.json")
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, jsonl_path)
    return len(lines)


def append(event: Dict[str, Any], path: str = JSONL) -> None:
    """The only writer. Single O_APPEND write, always newline-terminated.

    Migrates a leftover published.json on first write so a register against
    an old clone does not drop existing url/rev/hash. Holds `.work/.lock`
    so compact cannot os.replace an inode a sibling write is targeting.
    """
    migrate_json()
    if event.get("op") not in OPS:
        sys.exit(f"worklog: unknown published op {event.get('op')!r}")
    if not event.get("key"):
        sys.exit("worklog: published event needs a key")
    line = json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n"
    raw = line.encode("utf-8")
    if len(raw) > MAX_LINE:
        sys.exit(f"worklog: published event exceeds {MAX_LINE}B atomicity envelope "
                 "(PIPE_BUF); shorten title or drop unused ledger fields")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    lock_fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            if os.fstat(fd).st_size:
                rfd = os.open(path, os.O_RDONLY)
                try:
                    os.lseek(rfd, -1, os.SEEK_END)
                    if os.read(rfd, 1) != b"\n":
                        raw = b"\n" + raw
                finally:
                    os.close(rfd)
            n = os.write(fd, raw)
            if n != len(raw):
                sys.exit("worklog: short write; published event not recorded")
        finally:
            os.close(fd)
    finally:
        os.close(lock_fd)


def event(key: str, op: str, actor: str, fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ev = {
        "ev": ulid.new(),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actor": actor,
        "op": op,
        "key": key,
    }
    sha = ulid.git_commit()
    if sha:
        ev["git"] = sha
    if fields:
        ev["set"] = fields
    return ev


def register(key: str, source: str, title: str, actor: str) -> Dict[str, Any]:
    """wiki-add. Merges source/title; does not wipe url/rev/hashes."""
    fields = {"source": source, "title": title}
    current = load().get(key) or {}
    # Preserve publish identity on re-register (spec 9.2 / 9.3). New keys
    # get explicit nulls so wiki-get has a stable shape.
    for k in ("url", "rev", "source_hash"):
        fields[k] = current[k] if k in current else None
    for k in ("render_hash", "page_id"):
        if k in current:
            fields[k] = current[k]
    ev = event(key, "register", actor, fields)
    append(ev)
    return load()[key]


def record(key: str, fields: Dict[str, Any], actor: str, op: str = "publish") -> Dict[str, Any]:
    """wiki-record. After a successful page push, or ia-normalize self-desc."""
    ev = event(key, op, actor, fields)
    append(ev)
    return load()[key]


MANIFEST = "docs/.index/publish-manifest.json"


def plan(manifest: Dict[str, Any], ledger: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Frozen-guard + render-hash skip. The wiki-publish dispatcher.

    Skip uses render_hash (a frozen page's banner can move while the source
    does not). The frozen guard uses source_hash (body hash from the
    manifest): if a frozen page's prose changed since last publish, that is
    a frozen-doc edit — stop, do not publish.
    """
    ledger = ledger if ledger is not None else load()
    publish: List[Dict[str, Any]] = []
    skip: List[Dict[str, Any]] = []
    violations: List[Dict[str, Any]] = []

    pages = list(manifest.get("pages") or [])
    sidebar = manifest.get("sidebar")
    if isinstance(sidebar, dict) and sidebar.get("source"):
        pages.append({
            "wiki_key": sidebar.get("wiki_key") or "sidebar",
            "source": sidebar["source"],
            "page_name": sidebar.get("page_name") or "_Sidebar",
            "title": sidebar.get("title") or "Sidebar",
            "render": sidebar.get("render") or "as-is",
            "frozen": False,
            "render_hash": sidebar.get("render_hash"),
        })

    for page in pages:
        if not isinstance(page, dict):
            continue
        key = page.get("wiki_key")
        if not key:
            continue
        entry = ledger.get(key) or {}
        src_hash = page.get("source_hash")
        led_hash = entry.get("source_hash")
        if page.get("frozen") and src_hash and led_hash and src_hash != led_hash:
            violations.append({
                "wiki_key": key,
                "source": page.get("source"),
                "manifest_source_hash": src_hash,
                "ledger_source_hash": led_hash,
            })
            continue
        rh = page.get("render_hash")
        if rh and entry.get("render_hash") == rh:
            skip.append({"wiki_key": key, "reason": "render_hash match"})
            continue
        item = {
            "wiki_key": key,
            "source": page.get("source"),
            "page_name": page.get("page_name"),
            "title": page.get("title"),
            "render": page.get("render"),
            "frozen": bool(page.get("frozen")),
            "render_hash": rh,
        }
        if src_hash:
            item["source_hash"] = src_hash
        if page.get("banner"):
            item["banner"] = page["banner"]
        if page.get("truth_state"):
            item["truth_state"] = page["truth_state"]
        publish.append(item)

    return {
        "publish": publish,
        "skip": skip,
        "frozen_violations": violations,
    }
