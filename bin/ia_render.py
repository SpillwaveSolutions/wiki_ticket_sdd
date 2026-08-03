"""Reader plane: generated Home, Sidebar, truth banners, indexes, and the
publish manifest (plan ia-content-model §7, §8, §10).

Everything here is a pure function of committed files (inventory, ledger,
fold) — byte-deterministic so the freshness gate can regenerate-and-diff.
No git commands (CI checkouts lack tags), no wall clock.

The manifest closes the legacy-banner gap: a frozen page's `source_hash`
never changes, so the ledger's hash-skip would keep already-published pages
banner-less forever. Each manifest page therefore carries a `render_hash`
(source BODY + banner + renderer); wiki-publish republishes when the
ledger's `render_hash` differs. Frozen still means the SOURCE never changes
— only the rendered overlay may.

Body, not whole file, and that word is load-bearing. Publish strips front
matter for Gollum wikis (wiki-publish §3), so a front-matter-only edit —
the normalizer stamping `wiki_key`, `adr.mark_superseded`, a provenance
backfill — produces byte-identical published output. Hashing the file made
all three look like content edits: they moved `render_hash`, republished
pages whose text had not changed, and tripped the publisher's frozen-source
guard. Hashing the body makes that guard mean "the prose changed", which is
the invariant §15.8/§15.9 actually protects.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia
import ia_graph
import render_roadmap
import wiki_flavor
from fold import fold, CLOSED_STATUSES

# The platform seam (#271). Prose below writes links in the canonical
# [[Page]] notation; the flavor translates every page once, at the output
# boundary (render_all and banner), so a second wiki engine is a new class in
# wiki_flavor.FLAVORS rather than an edit to forty link sites here.
FLAVOR = wiki_flavor.get()


def use_flavor(system=None):
    """Swap the render flavor. Tests use it; a repo picks one via
    wiki.system in .work/config.yml."""
    global FLAVOR
    FLAVOR = wiki_flavor.get(system)
    return FLAVOR


def _links(text):
    return wiki_flavor.render_links(text, FLAVOR)

RENDERED = os.path.join(ia.INDEX_DIR, "rendered")
MANIFEST = os.path.join(ia.INDEX_DIR, "publish-manifest.json")
ALIASES = os.path.join(ia.INDEX_DIR, "aliases.json")

INDEX_PAGES = (  # wiki_key, filename, page name, title
    ("home", "home.md", "Home", "Home"),
    ("index/decisions", "decisions.md", "Index-Decisions", "Decisions Index"),
    ("index/releases", "releases.md", "Index-Releases", "Releases Index"),
    ("index/status", "status.md", "Index-Status", "Status Archive"),
    ("index/traceability", "traceability.md", "Index-Traceability",
     "Traceability Index"),
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
    return FLAVOR.sanitize(rec.get("title", stem))


def item_page_name(iid):
    """Wiki page name for a ticket page — stable on the ULID; titles can
    change without breaking the published URL (same rule as page_name())."""
    return "Ticket-" + iid


def release_page_name(tag):
    """Wiki page name for a release page, e.g. 'Release-v0.13.0'."""
    return "Release-" + tag


def pr_page_name(pr_num):
    """Wiki page name for a PR page, e.g. 'PR-122'."""
    return "PR-%s" % pr_num


def banner(rec, by_key):
    """Reader-visible truth banner (§6.1), one blockquote line.

    Wraps _banner_text so banner links get flavor-translated too: banners
    reach the reader through the MANIFEST, not through `rendered`, so the
    boundary in render_all() never sees them."""
    return _links(_banner_text(rec, by_key))


PLAN_STATE = {"completed": "completed plan",
              "active": "plan in flight",
              "planned": "plan not yet started"}


def _plan_state(rec):
    """A plan's banner label, from the leading word of its status (#292).

    `status` on a plan is free prose, not an enum. Real values run from
    "completed" to "planned — not yet scheduled; implementation tasks attach
    to the epic when work starts" — a whole sentence that cannot be dropped
    into a one-line banner. Only the leading word carries the state; the rest
    is detail that belongs in the page.

    Unknown prose returns None and the caller falls back to saying nothing
    about state. That is deliberate: inventing a label for prose we cannot
    read is how the banner came to announce plans as status reports in the
    first place. Silence beats a confident guess.
    """
    first = (rec.get("status") or "").split()[:1]
    return PLAN_STATE.get(first[0].lower()) if first else None


def _banner_text(rec, by_key):
    ts = rec["truth_state"]
    if ts == "current" and ia.is_frozen(rec):
        # is_frozen() covers plan/roadmap-snapshot/status/dated-design (#137)
        # — only status is a "report"; the rest need their own wording.
        if rec["doc_type"] == "status":
            # e.g. the newest status report: current truth, but frozen — it
            # will be archived by its successor, never regenerated.
            # rec["kind"], not .get(..., "status"): kind is REQUIRED on a
            # status record (ia.py schema), so a missing one is a schema
            # violation and must raise. The old default silently rendered
            # plausible prose over broken data (#292).
            return ("> **Current** — the latest %s report. Reports freeze "
                    "once published; corrections appear in later reports."
                    % rec["kind"])
        if rec["doc_type"] == "plan":
            return ("> **Current** — %s; plans are frozen "
                    "once written, a changed design gets a new plan."
                    % (_plan_state(rec) or "the current plan"))
        if rec["doc_type"] == "roadmap-snapshot":
            return ("> **Current** — the current roadmap snapshot; frozen "
                    "once published, a new snapshot supersedes it.")
        return ("> **Current** — the current design record; frozen once "
                "written, an updated design gets a new dated copy.")
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
        "[[User-Guide]] · [[Design-Doc]] · [[Code-Walkthrough]] · "
        "[[Worklog-Spec]]",
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


def render_traceability(graph, records):
    """§9.5: the evidence chain per work item, forward and backward links
    derived from one edge set."""
    fwd, back = {}, {}
    for e in graph["edges"]:
        fwd.setdefault(e["from"], []).append((e["type"], e["to"]))
        back.setdefault(e["to"], []).append(
            (ia_graph.REVERSE[e["type"]], e["from"]))
    nodes = graph["nodes"]

    def show(key):
        n = nodes.get(key, {})
        rec = records.get(key)
        if rec:
            return "[[%s]]" % page_name(rec)
        if n.get("doc_type") == "ticket":
            return "[%s](%s)" % (key.split("/", 1)[1], n["url"]) if n.get("url") else key
        return n.get("title", key) if n.get("doc_type") == "item" else key

    lines = ["# Traceability", "",
             "_The evidence chain: plan → item → ticket → code → release, "
             "forward and backward. Generated from `docs/.index/_graph.json`; "
             "do not edit._", ""]
    items = sorted((k for k, n in nodes.items()
                    if n.get("doc_type") == "item"),
                   key=lambda k: k, reverse=True)
    for key in items:
        n = nodes[key]
        lines.append("### %s" % n.get("title", key))
        lines.append("`%s` · status: %s" % (key.split("/", 1)[1],
                                            n.get("status", "?")))
        for typ, to in sorted(fwd.get(key, [])):
            lines.append("- %s: %s" % (typ, show(to)))
        for typ, frm in sorted(back.get(key, [])):
            lines.append("- %s: %s" % (typ, show(frm)))
        lines.append("")
    return "\n".join(lines) + "\n"


TICKET_BADGE = {"todo": "open", "in_progress": "in-progress",
                "blocked": "blocked", "done": "done", "cancelled": "done"}


def one_line_summary(it):
    """First sentence of the item's body — derived at render time from
    committed state, never stored/cached (module docstring, byte-determinism).
    Falls back to the title when there's no body."""
    text = (it.get("body") or it.get("title") or "").strip()
    if not text:
        return ""
    m = re.match(r"(.+?[.!?])(\s|$)", text, flags=re.S)
    return (m.group(1) if m else text).strip()


def _upward_chain(iid, items, fwd, back):
    """(id, item) pairs from the immediate parent up to the root — stops on
    a missing item or a cycle rather than looping forever on a corrupt log."""
    chain, seen, cur = [], {iid}, iid
    while True:
        parent_key = ia_graph.item_links(cur, fwd, back)["parent"]
        if not parent_key:
            return chain
        pid = parent_key.split("/", 1)[1]
        if pid in seen:
            return chain
        p_it = items.get(pid)
        if not p_it:
            return chain
        seen.add(pid)
        chain.append((pid, p_it))
        cur = pid


def render_item_page(iid, items, fwd, back):
    """A ticket page (§ artifact-pages plan): own description + status,
    upward hierarchy to the epic, downward to children with an aggregate
    progress rollup, linked PRs, and the linked release — one function,
    branching by level rather than four near-duplicate renderers."""
    it = items[iid]
    level = it.get("level", "task")
    links = ia_graph.item_links(iid, fwd, back)

    lines = ["# %s" % it.get("title", iid), "",
             "`%s` · %s/%s · **%s**" % (
                 iid, level, it.get("kind", "?"),
                 TICKET_BADGE.get(it.get("status"), it.get("status") or "?")),
             ""]
    summary = one_line_summary(it)
    if summary:
        lines += [summary, ""]

    upward = _upward_chain(iid, items, fwd, back)
    if upward:
        lines += ["## Hierarchy", ""]
        lines += ["- %s: [[%s]] %s — %s" % (
            p_it.get("level", "?"), item_page_name(pid),
            p_it.get("title", pid), one_line_summary(p_it))
                  for pid, p_it in upward]
        lines += [""]

    child_ids = sorted(c.split("/", 1)[1] for c in links["children"])
    if child_ids:
        lines += ["## Subtasks" if level in ("task", "subtask")
                  else "## Children", ""]
        for cid in child_ids:
            c_it = items.get(cid)
            if not c_it:
                continue
            lines.append("- [[%s]] %s — %s (%s)" % (
                item_page_name(cid), c_it.get("title", cid),
                one_line_summary(c_it),
                TICKET_BADGE.get(c_it.get("status"), c_it.get("status") or "?")))
        done = sum(1 for cid in child_ids
                  if items.get(cid, {}).get("status") in CLOSED_STATUSES)
        lines += ["", "Progress: %d/%d done" % (done, len(child_ids)), ""]

    if links["prs"]:
        lines += ["## Linked PRs", ""]
        lines += ["- [[%s]]" % pr_page_name(pr_key.split("/", 1)[1])
                 for pr_key in links["prs"]]
        lines += [""]

    if links["release"]:
        lines += ["## Release", "",
                  "- [[%s]]" % release_page_name(
                      links["release"].split("/", 1)[1]), ""]

    ext = it.get("external") or {}
    if ext.get("url"):
        lines += ["## Related tickets", "",
                  "- [%s #%s](%s)" % (ext.get("system", "ticket"),
                                      ext.get("key", ""), ext["url"]), ""]

    return "\n".join(lines).rstrip() + "\n"


def _release_tree(shipped_ids, items):
    """Nested-list hierarchy of the items that shipped in a release —
    roots (no parent among the shipped set) with their shipped descendants
    indented beneath. A lighter-weight 'visual hierarchy' than a Mermaid
    diagram; viz_mermaid.hierarchy() only covers OPEN items (a different,
    unrelated use case: 'what's left'), so it isn't reused here."""
    shipped = set(shipped_ids)
    children_of = {}
    for iid in shipped_ids:
        pid = items[iid].get("parent")
        if pid in shipped:
            children_of.setdefault(pid, []).append(iid)
    roots = sorted(iid for iid in shipped_ids if items[iid].get("parent") not in shipped)

    def walk(iid, depth):
        it = items[iid]
        yield "%s- [[%s]] %s (%s)" % (
            "  " * depth, item_page_name(iid), it.get("title", iid),
            it.get("level", "?"))
        for cid in sorted(children_of.get(iid, [])):
            yield from walk(cid, depth + 1)

    lines = []
    for iid in roots:
        lines.extend(walk(iid, 0))
    return lines


def render_release_page(tag, items, fwd, back):
    """A release page (§ artifact-pages plan): Change Log and Related PRs/
    Tickets are graph-derived from milestone-tagged closed items — not a
    CHANGELOG.md parser (that file stays human-authored prose, untouched;
    this is a separate, always-accurate, mechanical list)."""
    shipped = sorted(iid for iid, it in items.items()
                     if it.get("status") in CLOSED_STATUSES
                     and it.get("milestone") == tag)
    lines = ["# Release %s" % tag, "",
             "`release/%s` · **shipped**" % tag, "",
             "%d item(s) shipped." % len(shipped), ""]

    if shipped:
        lines += ["## Change Log", ""]
        for iid in shipped:
            it = items[iid]
            ext = (it.get("external") or {}).get("key")
            ref = " (#%s)" % ext if ext else ""
            lines.append("- [[%s]] %s%s — %s" % (
                item_page_name(iid), it.get("title", iid), ref,
                one_line_summary(it)))
        lines += [""]

        lines += ["## Release Tree", ""]
        lines += _release_tree(shipped, items) + [""]

    all_prs, all_related, deps = set(), set(), set()
    for iid in shipped:
        links = ia_graph.item_links(iid, fwd, back)
        all_prs.update(links["prs"])
        for pid, _ in _upward_chain(iid, items, fwd, back):
            all_related.add(pid)
        for dep in items[iid].get("depends_on") or []:
            deps.add(dep)
    all_related -= set(shipped)

    if all_prs:
        lines += ["## Related PRs", ""]
        lines += ["- [[%s]]" % pr_page_name(pr_key.split("/", 1)[1])
                 for pr_key in sorted(all_prs)]
        lines += [""]

    if all_related:
        lines += ["## Related Tickets", ""]
        lines += ["- [[%s]] %s (%s)" % (
            item_page_name(rid), items[rid].get("title", rid),
            items[rid].get("level", "?")) for rid in sorted(all_related)]
        lines += [""]

    if deps:
        lines += ["## Dependencies & Risks", ""]
        lines += ["- depends on: [[%s]] %s" % (
            item_page_name(d), items.get(d, {}).get("title", d))
                 for d in sorted(deps)]
        lines += [""]

    return "\n".join(lines).rstrip() + "\n"


def render_pr_page(pr_num, items, fwd, back):
    """A PR page (§ artifact-pages plan): linked tickets + related release
    from existing graph edges, plus live state/files/review from the
    `pr/<N>` sidecar that `worklog pr-sync` writes. The sidecar is a
    committed file, so this stays a pure function of the working tree; a PR
    that has never been synced degrades to the original 'not tracked'."""
    pr_key = "pr/%s" % pr_num
    meta = ia.read_sidecar(pr_key)
    linked = sorted(frm.split("/", 1)[1] for typ, frm in back.get(pr_key, [])
                    if typ == "delivers")
    title = meta.get("title")
    lines = ["# PR #%s%s" % (pr_num, " — %s" % title if title else ""), ""]
    if meta:
        lines += ["`%s` · status: **%s**" % (pr_key, meta.get("state", "?")),
                  "",
                  "- Review: %s" % meta.get("review", "none"),
                  "- Checks: %s" % meta.get("checks", "none")]
        if meta.get("merged_at"):
            lines.append("- Merged: %s" % meta["merged_at"])
        if meta.get("url"):
            lines.append("- Source: %s" % meta["url"])
        lines += [""]
        files = [f for f in meta.get("files") or [] if f]
        lines += ["## Changed Files", ""]
        lines += ["- `%s`" % f for f in files] if files else \
                 ["_No files recorded._"]
        lines += [""]
    else:
        lines += ["`%s` · status: **not tracked**" % pr_key, "",
                  "Changed files: not tracked. Test/Review status: not "
                  "tracked — run `worklog pr-sync %s`." % pr_num, ""]

    if linked:
        lines += ["## Linked Tickets", ""]
        for iid in linked:
            it = items.get(iid)
            if not it:
                continue
            lines.append("- [[%s]] %s — %s" % (
                item_page_name(iid), it.get("title", iid), one_line_summary(it)))
        lines += [""]

        releases, epics = set(), set()
        for iid in linked:
            links = ia_graph.item_links(iid, fwd, back)
            if links["release"]:
                releases.add(links["release"])
            chain = _upward_chain(iid, items, fwd, back)
            if chain:
                epics.add(chain[-1][0])  # root ancestor
        if releases:
            lines += ["## Related Releases", ""]
            lines += ["- [[%s]]" % release_page_name(r.split("/", 1)[1])
                     for r in sorted(releases)]
            lines += [""]
        if epics:
            lines += ["## Traceability", ""]
            lines += ["- back to: [[%s]] %s" % (
                item_page_name(e), items.get(e, {}).get("title", e))
                     for e in sorted(epics)]
            lines += [""]

    return "\n".join(lines).rstrip() + "\n"


# ------------------------------------------------------------- manifest

def _hash_bytes(data):
    return hashlib.sha256(data).hexdigest()[:12]


def _file_hash(path):
    with open(path, "rb") as fh:
        return _hash_bytes(fh.read())


def _body_hash(path):
    """Hash of the doc BELOW its front matter — what a reader actually gets.

    Publish strips front matter, so two files differing only there publish
    identically. Hashing the body is therefore both cheaper (no needless
    republish) and stricter in the way that matters: a change to this hash
    means the prose changed, which is the only thing the frozen-doc rule
    was ever protecting.
    """
    with open(path, encoding="utf-8") as fh:
        return _hash_bytes(ia.parse_front_matter(fh.read())[1].encode())


def build_manifest(records, rendered, items=None):
    """The intended publish set (§10.2): every rendered page + every doc the
    default set publishes, each with its banner and render_hash. Also one
    entry per work item/release/PR once its page exists in `rendered` --
    keyed off the tickets/releases/prs filename prefix rather than three
    separate loops, so a new entity type only needs a new prefix here."""
    pages = []
    for key, fname, pname, title in INDEX_PAGES:
        src = "%s/%s" % (RENDERED, fname)
        pages.append({"wiki_key": key, "source": src, "title": title,
                      "page_name": pname, "truth_state": "current",
                      "render": "as-is", "frozen": False,
                      "render_hash": _hash_bytes(rendered[fname].encode())})
    items = items or {}
    for fname in sorted(rendered):
        if fname.startswith("tickets/"):
            iid = fname[len("tickets/"):-3]
            it = items.get(iid, {})
            wiki_key, pname = "item/" + iid, item_page_name(iid)
            title = it.get("title", iid)
            ts = TICKET_BADGE.get(it.get("status"), it.get("status") or "?")
        elif fname.startswith("releases/"):
            tag = fname[len("releases/"):-3]
            wiki_key, pname = "release/" + tag, release_page_name(tag)
            title, ts = "Release %s" % tag, "shipped"
        elif fname.startswith("prs/"):
            num = fname[len("prs/"):-3]
            wiki_key, pname = "pr/" + num, pr_page_name(num)
            meta = ia.read_sidecar(wiki_key)
            title = "PR #%s%s" % (num, " — %s" % meta["title"]
                                  if meta.get("title") else "")
            ts = meta.get("state") or "not tracked"
        else:
            continue
        pages.append({"wiki_key": wiki_key,
                      "source": "%s/%s" % (RENDERED, fname),
                      "title": title, "page_name": pname,
                      "truth_state": ts, "render": "as-is", "frozen": False,
                      "render_hash": _hash_bytes(rendered[fname].encode())})
    for key in sorted(records):
        rec = records[key]
        if rec["doc_type"] == "guide" and key == "home":
            continue  # the home SOURCE is the intro; the PAGE is rendered
        b = banner(rec, records)
        frozen = ia.is_frozen(rec)
        body = _body_hash(rec["source"])
        pages.append({
            "wiki_key": key, "source": rec["source"],
            "title": rec.get("title", key), "page_name": page_name(rec),
            "truth_state": rec["truth_state"], "banner": b,
            # source_hash is the FROZEN-DOC GUARD's input: the publisher
            # compares it against the ledger and stops when a frozen doc's
            # prose changed. Carried here so the publisher never has to hash
            # files itself — and so it cannot accidentally hash the wrong
            # thing and mistake a metadata stamp for an edit.
            "source_hash": body,
            "render": "doc+banner", "frozen": frozen,
            "render_hash": _hash_bytes((body + b).encode())})
    out = {"version": 1, "pages": pages,
           "sidebar": {"source": "%s/_Sidebar.md" % RENDERED,
                       "render_hash": _hash_bytes(
                           rendered["_Sidebar.md"].encode())}}
    # Build provenance, recorded ONCE here rather than on every rendered
    # page. Each page under docs/.index/rendered/ is a projection of the
    # whole log by one build, so "the commit" is a property of the build,
    # not of any page. Stamping all ~344 of them would be 344 copies of one
    # fact, would move every render_hash at once, and would be invisible to
    # every reader anyway — publish strips front matter (wiki-publish §3).
    #
    # From the newest event's `git` field, never `git rev-parse`: write_all
    # regenerates and byte-compares this file, so a HEAD-derived value would
    # differ from the committed one on the very next run. Omitted when the
    # log carries no sha; never written empty.
    top = render_roadmap.top_event(render_roadmap.PATHS)
    if top and top.get("git"):
        out["git_hash"] = top["git"]
    return out


def build_aliases(records):
    """legacy key -> canonical key redirect insurance (§14.3)."""
    return {r["wiki_key"]: r["canonical_key"] for r in records.values()
            if r["wiki_key"] != r["canonical_key"]}


# ------------------------------------------------------------ driver

def render_all():
    """-> ({filename: content}, manifest, aliases, graph)."""
    records = ia.build_records()
    fr = fold((".work/todo.jsonl", ".work/done.jsonl"))
    graph = ia_graph.build_graph(records, fr.items)
    fwd, back = ia_graph.build_adjacency(graph)
    rendered = {
        "home.md": render_home(records, True),
        "_Sidebar.md": render_sidebar(records, True),
        "decisions.md": render_decisions(records),
        "releases.md": render_releases(records, fr.items),
        "status.md": render_status_index(records),
        "traceability.md": render_traceability(graph, records),
    }
    for iid in fr.items:
        rendered["tickets/%s.md" % iid] = render_item_page(iid, fr.items, fwd, back)
    for key, node in graph["nodes"].items():
        if node.get("doc_type") == "release":
            tag = key.split("/", 1)[1]
            rendered["releases/%s.md" % tag] = render_release_page(
                tag, fr.items, fwd, back)
        elif node.get("doc_type") == "pr":
            num = key.split("/", 1)[1]
            rendered["prs/%s.md" % num] = render_pr_page(
                num, fr.items, fwd, back)
    # The link boundary: translate canonical [[Page]] notation into the
    # configured wiki's syntax BEFORE the manifest hashes the bytes, so
    # render_hash always describes what actually gets published.
    rendered = {name: _links(text) for name, text in rendered.items()}
    manifest = build_manifest(records, rendered, fr.items)
    aliases = build_aliases(records)
    return rendered, manifest, aliases, graph


def write_all(check=False):
    """Write rendered pages + manifest + aliases + graph; in check mode
    report what is stale instead. -> list of stale/written paths."""
    rendered, manifest, aliases, graph = render_all()
    out = []
    targets = [(os.path.join(RENDERED, f), c + ("" if c.endswith("\n") else "\n"))
               for f, c in rendered.items()]
    targets += [(MANIFEST, json.dumps(manifest, indent=1, sort_keys=True) + "\n"),
                (ALIASES, json.dumps(aliases, indent=1, sort_keys=True) + "\n"),
                (ia_graph.GRAPH, json.dumps(graph, indent=1, sort_keys=True) + "\n")]
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
