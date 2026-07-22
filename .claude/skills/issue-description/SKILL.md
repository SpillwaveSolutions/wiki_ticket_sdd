---
name: issue-description
description: Write rich, durable issue/ticket descriptions. Use when creating or updating tickets by hand, when composing bodies for ticket-sync, or when a work item needs a description a future reader (human or agent) can act on without archaeology.
---

# Rich issue descriptions

An issue is a durable intent record, not a task title. Issues outlive PRs
and are read by more people — including future agents. Every issue should
let a zero-context reader understand what, why, where it sits, and what
"done" looks like.

## The mechanical path (worklog-synced tickets)

For items in the event log, do not hand-write bodies:
`bin/worklog ticket-body <ulid>` renders the item's graph node — summary
(from `--body`), context (epic, generating plan with its frozen wiki page,
milestone, unplanned provenance), and traceability (decides/implements
edges, delivered-by PRs). ticket-sync pushes that. To make a ticket richer,
enrich the SOURCE: `worklog update --body`, `worklog link-pr`, sidecar
`relates_to` edges — never just the remote ticket (it would drift back).

## Template (hand-written issues, or systems without worklog)

    ## Summary
    One or two sentences: what needs to be done and why it matters.

    ## Context / Big picture
    Where this sits in the larger system or epic. Link the parent epic and
    the plan that generated it.

    ## Problem / Motivation
    What is painful or missing today? "What"-only issues rot; "why" keeps
    them useful.

    ## Desired outcome
    What does done look like? Concrete and observable.

    ## Scope
    In scope: ...
    Explicitly out of scope: ...

    ## Proposed approach (optional)
    High-level design or sequence if known. Link relevant ADRs/design docs.

    ## Acceptance criteria
    - [ ] ...

    ## Traceability
    Plan / Epic / ADRs / Spec sections / Related issues.

    ## Notes for implementers & agents
    Traps, sequencing rules, non-obvious constraints, "never do X" guidance
    written for the next agent that picks this up.

## Rules

- Omit sections that have no real content — no boilerplate placeholders.
- Every plan-generated issue links back to its frozen plan page: the why
  lives in the plan, the issue carries the pointer.
- Surface risks and open questions early; uncertainty stated is uncertainty
  managed.
- Body text must be readable by a junior dev or PM: no bare ULIDs in prose
  (spec §13.4); ULIDs belong in the machine footer.
