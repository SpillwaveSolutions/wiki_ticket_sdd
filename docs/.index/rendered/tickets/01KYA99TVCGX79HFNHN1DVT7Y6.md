# close/update silently corrupt log when given an item-id prefix instead of the full ULID

`01KYA99TVCGX79HFNHN1DVT7Y6` · task/bug · **done**

worklog close and worklog update look up the item by exact dict key (fold(...).items.get(a.item) / base(a.item, ...)) instead of resolving prefixes the way worklog reopen already does (id.startswith(a.item)).

## Related tickets

- [github #123](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/123)
