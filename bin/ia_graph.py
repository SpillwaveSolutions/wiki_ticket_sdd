"""Bidirectional traceability (plan ia-content-model §9): typed-edge graph
over docs + work items, PR/commit linking, and the unlinked-evidence check.

Forward edges only are stored; reverse edges are DERIVED (§9.4) — the graph
builder inverts `relates_to` plus the fields the log already carries
(`parent`, `plan`, `milestone`, `external`, `supersedes`). Deterministic:
pure function of records + fold; no git or network calls. `pr_sync` is the
one exception and is deliberately not on that path — it is an explicit
command that writes a sidecar, so the builder and the renderer keep reading
committed files only.

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
            if not isinstance(c, dict):
                continue
            if c.get("pr") is not None:
                pkey = "pr/%s" % c["pr"]
                nodes[pkey] = {"doc_type": "pr"}
                edge(key, "lands-in", pkey)
            elif c.get("commit"):
                ckey = "commit/%s" % c["commit"]
                nodes[ckey] = {"doc_type": "commit"}
                edge(key, "lands-in", ckey)
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


def build_adjacency(graph):
    """Forward/backward edge maps keyed by node — the traversal every
    per-entity page renderer needs, built once per render pass rather than
    once per item."""
    fwd, back = {}, {}
    for e in graph["edges"]:
        fwd.setdefault(e["from"], []).append((e["type"], e["to"]))
        back.setdefault(e["to"], []).append((REVERSE[e["type"]], e["from"]))
    return fwd, back


def item_links(iid, fwd, back):
    """Parent/children/PRs/release for one item — a thin projection over
    graph adjacency (from build_adjacency), shared by every ticket/release/PR
    page renderer instead of each re-walking the edge list."""
    key = item_key(iid)
    parent = next((to for typ, to in fwd.get(key, []) if typ == "belongs-to"),
                  None)
    children = sorted(to for typ, to in back.get(key, []) if typ == "contains")
    prs = sorted(to for typ, to in fwd.get(key, []) if typ == "lands-in")
    release = next((to for typ, to in fwd.get(key, [])
                    if typ == "targets" and to.startswith("release/")), None)
    return {"parent": parent, "children": children, "prs": prs,
            "release": release}


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


# ------------------------------------------------------------- PR sync

PR_FIELDS = ("title", "url", "state", "files", "reviewDecision",
             "statusCheckRollup", "mergedAt")

# gh reports one row per check; a page shows one word. Worst state wins —
# a page that says "passing" while a gate is red is worse than no page.
_CHECK_BAD = ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED",
              "ERROR", "STARTUP_FAILURE")
_CHECK_WAIT = ("PENDING", "IN_PROGRESS", "QUEUED", "WAITING", "REQUESTED",
               "EXPECTED")


def rollup_checks(rows):
    """statusCheckRollup rows -> passing|failing|pending|mixed|none."""
    states = set()
    for c in rows or []:
        if not isinstance(c, dict):
            continue
        # A finished check run carries `conclusion`; a running one carries
        # only `status`. Commit statuses use `state`.
        s = (c.get("conclusion") or c.get("state") or c.get("status") or "")
        if s:
            states.add(s.upper())
    if not states:
        return "none"
    if states & set(_CHECK_BAD):
        return "failing"
    if states & set(_CHECK_WAIT):
        return "pending"
    if states <= {"SUCCESS", "NEUTRAL", "SKIPPED", "COMPLETED"}:
        return "passing"
    return "mixed"


def _gh_pr_view(num):
    import subprocess
    p = subprocess.run(["gh", "pr", "view", str(num),
                        "--json", ",".join(PR_FIELDS)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError("gh pr view %s failed: %s"
                         % (num, (p.stderr or "").strip()))
    return json.loads(p.stdout or "{}")


def pr_sync(num, fetch=None):
    """Live PR metadata -> the pr/<num> sidecar. -> the sidecar dict.

    The network call lives HERE and never in the renderer: `ia-render
    --check` regenerates and byte-diffs, so a renderer that reached the
    network would flap against mutable remote state. Same split as link_pr:
    a command writes a committed file, render reads it off disk.

    Files are flattened to paths — the sidecar's YAML subset inlines lists
    on one line, and a comma inside an inline `{...}` would not round-trip.
    """
    raw = (fetch or _gh_pr_view)(int(num))
    meta = {
        "number": int(num),
        "title": raw.get("title") or "",
        "url": raw.get("url") or "",
        "state": (raw.get("state") or "unknown").lower(),
        "review": (raw.get("reviewDecision") or "none").lower(),
        "checks": rollup_checks(raw.get("statusCheckRollup")),
        "merged_at": raw.get("mergedAt") or None,
        "files": sorted(f.get("path") for f in raw.get("files") or []
                        if isinstance(f, dict) and f.get("path")),
    }
    ia.write_sidecar("pr/%s" % int(num), meta)
    return meta


def pr_meta(num):
    """The pr/<num> sidecar, or {} when pr-sync has never run for it."""
    return ia.read_sidecar("pr/%s" % num)


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


# --- read-only search over the generated model (#272) ---------------------
#
# There was no way to ask the content model a question from the command line.
# Everything an answer needs is already generated and on disk -- every
# document with its type and truth state in the inventory, every typed edge
# between documents, items, tickets and PRs in the graph. So this is a reader,
# not an index: no network call, no new store, nothing written.

def load_graph():
    """The generated graph, or a clear instruction when it isn't there yet."""
    try:
        with open(GRAPH, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise SystemExit("worklog find: no graph yet — run: worklog ia-graph")
    except json.JSONDecodeError as e:
        raise SystemExit(f"worklog find: {GRAPH} is unreadable ({e}); "
                         "regenerate with: worklog ia-graph")


def search_nodes(graph, query=None, doc_type=None, truth=None):
    """Nodes matching a case-insensitive substring over key, title and source.

    Substring rather than tokens or fuzzy matching: the keys are structured
    (`adr/0005-...`, `item/01KY...`), so a plain substring already answers
    "show me the ADRs" and "show me this item" without a query language to
    learn or maintain.
    """
    q = (query or "").lower()
    out = []
    for key, node in graph.get("nodes", {}).items():
        if doc_type and node.get("doc_type") != doc_type:
            continue
        if truth and node.get("truth_state") != truth:
            continue
        if q and q not in " ".join(
                str(node.get(f) or "") for f in ("title", "source")).lower() \
                and q not in key.lower():
            continue
        out.append((key, node))
    return sorted(out)


def resolve_node(graph, key):
    """Exact key, else unique substring match. Ambiguity is an error, never a
    silent pick -- the same rule `worklog show` uses for item prefixes."""
    nodes = graph.get("nodes", {})
    if key in nodes:
        return key
    hits = sorted(k for k in nodes if key.lower() in k.lower())
    if not hits:
        raise SystemExit(f"worklog find: no node matching {key!r}")
    if len(hits) > 1:
        raise SystemExit("worklog find: %r is ambiguous — matches %d nodes:\n  %s"
                         % (key, len(hits), "\n  ".join(hits[:10])))
    return hits[0]


def node_links(graph, key):
    """(outbound, inbound) edges for one node, each [(type, other_key)].

    Both directions, because the questions this exists to answer run each way:
    "which plan decided this?" is inbound, "what did this supersede?" is
    outbound.
    """
    fwd, back = build_adjacency(graph)
    return sorted(fwd.get(key, [])), sorted(back.get(key, []))


def edges_of_type(graph, edge_type):
    known = sorted(REVERSE)
    if edge_type not in known:
        raise SystemExit("worklog find: unknown edge type %r; known: %s"
                         % (edge_type, ", ".join(known)))
    return sorted((e["from"], e["to"]) for e in graph.get("edges", [])
                  if e["type"] == edge_type)


def _label(graph, key):
    node = graph.get("nodes", {}).get(key) or {}
    title = node.get("title")
    return f"{key} — {title}" if title else key


def find(query=None, doc_type=None, truth=None, links=None, edge=None,
         as_json=False):
    """The `worklog find` command. Returns an exit code."""
    graph = load_graph()

    if links:
        key = resolve_node(graph, links)
        out, back = node_links(graph, key)
        if as_json:
            print(json.dumps({"node": key, "outbound": out, "inbound": back},
                             indent=2, sort_keys=True))
            return 0
        print(_label(graph, key))
        if not out and not back:
            print("  (no edges)")
        for typ, other in out:
            print(f"  -> {typ}: {_label(graph, other)}")
        for typ, other in back:
            print(f"  <- {typ}: {_label(graph, other)}")
        return 0

    if edge:
        pairs = edges_of_type(graph, edge)
        if as_json:
            print(json.dumps([{"from": a, "to": b} for a, b in pairs],
                             indent=2, sort_keys=True))
            return 0
        for a, b in pairs:
            print(f"{a}  --{edge}->  {b}")
        print(f"\n{len(pairs)} {edge} edge(s)")
        return 0 if pairs else 1

    hits = search_nodes(graph, query, doc_type, truth)
    if as_json:
        print(json.dumps([dict(key=k, **n) for k, n in hits],
                         indent=2, sort_keys=True))
        return 0
    for key, node in hits:
        bits = [node.get("doc_type") or "?"]
        if node.get("truth_state"):
            bits.append(node["truth_state"])
        print("%-14s %s" % ("[" + "/".join(bits) + "]", _label(graph, key)))
    print(f"\n{len(hits)} node(s)")
    # Non-zero on no matches so a script can branch on it, the way grep does.
    return 0 if hits else 1
