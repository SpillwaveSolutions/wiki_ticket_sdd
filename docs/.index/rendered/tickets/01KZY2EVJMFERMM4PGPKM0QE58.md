# Stop hook accuses a correctly-logged worktree session of skipping the log

`01KZY2EVJMFERMM4PGPKM0QE58` · task/bug · **done**

The Stop hook, hooks/stop-worklog-check.sh, runs every git command as 'git -C "$PWD"' and never calls 'git worktree list'.
