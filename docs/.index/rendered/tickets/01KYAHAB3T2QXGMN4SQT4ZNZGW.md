# ia_graph build_graph() ignores commit-only sidecar code links (lands-in only honors code.pr)

`01KYAHAB3T2QXGMN4SQT4ZNZGW` · task/bug · **open**

bin/ia_graph.py's build_graph() only creates a 'lands-in' edge when an item sidecar's code entry has a 'pr' key (c.get('pr') is not None) -- a commit-only entry ({'commit': '<sha>'}, written by worklog link-pr --commit with no --pr) creates no edge at all, so trace-check --strict still reports 'no PR/commit link' even after linking a real commit.

## Related tickets

- [github #142](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/142)
