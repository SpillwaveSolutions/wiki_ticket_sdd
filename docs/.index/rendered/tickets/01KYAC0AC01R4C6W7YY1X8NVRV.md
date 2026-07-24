# Auto-draft the release CHANGELOG unreleased section from git log

`01KYAC0AC01R4C6W7YY1X8NVRV` · task/feature · **open**

The release skill requires a hand-written '## X.Y.Z — unreleased' CHANGELOG section before a release can be cut, but nothing enforces writing it as features land — v0.13.0's section had to be manually reconstructed from 'git log v0.12.1..HEAD' after 36 commits piled up unlogged.
