# banner() mislabels frozen 'current' plans as status reports

`01KYACFJA0SQSF4C83BJZXB5MY` · task/bug · **open**

bin/ia_render.py's banner() (~line 68) returns the 'the latest %s report' text for ANY doc that is truth_state:current AND frozen (ia.is_frozen()) — but is_frozen() is true for plan/roadmap-snapshot/status/dated-design, not just status reports, and the message hardcodes rec.get('kind','status') which plans never set.

## Related tickets

- [github #137](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/137)
