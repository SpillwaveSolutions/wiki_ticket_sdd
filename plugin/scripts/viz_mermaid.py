#!/usr/bin/env python3
"""
viz_mermaid.py -- Mermaid diagrams for the roadmap. Pure functions over the
fold; imported by render_roadmap. Plan: docs/plans/2026-07-19-grok-compat-and-mermaid-viz.md.

Gantt dates are HISTORICAL FACT, never plans: created/started/closed come from
event ULID timestamps; "now" is the max event timestamp (never wall clock), so
output stays byte-deterministic for the pre-commit freshness gate.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulid
from fold import OPEN_STATUSES

KIND_EMOJI = {"feature": "\U0001F4E6", "bug": "\U0001F41B",
              "ops": "\U0001F527", "triage": "❓"}
MAX_NODES = 40
_STRIP = set('[]{}"`<>|:;,#')  # mermaid-breaking chars, incl. gantt separators


def _safe(text):
    return "".join(c for c in (text or "") if c not in _STRIP).strip()[:30].rstrip()


def _day(ms):
    return time.strftime("%Y-%m-%d", time.gmtime(ms / 1000))


def item_dates(paths):
    """{item_id: {created, started, closed}} in ms from event ULIDs, plus the
    max event ms ("now"). Raw-line scan, both files, unparseable lines skipped
    -- same leniency as the fold. started = FIRST in_progress-setting event;
    closed = last close event (a reopen makes earlier closes moot)."""
    dates, now = {}, None
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
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(e, dict):
                    continue
                ev, iid = e.get("ev"), e.get("item")
                if not isinstance(ev, str) or not ev or not iid:
                    continue
                try:
                    ms = ulid.timestamp_ms(ev)
                except ValueError:
                    continue
                if now is None or ms > now:
                    now = ms
                d = dates.setdefault(iid, {"created": None, "started": None,
                                           "closed": None})
                op = e.get("op")
                if op == "create" and (d["created"] is None or ms < d["created"]):
                    d["created"] = ms
                if ((e.get("set") or {}).get("status") == "in_progress"
                        and (d["started"] is None or ms < d["started"])):
                    d["started"] = ms
                if op == "close" and (d["closed"] is None or ms > d["closed"]):
                    d["closed"] = ms
    return dates, now


def _select(items):
    """Open items capped at MAX_NODES by (priority, id); (chosen_ids, overflow)."""
    ranked = sorted((i for i in items.values() if i.get("status") in OPEN_STATUSES),
                    key=lambda i: (i.get("priority", "P9"), i["id"]))
    return [i["id"] for i in ranked[:MAX_NODES]], max(0, len(ranked) - MAX_NODES)


# ponytail: deps_graph and hierarchy share _graph; hierarchy is just the
# parent edges without dep edges or status classes.
def _graph(items, with_deps):
    ids, more = _select(items)
    if not ids:
        return ""
    ids_set, ids = set(ids), sorted(ids)
    lines = ["```mermaid", "graph TD"]
    for iid in ids:
        i = items[iid]
        emoji = KIND_EMOJI.get(i.get("kind"), KIND_EMOJI["triage"])
        lines.append(f'    {iid}["{emoji} {_safe(i.get("title"))}"]')
    for iid in ids:
        if items[iid].get("parent") in ids_set:
            lines.append(f"    {items[iid]['parent']} --> {iid}")
    if with_deps:
        for iid in ids:
            for dep in sorted(items[iid].get("depends_on") or []):
                if dep in ids_set:
                    lines.append(f"    {dep} -.-> {iid}")
        styles = {"todo": "fill:#f4f4f4,stroke:#999999",
                  "in_progress": "fill:#d9f2d9,stroke:#2e7d32",
                  "blocked": "fill:#fde0e0,stroke:#c62828"}
        by_status = {}
        for iid in ids:
            by_status.setdefault(items[iid].get("status"), []).append(iid)
        for st in ("todo", "in_progress", "blocked"):
            if st in by_status:
                lines.append(f"    classDef {st} {styles[st]}")
                lines.append(f"    class {','.join(by_status[st])} {st}")
    lines.append("```")
    out = "\n".join(lines)
    if more:
        out += f"\n\n_+{more} more items not shown_"
    return out


def deps_graph(items):
    """Open items; solid parent edges, dashed depends_on, status classes."""
    return _graph(items, with_deps=True)


def hierarchy(items):
    """Open items; parent (epic -> story -> task/subtask) edges only."""
    return _graph(items, with_deps=False)


def gantt(items, dates, now):
    """Per-milestone sections. Only items carrying a milestone AND a started
    or closed date -- historical fact only; unscheduled work is omitted."""
    by_ms = {}
    for iid in sorted(items):
        i = items[iid]
        if not i.get("milestone") or i.get("status") == "cancelled":
            continue
        d = dates.get(iid) or {}
        if not (d.get("started") or d.get("closed")):
            continue
        by_ms.setdefault(i["milestone"], []).append(i)
    if not by_ms:
        return ""
    lines = ["```mermaid", "gantt", "    dateFormat YYYY-MM-DD"]
    tags = {"done": "done, ", "blocked": "crit, ", "in_progress": "active, "}
    for ms in sorted(by_ms):
        lines.append(f"    section {_safe(ms)}")
        for i in sorted(by_ms[ms], key=lambda x: (x.get("priority", "P9"), x["id"])):
            d = dates[i["id"]]
            start = _day(d.get("started") or d.get("created") or now)
            end = _day(d.get("closed") or now)
            title = _safe(i.get("title"))
            if i.get("unplanned"):
                title += " ⚡"
            lines.append(f"    {title} :{tags.get(i.get('status'), '')}{start}, {end}")
    lines.append("```")
    return "\n".join(lines)


def render_viz(fold_result, paths, which):
    """'## Visual roadmap' section for the enabled diagrams; '' when all empty."""
    items = fold_result.items
    parts = []
    if "deps" in which:
        d = deps_graph(items)
        if d:
            parts += ["### Dependency graph", "", d, ""]
    if "hierarchy" in which:
        h = hierarchy(items)
        if h:
            parts += ["### Hierarchy", "", h, ""]
    if "gantt" in which:
        dates, now = item_dates(paths)
        g = gantt(items, dates, now)
        if g:
            parts += ["### Gantt (event-dated)", "", g, ""]
    if not parts:
        return ""
    return "\n".join(["## Visual roadmap", ""] + parts).rstrip("\n")
