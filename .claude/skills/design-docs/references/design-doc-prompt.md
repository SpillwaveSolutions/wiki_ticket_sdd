# Design Document Prompt

Store the document per the design-docs skill layout:
`docs/designs/<DATE>_<NAME>_design_doc.md` (dated, frozen) or
`docs/designs/current_design_doc.md` (live). Frontmatter is required and is
stamped by the skill (tag / git_hash / branch / roadmap reference / generated_at
for the live copy) — a reader must be able to tell exactly which commit the
document describes.

You are a senior software architect and technical documentation specialist.

Create a comprehensive software design document for the system in this
repository. The document must be understandable to both:

- Junior software developers who need implementation-level guidance
- Project managers who need to understand scope, dependencies, risks, and
  system behavior

## How to apply this template

- **The section list is a menu, not a quota.** Include only sections whose
  subject actually exists in the analyzed system. Close the document with an
  "Omitted sections" list naming each skipped section with one line of reason
  ("no message queue exists", "no external AI provider"). An honest omission
  beats a page of N/A.
- **The repository is the source of truth.** Fill System Context and Source
  Material from the repo itself: README, specs, docs/plans/, docs/adr/,
  configuration files, schemas, and the test suites. Do not wait for inserts.
- **Never invent.** Base every claim on actual repository contents. Quote
  source exactly (clearly marked ellipses allowed). Label everything that is
  not confirmed: **Confirmed** / **Assumption** / **Recommendation** /
  **Open Question**.
- **Cite every code claim**: repository-relative path, class/function/method,
  line numbers when available — `src/refunds/policy.py —
  evaluate_refund_request(), lines 42–87`.
- Distinguish production code, test code, fixtures, and deprecated code.
  Never include secrets or real credentials.
- Prefer depth on major decision points over broad but shallow file-by-file
  coverage. Omit boilerplate; document trivial getters/setters/generated code
  only when they contain business behavior.

## System Context

Describe the product, business problem, users, major workflows, existing
systems, and technical constraints — derived from the repo per the rules
above.

## Primary Objective

Produce a design document that explains:

1. What the system does
2. Why the architecture is designed this way
3. How the major components interact
4. How data moves through the system
5. How complex business logic behaves
6. How each module, package, and important class should be implemented
7. How the system integrates with databases, caches, MCP servers, AI
   endpoints, managed AI platforms, and other external services
8. What a developer must know before modifying or extending the system

## Documentation Style

Write in clear, direct language. For each technical concept:

- Explain it first in plain language, then provide the technical detail
- Define acronyms on first use
- Explain why each important design decision was made
- Include examples for complex workflows
- Distinguish confirmed facts, assumptions, recommendations, and open
  questions

Avoid vague statements such as "the service handles the request." Explain
which service, which method or component, what data it receives, what it
returns, and what can fail.

## Required Document Structure

(Apply the menu rule above; numbering stays stable so omissions are visible.)

# 1. Document Overview

Purpose, intended audience, scope, out-of-scope items, related documents,
definitions and acronyms, assumptions, open questions.

# 2. Executive Summary

Non-technical: business purpose, main user workflows, major system
components, external dependencies, key architectural decisions, primary
risks.

# 3. Requirements Summary

Functional, non-functional, performance, availability, scalability,
security, compliance, observability, data retention, disaster recovery.
Include a requirements traceability table mapping each requirement to the
relevant architecture component or module.

# 4. System Context

Actors, users, external systems, trust boundaries, upstream and downstream
dependencies, major inputs and outputs. Mermaid system context diagram.

# 5. High-Level Architecture

The overall architecture: client applications, API layer, application
services, domain logic, background workers, event processing, databases,
caches, queues/event buses, file/object storage, AI services, MCP servers,
managed AI platforms, third-party integrations, monitoring/logging,
deployment environment — whichever exist.

Mermaid diagrams for: logical architecture, runtime architecture,
deployment architecture, data flow, trust boundaries. Each diagram gets a
short explanation of how to read it.

# 6. Architectural Decisions

For every major decision: decision, context, alternatives considered,
selected option, rationale, benefits, tradeoffs, risks, consequences,
conditions that would justify revisiting. Cover (where applicable):
monolith vs microservices, sync vs async, REST vs GraphQL vs messaging,
SQL vs NoSQL, cache strategy, AI provider and model selection, MCP server
responsibilities, authn/authz model, deployment strategy, error-handling
strategy. Where the repo keeps ADRs (docs/adr/), reference them instead of
restating — this section summarizes and links.

# 7. Component Inventory

Table: component name, type, responsibility, owner, inputs, outputs,
dependencies, data stores, external integrations, scaling model, failure
impact, relevant requirements.

# 8. End-to-End Workflows

Every major business workflow: trigger, preconditions, main flow,
alternative flows, failure flows, retry behavior, timeout behavior,
idempotency, state changes, data written, events emitted, external systems
called, security checks, observability signals. Mermaid activity diagram
and sequence diagram for each significant workflow.

# 9. Complex Business Logic

For processes with multiple states, conditional branches, validation
rules, approval steps, retries, time-based transitions, human
intervention, external dependencies, partial failures, or compensation
logic: plain-language explanation, formal business rules, decision table,
state transition table, Mermaid state diagram, Mermaid activity diagram,
pseudocode, edge cases, invalid transitions, recovery behavior, audit
requirements.

# 10. Domain Model

Core business entities, value objects, aggregates, relationships,
ownership boundaries, invariants, lifecycle rules. Mermaid class diagram,
entity relationship diagram, domain relationship table. Per entity:
purpose, important fields, validation rules, lifecycle, allowed
operations, persistence model, events produced, security considerations.

# 11. Module-by-Module Design

Per application module: name, purpose, business responsibility, public
interface, internal responsibilities, inputs, outputs, dependencies, data
access, external integrations, configuration, error handling, logging,
metrics, testing strategy, known risks, extension points. Mermaid
component diagram of module dependencies. Also identify: circular
dependencies, excessive coupling, shared utility risks, boundary
violations, recommended refactoring opportunities.

# 12. Package-by-Package Design

Per package/namespace: name, purpose, contained modules, public vs
internal-only classes and functions, dependencies, allowed import
directions, prohibited dependencies, shared models, exceptions,
configuration objects, test packages. Dependency table and Mermaid package
dependency diagram.

# 13. Class-by-Class Design

For every important class, interface, service, controller, repository,
handler, adapter, client, worker, or domain object: fully qualified name,
responsibility, why it exists, interfaces implemented, parent classes,
constructor dependencies, public methods, important private methods,
input/output types, state managed, concurrency considerations, exceptions
raised, database/cache interactions, external API calls, events emitted,
logging and metrics, unit-test expectations, mocking boundaries, example
usage.

Per public method: signature, purpose, parameters, return value,
preconditions, postconditions, side effects, exceptions, transaction
boundaries, retry behavior, idempotency guarantees, authorization
requirements. Mermaid class diagrams for complex or highly connected
groups.

# 14. API Design

Per endpoint (or CLI subcommand, where the CLI is the API): method/name,
path, purpose, authentication, authorization, request
headers/body/parameters, response body, status/exit codes, validation
rules, rate limits, idempotency, timeout behavior, error format, example
request and response, downstream dependencies, database operations, events
emitted. Sequence diagrams for important calls. Versioning, backward
compatibility, pagination, filtering, deprecation policies.

# 15. Database Design

Per database (or persistent store — an event log counts): type, purpose,
ownership, connection strategy, schema organization, transaction model,
isolation requirements, indexing, partitioning/sharding, replication,
backup and recovery, migration strategy, retention, encryption, access
control. Per table/collection (or record type): name, purpose, fields,
data types, keys, indexes, constraints, defaults, ownership, read/write
patterns, retention, sensitive-data classification. Mermaid ER diagram,
data lifecycle diagram, transaction sequence diagrams for complex writes.
Explain: duplicate prevention, concurrent updates, failed-transaction
recovery, safe schema migration, eventual-consistency management.

# 16. Cache Design

**For each cache actually present** (Redis is the canonical example — apply
the checklist to whatever the system uses; omit the section if nothing
caches): why it is used, key naming conventions, data structures, cacheable
vs non-cacheable data, TTL rules, invalidation strategy, read/write-through
behavior, distributed locking, rate limiting, session storage, pub/sub or
stream usage, failure and fallback behavior, memory limits, eviction
policy, hot-key risks, stampede prevention, serialization format, security
controls. Example keys and lifecycles. Sequence diagram: hit, miss,
invalidation, cache-down.

# 17. MCP Server Integration

Per Model Context Protocol server: name, purpose, ownership, tools,
resources, prompts/capabilities, authentication, authorization boundaries,
connection lifecycle, request/response format, timeout and retry rules,
rate limits, error handling, logging, data-exposure risks, prompt-injection
risks, tool approval requirements, fallback behavior, health checks.
Sequence diagrams: client-to-MCP, AI tool invocation, request processing,
success, timeout, permission failure, partial failure. Clearly show which
system validates MCP outputs before use.

# 18. AI Endpoint Design

Per AI endpoint or model integration: provider, model and version, purpose,
input structure, system-prompt responsibility, user-content handling,
context construction, retrieval, tool use, output schema,
structured-output validation, generation settings, token limits, timeout,
retry, cost controls, rate limits, guardrails, safety checks, privacy
controls, logging policy, evaluation strategy, fallback model, human
review requirements. Explain handling of: hallucinations, prompt
injection, sensitive data, invalid structured output, model
unavailability, latency, token overflow, tool-call failures,
non-determinism, provider changes. Sequence diagram of the full request
lifecycle.

# 19. Managed AI Platform Integration

**For each managed AI platform actually present** (Amazon Bedrock is the
canonical example — apply to Vertex, Azure OpenAI, etc.; omit if none):
account/environment boundaries, region, models, access configuration,
inference profiles, runtime API usage, streaming, guardrails, knowledge
bases, agents, prompt management, model evaluation, IAM roles/policies,
network endpoints, encryption, logging, cost monitoring, throttling, retry
and backoff, quotas, fallback, multi-region considerations. Sequence
diagrams: standard inference, streaming, retrieval-augmented, tool use,
failure and fallback. Identify where prompts, retrieved context, generated
content, and audit logs are stored.

# 20. External Service Integrations

Per external service: purpose, protocol, authentication, request/response
formats, timeouts, retries, circuit breaker, rate limits, idempotency,
data mapping, error mapping, monitoring, failure impact, fallback,
sandbox/test support. Sequence diagram per business-critical integration.

# 21. Event-Driven and Asynchronous Processing

Events, producers, consumers, topics/queues, schemas, ordering, delivery
guarantees, deduplication, idempotent consumption, retry queues,
dead-letter queues, poison messages, replay, event versioning, monitoring,
backpressure. Mermaid event-flow diagram, producer-consumer sequence
diagram, retry/dead-letter activity diagram.

# 22. Security Design

Authentication, authorization, RBAC/ABAC, service-to-service auth, secret
management, key rotation, encryption in transit and at rest, sensitive
data handling, tenant isolation, input validation, output encoding, audit
logging, threat boundaries, AI-specific threats, MCP-specific threats,
store access controls, platform IAM controls, supply-chain risks.
Trust-boundary diagram, authentication sequence diagram, authorization
decision flow, threat model table. Per threat: threat, affected component,
likelihood, impact, mitigation, residual risk, detection method.

# 23. Error Handling and Resilience

Error taxonomy: domain, validation, infrastructure, external-dependency,
AI-model errors; retryable vs non-retryable; user-facing vs diagnostic
messages; correlation IDs; timeout policies; retry policies with backoff;
circuit breakers; bulkheads; graceful degradation; compensation logic.
Activity diagram of system-wide error handling.

# 24. Performance and Scalability

Expected and peak load, request and data volume, concurrency, latency and
throughput targets, inference latency, cache effectiveness, database
bottlenecks, scaling units, horizontal/vertical scaling, connection
pooling, rate limiting, load shedding, backpressure, capacity assumptions.
Likely bottlenecks with mitigations.

# 25. Observability

Logging standards and levels, structured log schema, correlation IDs,
trace propagation, metrics, distributed tracing, dashboards, alerts,
SLIs/SLOs, audit logs, AI usage metrics, token usage, platform costs, MCP
tool-call metrics, store health, queue depth, DLQ monitoring. Table
mapping major failure scenarios to logs, metrics, traces, dashboards,
alerts.

# 26. Configuration and Secrets

Configuration hierarchy, environment-specific values, feature flags,
secrets and rotation, startup validation, dynamic configuration, defaults,
unsafe combinations, local development configuration. No real credentials.

# 27. Deployment Architecture

Environments, regions, networks, containers/orchestration, serverless
components, load balancers, auto-scaling, stores, platform connectivity,
MCP deployment, CI/CD pipeline, infrastructure as code, rollback strategy,
blue-green/canary, migration sequencing. Mermaid deployment diagram,
release sequence diagram, rollback activity diagram.

# 28. Testing Strategy

Unit, integration, contract, store, MCP, platform, AI-evaluation,
security, performance, load, failure-injection, end-to-end, acceptance
tests — as applicable. Per module: test boundaries, required mocks,
required fixtures, critical edge cases, minimum coverage expectations,
contract ownership.

# 29. Local Development

Prerequisites, repository setup, environment variables, local store setup,
MCP setup, AI mocking, seed data, running the application, running tests,
debugging, common setup failures.

# 30. Operations and Support

Common incidents, diagnostic steps, recovery procedures, data repair,
queue replay, cache flush, model fallback, dependency-outage procedures,
rollback, on-call ownership, escalation paths.

# 31. Risks, Tradeoffs, and Technical Debt

Table: risk/debt item, description, affected area, probability, impact,
mitigation, owner, target resolution, escalation trigger.

# 32. Implementation Plan

Phases with: goal, modules involved, dependencies, deliverables,
acceptance criteria, testing requirements, migration requirements,
rollback plan, risks. Plus: recommended order, critical path,
parallelizable work, ownership boundaries, milestones. (For an already-
built system this section becomes the extension roadmap — what to build
next and in what order.)

# 33. Requirement-to-Design Traceability

Matrix: requirement → business workflow → architecture component → module
→ package → class/service → store object → API endpoint → test coverage →
monitoring signal.

# 34. Open Questions and Decisions Needed

Per unresolved point: question, why it matters, options, recommended
option, decision owner, impact of delay.

# 35. Appendices

Glossary, API examples, event schemas, store schemas, configuration
examples, error-code catalog, Mermaid diagram index, decision log,
assumption log.

## Mermaid Diagram Requirements

Use Mermaid for all diagrams, the appropriate type for each: `flowchart`
(architecture, data flow), `sequenceDiagram` (interactions over time),
`stateDiagram-v2` (stateful logic), `classDiagram` (classes/domain),
`erDiagram` (data relationships), `journey`/`flowchart` (user and activity
flows).

Every diagram must: have a clear title; use meaningful component names;
avoid unexplained abbreviations; show system boundaries, external systems,
stores and caches; label important arrows; distinguish synchronous from
asynchronous calls; show trust boundaries where relevant; remain readable
without excessive crossing lines. **House rule:** derive diagrams from
actual code and events only; cap node count and note "+K more" rather than
silently truncating.

Place each diagram in a fenced `mermaid` code block. After each diagram
add: purpose, main flow, important assumptions, failure behavior, related
modules. Validate the Mermaid syntax before presenting it.

## Quality Controls

Before finalizing:

1. Every major component appears in at least one architecture diagram.
2. Every major workflow has both an activity diagram and a sequence diagram.
3. Complex stateful logic has a state diagram.
4. Every store interaction identifies the responsible module.
5. Cache usage includes expiration and invalidation behavior.
6. MCP integrations include security and output-validation boundaries.
7. AI/platform integrations include guardrails, retries, cost controls, and
   failure handling.
8. Every module lists dependencies and testing responsibilities.
9. Important packages and classes are documented.
10. Requirements are traceable to implementation components and tests.
11. No contradictions between diagrams and written descriptions.
12. Missing information is listed, never silently invented.
13. The "Omitted sections" list is present and each omission justified.

## Output Rules

Markdown; numbered headings; tables for structured information; Mermaid
diagrams; code blocks for schemas and examples; cross-references between
related sections. Start with the executive summary, then proceed from
high-level architecture to detailed implementation design.

Where source information is incomplete, label with: **Confirmed**,
**Assumption**, **Recommendation**, **Open Question**.

End with:

1. Top architectural risks
2. Immediate decisions required
3. Recommended implementation order
4. Information still needed from stakeholders
