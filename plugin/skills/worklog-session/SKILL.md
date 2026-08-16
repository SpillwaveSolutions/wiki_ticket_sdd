---
name: worklog-session
metadata:
  version: "0.24.0"
description: Open or close an isolated second-brain write session (worktree + PR). Use before writing knowledge when multiple agents share one knowledge remote.
---

# worklog-session

## When

- More than one agent or machine writes the shared second brain
- The current project worktree is not the knowledge repo
- The user asks to isolate writes, open a knowledge PR, or avoid clobbering main

## Open

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/brain_session.py" open \
  --repo . \
  --bundle knowledge \
  --actor "${SECOND_BRAIN_IDENTITY:?claim an identity first}" \
  --plugin worklog \
  --host claude-code
```

Export `SECOND_BRAIN_ROOT` and `BRAIN_SESSION_ID` from the JSON.

## Close

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/brain_session.py" close \
  --repo . \
  --session "${BRAIN_SESSION_ID}"
```

Pushes to whatever remote the checkout already has and opens a PR when `gh` is available. Never force-push. Never invent a remote URL.

## Rules

- Read shared truth from main. Overlay this session only.
- Do not pack other agents' open branches.
- Public examples use fictional **lumenfield-detector** and **northstar-console** only.
- See `docs/ISOLATION.md`.

## Worklog vs knowledge tree

Worklog appends via `bin/worklog` do **not** use this skill. Only OKF knowledge-tree writes do.
