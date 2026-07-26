# user-guide.md miscounts branch-discipline hook checks (code-review finding)

`01KYDKDJFCJTDVFZJ27Q9Y08TV` · task/bug · **done**

user-guide.md said 'Two more pre-commit checks enforce branch discipline' but describes one pre-commit check (branch guard) plus a separate commit-msg hook -- could mislead a reader about what a --no-verify bypass actually skips, since commit-msg fires independently with its own MERGE_HEAD exemption.

## Linked PRs

- [[PR-160]]

## Related tickets

- [github #182](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/182)
