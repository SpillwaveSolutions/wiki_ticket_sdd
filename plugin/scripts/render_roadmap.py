#!/usr/bin/env python3
"""
render_roadmap.py -- generate the roadmap from the log. WORKLOG-SPEC 13.1.

Pure function of the log: fold in, markdown out, byte-deterministic. The
pre-commit hook regenerates and diffs, so `generated-at` is derived from the
newest event's ULID timestamp -- wall clock here would fail every commit.

Read-only for humans (invariant 15.7). There is no parser; to change the
roadmap, change the work items.
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulid
from fold import fold, CLOSED_STATUSES

PATHS = (".work/todo.jsonl", ".work/done.jsonl")
KINDS = ("feature", "bug", "ops", "triage")  # fixed order: deterministic mix
# ponytail: paths hardcoded to spec defaults; parse .work/config.yml when
# someone actually changes paths: (stdlib has no yaml).


def max_ev(paths):
    """Newest event ULID across the input files; None on an empty log."""
    top = None
    for path in paths:
        try:
            fh = open(path, encoding="utf-8")
        except FileNotFoundError:
            continue
        with fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    e = json.loads(line).get("ev")
                except (json.JSONDecodeError, AttributeError):
                    continue
                if isinstance(e, str) and (top is None or e > top):
                    top = e
    return top


def root_epic_id(item_id, items):
    seen = set()
    cur = items.get(item_id)
    while cur and cur.get("parent") in items and cur["parent"] not in seen:
        seen.add(cur["parent"])
        cur = items[cur["parent"]]
    # Taxonomy migration: fold guarantees `level` on every item; the old
    # `type` field no longer survives the fold.
    return cur["id"] if cur and cur.get("level") == "epic" else None


def ref(item):
    ext = item.get("external") or {}
    if ext.get("key") and ext.get("url"):
        return f"[{ext['key']}]({ext['url']})"
    if ext.get("key"):
        return ext["key"]
    return item["id"][:8]


def open_blockers(item, items):
    out = []
    for dep in item.get("depends_on") or []:
        blocker = items.get(dep)
        if blocker is None or blocker.get("status") not in CLOSED_STATUSES:
            out.append(ref(blocker) if blocker else dep[:8])
    return out


def section(item, items):
    if item.get("priority") == "P0" or item.get("status") == "in_progress":
        return "Now"
    if item.get("priority") == "P1":
        return "Next"
    if item.get("priority") == "P2" and not open_blockers(item, items):
        return "Next"
    return "Later"


def epic_members(eid, items):
    """Non-epic, non-cancelled members of the epic's subtree (open+closed)."""
    return [i for i in items.values()
            if i.get("level") != "epic" and i.get("status") != "cancelled"
            and root_epic_id(i["id"], items) == eid]


def kind_mix(members):
    """'feature 4 / bug 2' segment; '' when everything is feature (the common case)."""
    counts = [(k, sum(1 for i in members if i.get("kind") == k)) for k in KINDS]
    if all(k == "feature" or n == 0 for k, n in counts):
        return ""
    return " / ".join(f"{k} {n}" for k, n in counts if n)


def derived_milestone(members):
    """Epic milestone is derived from children (spec 2.5): unanimous value or 'mixed'."""
    ms = {i.get("milestone") for i in members if i.get("milestone")}
    if not ms:
        return ""
    return ms.pop() if len(ms) == 1 else "mixed"


def row(i, items):
    blockers = ", ".join(open_blockers(i, items)) or "—"
    return (f"| {ref(i)} | {i.get('title', '')} | {i.get('level', '')} "
            f"| {i.get('priority', '—')} "
            f"| {i.get('status', '').replace('_', ' ')} | {blockers} |")


VIZ_ALL = ("deps", "hierarchy", "gantt")


def render(paths=PATHS, viz="deps,hierarchy"):
    # Default MUST match cmd_roadmap_render's --viz default: the pre-commit
    # freshness gate diffs bare `python3 bin/render_roadmap.py` output against
    # the file worklog wrote.
    r = fold(paths)
    items = r.items

    src = json.dumps(sorted(items.values(), key=lambda i: i["id"]),
                     sort_keys=True, separators=(",", ":"))
    source_hash = hashlib.sha256(src.encode()).hexdigest()[:8]
    top = max_ev(paths)
    gen = (time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         time.gmtime(ulid.timestamp_ms(top) / 1000))
           if top else "never")

    open_non_epic = [i for i in r.open_items() if i.get("level") != "epic"]
    blocked = [i for i in open_non_epic
               if i.get("status") == "blocked" or open_blockers(i, items)]
    epics_in_flight = {root_epic_id(i["id"], items) for i in open_non_epic} - {None}
    triage = sorted((i for i in r.open_items() if i.get("kind") == "triage"),
                    key=lambda i: i["id"])

    lines = [
        # YAML frontmatter replaces the legacy HTML-comment header (plan
        # ia-content-model §5.4). Deterministic: generated_at derives from
        # the newest event ULID, never wall clock. Gollum-style wikis strip
        # this block at publish time (wiki-publish §3).
        "---",
        "wiki_key: roadmap",
        "doc_type: roadmap",
        "truth_state: current",
        f"source_hash: {source_hash}",
        f"generated_at: {gen}",
        "---",
        "",
        "<!-- GENERATED by worklog roadmap-render. DO NOT EDIT. -->",
        "",
        "> This file is generated from `.work/todo.jsonl`. Edits will be overwritten.",
        "> To change the roadmap, change the work items: `worklog add|update|close`.",
        "",
        "# Roadmap",
        "",
        f"_{len(epics_in_flight)} epic(s) in flight, "
        f"{len(open_non_epic)} open item(s), {len(blocked)} blocked, "
        f"{len(triage)} unclassified._",
    ]

    for sec in ("Now", "Next", "Later"):
        bucket = [i for i in open_non_epic if section(i, items) == sec]
        lines += ["", f"## {sec}"]
        if not bucket:
            lines += ["", "_Nothing here._"]
            continue
        groups = {}
        for i in bucket:
            groups.setdefault(root_epic_id(i["id"], items), []).append(i)
        for eid in sorted(groups, key=lambda e: e or "~"):  # "~" sorts no-epic last
            epic = items.get(eid) if eid else None
            lines.append("")
            if epic:
                members = epic_members(eid, items)
                done = sum(1 for i in members if i.get("status") == "done")
                head = f"### {epic.get('title', '?')}"
                if epic.get("priority"):
                    head += f"  ·  {epic['priority']}"
                head += f"  ·  {done} of {len(members)} done"
                mix = kind_mix(members)
                if mix:
                    head += f"  ·  {mix}"
                if sec in ("Now", "Next"):  # derived milestone: Now/Next only (spec 5)
                    dm = derived_milestone(members)
                    if dm:
                        head += f"  ·  → {dm}"
                lines.append(head)
                if epic.get("body"):
                    lines += [epic["body"].strip()]
            else:
                lines.append("### (no epic)")
            lines += ["", "| # | Item | Type | Priority | Status | Blocked by |",
                      "|---|---|---|---|---|---|"]
            for i in sorted(groups[eid], key=lambda x: (x.get("priority", "P9"), x["id"])):
                lines.append(row(i, items))

    if triage:
        lines += ["", "## Needs classification", ""]
        lines += [f"- {ref(i)} {i.get('title', '')} ({i.get('level', '')})"
                  for i in triage]

    by_ms = {}
    for i in r.open_items():
        if i.get("milestone"):
            by_ms.setdefault(i["milestone"], []).append(i)
    if by_ms:
        lines += ["", "## Milestones"]
        for ms in sorted(by_ms):
            lines += ["", f"### {ms}", "",
                      "| # | Item | Type | Priority | Status | Blocked by |",
                      "|---|---|---|---|---|---|"]
            for i in sorted(by_ms[ms], key=lambda x: (x.get("priority", "P9"), x["id"])):
                lines.append(row(i, items))

    attention = []
    for iid, c in r.conflicts():
        attention.append(
            f"- **{ref(items[iid])}** — `{c.get('field', '?')}` conflicts: "
            f"local `{c.get('local', '?')}`, remote `{c.get('remote', '?')}`. "
            f"Resolve with `worklog resolve {iid} --field {c.get('field', '?')} "
            f"--take local|remote`.")
    for iid in sorted(set(r.orphans)):
        attention.append(f"- Orphan events for `{iid[:8]}` — no create/snapshot yet.")
    if attention:
        lines += ["", "## Needs attention", ""] + attention

    which = VIZ_ALL if viz == "all" else \
        tuple(s.strip() for s in (viz or "").split(",") if s.strip() != "")
    if viz not in ("none", "", None) and which:
        import viz_mermaid
        vsec = viz_mermaid.render_viz(r, paths, which)
        if vsec:
            lines += ["", vsec]

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render())
