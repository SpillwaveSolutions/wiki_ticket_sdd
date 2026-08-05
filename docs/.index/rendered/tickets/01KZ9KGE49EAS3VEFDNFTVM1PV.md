# merge-rescue can invert an item's state

`01KZ9KGE49EAS3VEFDNFTVM1PV` · task/bug · **done**

When a compaction lands mid-branch, the rescue re-emits the branch's own events with fresh identifiers so the snapshot cannot overwrite them.

## Release

- [[Release-v0.22.0]]
