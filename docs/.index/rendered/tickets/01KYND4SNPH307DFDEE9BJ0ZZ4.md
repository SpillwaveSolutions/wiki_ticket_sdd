# Make undoing or moving a link actually re-push

`01KYND4SNPH307DFDEE9BJ0ZZ4` · task/bug · **open**

The change detection only looks at an item's content, so unlinking or re-pointing
it is silently a no-op and the damaged ticket is never repaired.

## Hierarchy

- epic: [[Ticket-01KYND4SNNVYRAEQ958HK83W72]] One local owner per remote ticket (#226) — Two local work items were allowed to point at the same ticket in the external tracker.

## Release

- [[Release-v0.18.0]]
