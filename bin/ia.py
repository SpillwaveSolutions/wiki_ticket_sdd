"""IA & content model: wiki_key identity, content inventory, sidecar
metadata (docs/plans/2026-07-22-ia-content-model.md).

Two planes: storage (docs/ as-is, unchanged) and a generated reader plane.
This module is the foundation: classify every doc, give it a stable
`wiki_key` (seeded verbatim from the publish ledger for legacy docs, derived
by §5.5 rules for new ones), compute `truth_state`, and emit the content
inventory `docs/.index/_inventory.json`.

Determinism rule: everything written under docs/.index/ is a pure function
of committed files — no wall clock, no environment. The freshness gate
regenerates and diffs, exactly like docs/roadmap.md.

Frozen docs are never edited; their metadata lives in sidecars
docs/.index/<wiki_key>.yml (invariant §15.8/§15.9).
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fold import fold, CLOSED_STATUSES

LEDGER = ".work/published.json"
INDEX_DIR = "docs/.index"
INVENTORY = os.path.join(INDEX_DIR, "_inventory.json")

DOC_TYPES = ("plan", "roadmap", "roadmap-snapshot", "status",
             "design", "adr", "guide")
# Graph/execution entities, not documents (schema/entity.schema.json).
# Today only "item"; release and code-change join when they need validation.
ENTITY_TYPES = ("item",)
TRUTH_STATES = ("current", "snapshot", "superseded", "archived")
EDGE_TYPES = ("produces", "decides", "implements", "supersedes",
              "verified-by", "lands-in", "belongs-to", "targets",
              "snapshot-of", "references")

# Mirrors schema/doc.schema.json + schema/entity.schema.json — same
# deliberate duplication as adr.ADR_SCHEMA, so a scaffolded repo needs
# only bin/.
REQUIRED_ALL = ("wiki_key", "doc_type", "truth_state")
REQUIRED_BY_TYPE = {
    # epic is NOT required: story-level plans float free (epic: null is
    # legitimate — see docs/plans/2026-07-19-adr.md)
    "plan": ("wiki_key", "doc_type", "title", "slug", "date", "truth_state",
             "status", "items"),
    "roadmap": ("wiki_key", "doc_type", "truth_state", "generated_at"),
    "roadmap-snapshot": ("wiki_key", "doc_type", "truth_state", "date"),
    "status": ("wiki_key", "doc_type", "kind", "date", "window", "through",
               "generated_at", "truth_state"),
    "design": ("wiki_key", "doc_type", "git_hash", "truth_state"),
    "adr": ("wiki_key", "doc_type", "id", "slug", "title", "date", "status",
            "truth_state"),
    "guide": ("wiki_key", "doc_type", "title", "slug", "truth_state"),
}
REQUIRED_BY_ENTITY = {
    "item": ("wiki_key", "doc_type", "title", "status", "truth_state"),
}


# ---------------------------------------------------------------- parsing

def parse_front_matter(text):
    """Generic `---`-fenced frontmatter -> (dict, body). No yaml lib (repo
    convention, see adr.parse_front_matter). Handles: null, ints where the
    value is all digits AND the key expects one, inline `[a, b]` lists,
    inline `{k: v}` maps, and block lists of `- {type: x, target: y}`.
    Returns ({}, text) when there is no fence at byte 0."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, text
    meta = {}
    key = None  # current block-list key
    for line in lines[1:end]:
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and key:
            meta[key].append(_scalar(stripped[2:].strip()))
            continue
        k, sep, v = line.partition(":")
        if not sep:
            continue  # tolerate junk; the schema check names real problems
        k, v = k.strip(), v.strip()
        if v == "":
            meta[k] = []
            key = k          # opening a block list
        else:
            meta[k] = _scalar(v)
            key = None
    return meta, "\n".join(lines[end + 1:])


def _scalar(v):
    if v == "null":
        return None
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(x.strip()) for x in inner.split(",")] if inner else []
    if v.startswith("{") and v.endswith("}"):
        out = {}
        for part in v[1:-1].split(","):
            pk, sep, pv = part.partition(":")
            if sep:
                out[pk.strip()] = _scalar(pv.strip())
        return out
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def dump_simple_yaml(meta):
    """Inverse of parse_front_matter for sidecars: flat keys, inline lists/
    maps, block lists for lists of dicts. Deterministic (sorted keys)."""
    out = []
    for k in sorted(meta):
        v = meta[k]
        if isinstance(v, list) and v and isinstance(v[0], dict):
            out.append("%s:" % k)
            for d in v:
                inner = ", ".join("%s: %s" % (dk, d[dk]) for dk in sorted(d))
                out.append("  - {%s}" % inner)
        elif isinstance(v, list):
            out.append("%s: [%s]" % (k, ", ".join(str(x) for x in v)))
        elif isinstance(v, dict):
            inner = ", ".join("%s: %s" % (dk, v[dk]) for dk in sorted(v))
            out.append("%s: {%s}" % (k, inner))
        elif v is None:
            out.append("%s: null" % k)
        else:
            out.append("%s: %s" % (k, v))
    return "\n".join(out) + "\n"


def html_comment_meta(text):
    """The roadmap family's legacy header: `<!-- key: value -->` lines."""
    meta = {}
    for m in re.finditer(r"<!--\s*([\w-]+):\s*(.+?)\s*-->", text):
        meta[m.group(1).replace("-", "_")] = m.group(2)
    return meta


def first_heading(body):
    m = re.search(r"^#\s+(.+?)\s*$", body, re.M)
    return m.group(1) if m else None


# ------------------------------------------------------- classification

def classify(path):
    """Repo path -> doc_type, or None for paths outside the content model
    (migrations, README, .index itself)."""
    p = path.replace(os.sep, "/")
    if p.startswith("docs/plans/"):
        return "plan"
    if p == "docs/roadmap.md":
        return "roadmap"
    if p.startswith("docs/roadmap/"):
        return "roadmap-snapshot"
    if p.startswith("docs/status/"):
        return "status"
    if p.startswith("docs/designs/"):
        return "design"
    if p.startswith("docs/adr/"):
        return "adr"
    if p.startswith("docs/user_guide/") or p in ("docs/wiki-home.md",
                                                 "docs/worklog-spec.md"):
        return "guide"
    return None


def derive_canonical_key(path):
    """§5.5 derivation rules — the canonical (new-style) key for a path."""
    p = path.replace(os.sep, "/")
    stem = os.path.splitext(os.path.basename(p))[0]
    t = classify(p)
    if t == "plan":
        return "plan/" + stem                      # <date>-<slug>
    if t == "roadmap":
        return "roadmap"
    if t == "roadmap-snapshot":
        return "roadmap-snapshot/" + stem
    if t == "status":
        return "status/" + stem
    if t == "design":
        if stem == "current_design_doc":
            return "design/current-design-doc"
        if stem == "current_code_walkthrough":
            return "design/current-code-walkthrough"
        m = re.match(r"(.+)_(design_doc|code_walkthrough)$", stem)
        if m:
            return "design/%s-%s" % (m.group(1), m.group(2).replace("_", "-"))
        return "design/" + stem
    if t == "adr":
        return "adr/" + stem
    if t == "guide":
        # home and spec keep their verbatim ledger identity — renaming the
        # Home page key buys nothing and risks links.
        if p == "docs/wiki-home.md":
            return "home"
        if p == "docs/worklog-spec.md":
            return "spec"
        return "guide/" + stem
    return None


def load_ledger(path=LEDGER):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def resolve_key(path, ledger):
    """-> (wiki_key, canonical_key, aliases). Legacy docs keep their ledger
    key verbatim (link preservation beats uniformity, §5.3); unpublished
    docs get the canonical derivation."""
    p = path.replace(os.sep, "/")
    canonical = derive_canonical_key(p)
    for key, entry in ledger.items():
        if entry.get("source") == p:
            aliases = [key] if canonical and key != canonical else []
            return key, canonical or key, aliases
    return canonical, canonical, []


# ------------------------------------------------------------ sidecars

def sidecar_path(wiki_key):
    return os.path.join(INDEX_DIR, wiki_key + ".yml")


def read_sidecar(wiki_key):
    try:
        with open(sidecar_path(wiki_key), encoding="utf-8") as fh:
            meta, _ = parse_front_matter("---\n" + fh.read() + "---")
            return meta
    except FileNotFoundError:
        return {}


def write_sidecar(wiki_key, meta):
    path = sidecar_path(wiki_key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(dump_simple_yaml(meta))


# ----------------------------------------------------------- inventory

def doc_paths():
    pats = ("docs/plans/*.md", "docs/roadmap.md", "docs/roadmap/*.md",
            "docs/status/*.md", "docs/designs/*.md", "docs/adr/*.md",
            "docs/user_guide/*.md", "docs/wiki-home.md",
            "docs/worklog-spec.md")
    out = []
    for pat in pats:
        out.extend(glob.glob(pat))
    return sorted(set(p.replace(os.sep, "/") for p in out))


def plan_lifecycle(meta, items):
    """Plan lifecycle status from its items' fold state (§4): planned until
    work starts, active while open, completed when every item is closed."""
    ids = meta.get("items") or []
    if not ids:
        # ponytail: only legacy pre-worklog plans lack items entirely, and
        # those shipped — plan-capture always emits items for new plans
        return "completed"
    states = [items[i].get("status") for i in ids if i in items]
    if not states:
        return "planned"
    if all(s in CLOSED_STATUSES for s in states):
        return "completed"
    if any(s != "todo" for s in states):
        return "active"
    return "planned"


SUPERSEDES_TITLE = re.compile(r"supersedes\s+([\w-]+)")


# Fields the normalizer owns and recomputes every run. Everything else in a
# sidecar (owner, relates_to, hand-added supersedes...) is authored and kept.
DYNAMIC_FIELDS = ("truth_state", "superseded_by", "status")


def build_records(ledger=None, paths=None, fold_paths=None,
                  drop_dynamic_sidecar=False):
    """One merged metadata record per doc: derived ∪ frontmatter ∪ sidecar.
    Frontmatter wins over derivation; the sidecar wins over both — it is
    the one writable metadata channel for frozen docs (§5.6), and the
    normalizer only ever adds what the artifact could not say."""
    ledger = load_ledger() if ledger is None else ledger
    paths = doc_paths() if paths is None else paths
    fr = fold(fold_paths or (".work/todo.jsonl", ".work/done.jsonl"))
    records = {}
    for path in paths:
        doc_type = classify(path)
        if not doc_type:
            continue
        wiki_key, canonical, aliases = resolve_key(path, ledger)
        if not wiki_key:
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        fm, body = parse_front_matter(text)
        if doc_type in ("roadmap", "roadmap-snapshot") and not fm:
            fm = html_comment_meta(text)
            fm.pop("source_hash", None)  # volatile; the ledger owns hashes
        rec = {"wiki_key": wiki_key, "canonical_key": canonical,
               "doc_type": doc_type, "source": path}
        if aliases:
            rec["aliases"] = aliases
        stem = os.path.splitext(os.path.basename(path))[0]
        rec["slug"] = fm.get("slug") or stem
        title = fm.get("title") or first_heading(body or text)
        if title:
            rec["title"] = str(title)
        # type-specific derivation
        if doc_type == "plan":
            rec["status"] = fm.get("status") or plan_lifecycle(fm, fr.items)
            m = re.match(r"(\d{4}-\d{2}-\d{2})", stem)
            if m and not fm.get("date"):
                rec["date"] = m.group(1)
            m = SUPERSEDES_TITLE.search(str(fm.get("title", "")))
            if m and "supersedes" not in fm:
                rec["supersedes"] = "plan/" + m.group(1)
        elif doc_type == "roadmap-snapshot":
            m = re.match(r"(\d{4}-\d{2}-\d{2})_(.+)$", stem)
            if m:
                rec["date"], rec["name"] = m.group(1), m.group(2)
                rel = re.match(r"(v[\w.]+?)(?:-release)?$", m.group(2))
                if rel:
                    rec["release"] = rel.group(1)
        elif doc_type == "design" and fm.get("tag"):
            rec["release"] = fm["tag"]
        entry = ledger.get(wiki_key, {})
        if entry.get("url"):
            rec["wiki"] = entry["url"]
        rec.update({k: v for k, v in fm.items() if v is not None})
        side = read_sidecar(wiki_key)
        if drop_dynamic_sidecar:
            side = {k: v for k, v in side.items() if k not in DYNAMIC_FIELDS}
        rec.update(side)
        rec["_fm"] = sorted(fm)  # what the artifact itself says (internal)
        records[wiki_key] = rec
    _link_supersedes(records)   # setdefault only: explicit sidecar wins
    _assign_truth(records)      # fills whatever is still unset
    return records


def _assign_truth(records):
    latest_status = {}  # kind -> wiki_key of newest report
    for key, rec in records.items():
        if rec["doc_type"] == "status":
            k = rec.get("kind", "daily")
            if k not in latest_status or rec["source"] > records[latest_status[k]]["source"]:
                latest_status[k] = key
    current_status = set(latest_status.values())
    for key, rec in records.items():
        if "truth_state" in rec:
            continue  # sidecar/frontmatter already says
        t = rec["doc_type"]
        if t in ("roadmap-snapshot",) or (t == "design" and not rec["source"].endswith(
                ("current_design_doc.md", "current_code_walkthrough.md"))):
            rec["truth_state"] = "snapshot"
        elif t == "status":
            rec["truth_state"] = "current" if key in current_status else "archived"
        elif t == "adr":
            s = rec.get("status")
            rec["truth_state"] = {"superseded": "superseded",
                                  "deprecated": "archived"}.get(s, "current")
        elif t == "plan":
            rec["truth_state"] = "current"  # flipped below if superseded
        else:
            rec["truth_state"] = "current"


def _link_supersedes(records):
    """Derive superseded_by (and truth_state: superseded) from successors'
    `supersedes` — reverse edges are computed, never authored (§9.4)."""
    for key, rec in records.items():
        target = rec.get("supersedes")
        if isinstance(target, str) and target in records:
            old = records[target]
            old.setdefault("superseded_by", key)
            if old["doc_type"] in ("plan", "adr"):
                old.setdefault("truth_state", "superseded")
                if old["doc_type"] == "plan":
                    old["status"] = "superseded"


def _public(rec):
    return {k: v for k, v in rec.items() if not k.startswith("_")}


def build_inventory():
    records = build_records()
    docs = [_public(records[k]) for k in sorted(records)]
    return {"version": 1, "docs": docs}


def write_inventory(inv=None):
    inv = inv or build_inventory()
    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(INVENTORY, "w", encoding="utf-8") as fh:
        json.dump(inv, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return inv


# ------------------------------------------------------------- checks

def validate_record(rec):
    """Per-type required subset + enum checks -> list of problems."""
    problems = []
    t = rec.get("doc_type")
    required = REQUIRED_BY_TYPE.get(t, REQUIRED_BY_ENTITY.get(t, REQUIRED_ALL))
    for f in required:
        if f not in rec:
            problems.append("%s: missing %s" % (rec.get("source", "?"), f))
    if rec.get("truth_state") not in TRUTH_STATES:
        problems.append("%s: bad truth_state %r"
                        % (rec.get("source", "?"), rec.get("truth_state")))
    if t not in DOC_TYPES and t not in ENTITY_TYPES:
        problems.append("%s: bad doc_type %r" % (rec.get("source", "?"), t))
    for edge in rec.get("relates_to") or []:
        if not isinstance(edge, dict) or "type" not in edge or "target" not in edge:
            problems.append("%s: malformed relates_to entry %r"
                            % (rec.get("source", "?"), edge))
        elif edge["type"] not in EDGE_TYPES:
            problems.append("%s: unknown edge type %r"
                            % (rec.get("source", "?"), edge["type"]))
    return problems


def check_inventory(records=None):
    """-> list of problems: schema violations, duplicate keys, stale file."""
    records = records or build_records()
    problems = []
    seen_sources = {}
    for key, rec in records.items():
        problems += validate_record(rec)
        src = rec["source"]
        if src in seen_sources:
            problems.append("%s: two wiki_keys (%s, %s)"
                            % (src, seen_sources[src], key))
        seen_sources[src] = key
    fresh = {"version": 1, "docs": [_public(records[k]) for k in sorted(records)]}
    try:
        with open(INVENTORY, encoding="utf-8") as fh:
            on_disk = json.load(fh)
        if on_disk != fresh:
            problems.append("%s is stale — run: worklog ia-inventory" % INVENTORY)
    except (FileNotFoundError, json.JSONDecodeError):
        problems.append("%s missing — run: worklog ia-inventory" % INVENTORY)
    return problems


# ----------------------------------------------------------- normalize

def is_frozen(rec):
    """Frozen docs are never edited (§15.8/§15.9): plans, snapshots, status
    reports, dated designs. Their metadata lives in sidecars."""
    t = rec["doc_type"]
    if t in ("plan", "roadmap-snapshot", "status"):
        return True
    return t == "design" and not rec["source"].endswith(
        ("current_design_doc.md", "current_code_walkthrough.md"))


def desired_sidecar(rec, existing):
    """The sidecar the normalizer wants on disk: identity + truth + computed
    relationships + gap-fills for fields the frozen artifact lacks. Additive
    over `existing` — authored fields are never removed."""
    side = dict(existing)
    side.update({"wiki_key": rec["wiki_key"],
                 "canonical_key": rec["canonical_key"],
                 "doc_type": rec["doc_type"],
                 "truth_state": rec["truth_state"]})
    if rec.get("aliases"):
        side["aliases"] = rec["aliases"]
    for f in ("superseded_by", "supersedes", "release"):
        if rec.get(f) is not None:
            side[f] = rec[f]
    if rec["doc_type"] == "plan":
        side["status"] = rec["status"]
    fm = rec.get("_fm", [])
    for f in ("date", "name", "items", "title", "slug"):
        if f not in fm and rec.get(f) is not None:
            side[f] = rec[f]
    if rec["doc_type"] == "plan" and "items" not in fm and "items" not in side:
        side["items"] = []   # legacy pre-worklog plan: nothing was tracked
    return side


def _snapshot_chain(records):
    """Each roadmap snapshot supersedes the previous one (date order)."""
    snaps = sorted((k for k, r in records.items()
                    if r["doc_type"] == "roadmap-snapshot"),
                   key=lambda k: records[k]["source"])
    for prev, cur in zip(snaps, snaps[1:]):
        records[cur].setdefault("supersedes", prev)
        records[prev].setdefault("superseded_by", cur)


def ensure_front_matter_fields(path, fields):
    """In-place, additive frontmatter edit for sanctioned-live docs: update
    lines whose value differs, append missing ones, never touch the body or
    unrelated keys (adr.mark_superseded pattern). -> list of changed keys."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    fm, _ = parse_front_matter(text)
    changed = [k for k, v in fields.items() if fm.get(k) != v]
    if not changed:
        return []
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        end = lines.index("---", 1)
        for k in changed:
            new = dump_simple_yaml({k: fields[k]}).rstrip("\n")
            for i in range(1, end):
                if lines[i].partition(":")[0].strip() == k:
                    lines[i] = new
                    break
            else:
                lines.insert(end, new)
                end += 1
    else:
        fence = ["---"] + dump_simple_yaml(
            {k: fields[k] for k in changed}).rstrip("\n").split("\n") + ["---"]
        lines = fence + lines
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return changed


def in_place_fields(rec):
    """What a sanctioned-live doc's own frontmatter must carry (§5.6)."""
    t = rec["doc_type"]
    fields = {"wiki_key": rec["wiki_key"], "truth_state": rec["truth_state"]}
    if t == "guide":
        fields.update({"doc_type": "guide", "title": rec.get("title"),
                       "slug": rec["slug"]})
        fields = {k: v for k, v in fields.items() if v is not None}
    elif t == "design":
        fields["doc_type"] = "design"
    return fields  # adr: just wiki_key + truth_state (rich set unchanged)


def normalize(check=False):
    """Backfill wiki_key + truth_state everywhere: sidecars for frozen docs,
    in-place frontmatter for sanctioned-live docs, self-description fields on
    the publish ledger. Idempotent and additive. -> list of change
    descriptions (applied, or pending when check=True)."""
    ledger = load_ledger()
    records = build_records(ledger, drop_dynamic_sidecar=True)
    _snapshot_chain(records)
    changes = []
    for key in sorted(records):
        rec = records[key]
        if rec["doc_type"] == "roadmap":
            # generated: render_roadmap owns its frontmatter; just verify
            if "wiki_key" not in rec.get("_fm", []):
                changes.append("docs/roadmap.md lacks frontmatter — "
                               "run: worklog roadmap-render")
            continue
        if is_frozen(rec):
            existing = read_sidecar(key)
            want = desired_sidecar(rec, existing)
            if want != existing:
                changes.append("sidecar %s" % sidecar_path(key))
                if not check:
                    write_sidecar(key, want)
        else:
            fields = in_place_fields(rec)
            fm = rec.get("_fm", [])
            with open(rec["source"], encoding="utf-8") as fh:
                cur, _ = parse_front_matter(fh.read())
            need = [k for k, v in fields.items() if cur.get(k) != v]
            if need:
                changes.append("%s frontmatter: %s"
                               % (rec["source"], ", ".join(sorted(need))))
                if not check:
                    ensure_front_matter_fields(rec["source"], fields)
    # ledger self-description (§5.3): additive fields on existing entries
    dirty = False
    for key, entry in ledger.items():
        rec = records.get(key)
        if not rec:
            continue
        want = {"wiki_key": key, "canonical_key": rec["canonical_key"],
                "doc_type": rec["doc_type"], "truth_state": rec["truth_state"]}
        if rec.get("aliases"):
            want["aliases"] = rec["aliases"]
        if any(entry.get(k) != v for k, v in want.items()):
            changes.append("ledger %s" % key)
            entry.update(want)
            dirty = True
    if dirty and not check:
        with open(LEDGER, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh, indent=2, sort_keys=True)
            fh.write("\n")
    return changes
