# Branch-discipline hooks: never commit on main, always reference work

`01KYBD2HYJVNHX698WR1JD96YC` · epic/feature · **open**

New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Children

- [[Ticket-01KYBD2HYK196RQN7JNCMV6PDS]] Add WORKLOG_SKIP_BRANCH_GUARD to the three bare pre-commit call sites — plugin/scripts/doctor.sh's own invocation, plugin/scripts/init.sh's CI
backstop step, and tests/test_integration.py's two "CI would pass"
assertions -- these run hooks/pre-commit with no real commit in flight
and would otherwise false-positive on main. (open)
- [[Ticket-01KYBD2HYK9XY02QHSVF1849BQ]] Wire commit-msg into install/uninstall/doctor/CANON — plugin/scripts/init.sh's hook-copy loop and CI template,
plugin/scripts/uninstall.sh's removal loop, plugin/scripts/doctor.sh's
existence check, tests/test_plugin.py's CANON list. (open)
- [[Ticket-01KYBD2HYKB5E4JXNYYQ9BPDAE]] Full test suite green + manual verification — Run the full suite, confirm TestCanonSync passes, and manually exercise
the incident scenario (branch -> commit -> merge onto main) plus
worklog doctor's health report on main. (open)
- [[Ticket-01KYBD2HYKET7WJARQFB2NVMFS]] Remove the "direct-commit repos" mode from the release skill — plugin/skills/release/SKILL.md section 3 currently documents committing
release stamps directly on the default branch -- dead once the branch
guard ships; describe branch+PR landing only. (open)
- [[Ticket-01KYBD2HYKG0DW7QJX7XG561A8]] Update test fixtures for the new hooks — tests/test_integration.py (~23 commit_all calls) and
tests/test_plugin.py (3 raw git commit calls) mostly commit on main with
no-reference messages -- give pure setup commits no_verify=True or move
them onto a branch via Sandbox.branch(), following the file's existing
precedent; leave the four pre-commit-content-testing call sites alone. (open)
- [[Ticket-01KYBD2HYKJHS5M2PFZ78Y585C]] Add TestBranchGuard and TestCommitMsgReference test classes — New tests in tests/test_integration.py covering: commit on main
rejected, commit on branch succeeds, merge onto main allowed (the
incident scenario), message without reference rejected, message with
ULID/ticket passes, merge commit message exempt. (open)
- [[Ticket-01KYBD2HYKKC2G9NW4VA3RVC6G]] Add the branch-guard block to hooks/pre-commit — Insert the MERGE_HEAD-exempt, WORKLOG_SKIP_BRANCH_GUARD-overridable check
that fails when HEAD is main/master, right after fail() is defined. (open)
- [[Ticket-01KYBD2HYKKZM22DFM16ZJXYFG]] Create hooks/commit-msg requiring a ULID or ticket reference — New hook: exempt merge commits via MERGE_HEAD, otherwise require a
26-char Crockford ULID or #123 ticket reference in the message, reusing
the bin/ulid.py alphabet. (open)
- [[Ticket-01KYBD2HYKYBBNGDMCQSW4VE2T]] Add a CI step validating commit messages on PRs — Walk git rev-list --no-merges base..HEAD through hooks/commit-msg in
.github/workflows/worklog.yml (template and this repo's installed
copy); needs fetch-depth 0. (open)

Progress: 0/9 done

## Related tickets

- [github #144](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/144)
