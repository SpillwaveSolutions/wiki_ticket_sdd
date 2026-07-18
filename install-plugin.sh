#!/usr/bin/env bash
# Install the worklog plugin into Claude Code from this repo's marketplace.
set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
    echo "claude CLI not found." >&2
    echo "Install Claude Code, then run:" >&2
    echo "  claude plugin marketplace add <repo-root-or-url>" >&2
    echo "  claude plugin install worklog@worklog-marketplace" >&2
    exit 1
fi

repo_root="$(cd "$(dirname "$0")" && pwd)"
claude plugin marketplace add "$repo_root"
claude plugin install worklog@worklog-marketplace

echo
echo "Installed. Next steps:"
echo "  1. Open a repo in Claude Code"
echo "  2. Run /worklog:init to scaffold work tracking"
