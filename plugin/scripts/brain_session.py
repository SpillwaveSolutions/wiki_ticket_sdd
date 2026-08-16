#!/usr/bin/env python3
"""Session isolation for a shared second brain.

Read shared truth from main. Write in a short-lived git worktree + branch.
Close by committing and optionally opening a PR against whatever remote the
checkout already has. Never hard-codes a remote URL.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SESSION_DIRNAME = ".brain-sessions"
WORKTREE_DIRNAME = ".brain-worktrees"
SESSION_FILE = ".brain-session.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_session_id() -> str:
    ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return f"{ms:011x}{secrets.token_hex(4)}"


def sanitize_actor(actor: str) -> str:
    s = actor.strip().lower()
    s = s.replace(" ", "-")
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "agent"


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def find_git_root(start: Path) -> Path | None:
    p = start.resolve()
    if p.is_file():
        p = p.parent
    cur = p
    for _ in range(12):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def default_base_ref(repo: Path) -> str:
    for cand in ("origin/main", "main", "origin/master", "master"):
        r = run_git(repo, "rev-parse", "--verify", cand, check=False)
        if r.returncode == 0:
            return cand
    r = run_git(repo, "rev-parse", "HEAD", check=False)
    if r.returncode == 0:
        return "HEAD"
    raise SystemExit(json.dumps({"error": "no git ref to base a session on"}))


def knowledge_rel(repo: Path, bundle: Path) -> str:
    try:
        rel = bundle.resolve().relative_to(repo.resolve())
        return str(rel)
    except ValueError:
        return ""


def session_store(repo: Path) -> Path:
    d = repo / SESSION_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_session(repo: Path, session_id: str) -> dict:
    path = session_store(repo) / f"{session_id}.json"
    if not path.is_file():
        raise SystemExit(json.dumps({"error": f"unknown session {session_id}"}))
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_session(repo: Path, session_id: str | None) -> dict:
    if session_id:
        return load_session(repo, session_id)
    env = os.environ.get("BRAIN_SESSION_ID", "").strip()
    if env:
        return load_session(repo, env)
    store = session_store(repo)
    files = sorted(store.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    open_ones = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("status") == "open":
            open_ones.append(data)
    if len(open_ones) == 1:
        return open_ones[0]
    if not open_ones:
        raise SystemExit(json.dumps({"error": "no open session; run brain_session.py open"}))
    raise SystemExit(json.dumps({"error": "multiple open sessions; pass --session", "ids": [s["session_id"] for s in open_ones]}))


def cmd_open(args) -> int:
    repo = find_git_root(Path(args.repo))
    if repo is None:
        print(json.dumps({"error": "not a git checkout; isolation requires a git repo"}))
        return 1
    actor = (args.actor or os.environ.get("SECOND_BRAIN_IDENTITY") or "").strip()
    if not actor:
        print(json.dumps({"error": "claim an identity first (--actor or SECOND_BRAIN_IDENTITY)"}))
        return 1
    bundle_in = Path(args.bundle) if args.bundle else Path(os.environ.get("SECOND_BRAIN_ROOT", "knowledge"))
    if not bundle_in.is_absolute():
        cand = (repo / bundle_in).resolve()
        bundle = cand if cand.exists() or args.bundle else repo
    else:
        bundle = bundle_in
    if not bundle.exists():
        # treat repo root as the bundle
        bundle = repo

    run_git(repo, "fetch", "--all", "--prune", check=False)
    base = args.base or default_base_ref(repo)
    sid = new_session_id()
    branch = f"brain/{sanitize_actor(actor)}/{sid}"
    worktrees = Path(args.worktrees) if args.worktrees else repo / WORKTREE_DIRNAME
    wt = worktrees / sid
    if wt.exists():
        print(json.dumps({"error": f"worktree already exists: {wt}"}))
        return 1
    worktrees.mkdir(parents=True, exist_ok=True)
    added = run_git(repo, "worktree", "add", "-b", branch, str(wt), base, check=False)
    if added.returncode != 0:
        print(json.dumps({"error": "git worktree add failed", "stderr": added.stderr.strip()}))
        return 1

    rel = knowledge_rel(repo, bundle)
    session_root = (wt / rel) if rel and rel != "." else wt
    session_root.mkdir(parents=True, exist_ok=True)

    record = {
        "session_id": sid,
        "status": "open",
        "actor": actor,
        "plugin": args.plugin or "",
        "host": args.host or os.environ.get("SECOND_BRAIN_HOST", "unknown"),
        "branch": branch,
        "base": base,
        "repo": str(repo),
        "worktree": str(wt),
        "bundle": str(session_root),
        "created": now_iso(),
        "project": args.project or "",
    }
    write_json(session_store(repo) / f"{sid}.json", record)
    write_json(wt / SESSION_FILE, record)
    print(
        json.dumps(
            {
                "ok": True,
                **record,
                "env": {
                    "SECOND_BRAIN_ROOT": str(session_root),
                    "SECOND_BRAIN_IDENTITY": actor,
                    "BRAIN_SESSION_ID": sid,
                },
            }
        )
    )
    return 0


def cmd_status(args) -> int:
    repo = find_git_root(Path(args.repo))
    if repo is None:
        print(json.dumps({"error": "not a git checkout"}))
        return 1
    store = session_store(repo)
    sessions = []
    for f in sorted(store.glob("*.json")):
        sessions.append(json.loads(f.read_text(encoding="utf-8")))
    print(json.dumps({"ok": True, "repo": str(repo), "sessions": sessions}, indent=2))
    return 0


def cmd_close(args) -> int:
    repo = find_git_root(Path(args.repo))
    if repo is None:
        print(json.dumps({"error": "not a git checkout"}))
        return 1
    rec = resolve_session(repo, args.session)
    wt = Path(rec["worktree"])
    if not wt.exists():
        print(json.dumps({"error": "worktree missing", "session": rec["session_id"]}))
        return 1

    # Never commit isolation bookkeeping into the knowledge history.
    # The session bundle lives inside the worktree (often knowledge/).
    wt_bundle = Path(rec.get("bundle") or wt)
    try:
        rel = str(wt_bundle.resolve().relative_to(wt.resolve()))
    except ValueError:
        rel = "knowledge"
    if rel in {".", ""}:
        run_git(wt, "add", "-A", check=False)
        run_git(wt, "rm", "-f", "--cached", SESSION_FILE, check=False)
    else:
        run_git(wt, "add", "-A", "--", rel, check=False)
    dirty = run_git(wt, "status", "--porcelain", check=False)
    committed = False
    sha = run_git(wt, "rev-parse", "HEAD", check=False).stdout.strip()
    if dirty.stdout.strip():
        msg = args.message or f"brain({rec['actor']}): session {rec['session_id']}"
        commit = run_git(
            wt,
            "-c",
            "user.email=brain-session@local",
            "-c",
            "user.name=brain-session",
            "commit",
            "-m",
            msg,
            check=False,
        )
        if commit.returncode != 0:
            print(json.dumps({"error": "commit failed", "stderr": commit.stderr.strip()}))
            return 1
        committed = True
        sha = run_git(wt, "rev-parse", "HEAD").stdout.strip()

    pushed = False
    pr_url = None
    if not args.no_push:
        remotes = run_git(repo, "remote", check=False).stdout.split()
        if remotes:
            push = run_git(wt, "push", "-u", remotes[0], rec["branch"], check=False)
            pushed = push.returncode == 0
            if not pushed and not args.allow_local:
                print(json.dumps({"error": "push failed", "stderr": push.stderr.strip()}))
                return 1
            if pushed and shutil.which("gh") and not args.no_pr:
                pr = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--repo",
                        ".",
                        "--head",
                        rec["branch"],
                        "--title",
                        args.title or f"brain: {rec['actor']} {rec['session_id'][:8]}",
                        "--body",
                        (
                            f"Actor: `{rec['actor']}`\n"
                            f"Host: `{rec.get('host', '')}`\n"
                            f"Plugin: `{rec.get('plugin', '')}`\n"
                            f"Session: `{rec['session_id']}`\n"
                            f"Project: `{rec.get('project', '')}`\n\n"
                            "Isolation write. Review owned types, then merge.\n"
                            "Do not force-push. Do not retarget a public remote.\n"
                        ),
                    ],
                    cwd=str(wt),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if pr.returncode == 0:
                    pr_url = pr.stdout.strip()

    rec["status"] = "closed"
    rec["closed"] = now_iso()
    rec["commit"] = sha
    rec["pushed"] = pushed
    rec["pr"] = pr_url
    write_json(session_store(repo) / f"{rec['session_id']}.json", rec)
    if (wt / SESSION_FILE).exists():
        write_json(wt / SESSION_FILE, rec)

    if args.teardown:
        run_git(repo, "worktree", "remove", "--force", str(wt), check=False)
        rec["worktree_removed"] = True
        write_json(session_store(repo) / f"{rec['session_id']}.json", rec)

    print(
        json.dumps(
            {
                "ok": True,
                "session_id": rec["session_id"],
                "branch": rec["branch"],
                "commit": sha,
                "committed": committed,
                "pushed": pushed,
                "pr": pr_url,
                "status": rec["status"],
            }
        )
    )
    return 0


def cmd_teardown(args) -> int:
    repo = find_git_root(Path(args.repo))
    if repo is None:
        print(json.dumps({"error": "not a git checkout"}))
        return 1
    rec = resolve_session(repo, args.session)
    wt = Path(rec["worktree"])
    if wt.exists():
        run_git(repo, "worktree", "remove", "--force", str(wt), check=False)
    rec["status"] = "torn-down"
    rec["torn_down"] = now_iso()
    write_json(session_store(repo) / f"{rec['session_id']}.json", rec)
    print(json.dumps({"ok": True, "session_id": rec["session_id"], "status": rec["status"]}))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Second-brain write isolation (worktree + PR)")
    sub = p.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("open", help="Create a worktree + branch for isolated writes")
    o.add_argument("--repo", default=".")
    o.add_argument("--bundle", default="")
    o.add_argument("--actor", default="")
    o.add_argument("--plugin", default="")
    o.add_argument("--host", default="")
    o.add_argument("--project", default="")
    o.add_argument("--base", default="")
    o.add_argument("--worktrees", default="")

    s = sub.add_parser("status", help="List isolation sessions")
    s.add_argument("--repo", default=".")

    c = sub.add_parser("close", help="Commit session writes and open a PR")
    c.add_argument("--repo", default=".")
    c.add_argument("--session", default="")
    c.add_argument("--message", default="")
    c.add_argument("--title", default="")
    c.add_argument("--no-push", action="store_true")
    c.add_argument("--no-pr", action="store_true")
    c.add_argument("--allow-local", action="store_true")
    c.add_argument("--teardown", action="store_true")

    t = sub.add_parser("teardown", help="Remove a session worktree")
    t.add_argument("--repo", default=".")
    t.add_argument("--session", default="")

    args = p.parse_args()
    return {
        "open": cmd_open,
        "status": cmd_status,
        "close": cmd_close,
        "teardown": cmd_teardown,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
