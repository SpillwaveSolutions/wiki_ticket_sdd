# Conflict markers can reach a commit: the merge exemption plus unparsed tests

`01KYZEC0C1MGQXQSH61ZPDD0YZ` · task/bug · **done**

The commit-msg hook exempts merge commits from its item-reference rule, and the pre-commit hook only syntax-checks the event log and bin/ -- it never looks at tests/ or the plugin scripts.
