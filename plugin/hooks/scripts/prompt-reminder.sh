#!/usr/bin/env bash
# Plugin hooks fire in every session; silence outside worklog repos.
[ -x bin/worklog ] || exit 0

# Fires on every prompt — keep it to one short line.
#
# Also the heartbeat for the concurrent-session advisory (#236): the harness
# hands us a stable session_id here, which is the only place in the system
# one exists. `worklog` itself is a short-lived CLI that cannot tell one
# session from another, so it reads what this writes.
python3 - <<'PY'
import json, os, sys

sys.path.insert(0, os.path.join(os.getcwd(), "bin"))
note = ("worklog policy: if this request produces work, record it first "
        "(bin/worklog add / work-track skill), move items in_progress/done "
        "as you go, and roadmap-render before committing.")
try:
    payload = json.load(sys.stdin)
except (ValueError, OSError):
    payload = {}
try:
    import session
    session.touch(payload.get("session_id"))
    warning = session.warning()
    if warning:
        note += " WARNING: " + warning
except Exception:
    pass          # the reminder must still fire if the advisory cannot
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit", "additionalContext": note}}))
PY
