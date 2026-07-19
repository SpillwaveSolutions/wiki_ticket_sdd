---
name: classify
description: Propose work items from recent conversation (flag-gated classifier). Use when the Stop hook requests classification or when asked to sweep a conversation for untracked work. Propose-only: writes .work/suggestions.jsonl, never the event log.
version: 0.7.0
---

# Classify — propose work items from conversation

Flag-gated (spec §6): meaningful only when `classifier.enabled: true` in
`.work/config.yml`. Propose, don't dispose — suggestions go to
`.work/suggestions.jsonl` (gitignored, per-clone, append-only); nothing enters
the event log until the main loop or the human promotes.

## 1. Spawn ONE background subagent

Spawn a single background subagent (never more than one) with this prompt:

> Analyze the recent exchange for trackable work that has no work item yet.
> For each plausible item, append ONE JSON line to `.work/suggestions.jsonl`:
>
>     {"suggestion_id": "<ULID>", "source_span": "<turn or transcript ref>",
>      "proposed": {"level": "task", "kind": "feature", "parent": null,
>                   "milestone": null, "title": "..."},
>      "confidence": 0.82,
>      "open_questions": [], "dedupe_against": ["<item ULIDs checked>"]}
>
> - Mint each `suggestion_id` fresh:
>   `python3 -c "import sys; sys.path.insert(0,'bin'); import ulid; print(ulid.new())"`
> - Dedupe FIRST: check the current `bin/worklog fold` titles AND prior
>   unconsumed suggestions already in `.work/suggestions.jsonl`. Never
>   re-propose an item that exists or was already suggested; record what you
>   checked in `dedupe_against`.
> - Read `classifier.min_confidence` from `.work/config.yml` (default 0.7).
>   If confidence < min_confidence, `proposed.kind` MUST be `"triage"` and the
>   doubt goes in `open_questions` — never a confident guess on a load-bearing
>   field.
> - NEVER append to `.work/todo.jsonl`, `.work/done.jsonl`, or any event log.
>   Suggestions only.
> - NEVER ask the user anything — you cannot block. Write suggestions and exit.

## 2. Dispose next turn (main loop)

Next turn, read `.work/suggestions.jsonl`, skipping records already marked
consumed:

- High-confidence suggestions: offer them for promotion —
  `bin/worklog promote <suggestion-id>` creates the real item.
- Low-confidence (`kind:triage`) suggestions: surface their `open_questions`
  to the user as questions, not items.
- Rejected suggestions: mark consumed by appending
  `{"consumed": true, "suggestion_id": "..."}` to `.work/suggestions.jsonl`.

The subagent gathers and proposes; the main loop, which can talk to the human,
disposes.
