#!/usr/bin/env python3
"""doc_verify.py -- check a generated document's code citations against the
commit it was written against (#294).

The v0.20.0 doc sync measured a 46% error rate on design-doc line citations:
12 of 26 stale. One of the wrong claims had been INTRODUCED while hand-fixing
the previous wrong claim. Correcting prose by hand without a check relocates
the error rather than removing it.

Checking against HEAD would be the obvious design and it is the wrong one.
HEAD moves; a frozen document is ALLOWED to age. Resolving citations at the
document's own `git_hash` instead separates two things that today look
identical:

  FABRICATED -- wrong even in the tree the author had open. A defect.
  DRIFT      -- right then, and the code has moved since. Not a defect for a
                frozen doc; a defect for one claiming to describe HEAD.

Today they are indistinguishable, so all 26 look equally suspect and nobody
triages them.

NEVER falls back to HEAD when a document is unstamped or its commit cannot be
resolved. That fallback is bug #294 with extra steps: it would report drift as
fabrication and quietly re-introduce the "checked against the wrong tree"
failure this module exists to end.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia  # noqa: E402

# The citation forms that actually occur in this repo's design docs. Ranges
# use an EN-DASH, not a hyphen -- a regex written for "-" matches nothing.
_PATH = r"(?:bin|tests|hooks|plugin|schema|docs|adapters)/[\w./-]+"
_DASH = r"[–—-]"

CITE_RANGE = re.compile(
    r"(?P<path>%s)`?"                      # bin/fold.py
    r"(?:\s*%s\s*(?P<symbol>[\w.]+)\(\))?" # — apply_watermark()
    r"[`,\s]*lines?\s+"
    r"(?P<start>\d+)\s*%s\s*(?P<end>\d+)" % (_PATH, _DASH, _DASH))

CITE_ONE = re.compile(r"(?P<path>%s):(?P<line>\d+)" % _PATH)

# (`ia_graph.ticket_body()`, lines 302–357) -- module, not path. Resolved
# against bin/<module>.py, which is where every such symbol lives here.
CITE_SYMBOL = re.compile(
    r"`(?P<module>[a-z_][\w]*)\.(?P<symbol>[\w]+)\(\)`,?\s*lines?\s+"
    r"(?P<start>\d+)\s*%s\s*(?P<end>\d+)" % _DASH)

LIVE_DOCS = ("current_design_doc.md", "current_code_walkthrough.md")


def _git(*args):
    try:
        p = subprocess.run(["git", *args], capture_output=True, text=True)
    except OSError:
        return None
    return p.stdout if p.returncode == 0 else None


def is_shallow():
    return (_git("rev-parse", "--is-shallow-repository") or "").strip() == "true"


def resolvable(sha):
    """Is this commit actually in the clone? Squash-merges and shallow
    checkouts both produce a stamp naming a commit nobody has."""
    return _git("cat-file", "-e", "%s^{commit}" % sha) is not None


def _at(sha, path, _cache={}):
    """File content at a commit, or None when the path did not exist.

    Keyed on the working directory as well as (sha, path). Symbolic refs are
    not unique across repositories -- caching "HEAD" globally returns one
    repo's file for another's, which is exactly the class of wrong-tree
    answer this module exists to prevent. Callers should resolve HEAD to a
    real sha anyway; this is the second line of defence.
    """
    key = (os.getcwd(), sha, path)
    if key not in _cache:
        _cache[key] = _git("show", "%s:%s" % (sha, path))
    return _cache[key]


def citations(text):
    """-> list of {path, symbol, start, end}. Deduped; order preserved."""
    out, seen = [], set()

    def add(path, symbol, start, end):
        k = (path, symbol, start, end)
        if k not in seen:
            seen.add(k)
            out.append({"path": path, "symbol": symbol,
                        "start": int(start), "end": int(end)})

    for m in CITE_RANGE.finditer(text):
        add(m.group("path"), m.group("symbol"), m.group("start"), m.group("end"))
    for m in CITE_SYMBOL.finditer(text):
        path = "bin/%s.py" % m.group("module")
        add(path, m.group("symbol"), m.group("start"), m.group("end"))
    for m in CITE_ONE.finditer(text):
        add(m.group("path"), None, m.group("line"), m.group("line"))
    return out


def _check_one(cite, sha, head):
    """-> (verdict, detail). Verdicts: ok | fabricated | drift.

    `head` is a resolved sha, never the symbolic ref: a symbolic ref caches
    badly and, worse, reads differently depending on where the process is
    standing.
    """
    body = _at(sha, cite["path"])
    if body is None:
        return "fabricated", "path did not exist at %s" % sha[:9]
    lines = body.split("\n")
    if cite["end"] > len(lines):
        return ("fabricated",
                "cites line %d of a %d-line file" % (cite["end"], len(lines)))
    if cite["symbol"]:
        window = "\n".join(lines[cite["start"] - 1:cite["end"]])
        if cite["symbol"] not in window:
            return ("fabricated",
                    "%s() is not in lines %d-%d at that commit"
                    % (cite["symbol"], cite["start"], cite["end"]))
    # Correct when written. Has it moved since?
    head_body = _at(head, cite["path"])
    if head_body is None:
        return "drift", "file no longer exists at HEAD"
    hl = head_body.split("\n")
    if cite["end"] > len(hl):
        return "drift", "file is now only %d lines" % len(hl)
    if cite["symbol"]:
        if cite["symbol"] not in "\n".join(hl[cite["start"] - 1:cite["end"]]):
            return "drift", "%s() has moved since" % cite["symbol"]
    return "ok", ""


def verify(records=None, strict=False):
    """-> (findings, summary). A finding is a dict; summary counts verdicts.

    `strict` only changes the EXIT policy of the caller, never the analysis:
    drift on a live doc (one claiming to describe HEAD) is a failure, drift
    on a frozen doc is information.
    """
    if records is None:
        records = ia.build_records()
    shallow = is_shallow()
    # Resolve once: a symbolic ref is not a stable cache key and reads
    # differently depending on where the process is standing.
    head = (_git("rev-parse", "HEAD") or "HEAD").strip()
    findings, summary = [], {"ok": 0, "fabricated": 0, "drift": 0,
                             "unstamped": 0, "unresolvable": 0, "docs": 0}
    for key in sorted(records):
        rec = records[key]
        src = rec.get("source")
        if not src or not src.endswith(".md") or not os.path.exists(src):
            continue
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        cites = citations(text)
        if not cites:
            continue
        summary["docs"] += 1
        sha = rec.get("git_hash")
        if not sha:
            summary["unstamped"] += 1
            findings.append({"doc": key, "source": src, "verdict": "unstamped",
                             "detail": "%d citation(s) not verifiable"
                                       % len(cites)})
            continue
        if shallow or not resolvable(sha):
            summary["unresolvable"] += 1
            findings.append({"doc": key, "source": src,
                             "verdict": "unresolvable",
                             "detail": "commit %s is not in this clone%s"
                                       % (sha[:9],
                                          " (shallow)" if shallow else "")})
            continue
        live = src.endswith(LIVE_DOCS)
        for c in cites:
            verdict, detail = _check_one(c, sha, head)
            summary[verdict] += 1
            if verdict == "ok":
                continue
            findings.append({
                "doc": key, "source": src, "verdict": verdict,
                "live": live, "detail": detail,
                "cite": "%s%s lines %d-%d" % (
                    c["path"], " %s()" % c["symbol"] if c["symbol"] else "",
                    c["start"], c["end"])})
    return findings, summary


def failing(findings):
    """What --strict exits 1 on: fabrication anywhere, and drift only on a
    document that claims to describe HEAD. A frozen doc is allowed to age --
    failing on that would make the gate un-passable by design."""
    return [f for f in findings
            if f["verdict"] == "fabricated"
            or (f["verdict"] == "drift" and f.get("live"))]


def report(findings, summary):
    by_doc = {}
    for f in findings:
        by_doc.setdefault(f["doc"], []).append(f)
    for doc in sorted(by_doc):
        print(doc)
        for f in by_doc[doc]:
            if f["verdict"] in ("unstamped", "unresolvable"):
                print("  %-12s %s" % (f["verdict"].upper(), f["detail"]))
            else:
                print("  %-12s %s — %s"
                      % (f["verdict"].upper(), f["cite"], f["detail"]))
    print("doc-verify: %d citation(s) ok, %d fabricated, %d drifted "
          "across %d document(s); %d unstamped, %d unresolvable"
          % (summary["ok"], summary["fabricated"], summary["drift"],
             summary["docs"], summary["unstamped"], summary["unresolvable"]))


if __name__ == "__main__":
    f, s = verify()
    report(f, s)
    if "--strict" in sys.argv and failing(f):
        sys.exit(1)
