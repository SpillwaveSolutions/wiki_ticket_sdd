#!/usr/bin/env python3
"""Canonical JSON + canonical hash for ticket sync (worklog spec section 10.3).

This is THE implementation of the canonical hash. The ticket-sync skill and
bin/sync_dispatch.py both call THIS function; nothing else may reimplement it.
Changing the serialization or the field set changes every item's hash, which
breaks echo suppression (last_pushed_hash comparison) for every existing
clone. Don't.
"""
import hashlib
import json

# Changed in the taxonomy migration (2026-07-18-work-taxonomy): `type` is
# replaced by level/kind/milestone. The one-time sync churn (every item's hash
# changes, so the next sync re-pushes everything once) is deliberate; spec
# section 10.3 is updated by the edges agent.
HASH_FIELDS = ("title", "body", "level", "kind", "milestone", "status",
               "priority", "parent", "labels", "assignee")


def canonical_json(fields: dict) -> str:
    """Sorted keys, no whitespace, list values sorted (set semantics)."""
    norm = {k: sorted(v) if isinstance(v, list) else v for k, v in fields.items()}
    return json.dumps(norm, sort_keys=True, separators=(",", ":"))


def canonical_hash(item: dict) -> str:
    """sha256(canonical_json of exactly HASH_FIELDS picked from item))[:16].

    Missing fields are included as None so the hash is stable regardless of
    which keys an item happens to carry.
    """
    picked = {f: item.get(f) for f in HASH_FIELDS}
    return hashlib.sha256(canonical_json(picked).encode("utf-8")).hexdigest()[:16]
