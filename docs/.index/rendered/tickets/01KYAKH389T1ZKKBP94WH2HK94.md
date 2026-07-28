# sync_dispatch push_items KeyError on ext['key'] when forcing a never-remote closed item into scope via --keys

`01KYAKH389T1ZKKBP94WH2HK94` · task/bug · **done**

bin/sync_dispatch.py push_items(): the scope skip ('closed and not ext.get("key") and not forced: continue') is correctly bypassed when --keys forces the item in, but the closed-item branch unconditionally reads ext['key'] (both the dry-run print and the real close() call), assuming a closed item always already has an external key.

## Linked PRs

- [[PR-188]]

## Related tickets

- [github #143](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/143)
