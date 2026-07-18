#!/usr/bin/env bash
# Remove the worklog plugin and its marketplace from Claude Code.
set -euo pipefail

claude plugin uninstall worklog || true
claude plugin marketplace remove worklog-marketplace || true

echo
echo "Uninstalled. Repos scaffolded with /worklog:init keep working —"
echo "their copies are committed. Run /worklog:uninstall in a repo to"
echo "remove its scaffolding."
