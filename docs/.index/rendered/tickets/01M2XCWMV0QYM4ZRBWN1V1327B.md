# Fix the v0.24.10 review findings and close #412 and #413

`01M2XCWMV0QYM4ZRBWN1V1327B` · epic/feature · **open**

The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.

## Children

- [[Ticket-01M2XCWMVD7KJ01FCNEV1X822S]] Council review, single edit pass, and plan capture — Copy the plan to the scratchpad, run grok, codex, and a Fable 5.1 subagent as reviewers, let one Fable 5.1 editor subagent apply the worthy edits once, then capture the plan with plan-capture. (done)
- [[Ticket-01M2XCWMVD7KJ01FCNEV1X822V]] Retention: stop re-snapshotting archived items into done.jsonl — done_state folds done and archive together, refreshed ids are pruned from the archive, and archive appends dedupe by item with the newest snapshot winning. (done)
- [[Ticket-01M2XCWMVD7KJ01FCNEV1X8237]] #412: consult the remote marker map before creating a ticket — observe_remote already fetches every remote ticket. (done)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XD]] Interim merge-gate hardening and ADR-0011 — Read-only permissions in worklog.yml, remove the dead bypass actor from the ruleset and apply the ruleset live with gh api, and write ADR-0011 that supersedes ADR-0010 with the PR-landing path and the PAT decision. (done)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XF]] Bot PRs use the WORKLOG_BOT_PAT identity — Open and merge compact and post-merge PRs with a maintainer's fine-grained PAT so pull_request CI runs natively, then delete the status bridge, actions: write, statuses: write, and the workflow_run trigger. (done)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XN]] #413: CI as the authoritative syncer behind ticketing.sync_owner: ci — post-merge sets the adapter env, runs a push-only sync with the bot token before rendering, stages the log with the docs, and caches sync-state. (done)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XQ]] Release gate for design-doc freshness in doc-verify --strict — A release fails when a live doc's git_hash does not descend from the previous tag or the freeze record for that tag is missing. (open)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XV]] #413: Azure Pipelines template from init.sh — init.sh writes azure-pipelines.yml with the same hook-only steps as the installed GitHub workflow when the origin remote is Azure DevOps. (done)

Progress: 7/8 done

## Related tickets

- [github #414](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/414)
