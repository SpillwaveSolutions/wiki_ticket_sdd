#!/usr/bin/env bash
# Plugin hooks fire in every session; silence outside worklog repos.
[ -x bin/wiki-ticket/worklog ] || exit 0

# Drop this session from the concurrent-session registry (#236). Without it a
# finished session keeps looking alive for a full window and warns the next
# one that opens the directory — an advisory that cries wolf gets ignored,
# which is the same as not having it.
#
# stdin is the hook payload and is not rewindable. Capture it first, then
# feed it to python -- a heredoc as stdin would swallow the payload and
# session.end() would always see no session_id.
payload=$(cat)
printf '%s' "$payload" | python3 -c '
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "bin", "wiki-ticket"))
try:
    sid = json.load(sys.stdin).get("session_id")
except Exception:
    sid = None
try:
    import session
    session.end(sid)
except Exception:
    pass
'
