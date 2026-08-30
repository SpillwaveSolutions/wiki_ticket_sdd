# Truth hygiene: spec fold/watermark, adapters exit-3, HOSTS/PORTS, plan-vs-ADR, freeze cap

`01M19T3CY572RT614FPDJYVTZJ` · story/ops · **done**

Stale sentences in the spec and host docs contradict shipped code: fold has no actor/hash tiebreak, compaction watermarks are per-item, status-report is shipped, adapter exit 3 never auto-unlinks, Cursor events are beforeSubmitPrompt/stop/sessionStart/sessionEnd, both hook manifests nest under hooks.

## Release

- [[Release-v0.24.10]]
