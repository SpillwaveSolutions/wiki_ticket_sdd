# Concurrent sessions in one working directory corrupt each other's work

`01KYNHEV5GCR1MDNECAXFT0GK2` · task/ops · **open**

Reported alongside the duplicate-ticket bug: two assistant sessions ran in the same directory, one switched branches out from under the other mid-operation, and both independently 'fixed' the same problem in different ways.

## Related tickets

- [github #236](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/236)
