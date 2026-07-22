"""Bidirectional traceability (plan ia-content-model §9): typed-edge graph
over docs + work items, PR/commit linking, and the unlinked-evidence check.

Forward edges only are stored; reverse edges are DERIVED (§9.4) — the graph
builder inverts `relates_to` plus the fields the log already carries
(`parent`, `plan`, `milestone`, `external`, `supersedes`). Deterministic:
pure function of records + fold; no git or network calls.

Item metadata stays overlay-only: an item sidecar
(docs/.index/item/<ULID>.yml) holds ONLY what the event log cannot represent
(code edges, authored relates_to) — never title/status/external, which the
fold owns. Anything else would be a second source of truth for item state.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia
from fold import fold, CLOSED_STATUSES

GRAPH = os.path.join(ia.INDEX_DIR, "_graph.json")
SUGGESTIONS = ".work/suggestions.jsonl"

REVERSE = {"produces": "produced-by", "decides": "decided-by",
           "implements": "implemented-by", "supersedes": "superseded-by",
           "verified-by": "verifies", "lands-in": "delivers",
           "belongs-to": "contains", "targets": "includes",
           "snapshot-of": "snapshots", "references": "referenced-by"}


def item_key(ulid_):
    return "item/" + ulid_


def item_sidecar(ulid_):
    return ia.read_sidecar(item_key(ulid_))


def build_graph(records=None, items=None):
    """-> {"nodes": {key: {...}}, "edges": [{"from","type","to"}...]}."""
    if records is None:
        records = ia.build_records()
    if items is None:
        items = fold((".work/todo.jsonl", ".work/done.jsonl")).items
    nodes, edges = {}, set()

    def edge(frm, typ, to):
        edges.add((frm, typ, to))

    for key in sorted(records):
        rec = records[key]
        nodes[key] = {"doc_type": rec["doc_type"],
                      "title": rec.get("title", key),
                      "truth_state": rec["truth_state"],
                      "source": rec["source"]}
        for iid in rec.get("items") or []:
            edge(key, "produces", item_key(iid))
        sup = rec.get("supersedes")
        if isinstance(sup, str):
            edge(key, "supersedes", sup)
        if rec["doc_type"] == "roadmap-snapshot":
            edge(key, "snapshot-of", "roadmap")
        if rec["doc_type"] == "design" and rec["truth_state"] == "snapshot":
            live = ("design/current-design-doc" if "design_doc" in rec["source"]
                    else "design/current-code-walkthrough")
            edge(key, "snapshot-of", live)
        if rec.get("release"):
            edge(key, "targets", "release/" + rec["release"])
        for e in rec.get("relates_to") or []:
            if isinstance(e, dict) and e.get("type") in REVERSE:
                edge(key, e["type"], str(e.get("target")))
    plans_by_path = {r["source"]: k for k, r in records.items()
                     if r["doc_type"] == "plan"}
    for iid in sorted(items):
        it = items[iid]
        key = item_key(iid)
        nodes[key] = {"doc_type": "item", "title": it.get("title", iid),
                      "status": it.get("status", "")}
        if it.get("parent"):
            edge(key, "belongs-to", item_key(it["parent"]))
        if it.get("plan") and it["plan"] in plans_by_path:
            edge(plans_by_path[it["plan"]], "produces", key)
        if it.get("milestone"):
            edge(key, "targets", "release/" + it["milestone"])
        ext = it.get("external") or {}
        if ext.get("key"):
            tkey = "ticket/%s#%s" % (ext.get("system", "?"), ext["key"])
            nodes[tkey] = {"doc_type": "ticket", "url": ext.get("url", "")}
            edge(key, "references", tkey)
        side = item_sidecar(iid)
        for c in side.get("code") or []:
            if isinstance(c, dict) and c.get("pr") is not None:
                pkey = "pr/%s" % c["pr"]
                nodes[pkey] = {"doc_type": "pr"}
                edge(key, "lands-in", pkey)
        for e in side.get("relates_to") or []:
            if isinstance(e, dict) and e.get("type") in REVERSE:
                edge(key, e["type"], str(e.get("target")))
    for rel in sorted({e[2] for e in edges if e[2].startswith("release/")}):
        nodes[rel] = {"doc_type": "release"}
    return {"version": 1, "nodes": nodes,
            "edges": [{"from": f, "type": t, "to": to}
                      for f, t, to in sorted(edges)]}


def write_graph(graph=None):
    graph = graph or build_graph()
    os.makedirs(ia.INDEX_DIR, exist_ok=True)
    with open(GRAPH, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return graph


def link_pr(ulid_, pr=None, commit=None):
    """Record a code edge on an item's sidecar (overlay-only). -> the entry."""
    side = ia.read_sidecar(item_key(ulid_))
    code = [c for c in side.get("code") or [] if isinstance(c, dict)]
    entry = {}
    if pr is not None:
        entry["pr"] = int(pr)
    if commit:
        entry["commit"] = commit
    if not entry:
        raise ValueError("need --pr or --commit")
    if entry not in code:
        code.append(entry)
    side["code"] = sorted(code, key=lambda c: (str(c.get("pr", "")),
                                               str(c.get("commit", ""))))
    ia.write_sidecar(item_key(ulid_), side)
    return entry


def trace_check(graph=None, items=None, strict=False):
    """Unlinked-evidence report (§9.6): every item in a released milestone
    should trace to a plan, a ticket, and a PR; verified-by stays advisory
    (a test link is proposed, never assumed). -> list of gaps."""
    if items is None:
        items = fold((".work/todo.jsonl", ".work/done.jsonl")).items
    graph = graph or build_graph(items=items)
    out_edges = {}
    for e in graph["edges"]:
        out_edges.setdefault(e["from"], set()).add(e["type"])
        if e["type"] == "produces":
            out_edges.setdefault(e["to"], set()).add("produced-by")
    gaps = []
    for iid in sorted(items):
        it = items[iid]
        if it.get("status") not in CLOSED_STATUSES or it.get("status") == "cancelled":
            continue
        key = item_key(iid)
        have = out_edges.get(key, set())
        scope = "released" if it.get("milestone") else "closed"
        if "produced-by" not in have and not it.get("plan"):
            gaps.append("%s (%s): no plan link" % (iid, scope))
        if "references" not in have:
            gaps.append("%s (%s): no external ticket" % (iid, scope))
        if strict and "lands-in" not in have:
            gaps.append("%s (%s): no PR/commit link" % (iid, scope))
    return gaps


def ticket_body(ulid_, records=None, items=None):
    """Rich issue body for a work item (issue-description skill): the
    human/agent-readable projection of the item's graph node. Sections are
    omitted when the data doesn't exist — no boilerplate placeholders."""
    if records is None:
        records = ia.build_records()
    if items is None:
        items = fold((".work/todo.jsonl", ".work/done.jsonl")).items
    it = items.get(ulid_)
    if it is None:
        raise KeyError(ulid_)
    lines = ["## Summary", "", it.get("body") or it.get("title", ""), ""]
    epic = items.get(it.get("parent") or "")
    plan_rec = next((r for r in records.values()
                     if r["doc_type"] == "plan"
                     and r["source"] == it.get("plan")), None)
    ctx = []
    if epic:
        eref = (epic.get("external") or {}).get("url")
        ctx.append("Part of epic: %s" % (
            "[%s](%s)" % (epic.get("title", ""), eref) if eref
            else epic.get("title", it["parent"])))
    if plan_rec:
        url = plan_rec.get("wiki")
        name = plan_rec.get("title", plan_rec["wiki_key"])
        ctx.append("Produced by plan: %s — the frozen design record; the "
                   "why lives there." % ("[%s](%s)" % (name, url) if url
                                         else name))
    if it.get("milestone"):
        ctx.append("Ships in: %s" % it["milestone"])
    if it.get("discovered_during"):
        d = items.get(it["discovered_during"])
        ctx.append("Unplanned — discovered during: %s"
                   % (d.get("title") if d else it["discovered_during"]))
    if ctx:
        lines += ["## Context", ""] + ["- " + c for c in ctx] + [""]
    trace = []
    side = item_sidecar(ulid_)
    plan_edges = (plan_rec or {}).get("relates_to") or []
    for e in list(side.get("relates_to") or []) + list(plan_edges):
        if isinstance(e, dict) and e.get("type") in ("decides", "implements"):
            trace.append("%s: %s" % (e["type"], e.get("target")))
    for c in side.get("code") or []:
        if isinstance(c, dict) and c.get("pr") is not None:
            trace.append("delivered by: PR #%s" % c["pr"])
    if trace:
        lines += ["## Traceability", ""] + ["- " + t for t in sorted(set(trace))] + [""]
    lines += ["---", "_Taxonomy: %s/%s · priority %s · worklog `%s`_" % (
        it.get("level", "?"), it.get("kind", "?"),
        it.get("priority", "?"), ulid_)]
    return "\n".join(lines) + "\n"


ADR_RE = re.compile(r"\bADR-(\d{4})\b")
SPEC_RE = re.compile(r"\bspec\s+§([\d.]+)|\bWORKLOG-SPEC\s+§?([\d.]+)", re.I)


def seed_edges(records=None):
    """Propose-only edge seeding (§14.2 step 4): scan plan bodies for ADR /
    spec-section mentions and append edge suggestions to
    .work/suggestions.jsonl for a human/agent to confirm. Never writes
    relates_to itself — silent auto-linking could fabricate evidence."""
    if records is None:
        records = ia.build_records()
    adr_by_id = {int(os.path.basename(r["source"])[:4]): k
                 for k, r in records.items() if r["doc_type"] == "adr"}
    existing = set()
    try:
        with open(SUGGESTIONS, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "proposed_edge" in rec:
                    pe = rec["proposed_edge"]
                    existing.add((pe.get("from"), pe.get("type"),
                                  pe.get("target")))
    except FileNotFoundError:
        pass
    proposed = []
    for key in sorted(records):
        rec = records[key]
        if rec["doc_type"] != "plan":
            continue
        authored = {(e.get("type"), str(e.get("target")))
                    for e in rec.get("relates_to") or [] if isinstance(e, dict)}
        with open(rec["source"], encoding="utf-8") as fh:
            _, body = ia.parse_front_matter(fh.read())
        targets = set()
        for m in ADR_RE.finditer(body):
            adr = adr_by_id.get(int(m.group(1)))
            if adr:
                targets.add(("decides", adr))
        for m in SPEC_RE.finditer(body):
            sec = m.group(1) or m.group(2)
            targets.add(("implements", "spec#" + sec))
        for typ, target in sorted(targets):
            if (typ, target) in authored or (key, typ, target) in existing:
                continue
            sid = "edge-" + hashlib.sha256(
                ("%s|%s|%s" % (key, typ, target)).encode()).hexdigest()[:10]
            proposed.append({"suggestion_id": sid, "source": "ia-graph --seed",
                             "proposed_edge": {"from": key, "type": typ,
                                               "target": target}})
    if proposed:
        with open(SUGGESTIONS, "a", encoding="utf-8") as fh:
            for rec in proposed:
                fh.write(json.dumps(rec, separators=(",", ":"),
                                    sort_keys=True) + "\n")
    return proposed
