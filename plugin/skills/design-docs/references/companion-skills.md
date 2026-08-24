# Companion skills for design docs, walkthroughs, and requirements

Load these skills before you write `docs/designs/` architecture docs,
code walkthroughs, or requirement docs (SRS / PRD).
Install from `SpillwaveSolutions/spillwave-documentation-marketplace`.

| Role | Skill | Rule |
|------|--------|------|
| Prose | `document-specialist` | Default voice is STE100. Switch to `google-docs-style` only when the user names Google style. Never mix packs. Wireframes belong in this skill's diagram pass. |
| GitHub-safe diagrams | `design-doc-mermaid` | Default for flowchart, sequence, class, ER, state, C4, and component views. Fenced `mermaid` in the Markdown. Validate before publish. |
| Leftover UML and wireframes | `plantuml` | Use case, timing, ArchiMate, Salt wireframes, nwdiag, WBS. Always render PNG or SVG. GitHub wiki does not render PlantUML source. |

Hard bans for prose in both voice packs:

- No em dash.
- Do not start a sentence with So, That, Thus, or Hence.

## Publish targets

| Target | Mermaid | PlantUML |
|--------|---------|----------|
| GitHub wiki | Keep the fenced block. GitHub renders it. | Render PNG or SVG, commit under `docs/diagrams/`, copy the image into the wiki checkout, link it. |
| Confluence | Render PNG or SVG and upload. Do not rely on Confluence to render Mermaid. | Render PNG or SVG and upload. |

Wiki-publish must upload diagram images with the page. A wiki page that
points at a missing `docs/diagrams/*.png` is a publish defect.
