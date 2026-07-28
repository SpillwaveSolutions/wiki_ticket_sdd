# Catch duplicate ticket ownership at merge time, not just at sync

`01KYNHEV9M01PQJZQ5QRZQ3C8J` · task/bug · **open**

Linking now refuses a ticket another item already owns, so the only remaining way to create a duplicate is a git merge of two branches that each claimed the same ticket.

## Related tickets

- [github #237](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/237)
