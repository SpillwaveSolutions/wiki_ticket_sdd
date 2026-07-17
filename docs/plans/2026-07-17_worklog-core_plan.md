# Worklog Core (Spec §18 Steps 3–4 + CI) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Assemble the worklog repo from the reviewed artifacts in `inputs/`, then implement the roadmap renderer, the plan-capture command, their CI guard, and the `ExitPlanMode` hook — completing spec §18 steps 3–4.

**Architecture:** Local-first, git-native work tracking (see `inputs/worklog-spec.md`, v1.2). `.work/todo.jsonl` is an append-only event log; state is a fold over events (`bin/fold.py`, done). This plan adds two pure generators on top of the fold: `render_roadmap.py` (deterministic markdown from the log) and `plan_capture.py` (markdown draft → items), both wired as `bin/worklog` subcommands. Everything downstream of the log — compaction, ticket/wiki adapters, sync, status reports — is deliberately **out of scope** (spec: "Do not build sync before you've lived with the log") and gets its own plan later.

**Tech Stack:** Python 3 stdlib only (no dependencies, no pip). Bash for hooks. GitHub Actions for CI.

## Global Constraints

Copied from `inputs/worklog-spec.md`; every task implicitly includes these.

- Python 3 stdlib only. No third-party imports anywhere.
- Nothing but `bin/worklog`'s `append()` writes to `.work/*.jsonl` (invariant §15.4). New code that needs to append events must go through it.
- Every `.jsonl` write ends in `\n` (invariant §15.1). `MAX_BODY = 2048` stays a code constant, never a config key (§8.3).
- Fold order is by `ev` (ULID string sort), never by `ts` or file position (§6).
- `docs/roadmap.md` is generated and never hand-edited (invariant §15.7). Renderer output must be **byte-deterministic**: same log → same bytes, or the freshness diff in `hooks/pre-commit:36-40` false-positives. Therefore `generated-at` derives from the newest event's ULID timestamp, not wall clock.
- A plan in `docs/plans/` is never edited or regenerated (invariant §15.8). `plan-capture` must refuse to overwrite.
- The core never reads or branches on ticketing/wiki specifics (§4.2 resolution rule). Nothing in this plan touches adapters.
- The item ULID is the primary key, always (§5.4).
- Do NOT copy `inputs/todo.jsonl` into the repo — it is demo data ending in a deliberately corrupt fused line. The real logs start empty.
- Deliberate simplification (ponytail): scripts hardcode the spec-default paths (`.work/todo.jsonl`, `docs/roadmap.md`, `docs/plans/`) instead of parsing `.work/config.yml`, because stdlib has no YAML parser. Revisit when someone actually changes `paths:` in config. `.work/schema/*.json` files are skipped for the same reason — the pre-commit hook already validates the envelope inline.

---

### Task 1: Assemble the repo skeleton from `inputs/`

**Files:**
- Create (copy): `bin/worklog`, `bin/fold.py`, `bin/ulid.py` ← from `inputs/`
- Create (copy): `tests/test_fold.py`, `tests/test_ulid.py` ← from `inputs/`
- Create (copy): `hooks/pre-commit` ← from `inputs/pre-commit`
- Create (copy): `CLAUDE.md` ← from `inputs/CLAUDE.md`; `AGENTS.md` as a symlink to it
- Create (copy): `.work/config.yml` ← from `inputs/config.yml`
- Create: `.work/todo.jsonl`, `.work/done.jsonl` (both empty), `.gitattributes`, `.gitignore`, `docs/plans/.gitkeep`, `docs/status/.gitkeep`

**Interfaces:**
- Consumes: nothing (first task; repo has no commits yet).
- Produces: working `bin/worklog` CLI (`add`, `update`, `close`, `list`, `show`, `fold` subcommands; `plan-capture`/`sync`/`status`/`roadmap-render`/`compact` stubbed), `fold(paths) -> FoldResult` in `bin/fold.py` (attributes: `.items` dict, `.open_items()`, `.closed_items()`, `.conflicts()`, `.orphans`, `.errors`), `ulid.new(timestamp_ms=None)` and `ulid.timestamp_ms(ulid_str)` in `bin/ulid.py`, armed pre-commit hook. Later tasks import these exact names.

- [ ] **Step 1: Copy files into place**

```bash
cd /Users/richardhightower/clients/spillwave/src/wiki_ticket_sdd
mkdir -p bin tests hooks .work docs/plans docs/status
cp inputs/worklog inputs/fold.py inputs/ulid.py bin/
cp inputs/test_fold.py inputs/test_ulid.py tests/
cp inputs/pre-commit hooks/pre-commit
cp inputs/CLAUDE.md CLAUDE.md
cp inputs/config.yml .work/config.yml
: > .work/todo.jsonl
: > .work/done.jsonl
touch docs/plans/.gitkeep docs/status/.gitkeep
ln -sf CLAUDE.md AGENTS.md
chmod +x bin/worklog hooks/pre-commit
```

Do **not** copy `inputs/todo.jsonl`, `inputs/done.jsonl`, `inputs/AGENTS.md` (placeholder prose — the symlink above replaces it), or any `.pyc` files.

- [ ] **Step 2: Write `.gitattributes`** (union merge, spec §8.1)

```
.work/todo.jsonl merge=union
.work/done.jsonl merge=union
```

- [ ] **Step 3: Write `.gitignore`** (spec §3)

```
.work/sync-state.json
.work/changeset.json
.work/results/
__pycache__/
*.pyc
```

- [ ] **Step 4: Arm the hook and run the existing test suites**

```bash
git config core.hooksPath hooks
python3 tests/test_fold.py
python3 tests/test_ulid.py
```

Expected: `OK` from both — 21 tests and 11 tests respectively. If an import fails, the `sys.path.insert` lines in the tests expect the layout `tests/../bin/`; verify the copies landed in `bin/`.

- [ ] **Step 5: Smoke the CLI end to end**

```bash
ID=$(bin/worklog add "Smoke test item" --priority P3)
bin/worklog show "$ID" | grep '"title": "Smoke test item"'
bin/worklog close "$ID" --status cancelled
bin/worklog list --all | grep cancelled
```

Expected: the grep lines match. This exercises `append()`'s newline invariant on the real log. The two events stay in the log — they're legitimate history and prove the hook passes on a non-empty file.

- [ ] **Step 6: Commit (the hook fires for the first time here)**

```bash
git add -A ':!inputs'
git commit -m "feat: worklog core — event log, fold, CLI, hooks (spec §18 steps 1–2)"
```

Expected: hook runs (newline check + schema check + fold tests), commit succeeds. `inputs/` stays uncommitted as raw material; delete it at the end of the plan if desired.

---

### Task 2: Roadmap renderer (`bin/render_roadmap.py`)

**Files:**
- Create: `bin/render_roadmap.py`
- Test: `tests/test_render_roadmap.py`

**Interfaces:**
- Consumes: `fold(paths) -> FoldResult` from `bin/fold.py`; `ulid.timestamp_ms(str) -> int` from `bin/ulid.py`; `write_log(lines) -> path` helper from `tests/test_fold.py`.
- Produces: `render(paths=(".work/todo.jsonl", ".work/done.jsonl")) -> str` returning the full markdown document, and a `__main__` that prints it to stdout (that exact stdout contract is what `hooks/pre-commit:37` invokes). Task 3 imports `render_roadmap.render`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_render_roadmap.py`:

```python
#!/usr/bin/env python3
"""Tests for bin/render_roadmap.py -- WORKLOG-SPEC section 13.1.

The renderer must be byte-deterministic: the pre-commit freshness check
regenerates and diffs, so any nondeterminism (wall-clock timestamps, dict
order) makes every commit fail.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
sys.path.insert(0, os.path.dirname(__file__))
from render_roadmap import render  # noqa: E402
from test_fold import write_log  # noqa: E402


def ev(n, item, op, **kw):
    e = {"ev": f"01J8X{n:04d}A0", "ts": "t", "actor": "t", "item": item, "op": op}
    e.update(kw)
    return e


class TestDeterminism(unittest.TestCase):
    EVENTS = [
        ev(1, "E1", "create", set={"type": "epic", "title": "Auth refactor",
                                   "status": "todo", "priority": "P0"}),
        ev(2, "T1", "create", set={"type": "task", "title": "Extract middleware",
                                   "status": "in_progress", "priority": "P0",
                                   "parent": "E1"}),
        ev(3, "T2", "create", set={"type": "task", "title": "Session migration",
                                   "status": "todo", "priority": "P1",
                                   "parent": "E1", "depends_on": ["T1"]}),
    ]

    def test_identical_output_regardless_of_file_order(self):
        a = render([write_log(self.EVENTS)])
        b = render([write_log(list(reversed(self.EVENTS)))])
        self.assertEqual(a, b)

    def test_two_renders_of_same_log_are_identical(self):
        path = write_log(self.EVENTS)
        self.assertEqual(render([path]), render([path]))

    def test_generated_marker_and_hash_present(self):
        out = render([write_log(self.EVENTS)])
        self.assertIn("<!-- GENERATED by worklog roadmap-render. DO NOT EDIT. -->", out)
        self.assertIn("<!-- source-hash: ", out)
        self.assertIn("<!-- generated-at: ", out)
        self.assertNotIn("generated-at: never", out)


class TestSections(unittest.TestCase):
    def test_in_progress_lands_in_now(self):
        out = render([write_log([
            ev(1, "A", "create", set={"type": "task", "title": "Mid-flight",
                                      "status": "in_progress", "priority": "P2"}),
        ])])
        now = out.split("## Now")[1].split("## Next")[0]
        self.assertIn("Mid-flight", now)

    def test_unblocked_p2_is_next_blocked_p2_is_later(self):
        out = render([write_log([
            ev(1, "D1", "create", set={"type": "task", "title": "Dep",
                                       "status": "todo", "priority": "P2"}),
            ev(2, "B1", "create", set={"type": "task", "title": "Waiting",
                                       "status": "todo", "priority": "P2",
                                       "depends_on": ["D1"]}),
        ])])
        nxt = out.split("## Next")[1].split("## Later")[0]
        later = out.split("## Later")[1]
        self.assertIn("Dep", nxt)
        self.assertIn("Waiting", later)

    def test_blocked_by_column_names_the_open_blocker(self):
        out = render([write_log([
            ev(1, "DEP12345XX", "create", set={"type": "task", "title": "Dep",
                                               "status": "todo", "priority": "P2"}),
            ev(2, "B1", "create", set={"type": "task", "title": "Waiting",
                                       "status": "todo", "priority": "P2",
                                       "depends_on": ["DEP12345XX"]}),
        ])])
        self.assertIn("DEP12345", out.split("## Later")[1])

    def test_closed_items_and_epics_do_not_appear_as_rows(self):
        out = render([write_log([
            ev(1, "E1", "create", set={"type": "epic", "title": "TheEpic",
                                       "status": "todo", "priority": "P1"}),
            ev(2, "T1", "create", set={"type": "task", "title": "Shipped",
                                       "status": "todo", "priority": "P1",
                                       "parent": "E1"}),
            ev(3, "T1", "close", set={"status": "done"}),
            ev(4, "T2", "create", set={"type": "task", "title": "Open task",
                                       "status": "todo", "priority": "P1",
                                       "parent": "E1"}),
        ])])
        self.assertNotIn("| Shipped |", out)          # closed: no table row
        self.assertNotIn("| TheEpic |", out)          # epic: heading, not row
        self.assertIn("### TheEpic", out)


class TestEpicProgress(unittest.TestCase):
    def test_done_counts_cancelled_does_not(self):
        out = render([write_log([
            ev(1, "E1", "create", set={"type": "epic", "title": "Auth",
                                       "status": "todo", "priority": "P1"}),
            ev(2, "T1", "create", set={"type": "task", "title": "One",
                                       "status": "todo", "priority": "P1", "parent": "E1"}),
            ev(3, "T2", "create", set={"type": "task", "title": "Two",
                                       "status": "todo", "priority": "P1", "parent": "E1"}),
            ev(4, "T3", "create", set={"type": "task", "title": "Three",
                                       "status": "todo", "priority": "P1", "parent": "E1"}),
            ev(5, "T2", "close", set={"status": "done"}),
            ev(6, "T3", "close", set={"status": "cancelled"}),
        ])])
        self.assertIn("1 of 2 done", out)


class TestNeedsAttention(unittest.TestCase):
    def test_conflict_is_surfaced_with_resolve_hint(self):
        out = render([write_log([
            ev(1, "A1", "create", set={"type": "task", "title": "Contested",
                                       "status": "todo", "priority": "P1"}),
            ev(2, "A1", "conflict", set={"field": "priority",
                                         "local": "P1", "remote": "P0"}),
        ])])
        self.assertIn("## Needs attention", out)
        self.assertIn("worklog resolve A1 --field priority", out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 tests/test_render_roadmap.py`
Expected: `ModuleNotFoundError: No module named 'render_roadmap'`

- [ ] **Step 3: Write the implementation**

Create `bin/render_roadmap.py`:

```python
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
    return cur["id"] if cur and cur.get("type") == "epic" else None


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


def epic_progress(eid, items):
    members = [i for i in items.values()
               if i.get("type") != "epic" and root_epic_id(i["id"], items) == eid]
    done = sum(1 for i in members if i.get("status") == "done")
    total = sum(1 for i in members if i.get("status") != "cancelled")
    return total, done


def render(paths=PATHS):
    r = fold(paths)
    items = r.items

    src = json.dumps(sorted(items.values(), key=lambda i: i["id"]),
                     sort_keys=True, separators=(",", ":"))
    source_hash = hashlib.sha256(src.encode()).hexdigest()[:8]
    top = max_ev(paths)
    gen = (time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         time.gmtime(ulid.timestamp_ms(top) / 1000))
           if top else "never")

    open_non_epic = [i for i in r.open_items() if i.get("type") != "epic"]
    blocked = [i for i in open_non_epic
               if i.get("status") == "blocked" or open_blockers(i, items)]
    epics_in_flight = {root_epic_id(i["id"], items) for i in open_non_epic} - {None}

    lines = [
        "<!-- GENERATED by worklog roadmap-render. DO NOT EDIT. -->",
        f"<!-- source-hash: {source_hash} -->",
        f"<!-- generated-at: {gen} -->",
        "",
        "> This file is generated from `.work/todo.jsonl`. Edits will be overwritten.",
        "> To change the roadmap, change the work items: `worklog add|update|close`.",
        "",
        "# Roadmap",
        "",
        f"_{len(epics_in_flight)} epic(s) in flight, "
        f"{len(open_non_epic)} open item(s), {len(blocked)} blocked._",
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
                total, done = epic_progress(eid, items)
                head = f"### {epic.get('title', '?')}"
                if epic.get("priority"):
                    head += f"  ·  {epic['priority']}"
                head += f"  ·  {done} of {total} done"
                lines.append(head)
                if epic.get("body"):
                    lines += [epic["body"].strip()]
            else:
                lines.append("### (no epic)")
            lines += ["", "| # | Item | Type | Priority | Status | Blocked by |",
                      "|---|---|---|---|---|---|"]
            for i in sorted(groups[eid], key=lambda x: (x.get("priority", "P9"), x["id"])):
                blockers = ", ".join(open_blockers(i, items)) or "—"
                lines.append(
                    f"| {ref(i)} | {i.get('title', '')} | {i.get('type', '')} "
                    f"| {i.get('priority', '—')} "
                    f"| {i.get('status', '').replace('_', ' ')} | {blockers} |")

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

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/test_render_roadmap.py`
Expected: `OK`, 9 tests. Also re-run `python3 tests/test_fold.py` — still 21 passing (renderer must not have touched fold).

- [ ] **Step 5: Commit**

```bash
git add bin/render_roadmap.py tests/test_render_roadmap.py
git commit -m "feat: deterministic roadmap renderer (spec §13.1, §18 step 3)"
```

Note: the hook's freshness check does not fire yet — `docs/roadmap.md` doesn't exist and the hook guards on both files existing.

---

### Task 3: Wire `worklog roadmap-render` and generate the first roadmap

**Files:**
- Modify: `bin/worklog` (replace the `roadmap-render` stub, ~line 137)
- Create: `docs/roadmap.md` (generated)

**Interfaces:**
- Consumes: `render_roadmap.render() -> str` from Task 2.
- Produces: `bin/worklog roadmap-render` subcommand that writes `docs/roadmap.md` and prints the path. From this commit on, **every commit must carry a fresh roadmap** — the hook's freshness check is now live. Any later task that appends events must run `bin/worklog roadmap-render` before committing.

- [ ] **Step 1: Replace the stub in `bin/worklog`**

Add this function after `cmd_fold` (around line 99):

```python
def cmd_roadmap_render(a):
    import render_roadmap
    md = render_roadmap.render()
    os.makedirs("docs", exist_ok=True)
    with open("docs/roadmap.md", "w", encoding="utf-8") as fh:
        fh.write(md)
    print("docs/roadmap.md")
```

Then change the stub loop at the bottom from:

```python
for name in ("plan-capture", "sync", "status", "roadmap-render", "compact"):
    sub.add_parser(name).set_defaults(fn=stub(name))
```

to:

```python
sub.add_parser("roadmap-render").set_defaults(fn=cmd_roadmap_render)
for name in ("plan-capture", "sync", "status", "compact"):
    sub.add_parser(name).set_defaults(fn=stub(name))
```

- [ ] **Step 2: Generate and eyeball**

```bash
bin/worklog roadmap-render
cat docs/roadmap.md
```

Expected: header comments, summary line (`0 epic(s) in flight, 0 open item(s)…` if the Task 1 smoke item was cancelled), three section headings. The cancelled smoke item must NOT appear.

- [ ] **Step 3: Verify the freshness guard actually guards**

```bash
echo "vandalism" >> docs/roadmap.md
git add -A ':!inputs' && git commit -m "should fail" ; echo "exit=$?"
```

Expected: `docs/roadmap.md is stale or hand-edited. Run: worklog roadmap-render`, `exit=1`. Then repair:

```bash
bin/worklog roadmap-render
```

- [ ] **Step 4: Commit**

```bash
git add -A ':!inputs'
git commit -m "feat: worklog roadmap-render subcommand + generated roadmap"
```

Expected: hook passes (regenerate + diff clean), commit succeeds.

---

### Task 4: CI workflow

**Files:**
- Create: `.github/workflows/worklog.yml`

**Interfaces:**
- Consumes: `hooks/pre-commit` (runs unchanged in CI — spec §18 step 2's outstanding item: "the hook is local-only; CI must re-run it").
- Produces: CI enforcement of invariants §15.1/§15.7 + all test suites on every push/PR.

- [ ] **Step 1: Write the workflow**

```yaml
name: worklog-invariants
on: [push, pull_request]

jobs:
  invariants:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Same script as the local hook: trailing newline, event schema,
      # roadmap freshness. A dev can --no-verify past the local hook; not this.
      - name: log invariants
        run: hooks/pre-commit
      - name: tests
        run: |
          python3 tests/test_fold.py
          python3 tests/test_ulid.py
          python3 tests/test_render_roadmap.py
          python3 tests/test_plan_capture.py
```

Note: `tests/test_plan_capture.py` arrives in Task 5. If executing tasks strictly in order, this workflow will fail on any push between Tasks 4 and 5 — fine if there's no remote yet (this repo has none); otherwise swap Task 4 after Task 5.

- [ ] **Step 2: Sanity-check locally** (CI has no runner here; simulate the job)

```bash
hooks/pre-commit && python3 tests/test_fold.py && python3 tests/test_ulid.py && python3 tests/test_render_roadmap.py
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/worklog.yml
git commit -m "ci: enforce log invariants and run test suites (spec §14)"
```

---

### Task 5: Plan-capture parser (`bin/plan_capture.py`)

**Files:**
- Create: `bin/plan_capture.py`
- Test: `tests/test_plan_capture.py`

**Interfaces:**
- Consumes: nothing from other modules (pure functions — all `.jsonl` writing stays in `bin/worklog`, invariant §15.4).
- Produces: `parse_tasks(draft: str) -> list[dict]` where each dict is `{"title": str, "priority": "P0".."P3", "subtask": bool}`, in document order; `front_matter(date, slug, title, epic_id, item_ids) -> str`. Task 6's `cmd_plan_capture` imports both names exactly.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_plan_capture.py`:

```python
#!/usr/bin/env python3
"""Tests for bin/plan_capture.py -- WORKLOG-SPEC sections 12 and 13.2."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from plan_capture import parse_tasks, front_matter  # noqa: E402

DRAFT = """# Auth refactor plan

Prose about why. Not a task:
- [ ] this checkbox is above the Tasks heading and must be ignored

## Tasks

- [ ] (P0) Extract auth middleware
  - [ ] Write failing test
- [x] Session store migration

## Notes

- [ ] this checkbox is after the Tasks section and must be ignored
"""


class TestParseTasks(unittest.TestCase):
    def test_only_the_tasks_section_is_parsed(self):
        self.assertEqual(
            [t["title"] for t in parse_tasks(DRAFT)],
            ["Extract auth middleware", "Write failing test",
             "Session store migration"])

    def test_priority_token_and_default(self):
        tasks = parse_tasks(DRAFT)
        self.assertEqual(tasks[0]["priority"], "P0")
        self.assertEqual(tasks[2]["priority"], "P2")  # no token -> P2

    def test_indent_marks_subtask(self):
        self.assertEqual([t["subtask"] for t in parse_tasks(DRAFT)],
                         [False, True, False])

    def test_no_tasks_section_yields_nothing(self):
        self.assertEqual(parse_tasks("# Plan\n\n- [ ] loose checkbox\n"), [])


class TestFrontMatter(unittest.TestCase):
    def test_shape(self):
        fm = front_matter("2026-07-17", "auth", "Auth refactor",
                          "01EPIC", ["01A", "01B"])
        self.assertTrue(fm.startswith("---\n"))
        self.assertIn("date: 2026-07-17\n", fm)
        self.assertIn("slug: auth\n", fm)
        self.assertIn("epic: 01EPIC\n", fm)
        self.assertIn("items: [01A, 01B]\n", fm)
        self.assertTrue(fm.endswith("---\n\n"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 tests/test_plan_capture.py`
Expected: `ModuleNotFoundError: No module named 'plan_capture'`

- [ ] **Step 3: Write the implementation**

Create `bin/plan_capture.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/test_plan_capture.py`
Expected: `OK`, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add bin/plan_capture.py tests/test_plan_capture.py
git commit -m "feat: plan draft parser (spec §13.2)"
```

---

### Task 6: Wire `worklog plan-capture` and prove it end to end

**Files:**
- Modify: `bin/worklog` (replace the `plan-capture` stub)

**Interfaces:**
- Consumes: `parse_tasks`, `front_matter` from Task 5; `append()`, `base()`, `ulid.new()` already in `bin/worklog`.
- Produces: `bin/worklog plan-capture --slug S --title T [--file F] [--priority P]` — reads the draft from `--file` or stdin, creates one epic + one item per task (subtasks parented to the preceding task, tasks to the epic, every item's `plan` field set), writes `docs/plans/<YYYY-MM-DD>-<slug>.md` with front matter, refuses to overwrite, prints the plan path then the epic ULID (two lines). Task 7's hook text references this exact invocation.

- [ ] **Step 1: Add `cmd_plan_capture` to `bin/worklog`** (after `cmd_roadmap_render`)

```python
def cmd_plan_capture(a):
    import plan_capture
    draft = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    tasks = plan_capture.parse_tasks(draft)
    if not tasks:
        sys.exit("worklog: no '- [ ]' tasks found under a '## Tasks' heading")
    date = time.strftime("%Y-%m-%d", time.gmtime())
    path = f"docs/plans/{date}-{a.slug}.md"
    if os.path.exists(path):
        sys.exit(f"worklog: {path} exists; plans are never rewritten "
                 "(invariant 15.8) — pick a new slug to supersede")

    epic_id = ulid.new()
    ev = base(epic_id, "create", a.actor)
    ev["set"] = {"type": "epic", "title": a.title, "status": "todo",
                 "priority": a.priority, "plan": path}
    append(ev)

    item_ids, last_task = [], epic_id
    for t in tasks:
        iid = ulid.new()
        ev = base(iid, "create", a.actor)
        ev["set"] = {"type": "subtask" if t["subtask"] else "task",
                     "title": t["title"], "status": "todo",
                     "priority": t["priority"],
                     "parent": last_task if t["subtask"] else epic_id,
                     "plan": path}
        append(ev)
        item_ids.append(iid)
        if not t["subtask"]:
            last_task = iid

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(plan_capture.front_matter(date, a.slug, a.title, epic_id, item_ids))
        fh.write(draft)
    print(path)
    print(epic_id)
```

Replace the stub wiring:

```python
sub.add_parser("roadmap-render").set_defaults(fn=cmd_roadmap_render)
for name in ("sync", "status", "compact"):
    sub.add_parser(name).set_defaults(fn=stub(name))
```

and add the parser next to the others:

```python
pc = sub.add_parser("plan-capture"); pc.set_defaults(fn=cmd_plan_capture)
pc.add_argument("--slug", required=True)
pc.add_argument("--title", required=True)
pc.add_argument("--file")
pc.add_argument("--priority", default="P1", choices=["P0", "P1", "P2", "P3"])
```

- [ ] **Step 2: End-to-end smoke in a throwaway dir** (keeps demo items out of the real log)

```bash
T=$(mktemp -d) && cp -R bin "$T/" && mkdir -p "$T/.work" && cd "$T"
: > .work/todo.jsonl && : > .work/done.jsonl
cat > draft.md <<'EOF'
# Demo plan

Why we are doing this.

## Tasks

- [ ] (P1) First task
  - [ ] A subtask
- [ ] Second task
EOF
bin/worklog plan-capture --slug demo --title "Demo plan" --file draft.md
bin/worklog list
bin/worklog roadmap-render
grep "First task" docs/roadmap.md && grep "### Demo plan" docs/roadmap.md
head -8 docs/plans/*-demo.md
bin/worklog plan-capture --slug demo --title "Demo plan" --file draft.md; echo "exit=$?"
cd - >/dev/null
```

Expected: `list` shows 4 open items (epic + 2 tasks + 1 subtask); both greps match; front matter shows `items: [...]` with 3 ULIDs; the second capture fails with the invariant-15.8 message, `exit=1`.

- [ ] **Step 3: Regenerate the real roadmap and run all suites**

```bash
cd /Users/richardhightower/clients/spillwave/src/wiki_ticket_sdd
bin/worklog roadmap-render
python3 tests/test_fold.py && python3 tests/test_ulid.py && \
python3 tests/test_render_roadmap.py && python3 tests/test_plan_capture.py
```

Expected: all `OK`. (The real log was untouched, but regenerating is free and keeps the hook green.)

- [ ] **Step 4: Commit**

```bash
git add -A ':!inputs'
git commit -m "feat: worklog plan-capture — plans become tracked items (spec §18 step 4)"
```

---

### Task 7: Plan-capture skill + `ExitPlanMode` hook ("hooks, not hope")

**Files:**
- Create: `.claude/skills/plan-capture/SKILL.md`
- Create: `hooks/exit-plan-capture.sh`
- Create: `.claude/settings.json`

**Interfaces:**
- Consumes: the exact `bin/worklog plan-capture --slug … --title … --file …` invocation from Task 6.
- Produces: a skill the model can invoke on demand, plus a `PostToolUse` hook that fires on every `ExitPlanMode` and injects the capture requirement into context — the mechanism backing the CLAUDE.md policy line "Exiting plan mode is not optional bookkeeping."

- [ ] **Step 1: Write the skill**

Create `.claude/skills/plan-capture/SKILL.md`:

```markdown
---
name: plan-capture
description: Capture an approved plan as tracked work items. Use when exiting plan mode, when the user approves a plan, or says "capture this plan". Writes docs/plans/<date>-<slug>.md and appends the plan's tasks to .work/todo.jsonl via bin/worklog.
---

# Plan capture

1. Write the approved plan as markdown. It MUST contain a `## Tasks` section:

       ## Tasks

       - [ ] (P1) Task title
         - [ ] Subtask of the task above

   Priority token `(P0)`–`(P3)` optional, default P2. Prose (the *why*) goes
   in other sections and is preserved verbatim in the plan doc.

2. Save it to a temp file and run:

       bin/worklog plan-capture --slug <kebab-slug> --title "<plan title>" --file <tempfile>

3. Run `bin/worklog roadmap-render`, then commit `docs/plans/`,
   `docs/roadmap.md`, and `.work/todo.jsonl` together.

Never append to `.work/*.jsonl` directly (invariant 15.4). Never overwrite an
existing plan (invariant 15.8) — a changed design gets a NEW plan that
supersedes the old one.
```

- [ ] **Step 2: Write the hook script**

Create `hooks/exit-plan-capture.sh` (mode 755):

```bash
#!/usr/bin/env bash
# WORKLOG-SPEC section 12, "Hooks, not hope": a CLAUDE.md instruction holds
# maybe 80% of the time; this hook holds 100%. Fires after ExitPlanMode and
# puts the capture requirement in front of the model, non-optionally.
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"POLICY (worklog): a plan was just approved. Before implementing anything, capture it: save the plan markdown (with a '## Tasks' section of '- [ ] (P#) title' checkboxes; two-space indent = subtask) to a temp file, then run `bin/worklog plan-capture --slug <kebab-slug> --title '<title>' --file <tempfile>`, then `bin/worklog roadmap-render`, and commit docs/plans/, docs/roadmap.md, and .work/todo.jsonl together. See .claude/skills/plan-capture/SKILL.md."}}
EOF
```

- [ ] **Step 3: Register the hook**

Create `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/hooks/exit-plan-capture.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Verify the hook script's output is valid JSON**

```bash
chmod +x hooks/exit-plan-capture.sh
hooks/exit-plan-capture.sh | python3 -m json.tool >/dev/null && echo VALID
```

Expected: `VALID`. (The live `ExitPlanMode` firing can only be observed in a future session that uses plan mode — note that in the final report.)

- [ ] **Step 5: Commit**

```bash
git add .claude hooks/exit-plan-capture.sh
git commit -m "feat: plan-capture skill + ExitPlanMode hook (spec §12)"
```

---

## Out of scope (future plans, in spec §18 order)

- **Compaction** (`bin/compact.py` + nightly CI job) — spec §7, step 5. Needed once the log grows; not before.
- **Adapter contract + `ticket-github`** — §9, step 6. First adapter; lives outside the core.
- **Push-only sync, then pull/echo-suppression/conflicts** — §10–§11, steps 7–8. Three-phase orchestration.
- **Wiki adapter + publish** (`published.json`) — §9.2, step 9.
- **`status-report` (daily/weekly), `plan-next`** — §13.3, step 10. `timecard` blocked on spec open question 4 (hours or narrative) — a human decision, flag it when that plan is written.
- **`worklog resolve`** — referenced by the roadmap's Needs-attention hint; only meaningful once sync can produce conflicts. Ships with step 8.

## Naming note

The spec's `plan-capture` writes `docs/plans/<YYYY-MM-DD>-<slug>.md`. This plan document itself uses the session convention `<DATE>_<NAME>_plan.md` as requested; the two coexist in `docs/plans/` harmlessly. If you want one convention, say which and the other gets renamed in a follow-up.
