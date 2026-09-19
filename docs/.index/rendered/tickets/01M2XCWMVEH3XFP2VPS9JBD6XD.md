# Interim merge-gate hardening and ADR-0011

`01M2XCWMVEH3XFP2VPS9JBD6XD` · task/bug · **done**

Read-only permissions in worklog.yml, remove the dead bypass actor from the ruleset and apply the ruleset live with gh api, and write ADR-0011 that supersedes ADR-0010 with the PR-landing path and the PAT decision.

## Hierarchy

- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.

## Linked PRs

- [[PR-436]]

## Related tickets

- [github #425](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/425)
