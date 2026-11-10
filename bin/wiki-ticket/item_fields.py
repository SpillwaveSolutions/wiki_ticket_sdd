#!/usr/bin/env python3
"""
item_fields.py -- the configurable optional-field model. Item #108.

The item model had a fixed shape. A lightweight team carried fields it never
filled in; a heavyweight one had nowhere to put risk, owner, or acceptance
criteria without inventing conventions in the body text. The ask was one log
that both processes can share, with the difference expressed in config.

Two populations, and the split is the whole design:

  CORE -- id, title, status, level, kind, priority, milestone, labels, parent,
  body, plan, depends_on, unplanned/discovered_during, external, resolution.
  Not configurable, ever. These are load-bearing: the fold keys on them, the
  roadmap renderer reads them, sync maps them onto tickets, and the
  traceability index walks them. A config that could switch `priority` off
  would be a config that can break the roadmap, so the "small stable core"
  principle from the ticket is enforced by not offering the knob.

  OPTIONAL -- everything in CATALOG below. Enabled per team. A disabled field
  is not merely rejected: its flag never gets built, so it cannot appear in
  the CLI, in --help, or in anything an agent reads to decide what to write.
  That is what "never appear in prompts, forms, or validation" has to mean
  for a CLI whose --help IS the prompt.

Every field carries a `description`. It is not decoration: agents read
`worklog fields` to learn what a field means before writing it, and a field
whose meaning is guessable from its name alone still gets guessed differently
by two people. The descriptions ship as defaults so a team does not have to
author them to switch a field on.

Defaults follow the ticket's recommendation. Of its default-on list --
priority, estimate, risk, owner, milestone, acceptance_criteria, labels --
priority, milestone and labels were already core here and stay there, so the
catalog carries the rest. Default-off is conservative on purpose: an
unfilled field is worse than a missing one, because it looks like an answer.
"""
import os
import re

CONFIG = ".work/config.yml"

# Never configurable. Listed so the CLI can refuse to shadow one.
CORE = ("id", "title", "status", "level", "kind", "priority", "milestone",
        "labels", "parent", "body", "plan", "depends_on", "unplanned",
        "discovered_during", "external", "resolution")

# name -> (default_enabled, choices or None, description)
CATALOG = {
    "estimate": (
        True, ("XS", "S", "M", "L", "XL"),
        "Relative size, not time. Compare items; never sum into a schedule."),
    "owner": (
        True, None,
        "Who is accountable for the item moving -- one name, not a team. "
        "Not the same as who does the work."),
    "risk": (
        True, ("low", "medium", "high"),
        "Chance this item goes badly or blocks others. Drives what gets "
        "planned first, not what gets estimated bigger."),
    "acceptance_criteria": (
        True, None,
        "What must be observably true to close this. Written before the "
        "work, checked at close; if it cannot be observed, it is not a "
        "criterion."),
    "value": (
        False, None,
        "Expected benefit if delivered. Only meaningful when something "
        "actually ranks by it -- off by default so it does not become a "
        "field everyone fills with 'high'."),
    "confidence": (
        False, ("low", "medium", "high"),
        "How much to trust this item's own estimate and value. Pairs with "
        "them; meaningless alone."),
    "due_date": (
        False, None,
        "External hard date (YYYY-MM-DD) -- a conference, an audit, a "
        "contract. Not a wish, and not a substitute for a milestone."),
    "severity": (
        False, ("sev1", "sev2", "sev3", "sev4"),
        "For bugs: how bad the impact is in production, independent of "
        "priority. Off unless the team runs an incident process."),
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _config_block(path=CONFIG, block="work_item_fields"):
    """`name: value` pairs under one top-level block of .work/config.yml.

    A targeted read, not a YAML dependency: this is one flat block of
    scalars, and the installer already reads config.yml the same way with
    awk. Anything malformed reads as "nothing configured", which falls back
    to the defaults rather than failing every command.
    """
    out = {}
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return out
    inside = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line[0].isspace():
            inside = line.strip().startswith(block + ":")
            continue
        if inside:
            m = re.match(r"\s+([A-Za-z_][\w]*)\s*:\s*(\S+)", line)
            if m:
                out[m.group(1)] = m.group(2).strip("\"'").lower()
    return out


TRUE = ("true", "yes", "on", "1")
FALSE = ("false", "no", "off", "0")


def enabled(path=CONFIG):
    """{name: (choices, description)} for every optional field switched on."""
    cfg = _config_block(path)
    out = {}
    for name, (default, choices, desc) in CATALOG.items():
        raw = cfg.get(name)
        on = default if raw is None else (raw in TRUE)
        if raw is not None and raw not in TRUE + FALSE:
            on = default          # unreadable value -> the documented default
        if on:
            out[name] = (choices, desc)
    return out


def is_enabled(name, path=CONFIG):
    return name in enabled(path)


def flag(name):
    """--acceptance-criteria for acceptance_criteria."""
    return "--" + name.replace("_", "-")


def dest(name):
    return name


def validate(name, value):
    """-> error string, or None. Choices are enforced by argparse; this is
    for shapes argparse cannot express."""
    if value is None:
        return None
    if name == "due_date" and not DATE_RE.match(value):
        return "--due-date wants YYYY-MM-DD, got %r" % value
    return None


def add_arguments(parser, path=CONFIG):
    """Build a flag per ENABLED optional field.

    Disabled fields get no flag at all, so `worklog add --risk high` in a repo
    with risk off is an argparse error naming an unrecognised option -- the
    field is invisible rather than rejected, which is what the ticket asked
    for.
    """
    for name, (choices, desc) in sorted(enabled(path).items()):
        kwargs = {"help": desc}
        if choices:
            kwargs["choices"] = list(choices)
        parser.add_argument(flag(name), dest=dest(name), **kwargs)


def collect(args, path=CONFIG):
    """{field: value} for enabled fields present on `args`. Exits on a bad
    shape, so a malformed value never reaches the log."""
    out = {}
    for name in enabled(path):
        value = getattr(args, dest(name), None)
        if value is None:
            continue
        err = validate(name, value)
        if err:
            raise SystemExit("worklog: " + err)
        out[name] = value
    return out


def describe(path=CONFIG):
    """Lines for `worklog fields` -- what an agent reads before writing."""
    on = enabled(path)
    lines = ["core (always on, not configurable):",
             "  " + ", ".join(CORE), "", "optional:"]
    for name in sorted(CATALOG):
        choices, desc = CATALOG[name][1], CATALOG[name][2]
        mark = "on " if name in on else "off"
        vals = " {%s}" % "|".join(choices) if choices else ""
        lines.append("  [%s] %s%s" % (mark, flag(name), vals))
        lines.append("        " + desc)
    lines += ["", "Switch a field on or off in %s:" % CONFIG,
              "  work_item_fields:", "    risk: off"]
    return lines
