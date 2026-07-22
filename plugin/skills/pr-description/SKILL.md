---
name: pr-description
description: Write a high-context PR description for any substantial PR. Use whenever creating or editing a pull request body — the description must let a reader with zero prior context understand what is being built, why, where it sits in the larger system, and exactly what changed, without digging through tickets or code.
version: 0.12.1
---

# High-quality PR descriptions

A PR description is a durable design record, useful long after the merge.
Write for a smart colleague who has never seen this part of the system.
Trivial PRs (typo, one-line fix) may use a short body; everything else
follows this structure.

## Structure

### 1. Title
Clear, specific, ticket-linked: `#98: ia-render — reader plane write path`.

### 2. The big picture (what we're building, where this PR fits)
Product context in plain language: the platform, the epic/capability this
belongs to, the epic broken into a numbered pipeline with **this PR marked**:

    Step 1: ...
    Step 2: ...
    Step 3: ...   <== THIS PR
    Step 4: ...

Define domain terms on first use (fold, ledger, sidecar, MCP, ...).

### 3. Who actually calls this? / runtime context
The real caller and execution model: human + AI assistant, background job,
hook, webhook, UI? What surrounding system runs it? Does anything run
automatically or is confirmation gated? Security/permission notes (e.g.
"forwards the user's real token").

### 4. The problem this PR solves
Concrete, numbered pain points that exist today. Why the naive approach
fails and what correct behavior must be. The reader should feel the pain
the PR eliminates.

### 5. What this PR actually does (scope)
The ticket's exact ask, then confirmation the PR delivers precisely that.
Explicit in-scope / out-of-scope boundaries.

### 6. What exactly was added / changed
File by file (or component by component): path, what it contains, why it
was designed that way (especially non-obvious decisions), implementation
constraints (framework-free, no schema drift, deterministic output, ...).
Describe new tools/prompts/schemas clearly.

### 7. The sequence / flow the code enforces
For multi-step processes (especially ones an AI must follow): exact ordered
steps, decision points, confirmation gates, error handling, and explicit
"never do X" rules.

### 8. How it was tested
Honest and specific: unit tests (count + coverage), how they were run,
smoke tests, what was NOT tested and why (and when it will be), CI status.

### 9. Deliberately out of scope
What a reader might expect but is intentionally left for later tickets.
Prevents scope-creep comments; shows intentional design.

### 10. Ticket glossary (recommended)
Every ticket mentioned, one line each, current status:

    | Ticket | What it is                             | Status      |
    |--------|----------------------------------------|-------------|
    | #91    | Epic: IA & content model               | In progress |
    | #98    | This PR                                | In progress |

## Style rules

- Plain language over jargon; define terms on first use.
- Short paragraphs, numbered/bulleted lists.
- Make the "why" as clear as the "what".
- Be precise about what this PR does NOT do.
- Professional, direct, slightly pedagogical tone.
- Call out non-obvious backend behaviors and traps explicitly so future
  agents and humans don't rediscover them the hard way.
- Keep the repo's standard PR footer (generated-with attribution) intact.

## Checklist before submitting

- [ ] A new reader can understand the product context and where this PR sits
- [ ] The exact problem being solved is clear
- [ ] The runtime caller and permissions model are stated
- [ ] What was added is described concretely (files + responsibilities)
- [ ] Any multi-step sequence is written out in order
- [ ] Testing is honest about coverage and gaps
- [ ] Out-of-scope items are listed
- [ ] All referenced tickets appear in a glossary table
