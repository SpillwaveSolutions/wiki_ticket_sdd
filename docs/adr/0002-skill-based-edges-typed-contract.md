---
id: 2
slug: skill-based-edges-typed-contract
title: Edge integration as skills, hardened by a typed adapter contract
date: 2026-07-19
status: accepted
deciders: [rick, claude]
tags: [sync, adapters]
supersedes: null
superseded_by: null
wiki_key: adr/0002-skill-based-edges-typed-contract
truth_state: current
---

## Context

The 1.2 spec designed per-system adapter binaries: `ticket-<system> push`, a
capabilities handshake, an exit-code table. None of it shipped. Writing,
testing, and maintaining an executable per tracker means re-encoding
knowledge the model already has — an LLM has absorbed the docs, CLIs, and
years of answers for GitHub Issues, Jira, ADO, GitLab, Confluence — and then
chasing remote API drift forever. The question was where the boundary
between model-driven integration and shipped code should sit.

## Decision

Recorded as the arc it actually was, because the middle step matters:

1. **v1.4 moved the edges to skills.** Prose tells the model to read
   `.work/config.yml`, use whatever tooling the team has (`gh`, `glab`,
   `az`, an MCP server), and research gaps instead of guessing. Shipped
   per-system integrations are dead weight; per-system work is model work.
2. **Three invariants regressed to prose**: idempotency
   (search-before-create), pull parsing (the fields that seed the
   deterministic `ev`), and capability degradation. Prose-enforced meant
   regression-prone — exactly the failure the adapter design had prevented.
3. **v1.6 landed the hybrid** (plan 2026-07-18-typed-adapter-contract, spec
   §9.5): a typed dispatcher (`bin/sync_dispatch.py`) owns every invariant
   in code — the capabilities gate that rejects a subtly wrong adapter at a
   typed boundary, ULID-marker idempotency, canonical-hash skip, echo
   suppression, conflicts — while adapters stay AI-generated dumb
   translators between canonical JSON and the platform. A shipped fake
   adapter, backed by a local JSON file, makes all three invariants
   CI-testable with no network. Skills orchestrate; the dispatcher enforces.

## Consequences

- Zero per-system maintenance in the core: swapping trackers is a config
  edit, and a new platform is a generated adapter plus `adapter check`, not
  a hand-written binary.
- The invariants that regressed under pure prose are regression-tested
  against the fake adapter in CI, without any network or live tracker.
- The dumbness rule keeps the boundary honest: if idempotency or hashing
  logic leaks into an adapter, tests fail — the dispatcher is the only place
  that knows the sync rules.
- The cost is a second layer to explain: skill → dispatcher → adapter →
  platform CLI, versus "the model just does it."

## Alternatives

- **Maintained per-system adapter binaries** (the 1.2 design) — rejected:
  permanent maintenance burden re-encoding model knowledge; never shipped.
- **Pure-prose skills with no typed layer** — tried (v1.4/v0.5); the three
  invariants above regressed from code-enforced to hopefully-followed, which
  is what forced the hybrid.
