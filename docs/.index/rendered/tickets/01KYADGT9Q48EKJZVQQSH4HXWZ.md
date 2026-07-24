# worklog pr-sync: fetch live PR metadata (files, review/CI status)

`01KYADGT9Q48EKJZVQQSH4HXWZ` · task/feature · **open**

PR pages (docs/.index/rendered/prs/<N>.md, from render_pr_page() in bin/ia_render.py) currently show files-changed and test/review status as 'not tracked' -- deliberately deferred out of the artifact-pages epic since no code in this repo fetches gh pr view data today.

## Hierarchy

- epic: [[Ticket-01KYABYEQP8ANXGYPBCV2T20D8]] Extend IA to tickets, PRs, and releases (artifact pages) — Give every ticket, PR, and release its own generated wiki page reusing the IA content model's wiki_key/truth_state/traceability-graph machinery already built for docs — so a reader sees hierarchy, related artifacts, and traceability in one place instead of hunting indexes/logs.

## Related tickets

- [github #138](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/138)
