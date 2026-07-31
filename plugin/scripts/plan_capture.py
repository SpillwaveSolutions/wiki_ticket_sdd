#!/usr/bin/env python3
"""
plan_capture.py -- parse a plan draft into work items. WORKLOG-SPEC 12, 13.2.

Pure functions only. All log writing happens in `worklog` (invariant 15.4).

Task syntax, inside a `## Tasks` section of the draft:

    - [ ] (P1) Extract auth middleware
      Plain lines under a task are its description -- written for a junior
      dev or a PM: what and why, no ULIDs (spec section 13.4).
      - [ ] Write failing test        <- indented checkbox = subtask

`[x]` boxes count too (a captured plan may arrive partially done). Checkboxes
outside the Tasks section are prose and are ignored. Priority token optional,
default P2. Description lines attach to the most recent task as `body`.
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
            if stripped and tasks:
                prev = tasks[-1]
                prev["body"] = (prev["body"] + "\n" + stripped
                                if prev["body"] else stripped)
            continue
        indent, prio, title = m.groups()
        tasks.append({"title": title, "priority": prio or "P2",
                      "subtask": bool(indent), "body": ""})
    return tasks


# `#123` not preceded by a word char or a slash, so `C#` and a URL path do
# not read as tickets. Trailing \b keeps `#12abc` out.
TICKET_REF_RE = re.compile(r"(?<![\w/])#\d+\b")


def ticket_refs(text):
    """Ticket numbers cited in an item title (worklog#242). -> list of refs.

    A title written before capture cannot know its own ticket number: the
    tracker mints that during the next sync. So a `#123` in a title is either
    a reference to some OTHER ticket — fine, but easy to misread as this
    item's own — or a guess that will be wrong. The one that actually bites is
    an item created and closed inside a single session: sync never files an
    issue for it, so the number cited in the commit message points at an
    unrelated ticket, or at nothing.

    Advisory only. Legitimate titles do cite ticket numbers ("supersede the
    workaround from #98"), so this must never refuse a write — it names what
    it saw and lets the author decide.
    """
    return TICKET_REF_RE.findall(text or "")


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
