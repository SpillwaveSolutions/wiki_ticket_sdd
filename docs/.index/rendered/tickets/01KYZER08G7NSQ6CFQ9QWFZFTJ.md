# Stamp generated ULIDs with the short git hash so concurrent branches diverge

`01KYZER08G7NSQ6CFQ9QWFZFTJ` · task/feature · **done**

Two agents working in different worktrees or branches mint event ids from the same clock and pure randomness, so ids created in the same millisecond sort arbitrarily and carry nothing about where they came from.
