# post-merge.yml YAML invalid: python heredoc dedents to column 0

`01M19YV9VCDNTVPXAHW3D2NSA5` · task/bug · **done**

GitHub rejected post-merge.yml at L57 on merge commit 0295c50: the python heredoc body started at column 0, which YAML forbids inside a literal block.

## Hierarchy

- story: [[Ticket-01M19XR46836RE9JSHJHM2DSGC]] Implement worklog sync --report; land compact/post-merge via PR — Two live holes in the merge pipeline #394 installed.

## Linked PRs

- [[PR-402]]

## Release

- [[Release-v0.24.10]]
