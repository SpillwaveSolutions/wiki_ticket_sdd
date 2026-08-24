# Requirements document prompt

Store the document as `docs/requirements/<NAME>_srs.md` or
`docs/requirements/<NAME>_prd.md` unless the user names another path.
Stamp frontmatter the same way as a design doc (`wiki_key`, `doc_type`,
`truth_state`, `git_hash`, `branch`, `tag`). `doc_type` is `requirements`.

You are writing a requirements document (SRS or PRD) for the system in this
repository.

## Companion skills (required)

Load `companion-skills.md` in this folder. Then:

1. `document-specialist` **v3.2.1** writes the prose from its SRS or PRD
   template. Default voice is STE100. Do not use an em dash. Do not start a
   sentence with So, That, Thus, or Hence. Use `google-docs-style` **v1.1.3**
   only when the user names Google style. Do not mix packs. Include Salt
   wireframes when the UI matters.
2. `design-doc-mermaid` **v1.1.0** draws every GitHub-safe diagram, including
   class, ER, state, sequence, flowchart, and C4. Put a fenced `mermaid`
   block in the Markdown. Validate before publish.
3. `plantuml` **v1.2.1** is opt-in for wireframes, use case, timing, and
   ArchiMate. Save `.puml` plus PNG or SVG under `docs/diagrams/`. Link the
   image. Upload the image with the wiki or Confluence page. Do not leave
   raw PlantUML as the only view.

GitHub wiki renders Mermaid. Confluence needs images for Mermaid and PlantUML.

## How to apply this template

- Pick SRS when the user wants IEEE-style numbered requirements. Pick PRD
  when the user wants an agile product brief. If they say only
  "requirements", ask which form, then proceed with SRS if they do not care.
- The repository is the source of truth. Do not invent features. Label
  **Confirmed** / **Assumption** / **Recommendation** / **Open Question**.
- Every functional requirement gets an ID (`FR-XXX-001`) and Given-When-Then
  acceptance criteria.
- Trace each requirement to a module, API, or store object that already
  exists, or mark it as a gap.
- Diagrams follow the mermaid-first rule in `companion-skills.md`.

## Required sections (menu, not a quota)

1. Purpose, audience, scope, out of scope
2. Actors and user goals
3. Functional requirements
4. Non-functional requirements (performance, security, availability)
5. Data and integrations
6. Wireframes when UI is in scope
7. Traceability matrix
8. Open questions
9. Omitted sections, each with one line of reason

## Output rules

Markdown. Numbered headings. Tables for requirements. Mermaid fences for
GitHub-safe diagrams. Image links for PlantUML leftovers. No em dash. No
sentence starting with So, That, Thus, or Hence.
