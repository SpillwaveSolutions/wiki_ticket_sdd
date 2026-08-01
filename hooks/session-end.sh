#!/usr/bin/env bash
# Plugin hooks fire in every session; silence outside worklog repos.
[ -x bin/worklog ] || exit 0

# Drop this session from the concurrent-session registry (#236). Without it a
# finished session keeps looking alive for a full window and warns the next
# one that opens the directory — an advisory that cries wolf gets ignored,
# which is the same as not having it.
python3 - <<'PY'
import json, os, sys

sys.path.insert(0, os.path.join(os.getcwd(), "bin"))
try:
    payload = json.load(sys.stdin)
except (ValueError, OSError):
    payload = {}
try:
    import session
    session.end(payload.get("session_id"))
except Exception:
    pass
PY
