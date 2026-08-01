---
date: 2026-08-01
slug: configurable-item-fields
title: Configurable optional fields on the work item
items: [01KY5NE0ZYGBWG44N0KPEBFCZ8]
---

# Configurable optional fields on the work item

## Context

The item model had one fixed shape. A lightweight team carried fields it never
filled in; a heavyweight one had nowhere to record risk, owner, or acceptance
criteria without inventing conventions inside the body text. Item #108 asked
for one log both processes can share, with the difference expressed in config
rather than in a fork of the tool.

The item was filed on 2026-07-22 with the note *"re-derive the detailed field
table when this is planned."* This is that derivation.

## The split, and why it is the whole design

**Core — not configurable, ever.** `id`, `title`, `status`, `level`, `kind`,
`priority`, `milestone`, `labels`, `parent`, `body`, `plan`, `depends_on`,
`unplanned`/`discovered_during`, `external`, `resolution`.

These are load-bearing. The fold keys on them, `render_roadmap.py` reads
`priority` and `depends_on` to build the roadmap and its blocker column, sync
maps them onto remote tickets, and the traceability index walks `parent` and
`plan`. A config able to switch `priority` off would be a config able to break
the roadmap — so the "small stable core" principle is enforced by **not
offering the knob**, not by documenting that you shouldn't turn it.

This is a narrower core than the ticket's phrasing implies. The ticket listed
`priority`, `milestone` and `labels` among "recommended default-on" *optional*
fields; here they were already core and stay there. Making them optional would
have been a large behavioural change to satisfy a category, and the ticket's
own principles (small stable core, conservative defaults) point the other way.

**Optional — enabled per team**, in `bin/item_fields.py`:

| Field | Default | Values | Why this default |
|---|---|---|---|
| `estimate` | **on** | XS/S/M/L/XL | Already shipped (#256); the catalog now owns it instead of two hardcoded flags. |
| `owner` | **on** | free text | Accountability is the most commonly missing field in practice. |
| `risk` | **on** | low/medium/high | Drives planning order; cheap to fill, useful immediately. |
| `acceptance_criteria` | **on** | free text | The one field that reliably prevents "done" disputes. |
| `value` | off | free text | Only meaningful when something actually ranks by it. Otherwise everyone writes "high". |
| `confidence` | off | low/medium/high | Pairs with estimate and value; meaningless alone. |
| `due_date` | off | YYYY-MM-DD | An *external* hard date. Off so it does not become a wish, or a second milestone. |
| `severity` | off | sev1–sev4 | Only for teams running an incident process; distinct from priority. |

Default-off is conservative deliberately: **an unfilled field is worse than a
missing one, because it looks like an answer.**

## Disabled means invisible, not rejected

The ticket said disabled fields must "never appear in prompts, forms, or
validation". For a CLI whose `--help` *is* the prompt an agent reads, the only
honest reading is that the flag must not exist. So `add_arguments()` builds a
flag per **enabled** field, and `worklog add --severity sev1` in a repo with
severity off fails as an unrecognised option. Nothing anywhere advertises a
field the team has switched off.

## Descriptions are not decoration

Every catalog entry carries a description, and `worklog fields` prints them.
Agents read that before writing a field, and a field whose meaning is
"guessable from the name" gets guessed differently by two people —
`value` and `severity` especially. Descriptions ship as defaults so switching
a field on costs one config line, not an authoring exercise.

## Config

```yaml
work_item_fields:
  severity: on
  risk: off
```

Read with the same targeted reader used for `wiki.system`, not a YAML
dependency: one flat block of scalars, the way `init.sh` already reads this
file. An unreadable value falls back to the documented default rather than to
`off` — a typo must not silently drop a field a team relies on.

## Deliberately not done

- **No migration.** Optional fields are additive; existing events are already
  valid, and the fold ignores fields it does not know.
- **No per-field `description:` override in config.** The defaults are the
  documentation. A team that wants different words can send a PR to the
  catalog, where every reader benefits.
- **`blocked_by`/`blocks` and `relates_to` are not added here.** `depends_on`
  already exists as a typed, set-valued core field feeding the traceability
  index (#256). A second spelling of the same edge would be drift.
- **Sync does not push optional fields.** `HASH_FIELDS` and the adapter
  contract are unchanged; mapping new fields onto every tracker is its own
  item, with its own per-platform degrade rules.
