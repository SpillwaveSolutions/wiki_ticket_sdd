#!/usr/bin/env python3
"""
plan_capture.py -- parse a plan draft into work items. WORKLOG-SPEC 12, 13.2.

Pure functions only. All log writing happens in `worklog` (invariant 15.4).

Task syntax, inside a `## Tasks` section of the draft:

    - [ ] (P1) Extract auth middleware
      - [ ] Write failing test        <- indented = subtask of the task above

`[x]` boxes count too (a captured plan may arrive partially done). Checkboxes
outside the Tasks section are prose and are ignored. Priority token optional,
default P2.
"""
import re

TASK_RE = re.compile(r"^(\s+)?- \[[ xX]\] (?:\((P[0-3])\)\s+)?(.+?)\s*$")


def parse_tasks(draft):
    tasks = []
    in_tasks = False
    for line in draft.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            in_tasks = stripped.lstrip("#").strip().lower() == "tasks"
            continue
        if not in_tasks:
            continue
        m = TASK_RE.match(line)
        if not m:
            continue
        indent, prio, title = m.groups()
        tasks.append({"title": title, "priority": prio or "P2",
                      "subtask": bool(indent)})
    return tasks


def front_matter(date, slug, title, epic_id, item_ids):
    return "\n".join([
        "---",
        f"date: {date}",
        f"slug: {slug}",
        f"title: {title}",
        f"epic: {epic_id}",
        "items: [" + ", ".join(item_ids) + "]",
        "---",
        "",   # blank line between front matter and the draft body
        "",
    ])
