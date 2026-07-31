# Merge guard's printed remedy cannot be run from the state it creates

`01KYWGJD1QCQRM6V6S0MWN5SCW` · task/bug · **open**

When a union merge resurrects events a compaction removed, the pre-commit merge guard blocks the merge commit and prints: 'Run: python3 bin/compact.py .work/todo.jsonl .work/done.jsonl to recompact.' That remedy cannot be followed.

## Related tickets

- [github #269](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/269)
