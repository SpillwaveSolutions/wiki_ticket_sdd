# Bot PRs use the WORKLOG_BOT_PAT identity

`01M2XCWMVEH3XFP2VPS9JBD6XF` · task/feature · **done**

Open and merge compact and post-merge PRs with a maintainer's fine-grained PAT so pull_request CI runs natively, then delete the status bridge, actions: write, statuses: write, and the workflow_run trigger.

## Hierarchy

- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.

## Subtasks

- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XH]] Pipeline hygiene: supersede open bot PRs, delete-branch, explicit loop guard — Each bot job closes the previous open bot PR before regenerating from main, so a stale PR never blocks under the strict checks policy. (done)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XK]] sync --report drift is never masked and the local-only comment is suppressed — A real drift finding must reach the PR comment. (done)

Progress: 2/2 done

## Related tickets

- [github #426](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/426)
