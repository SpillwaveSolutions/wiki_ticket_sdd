# Scheduled compaction pushes a stale IA manifest and roadmap to main

`01M095WZRZC0J94D3FDZV9Q7V0` · task/bug · **done**

The scheduled worklog-compact workflow (.github/workflows/compact.yml) runs
bin/compact.py on main and commits the result.
