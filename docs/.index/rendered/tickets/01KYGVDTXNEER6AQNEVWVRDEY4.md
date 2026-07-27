# Glob boundary bug in the new slug guard causes false-positive refusal

`01KYGVDTXNEER6AQNEVWVRDEY4` · task/bug · **open**

docs/plans/*-<slug>.md matches by raw suffix, not by field boundary: searching for slug 'migration' also matches an existing 2026-07-01-database-migration.md (slug 'database-migration'), since that filename also ends in '-migration.md'.
