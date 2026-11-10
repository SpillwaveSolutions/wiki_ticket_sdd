#!/usr/bin/env python3
"""
session.py -- advisory registry of assistant sessions sharing this worklog.

Item #236: two sessions ran in one working directory, one switched branches
out from under the other mid-operation, and both independently "fixed" the
same problem in different ways. Nothing warned.

There is no process identity to key on. `worklog` is a short-lived CLI, so
every invocation has a fresh pid -- and ppid and POSIX session id turn over
too, because each tool call gets its own shell. The HARNESS is the only thing
that knows a session is one session, and it hands that id to its hooks. So
the hook heartbeats here and the CLI reads the result.

The CLI deliberately never learns which session it is. "Two live heartbeats
in this directory" is the whole condition worth warning about, and it needs
no self-knowledge to evaluate.

Advisory only, in both directions: nothing here ever blocks a write, and a
registry that is missing, stale or corrupt is silently treated as empty. A
bad advisory file must never be the reason someone cannot record work.
"""
import json
import os
import subprocess
import time

REGISTRY = ".work/.sessions"
# How long a session counts as live without a heartbeat. The UserPromptSubmit
# hook fires every turn, so a live session refreshes constantly; this only has
# to outlast one long-running turn. SessionEnd prunes the common case, so the
# window is the backstop for a session that died without one.
WINDOW = 3600


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}   # missing or corrupt: no opinion, never an error


def _write(path, data):
    """Atomic, and best-effort: losing an advisory heartbeat is not a failure."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = f"{path}.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, sort_keys=True)
        os.replace(tmp, path)
    except OSError:
        pass


def branch():
    try:
        p = subprocess.run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
                           capture_output=True, text=True)
        return p.stdout.strip() or None
    except OSError:
        return None


def head():
    try:
        p = subprocess.run(["git", "rev-parse", "HEAD"],
                           capture_output=True, text=True)
        return p.stdout.strip() or None
    except OSError:
        return None


def live(path=REGISTRY, window=WINDOW, now=None):
    """Sessions that have heartbeated within `window` seconds."""
    now = time.time() if now is None else now
    return {sid: rec for sid, rec in _read(path).items()
            if isinstance(rec, dict) and now - rec.get("ts", 0) <= window}


def touch(session_id, path=REGISTRY, window=WINDOW, now=None,
          branch_name=None, base_sha=None):
    """Record this session as alive. Prunes anything past the window so the
    file cannot grow without bound."""
    if not session_id:
        return
    now = time.time() if now is None else now
    data = live(path, window, now)
    prev = data.get(session_id) or {}
    rec = {"ts": now,
           "branch": branch_name if branch_name is not None else branch()}
    # `base` is the commit this session started from, and it must NOT move.
    # The Stop hook diffs .work/todo.jsonl against it to decide whether this
    # session recorded anything. Re-stamping it every heartbeat would erase
    # that evidence the moment the session commits its own log -- which is the
    # exact bug this field exists to fix.
    rec["base"] = prev.get("base") or (base_sha if base_sha is not None
                                       else head())
    data[session_id] = rec
    _write(path, data)


def base(session_id, path=REGISTRY, window=WINDOW, now=None):
    """The commit this session started from, or None when unknown.

    The Stop hook's old proof that work was recorded was an UNCOMMITTED change
    to the log versus HEAD. That proof vanishes when the session commits its
    own items, so a correctly-logged session read as an unrecorded one and got
    blocked. Diffing against this fixed point instead survives the commit.

    The trade-off is deliberate: a session that pulls someone else's log
    changes now also looks like it recorded something. That direction fails
    quiet -- a missed nag -- where the old direction failed loud, refusing to
    let a session that did everything right finish its turn.
    """
    if not session_id:
        return None
    rec = live(path, window, now).get(session_id) or {}
    sha = rec.get("base")
    return sha if isinstance(sha, str) and sha else None


def end(session_id, path=REGISTRY):
    """Drop a session on its way out, so a finished session stops warning the
    next one. Without this the registry cries wolf for a full window."""
    if not session_id:
        return
    data = _read(path)
    if data.pop(session_id, None) is not None:
        _write(path, data)


def warning(path=REGISTRY, window=WINDOW, now=None):
    """One line naming the risk, or None when this directory has one session.

    Deliberately does NOT try to name which session is 'the other one' -- the
    caller may be any of them, or a hook, or the nightly job.
    """
    sessions = live(path, window, now)
    if len(sessions) < 2:
        return None
    branches = sorted({rec.get("branch") or "?" for rec in sessions.values()})
    where = f" (branches: {', '.join(branches)})" if len(branches) > 1 else ""
    return (f"{len(sessions)} assistant sessions are active in this working "
            f"directory{where}. They share one checkout, so one can switch "
            f"branches under the other mid-operation and both can 'fix' the "
            f"same thing differently. Give each session its own git worktree.")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "touch":
        touch(argv[2] if len(argv) > 2 else "")
    elif cmd == "end":
        end(argv[2] if len(argv) > 2 else "")
    elif cmd == "base":
        sha = base(argv[2] if len(argv) > 2 else "")
        if sha:
            print(sha)
    elif cmd == "warn":
        w = warning()
        if w:
            print(w)
    else:
        print("usage: session.py touch|end|base|warn [session-id]")
        return 2
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
