---
name: plan-next
description: Decide what to work on next — use when asked "what should we do next", "what's most important", or when planning a new work session.
version: 0.12.1
---

# Plan next

READ-ONLY skill: it never changes state (spec 17, open question 1).

1. Run `bin/worklog fold` to get the full item state as JSON.
2. Filter to open items (status `todo`, `in_progress`, or `blocked`) whose
   `depends_on` items are all closed.
3. Rank: priority first (P0 before P1 before P2 before P3), then group by
   parent epic, then creation order (ULID string order).
4. Present the top 3–5 candidates with a one-line rationale each. Note
   anything blocked and name what blocks it.

Do NOT mark items `in_progress` from this skill — starting work is
`work-track`'s job.
