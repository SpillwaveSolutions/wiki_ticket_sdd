# Stop hook cannot see work that was recorded and then committed

`01M032YRXR61XAJBBNP355AVQW` · task/bug · **open**

The Stop hook, hooks/stop-worklog-check.sh, treats an UNCOMMITTED change to
.work/todo.jsonl as its only proof that the session recorded its work.
