# pre-commit hook pollutes worktree with bin/__pycache__ after git add — merge aborts on tracked-vs-untracked pyc collision

`01KY5P9V0CMM86G43HH4Q28ZDD` · task/bug · **done**

The IA gates added to pre-commit import new modules during the hook, creating .pyc files after staging.

## Linked PRs

- PR #104

## Related tickets

- [github #107](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/107)
