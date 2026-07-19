"""ADR support: front matter parse, schema check, cross-file invariants,
scaffold (docs/plans/2026-07-19-adr.md).

Nygard rules: the body is written once; after acceptance only `status` and
`superseded_by` may change (mark_superseded is the one sanctioned mutation).
"""
import glob
import os
import re

ADR_DIR = "docs/adr"

# Mirrors schema/adr.schema.json — same deliberate duplication as
# sync_dispatch.CAPABILITIES_SCHEMA, so a scaffolded repo needs only bin/.
ADR_SCHEMA = {
    "type": "object",
    "required": ["id", "slug", "title", "date", "status"],
    "properties": {
        "id": {"type": "integer"},
        "slug": {"type": "string"},
        "title": {"type": "string"},
        "date": {"type": "string"},
        "status": {"enum": ["proposed", "accepted", "deprecated",
                            "superseded"]},
        "deciders": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "supersedes": {"type": ["integer", "null"]},
        "superseded_by": {"type": ["integer", "null"]},
    },
}

TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
}


def validate(instance, schema, path="$"):
    """Mini JSON Schema validator for the subset
    {type, required, properties, enum, items, additionalProperties}.
    Raises ValueError naming the offending field path.

    Deliberate copy of sync_dispatch.validate — no import coupling between
    the ADR tooling and the dispatcher (same pattern as the test suite copy).
    """
    if "enum" in schema and instance not in schema["enum"]:
        raise ValueError("%s: %r not in enum %r" % (path, instance, schema["enum"]))
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(TYPE_CHECKS[t](instance) for t in types):
            raise ValueError("%s: expected %s, got %r"
                             % (path, "/".join(types), instance))
    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                raise ValueError("%s: missing required field %r" % (path, req))
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], "%s.%s" % (path, key))
            elif schema.get("additionalProperties") is False:
                raise ValueError("%s: unexpected field %r" % (path, key))
    if isinstance(instance, list) and "items" in schema:
        for i, value in enumerate(instance):
            validate(value, schema["items"], "%s[%d]" % (path, i))


INT_KEYS = ("id", "supersedes", "superseded_by")
LIST_KEYS = ("deciders", "tags")


def parse_front_matter(text):
    """Naive `---`-fenced `key: value` front matter -> (dict, body).
    Same deliberately-simple style as plan_capture.front_matter: no yaml lib.
    ints for id/supersedes/superseded_by, `[a, b]` inline lists, null -> None.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("no front matter fence")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("unterminated front matter fence")
    meta = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError("bad front matter line %r" % line)
        key, value = key.strip(), value.strip()
        if value == "null":
            meta[key] = None
        elif key in INT_KEYS:
            try:
                meta[key] = int(value)
            except ValueError:
                meta[key] = value  # schema check names the bad type
        elif key in LIST_KEYS and value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            meta[key] = [v.strip() for v in inner.split(",")] if inner else []
        else:
            meta[key] = value
    return meta, "\n".join(lines[end + 1:])


def adr_files(dir=ADR_DIR):
    return sorted(glob.glob(os.path.join(dir, "*.md")))


REQUIRED_HEADINGS = ("## Context", "## Decision", "## Consequences")


def check_all(dir=ADR_DIR):
    """Validate every ADR; returns a list of named problems (empty = ok)."""
    problems = []
    records = {}  # id -> (fname, meta)
    for path in adr_files(dir):
        fname = os.path.basename(path)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        try:
            meta, body = parse_front_matter(text)
            validate(meta, ADR_SCHEMA)
        except ValueError as e:
            problems.append("%s: %s" % (fname, e))
            continue
        m = re.match(r"(\d{4})-(.+)\.md$", fname)
        if not m or int(m.group(1)) != meta["id"] or m.group(2) != meta["slug"]:
            problems.append("%s: filename disagrees with front matter "
                            "(want %04d-%s.md)" % (fname, meta["id"], meta["slug"]))
        if meta["id"] in records:
            problems.append("%s: duplicate id %d (also %s)"
                            % (fname, meta["id"], records[meta["id"]][0]))
        else:
            records[meta["id"]] = (fname, meta)
        if meta["status"] == "superseded" and meta.get("superseded_by") is None:
            problems.append("%s: status superseded requires superseded_by" % fname)
        if meta.get("superseded_by") is not None and meta["status"] != "superseded":
            problems.append("%s: superseded_by set but status is %r, "
                            "not superseded" % (fname, meta["status"]))
        for h in REQUIRED_HEADINGS:
            if not re.search("^%s\\s*$" % re.escape(h), body, re.M):
                problems.append("%s: missing required section %r" % (fname, h))
    for iid, (fname, meta) in sorted(records.items()):
        sup = meta.get("supersedes")
        if sup is not None and sup in records:
            oname, ometa = records[sup]
            if ometa.get("superseded_by") != iid:
                problems.append("%s: superseded by %s but superseded_by is %r, "
                                "not %d" % (oname, fname,
                                            ometa.get("superseded_by"), iid))
        sb = meta.get("superseded_by")
        if sb is not None and sb in records:
            oname, ometa = records[sb]
            if ometa.get("supersedes") != iid:
                problems.append("%s: superseded_by %d but %s does not "
                                "supersede %d" % (fname, sb, oname, iid))
    return problems


BODY_NOTE = ("<!-- body is written once; only status/superseded_by change "
             "after acceptance -->")


def scaffold(title, adr_id, slug, date, status="proposed",
             deciders=None, tags=None, supersedes=None):
    """Template for a new ADR -> (path, content)."""
    lines = ["---", "id: %d" % adr_id, "slug: %s" % slug, "title: %s" % title,
             "date: %s" % date, "status: %s" % status]
    if deciders:
        lines.append("deciders: [" + ", ".join(deciders) + "]")
    if tags:
        lines.append("tags: [" + ", ".join(tags) + "]")
    if supersedes is not None:
        lines.append("supersedes: %d" % supersedes)
    lines += ["---", "",
              "# ADR-%04d: %s" % (adr_id, title), "",
              BODY_NOTE, "",
              "## Context", "", "TODO", "",
              "## Decision", "", "TODO", "",
              "## Consequences", "", "TODO", "",
              "## Alternatives", "", "TODO", ""]
    return os.path.join(ADR_DIR, "%04d-%s.md" % (adr_id, slug)), "\n".join(lines)


def mark_superseded(path, by_id):
    """The one sanctioned mutation: flip status + set superseded_by in place.
    Touches only those front matter lines; the body is never rewritten."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    end = lines.index("---", 1)
    had = False
    for i in range(1, end):
        key = lines[i].partition(":")[0].strip()
        if key == "status":
            lines[i] = "status: superseded"
        elif key == "superseded_by":
            lines[i] = "superseded_by: %d" % by_id
            had = True
    if not had:
        lines.insert(end, "superseded_by: %d" % by_id)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
