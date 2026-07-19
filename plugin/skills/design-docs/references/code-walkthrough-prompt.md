# Code Walkthrough Prompt

Store per the design-docs skill layout:
`docs/designs/<DATE>_<NAME>_code_walkthrough.md` (dated, frozen) or
`docs/designs/current_code_walkthrough.md` (live). Frontmatter stamped by the
skill (tag / git_hash / branch / roadmap reference / generated_at).

You are a senior engineer writing the guided tour a new team member reads on
day one — and can trust, because every claim is anchored in the actual code.

## Ground rules

- **Base the walkthrough on the actual repository contents.** Do not invent
  code, configuration, or runtime behavior. Quote source exactly, apart from
  clearly marked ellipses or redactions.
- **Use the design document as context, not as proof.** Where the code
  contradicts the design doc, the code wins and the contradiction is
  reported (see Gaps section).
- **Cite everything**: `path — function(), lines N–M` for every code
  listing and every behavioral claim.
- Call out anything that cannot be confirmed statically. Distinguish
  production code, test code, fixtures, and deprecated code.
- Never include secrets. Prefer depth on major decision points over broad
  but shallow file-by-file coverage.

## Structure

### 1. Orientation

The system in three sentences; the directory map (what lives where and
why); the one diagram that explains the architecture (Mermaid, derived from
actual imports/calls).

### 2. Execution-order tour

Walk the main flows in the order they actually execute — entry point to
exit, following real call chains. For each stop: the code (quoted), what it
receives, what it returns, what can fail, and why it is written this way.
Cover the primary user-facing flow, the write path for persistent state,
and the automation paths (hooks, CI, scheduled jobs) — whichever exist.

### 3. Load-bearing invariants

The rules the code depends on to stay correct. For each: the invariant,
where it is enforced (cited), and what breaks if it is violated.

### 4. Tests as executable specification

Highlight the tests that best prove core behavior. For each selected test:
show the relevant test code, state the rule it proves, and explain what
regression it would catch. Do not list every test.

### 5. Junior engineer orientation

- The five most important things to internalize
- Where to start debugging
- Where common changes are made
- Which files are risky to modify and why
- Which invariants must never be broken

### 6. Gaps and design drift

- Design-document claims the code does not support
- Important code behavior missing from the design doc
- Dead or apparently unused code
- Inconsistent prompts or schemas
- Missing tests
- Unclear ownership or duplicated logic

Clearly distinguish confirmed facts from reasonable inferences.

## Final quality check

- Every major flow is walked in execution order with real citations.
- Important code is shown, not merely described.
- The document explains why, not just what.
- Boilerplate omitted; ellipses hide nothing load-bearing.
- Diagrams match the implementation.
- A junior engineer can navigate the codebase from this document alone.
- Drift and uncertainty are explicitly identified.
