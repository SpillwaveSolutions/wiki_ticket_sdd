---
date: 2026-07-18
slug: work-taxonomy
title: Work Taxonomy + Flag-Gated Classifier
epic: 01KXV61H5BDS7TD99H0FF9FE11
items: [01KXV61H5BDS7TD99H0FF9FE11]
status: planned — not yet scheduled; implementation tasks attach to the epic when work starts
origin: authored by Rick with the claude.ai design session, stored verbatim
merged_in: 0a15e5cebfc5b381f4156c8c14cb39ca54031aa8
---

# Spec: Work Taxonomy + Flag-Gated Classifier

**Target repo:** `SpillwaveSolutions/wiki_ticket_sdd` (at/after `v0.5.0`)
**Deliverable:** a four-axis work taxonomy taught to the model via a permissioned `CLAUDE.md` block (always on, zero runtime cost), plus an opt-in classifier hook that stages item *suggestions* (off by default).
**Audience:** Claude Code, implementing in the repo. And a human reviewer.

This is independent of the adapter-contract work — it touches the schema, `CLAUDE.md`, config, and hooks, not sync. It can land before or after that spec.

---

## 0. Read first

- `.work/config.yml` — the `sync:` / `status:` blocks; the new `classifier:` block slots beside them.
- `CLAUDE.md` and its `AGENTS.md` symlink — the taxonomy block appends here.
- `bin/fold.py` — the canonical item shape; `type` becomes two fields (`level`, `kind`).
- `.work/schema/*` — item schema to extend.
- `.claude/hooks/stop-worklog-check.sh` — the classifier graduates this existing hook; do not add a second Stop hook.
- `.claude/skills/plan-capture/`, `work-track/` — where `create` events originate; they set `level`/`kind`.
- `docs/worklog-spec.md` §5 (data model), §7 (fold).

**Do not** change `ulid.py`, the event-log append semantics, or the fold's dedupe/sort. This is a field-model + policy + optional-hook change.

---

## 1. The model: four orthogonal axes

The core mistake to avoid is collapsing *how big* and *what kind* into one enum (v0.5's `type`). Split them. Four axes that do not interfere:

| Axis | Field | Values | What it answers |
|---|---|---|---|
| **Level** | `level` | `epic` / `story` / `task` / `subtask` | Size & place in the parent tree (decomposition) |
| **Kind** | `kind` | `feature` / `bug` / `ops` / `triage` | Nature of the work |
| **Milestone** | `milestone` | free string (`v0.6.0`) or null | What ships together (the release axis) |
| **Planned** | `unplanned` + `discovered_during` | bool + ULID | Deliberate vs discovered (already in schema) |

### 1.1 Level is pure decomposition

`epic → story → task → subtask`, each a level down via `parent`. Unchanged from today except that it no longer also encodes kind. A leaf is a task or subtask; a bug is **not** a level.

### 1.2 Kind is nature-of-work, defined against `feature`

- **`feature`** — delivers user-facing value. The **default kind**. Bug and ops are defined by contrast with it.
- **`bug`** — a defect: something that should already work. Leaf-level, sibling to task. **Not necessarily under any epic** (`parent` optional for bugs).
- **`ops`** — operations / maintenance / toil: upgrades, patching, release-engineering, chores that keep the lights on. A real destination you want to **shrink by automating**. Trends down over time.
- **`triage`** — **unclassified.** The default when an item is created without a deliberate kind. Not a guess — an explicit "not sorted yet." Shows up in a needs-classification view. Shrinks by **classifying**, not automating. Distinct from `ops`: `ops` is toil you reduce; `triage` is a waiting room you empty.

### 1.3 Milestone is the release axis (cross-cutting)

A release is not a level or a kind — it's a *set of items that ship together* (Jira `fixVersion`, GitHub milestone, git tag). It cross-cuts the tree: one milestone holds stories and bugs of several kinds. Model it as a `milestone` field; a "release" is just the query `milestone == v0.6.0`. Release-*engineering* work (cut build, run checklist) is `kind:ops` tasks carrying that milestone — no new tier needed. Wire to the existing `release` skill and release-notes wiki page; do not invent a release object.

### 1.4 Default workflow = normal agile + Confluence

The defaults encode the most common flow without railroading:
- Epics decompose into stories into tasks; leaves carry a `kind`.
- Milestones group across the tree.
- Docs: epics and plans get wiki pages; releases get release-notes pages (existing `wiki-publish`).

The **axes** are fixed; the **vocabulary** may flex later (an ADO shop renaming, a SAFe shop adding a tier) without changing the model. That is the "generic but not useless" line — fix the shape, not the words. Alternate workflows are a later concern; ship the agile/Confluence default now.

---

## 2. Axis rules (the defaults — write these into the schema AND the CLAUDE.md block)

These are the locked defaults. They are what the validator enforces and what the model is taught.

1. **Kind is free at `story` / `task` / `subtask`.** Any of feature/bug/ops/triage.
2. **Epics are `feature` or `ops` only.** A bug is never epic-sized; an epic-level defect is a category error. Validator rejects `level:epic, kind:bug|triage`.
3. **`kind` defaults to `triage`** when a `create` event omits it. Never silently default to `feature` — an unclassified item must *look* unclassified.
4. **`bug.parent` is optional.** Bugs may float free of any epic. Every other level keeps its usual parent expectations (subtask needs a parent; epic has none).
5. **`milestone` lives on leaves (story and below).** An epic's target release is *derived* from its children, not set directly. Rationale: fixVersion is per-story in practice; a directly-set epic milestone drifts from what its stories actually carry. (If a later batch wants epic-level target milestones, that's a new field `target_milestone`, not an overload of `milestone`.)
6. **`triage` and `ops` are both "reduce over time" but for different reasons** — surface both in the roadmap so the trend is visible (see §5).

---

## 3. Schema & fold changes

### 3.1 Item fields

- Replace single `type` with **`level`** (`epic|story|task|subtask`) and **`kind`** (`feature|bug|ops|triage`).
- Add **`milestone`** (string|null).
- Keep `unplanned` / `discovered_during` as-is.

### 3.2 Migration

- A migration step maps old `type` → (`level`,`kind`): `epic→(epic,feature)`, `story→(story,feature)`, `task→(task,feature)`, `subtask→(subtask,feature)`, `bug→(task,bug)`. Emit it as a `snapshot`-free, one-time transform documented in `docs/migrations/` — but since the log is append-only, prefer a **compaction-time rewrite** (main-branch, CI-only, `fold(new)==fold(old)` modulo the field split) rather than rewriting history ad hoc. If that's too heavy for one release, accept `type` as a deprecated alias the fold reads and normalizes into (`level`,`kind`) on load, and drop it at the next compaction.
- The fold's `create` handler sets `kind:triage` when absent (§2.3) and validates §2.1/§2.2.

### 3.3 Validator

Extend the schema check (pre-commit + CI) to enforce §2.1–§2.5. A violating event fails the commit with a message naming the bad `level`/`kind` pair.

### 3.4 Ticket mapping

`kind` → platform label/type is the adapter's job (see adapter-contract spec §3.1 `capabilities.types`): `kind:bug`→bug label/Bug issue-type, `ops`→maintenance label, `triage`→needs-triage label, `feature`→default. `milestone` → GitHub milestone / Jira fixVersion. This spec only defines the fields; mapping stays in the edge.

---

## 4. Always-on path: the `CLAUDE.md` taxonomy block

**Cost: zero at runtime.** This is documentation the model reads like any other policy. It teaches the four axes and *inline proposal* behavior. No hook, no subagent.

### 4.1 Written at setup, with permission, idempotently

`/worklog:init` (or a new `worklog taxonomy install` step):

1. Show the block to the user.
2. Ask yes/no to append it to `CLAUDE.md`.
3. On yes, write **between markers** so re-running updates in place, never duplicates:
   ```
   <!-- worklog:taxonomy:start -->
   ...block...
   <!-- worklog:taxonomy:end -->
   ```
4. Because `AGENTS.md` is the symlink to `CLAUDE.md`, Codex/Grok/OpenCode inherit it for free — no second write.

This honors "nothing enters without intent": the model's own operating instructions are not silently rewritten. Same marker discipline the roadmap uses.

### 4.2 What the block says (policy, not code)

- The four axes (§1) and the rules (§2), in prose the model applies.
- **Inline proposal instruction:** when trackable work surfaces in conversation, propose an item as part of the normal response — "want me to file this? `level:story kind:feature parent:auth-epic milestone:v0.6.0`" — and only create it on the user's assent (or per existing `push_on_capture` policy). The model already has full conversation context, so these proposals are high quality and cost nothing extra.
- **When unsure, propose `kind:triage`** with the open question stated, rather than guessing a kind. Triage is the honest default.
- Pointers to `work-track` / `plan-capture` skills for the actual `create`.

The inline path is the 90% path. It is *better* than the classifier because it runs with the whole conversation in context, not a re-derived transcript span.

---

## 5. Roadmap surfacing

`render_roadmap.py` gains:
- A **Needs classification** section: all `kind:triage` items. This is the queue humans (or the classifier) empty. Its size is the health metric — it should trend to zero.
- **Kind mix** per epic/milestone: feature/bug/ops/triage counts, so "bug ratio" and "ops load trending down" are visible without a query. These are the two metrics the taxonomy exists to expose.
- Milestone grouping: items under each `milestone`, with epics showing their *derived* milestone (from children, §2.5).

CI hash-checks the roadmap as today; no new parser (roadmap stays read-only/generated).

---

## 6. Opt-in path: the classifier (OFF by default)

For teams where work escapes the log despite the inline path. **Dormant until flagged on.**

### 6.1 Config

```yaml
# .work/config.yml  (new block, beside sync:/status:)
classifier:
  enabled: false             # OFF by default. Inline CLAUDE.md path handles the common case.
  min_confidence: 0.7        # below this, propose kind:triage + open question, never a confident kind
  debounce: stop             # fire on the Stop hook (end of response), not per user message
```

### 6.2 Trigger — graduate the existing Stop hook

Extend `.claude/hooks/stop-worklog-check.sh` (do **not** add a second Stop hook). When `classifier.enabled`:

1. **Cheap gate (no model call):** is there plausibly trackable work in this exchange, and does an item already exist for it? Check against the current fold **and** existing `.work/suggestions.jsonl` to dedupe. No → stop, zero cost.
2. **On a pass:** spin an async subagent to analyze the span and *propose* an item.

When `enabled:false`, the hook keeps its current v0.5 behavior (reminder only) — this is purely additive.

### 6.3 Propose, don't dispose — the load-bearing rule

The subagent **never writes to the event log** and **never asks the user** (it can't block). It writes a suggestion to a staging file:

```
.work/suggestions.jsonl   (gitignored, per-clone, append-only)
```

Each record:
```json
{
  "suggestion_id": "01J...",
  "source_span": "<turn or transcript ref>",
  "proposed": {"level": "task", "kind": "feature", "parent": "01J...", "milestone": "v0.6.0", "title": "..."},
  "confidence": 0.82,
  "open_questions": ["is this under the auth epic or its own story?"],
  "dedupe_against": ["01J...existing items checked"]
}
```

- `confidence < min_confidence` → `proposed.kind` MUST be `triage` and the uncertainty goes in `open_questions`. No confident guess on a load-bearing field.
- The **main** Claude, next turn, reads staging: high-confidence → offer to promote (one `create` event); low-confidence → surface via `ask_user`. The subagent gathers and proposes; the main loop, which can talk to the human, disposes. That division is why an async worker that can't block still works.

### 6.4 Promotion

A suggestion becomes real only when the main Claude or the human promotes it into a `create` event (via `work-track`). Promotion may carry a provenance note linking back to `source_span` (optional; default clean entry). Promoted or rejected suggestions are marked consumed so the gate in §6.2 dedupes against them.

### 6.5 Why gated

Classifying every round is expensive and, worse, noisy — it re-recommends the same task and erodes trust in the log. The inline path already covers the common case for free with better context. So the classifier is for the specific "work keeps escaping" problem and stays off until someone opts in. Document it in the block as exactly that.

---

## 7. Files

**Change**
```
bin/fold.py                         # type → level+kind; default kind:triage; validate §2
.work/schema/*                      # level, kind, milestone; §2 rules
.work/config.yml                    # new classifier: block
bin/render_roadmap.py               # Needs-classification, kind-mix, milestone grouping
.claude/hooks/stop-worklog-check.sh # graduate: gate + subagent when classifier.enabled
.claude/skills/work-track/          # set level/kind/milestone on create
.claude/skills/plan-capture/        # emit level/kind on captured items
hooks/pre-commit + CI schema check  # enforce §2
```

**Add**
```
CLAUDE.md taxonomy block            # between worklog:taxonomy markers (written at setup)
docs/migrations/000N-type-split.md  # the type → level+kind migration note
.work/suggestions.jsonl             # gitignored; created on first classifier run
.claude/skills/classify/ (or subagent prompt)  # the flag-gated proposer
tests/test_taxonomy.py              # §2 rules, default triage, migration mapping
tests/test_classifier.py            # staging-only, never-writes-log, confidence→triage, dedupe
```

`.gitignore`: add `.work/suggestions.jsonl`.

---

## 8. Tests (definition of done)

1. `create` with no kind → `kind:triage` (§2.3).
2. `level:epic, kind:bug` → validator rejects (§2.2).
3. `level:task, kind:bug, parent:null` → valid (§2.4).
4. `milestone` set on an epic directly → rejected; epic milestone derives from children (§2.5).
5. Old `type` values migrate to the correct (`level`,`kind`) pairs (§3.2).
6. Roadmap renders Needs-classification + kind-mix + milestone groups; CI hash-check passes.
7. Setup writes the taxonomy block between markers; re-running updates in place, no duplicate.
8. Classifier **off** by default: Stop hook behaves as v0.5 (reminder only).
9. Classifier **on**: writes only to `.work/suggestions.jsonl`, never to `todo.jsonl`; `confidence < min_confidence` ⇒ `kind:triage` + open question; dedupes against fold and prior suggestions.
10. A promoted suggestion produces exactly one `create` event and is marked consumed.

---

## 9. Non-goals

- Not supporting alternate workflows (ADO Feature tier, SAFe) yet — ship the agile/Confluence default; keep axes stable so they can be added by vocabulary later.
- Not making the classifier on-by-default or per-turn. Inline CLAUDE.md path is the default; classifier is the gated escape hatch.
- Not letting the classifier write the log or ask the user. Propose-only, staging-only.
- Not changing ulid/fold dedupe/append semantics.
- Not building a release *object* — a release is `milestone ==` a query plus the existing release skill.
