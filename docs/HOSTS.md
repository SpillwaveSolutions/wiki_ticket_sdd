# Hosts

## Three-host hooks

If Claude Code ships `hooks/hooks.json`, this plugin also ships:

- `hooks/codex-hooks.json` — Codex event map (same scripts; `ExitPlanMode` omitted)
- `hooks/cursor-hooks.json` — Cursor-native events: `beforeSubmitPrompt`, `stop`, `sessionStart`, `sessionEnd`

Both Claude and Codex manifests nest the event map under a top-level `hooks` key. Cursor uses a flat-per-event list under that same `hooks` key, with Cursor's own event names (not Claude's `PostToolUse` / `UserPromptSubmit`).

`.cursor/rules/` remains soft guidance and is not a substitute for hooks.
