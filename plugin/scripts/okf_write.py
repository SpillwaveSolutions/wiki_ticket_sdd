#!/usr/bin/env python3
"""Write owned WikiTicket types into an OKF knowledge tree.

Knowledge-tree writes fail-closed without --author / SECOND_BRAIN_IDENTITY
and emit a WriteEvent. Worklog appends stay on bin/worklog --actor
(union-merge) and do not go through this module.
"""
from __future__ import annotations

import argparse
import contextvars
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

OWNED_TYPES = {
    "TicketLink": "tickets",
    "Epic": "epics",
    "Story": "stories",
    "Task": "tasks",
    "Subtask": "subtasks",
    "Bug": "bugs",
}

_AUTHOR: contextvars.ContextVar[str] = contextvars.ContextVar(
    "wiki_author", default=""
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def yaml_quote(value: str) -> str:
    if value == "" or any(c in value for c in ":#/{}[]&*!|>%@`'\" \n") or value.lower() in (
        "true",
        "false",
        "null",
    ):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def slugify(text: str, max_len: int = 80) -> str:
    text = text.strip().lower().replace("_", "-")
    text = re.sub(r"[^\w\s.-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[.\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if not text:
        text = "untitled"
    return text[:max_len].rstrip("-")


def resolve_author(explicit: str | None = None) -> str:
    """Fail-closed identity claim. Prefer --author, else SECOND_BRAIN_IDENTITY."""
    author = (explicit or os.environ.get("SECOND_BRAIN_IDENTITY") or "").strip()
    if not author:
        print(
            json.dumps(
                {
                    "error": "claim an identity first",
                    "hint": "pass --author or set SECOND_BRAIN_IDENTITY",
                }
            )
        )
        raise SystemExit(1)
    _AUTHOR.set(author)
    return author


def claimed_author(explicit: str | None = None) -> str:
    author = (explicit or "").strip() or _AUTHOR.get()
    if not author:
        return resolve_author(explicit)
    return author


def write_concept(bundle: Path, rel_path: str, text: str) -> Path:
    """Pure write. Does not stamp author or emit WriteEvent."""
    path = bundle / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def emit_write_event(
    bundle: Path,
    *,
    author: str,
    typ: str,
    dest: Path,
    host: str = "",
) -> Path | None:
    """Record a WriteEvent node. Skip self."""
    if typ == "WriteEvent":
        return None
    try:
        rel = "/" + dest.relative_to(bundle).as_posix()
    except ValueError:
        rel = "/" + dest.name
    event_id = f"{int(datetime.now(timezone.utc).timestamp())}-{secrets.token_hex(3)}"
    ev_path = bundle / "write-events" / f"{event_id}.md"
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "type: WriteEvent\n"
        f'title: "write {typ} {dest.name}"\n'
        "status: recorded\n"
        f"timestamp: {utc_now()}\n"
        f"author: {yaml_quote(author)}\n"
        "tags:\n"
        "  - write-event\n"
        f"  - {typ.lower()}\n"
        "links:\n"
        f"  - target: {rel}\n"
        "    rel: documents\n"
        "---\n\n"
        f"# Write {typ}\n\n"
        f"- actor: `{author}`\n"
        f"- host: `{host or os.environ.get('SECOND_BRAIN_HOST', '') or 'unknown'}`\n"
        f"- path: `{rel}`\n"
        f"- type: `{typ}`\n"
    )
    ev_path.write_text(body, encoding="utf-8")
    return ev_path


def write_knowledge(
    bundle: Path,
    *,
    typ: str,
    title: str,
    author: str | None = None,
    slug: str | None = None,
    item: str = "",
    body: str = "",
    host: str | None = None,
) -> tuple[Path, Path | None]:
    """Stamp author, write an owned type, emit WriteEvent."""
    if typ not in OWNED_TYPES:
        print(json.dumps({"error": f"unowned type: {typ}", "owned": sorted(OWNED_TYPES)}))
        raise SystemExit(1)
    claimed = claimed_author(author)
    catalog = OWNED_TYPES[typ]
    name = slugify(slug or title)
    rel = f"{catalog}/{name}.md"
    extra = f"item: {item}\n" if item else ""
    prose = body.strip() or f"# {title}\n"
    text = (
        "---\n"
        f"type: {typ}\n"
        f"title: {yaml_quote(title)}\n"
        f"author: {yaml_quote(claimed)}\n"
        f"{extra}"
        f"timestamp: {utc_now()}\n"
        "---\n\n"
        f"{prose.rstrip()}\n"
    )
    path = write_concept(bundle, rel, text)
    event = emit_write_event(
        bundle,
        author=claimed,
        typ=typ,
        dest=path,
        host=host if host is not None else os.environ.get("SECOND_BRAIN_HOST", ""),
    )
    return path, event


def cmd_write(args: argparse.Namespace) -> int:
    author = resolve_author(args.author)
    bundle = Path(args.bundle)
    path, event = write_knowledge(
        bundle,
        typ=args.type,
        title=args.title,
        author=author,
        slug=args.slug,
        item=args.item or "",
        body=args.body or "",
    )
    print(
        json.dumps(
            {
                "path": str(path),
                "event": str(event) if event else None,
                "author": author,
                "type": args.type,
            }
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write WikiTicket owned types into an OKF knowledge tree"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write", help="Create a TicketLink / work-item node")
    w.add_argument("--type", required=True, choices=sorted(OWNED_TYPES))
    w.add_argument("--title", required=True)
    w.add_argument("--bundle", default=os.environ.get("SECOND_BRAIN_ROOT", "knowledge"))
    w.add_argument("--author", default=None, help="or SECOND_BRAIN_IDENTITY")
    w.add_argument("--slug")
    w.add_argument("--item", help="worklog ULID this node tracks")
    w.add_argument("--body")
    w.set_defaults(func=cmd_write)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
