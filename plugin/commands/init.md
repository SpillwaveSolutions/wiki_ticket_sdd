---
name: init
description: Scaffold or upgrade the current repo as a worklog repo (bin/, git hooks, .work/, CI workflow, CLAUDE.md policy block), then detect and configure the repo's ticketing/wiki systems
---

Install (or upgrade) worklog in the current repo:

1. From the repo root, run:

   ```
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/init.sh"
   ```

2. Show the user the script's output (version installed, what was written vs skipped, upgraded-from if applicable).

3. **Detect the repo's systems** — but first check `.work/config.yml`: if its `ticketing:` and `wiki:` blocks already name real systems (not the template defaults), this is an upgrade re-run — SKIP detection entirely, do not re-ask, go to step 7. Otherwise gather evidence:

   - `git remote -v` — map hostnames to platforms: `github.com` → GitHub (Issues, PRs, wiki); `gitlab` → GitLab; `dev.azure.com` / `visualstudio.com` → Azure DevOps; `bitbucket` → Bitbucket.
   - `command -v gh glab az jira acli` — which platform CLIs are installed. For the remote's platform CLI, check auth (e.g. `gh auth status`).
   - MCP tools available in this session — a Jira/Confluence/Notion MCP is evidence the team uses that system.

4. **Confident case.** If tickets, PRs, and wiki are all confidently determined (e.g. a single `github.com` origin and `gh` is authenticated), present ONE short summary and ask a single yes/no via AskUserQuestion:

   > Detected: GitHub Issues for tickets, GitHub PRs, GitHub wiki — correct?

5. **Unsure case** (mixed signals, no remote, or the user said no): AskUserQuestion per area, multiSelect on, so teams can pick and mix (GitHub PRs + Jira tickets + Confluence wiki is a legal combination):

   - **Tickets**: GitHub Issues, GitLab, Azure DevOps, Jira
   - **Wiki**: GitHub wiki, GitLab wiki, ADO wiki, Confluence, none

6. **Write the answers** into `.work/config.yml` by editing the existing `ticketing:` and `wiki:` blocks in place — set `system`, and fill `project` / `root_url` from what's known (remote URL, org/repo). Keep the file's comments intact.

7. Run `git status`, review the scaffolding it added or updated, and commit it all — scaffold plus config — in ONE commit (e.g. `worklog: scaffold repo (plugin v0.1.0)`). The copies are committed deliberately so git hooks and CI work for teammates who do not have the plugin.

The script is idempotent: re-running on an installed repo is the upgrade path. It never touches existing `.work/*.jsonl` logs.
