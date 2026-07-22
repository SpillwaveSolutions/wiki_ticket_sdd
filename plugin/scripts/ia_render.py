"""Reader plane: generated Home, Sidebar, truth banners, indexes, and the
publish manifest (plan ia-content-model §7, §8, §10).

Everything here is a pure function of committed files (inventory, ledger,
fold) — byte-deterministic so the freshness gate can regenerate-and-diff.
No git commands (CI checkouts lack tags), no wall clock.

The manifest closes the legacy-banner gap: a frozen page's `source_hash`
never changes, so the ledger's hash-skip would keep already-published pages
banner-less forever. Each manifest page therefore carries a `render_hash`
(source bytes + banner + renderer); wiki-publish republishes when the
ledger's `render_hash` differs. Frozen still means the SOURCE never changes
— only the rendered overlay may.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia
from fold import fold, CLOSED_STATUSES

RENDERED = os.path.join(ia.INDEX_DIR, "rendered")
MANIFEST = os.path.join(ia.INDEX_DIR, "publish-manifest.json")
ALIASES = os.path.join(ia.INDEX_DIR, "aliases.json")

INDEX_PAGES = (  # wiki_key, filename, page name, title
    ("home", "home.md", "Home", "Home"),
    ("index/decisions", "decisions.md", "Index-Decisions", "Decisions Index"),
    ("index/releases", "releases.md", "Index-Releases", "Releases Index"),
    ("index/status", "status.md", "Index-Status", "Status Archive"),
)


def page_name(rec):
    """Wiki page name for a doc: the published URL's basename when it exists
    (never rename a published page), else the repo's naming convention."""
    url = rec.get("wiki") or ""
    if "/wiki/" in url:
        return url.rsplit("/", 1)[1]
    t, stem = rec["doc_type"], os.path.splitext(
        os.path.basename(rec["source"]))[0]
    if t == "plan":
        return "Plan-" + rec.get("slug", stem)
    if t == "adr":
        return "ADR-" + stem
    if t == "roadmap-snapshot":
        return "Roadmap-" + stem
    if t == "status":
        return "Status-" + stem
    if t == "roadmap":
        return "Roadmap"
    if t == "design":
        base = ("Design-Doc" if "design_doc" in stem else "Code-Walkthrough")
        m = re.match(r"(\d{4}-\d{2}-\d{2}_.+?)_(?:design_doc|code_walkthrough)$", stem)
        return base + ("-" + m.group(1) if m else "")
    return rec.get("title", stem).replace(" ", "-")


def banner(rec, by_key):
    """Reader-visible truth banner (§6.1), one blockquote line."""
    ts = rec["truth_state"]
    if ts == "current" and ia.is_frozen(rec):
        # e.g. the newest status report: current truth, but frozen — it will
        # be archived by its successor, never regenerated
        return ("> **Current** — the latest %s report. Reports freeze once "
                "published; corrections appear in later reports."
                % rec.get("kind", "status"))
    if ts == "current":
        gen = rec.get("generated_at")
        src = " regenerated at %s" % gen if gen else ""
        return ("> **Current** — this is the living version;%s. "
                "Historical snapshots are linked from [[Index-Releases]]." % src
                if src else
                "> **Current** — this is the living version. Historical "
                "snapshots are linked from [[Index-Releases]].")
    if ts == "snapshot":
        rel = rec.get("release")
        of = " of release %s" % rel if rel else ""
        live = ("[[Design-Doc]]" if rec["doc_type"] == "design" and
                "design_doc" in rec["source"] else
                "[[Code-Walkthrough]]" if rec["doc_type"] == "design" else
                "[[Roadmap]]")
        date = rec.get("date", "")
        return ("> **Snapshot**%s (%s) — frozen record. The current version "
                "is %s." % (of, date, live))
    if ts == "superseded":
        succ = by_key.get(rec.get("superseded_by"))
        link = "[[%s]]" % page_name(succ) if succ else "a newer document"
        return ("> **Superseded** by %s — kept as the record of why the "
                "earlier approach changed." % link)
    return ("> **Archived** — corrections, if any, appear in later reports; "
            "do not act on this page.")


def _plans_and_adrs(records):
    plans = [r for r in records.values() if r["doc_type"] == "plan"]
    adrs = [r for r in records.values() if r["doc_type"] == "adr"]
    plans.sort(key=lambda r: r["source"], reverse=True)   # newest first
    adrs.sort(key=lambda r: r["source"])
    return plans, adrs


def render_home(records, has_graph=False):
    """Question-driven Home (§3): hand-written intro + six tiles."""
    intro = ""
    home = records.get("home")
    if home:
        with open(home["source"], encoding="utf-8") as fh:
            _, body = ia.parse_front_matter(fh.read())
        intro = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
    latest = [r for r in records.values()
              if r["doc_type"] == "status" and r["truth_state"] == "current"]
    latest.sort(key=lambda r: r["source"], reverse=True)
    status_link = (" · latest status: [[%s]]" % page_name(latest[0])
                   if latest else "")
    active = [r for r in records.values() if r["doc_type"] == "plan"
              and r.get("status") in ("planned", "active")]
    active.sort(key=lambda r: r["source"], reverse=True)
    active_links = ", ".join("[[%s]]" % page_name(r) for r in active[:5])
    lines = [intro, "", "---", ""]
    lines += [
        "## What is this project?",
        "[[User-Guide]] · [[Design-Doc]] · [[Worklog-Spec]]",
        "",
        "## What are we working on now?",
        "[[Roadmap]]%s" % status_link,
        ("Active plans: " + active_links) if active_links else "",
        "",
        "## Why was it built this way?",
        "[[Index-Decisions]] — ADRs and plans, with supersede chains",
        "",
        "## What has shipped?",
        "[[Index-Releases]] — releases with their frozen snapshots · "
        "[[Index-Status]] — the report archive",
        "",
        "## How do I use it?",
        "[[User-Guide]] · [[CLI-Reference]] · [[Plugin-Guide]]",
    ]
    if has_graph:
        lines += ["", "## Where is the evidence?",
                  "[[Index-Traceability]] — the plan → item → ticket → "
                  "release chain"]
    lines += ["", "---",
              "_Generated by `worklog ia-render`; edit the intro in "
              "`docs/wiki-home.md`, never this page._"]
    return "\n".join(l for l in lines if l is not None) + "\n"


def render_sidebar(records, has_graph=False):
    """Two-plane sidebar (§7.1): Current Truth / History / Reference."""
    plans, adrs = _plans_and_adrs(records)
    snaps = sorted((r for r in records.values()
                    if r["doc_type"] == "roadmap-snapshot"),
                   key=lambda r: r["source"], reverse=True)
    lines = ["### Current truth", "",
             "- [[Roadmap]]",
             "- [[Design-Doc]] · [[Code-Walkthrough]]"]
    for r in plans:
        if r["truth_state"] == "current" and r.get("status") in ("planned", "active"):
            lines.append("- Plan: [[%s]]" % page_name(r))
    for r in adrs:
        if r["truth_state"] == "current":
            lines.append("- [[%s]]" % page_name(r))
    lines += ["", "### History", "", "- [[Index-Releases]]"]
    if snaps:
        lines.append("- Latest snapshot: [[%s]]" % page_name(snaps[0]))
    lines += ["- [[Index-Status]]", "- [[Index-Decisions]]"]
    lines += ["", "### Reference", "",
              "- [[User-Guide]] · [[CLI-Reference]] · [[Plugin-Guide]]",
              "- [[Worklog-Spec]]"]
    if has_graph:
        lines.append("- [[Index-Traceability]]")
    return "\n".join(lines) + "\n"


def render_decisions(records):
    """Q3: ADRs by status + plans with lifecycle, supersede chains (§8.2)."""
    plans, adrs = _plans_and_adrs(records)
    lines = ["# Decisions", "",
             "_Why things are the way they are: ADRs (rules adopted) and "
             "plans (designs executed). Generated; do not edit._", "",
             "## Architecture Decision Records", "",
             "| ADR | Status | Date | Supersedes |", "|---|---|---|---|"]
    for r in adrs:
        sup = r.get("supersedes")
        lines.append("| [[%s]] %s | %s | %s | %s |" % (
            page_name(r), r.get("title", ""), r.get("status", ""),
            r.get("date", ""), sup if sup is not None else "—"))
    lines += ["", "## Plans", "",
              "| Plan | Lifecycle | Truth | Date |", "|---|---|---|---|"]
    for r in plans:
        note = (" → superseded by [[%s]]" % page_name(records[r["superseded_by"]])
                if r.get("superseded_by") in records else "")
        lines.append("| [[%s]] %s | %s%s | %s | %s |" % (
            page_name(r), r.get("title", ""), r.get("status", ""), note,
            r["truth_state"], r.get("date", "")))
    return "\n".join(lines) + "\n"


def render_releases(records, items):
    """Q4: one section per release, joining snapshots, designs, and closed
    items by milestone (§8.3). No git calls — releases come from doc
    metadata, which is committed state."""
    releases = {}
    for r in records.values():
        rel = r.get("release")
        # snapshots only: the live design pair carries release (its tag) but
        # is not frozen evidence of that release
        if rel and r["truth_state"] == "snapshot":
            releases.setdefault(rel, []).append(r)
    closed = {}
    for i in items.values():
        if i.get("status") in CLOSED_STATUSES and i.get("milestone"):
            closed.setdefault(i["milestone"], []).append(i)
    lines = ["# Releases", "",
             "_What shipped, with the frozen evidence for each release. "
             "Generated; do not edit._", ""]

    def vkey(rel):
        return [int(x) for x in re.findall(r"\d+", rel)]
    for rel in sorted(releases, key=vkey, reverse=True):
        docs = sorted(releases[rel], key=lambda r: r["source"])
        date = next((r.get("date") for r in docs if r.get("date")), "")
        lines.append("## %s%s" % (rel, " — %s" % date if date else ""))
        lines.append("")
        for r in docs:
            kind = {"roadmap-snapshot": "Roadmap snapshot",
                    "design": "Design"}.get(r["doc_type"], r["doc_type"])
            lines.append("- %s: [[%s]]" % (kind, page_name(r)))
        for i in sorted(closed.get(rel, []), key=lambda i: i["id"]):
            ext = (i.get("external") or {}).get("key")
            ref = " (#%s)" % ext if ext else ""
            lines.append("- Shipped: %s%s" % (i.get("title", i["id"]), ref))
        lines.append("")
    return "\n".join(lines) + "\n"


def render_status_index(records):
    """Status Archive (§8.4): newest first, current flagged."""
    reports = sorted((r for r in records.values() if r["doc_type"] == "status"),
                     key=lambda r: r["source"], reverse=True)
    lines = ["# Status Archive", "",
             "_All status reports; the newest of each kind is the current "
             "one. Generated; do not edit._", "",
             "| Report | Kind | Date | Truth |", "|---|---|---|---|"]
    for r in reports:
        lines.append("| [[%s]] | %s | %s | %s |" % (
            page_name(r), r.get("kind", ""), r.get("date", ""),
            r["truth_state"]))
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------- manifest

def _hash_bytes(data):
    return hashlib.sha256(data).hexdigest()[:12]


def _file_hash(path):
    with open(path, "rb") as fh:
        return _hash_bytes(fh.read())


def build_manifest(records, rendered):
    """The intended publish set (§10.2): every rendered page + every doc the
    default set publishes, each with its banner and render_hash."""
    pages = []
    for key, fname, pname, title in INDEX_PAGES:
        src = "%s/%s" % (RENDERED, fname)
        pages.append({"wiki_key": key, "source": src, "title": title,
                      "page_name": pname, "truth_state": "current",
                      "render": "as-is", "frozen": False,
                      "render_hash": _hash_bytes(rendered[fname].encode())})
    for key in sorted(records):
        rec = records[key]
        if rec["doc_type"] == "guide" and key == "home":
            continue  # the home SOURCE is the intro; the PAGE is rendered
        b = banner(rec, records)
        frozen = ia.is_frozen(rec)
        pages.append({
            "wiki_key": key, "source": rec["source"],
            "title": rec.get("title", key), "page_name": page_name(rec),
            "truth_state": rec["truth_state"], "banner": b,
            "render": "doc+banner", "frozen": frozen,
            "render_hash": _hash_bytes(
                (_file_hash(rec["source"]) + b).encode())})
    return {"version": 1, "pages": pages,
            "sidebar": {"source": "%s/_Sidebar.md" % RENDERED,
                        "render_hash": _hash_bytes(
                            rendered["_Sidebar.md"].encode())}}


def build_aliases(records):
    """legacy key -> canonical key redirect insurance (§14.3)."""
    return {r["wiki_key"]: r["canonical_key"] for r in records.values()
            if r["wiki_key"] != r["canonical_key"]}


# ------------------------------------------------------------ driver

def render_all():
    """-> {filename: content} for rendered/, plus manifest + aliases dicts."""
    records = ia.build_records()
    fr = fold((".work/todo.jsonl", ".work/done.jsonl"))
    has_graph = os.path.exists(os.path.join(ia.INDEX_DIR, "_graph.json"))
    rendered = {
        "home.md": render_home(records, has_graph),
        "_Sidebar.md": render_sidebar(records, has_graph),
        "decisions.md": render_decisions(records),
        "releases.md": render_releases(records, fr.items),
        "status.md": render_status_index(records),
    }
    manifest = build_manifest(records, rendered)
    aliases = build_aliases(records)
    return rendered, manifest, aliases


def write_all(check=False):
    """Write rendered pages + manifest + aliases; in check mode report what
    is stale instead. -> list of stale/written paths."""
    rendered, manifest, aliases = render_all()
    out = []
    targets = [(os.path.join(RENDERED, f), c + ("" if c.endswith("\n") else "\n"))
               for f, c in rendered.items()]
    targets += [(MANIFEST, json.dumps(manifest, indent=1, sort_keys=True) + "\n"),
                (ALIASES, json.dumps(aliases, indent=1, sort_keys=True) + "\n")]
    for path, content in targets:
        try:
            with open(path, encoding="utf-8") as fh:
                if fh.read() == content:
                    continue
        except FileNotFoundError:
            pass
        out.append(path)
        if not check:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
    return out
