#!/usr/bin/env python3
"""
ulid.py -- ULID generation, including the deterministic form used for ingested
remote changes.

WORKLOG-SPEC sections 5.2 and 10.2.

A ULID is 128 bits: 48 bits of millisecond timestamp + 80 bits of entropy,
Crockford base32 encoded to 26 characters. Lexicographic sort == time sort,
which is why the fold can sort with a plain string comparison.

The reason this file exists rather than a dependency: `ev_remote` for ingested
events must be DETERMINISTIC. Two developers polling the same Jira change must
produce byte-identical log lines, so that union merge plus dedupe-by-`ev`
collapses them to one. A random ULID per ingest means both survive, and an old
remote value can sort above a newer local edit and silently revert it.
See tests/test_ulid.py::test_the_bug_this_prevents.
"""

import hashlib
import os
import time

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # no I, L, O, U


def _encode(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        out.append(CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def encode(timestamp_ms: int, entropy: bytes) -> str:
    if len(entropy) != 10:
        raise ValueError(f"entropy must be exactly 10 bytes, got {len(entropy)}")
    if not 0 <= timestamp_ms < (1 << 48):
        raise ValueError("timestamp out of 48-bit range")
    return _encode(timestamp_ms, 10) + _encode(int.from_bytes(entropy, "big"), 16)


def new(timestamp_ms: int = None) -> str:
    """A fresh ULID for a locally-originated event."""
    ms = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return encode(ms, os.urandom(10))


def deterministic(system: str, key: str, rev: str, rev_timestamp_ms: int) -> str:
    """The ULID for an ingested remote change (section 10.2).

    Timestamp is the REMOTE revision time, not now(). Entropy is
    sha256(system|key|rev) truncated to the 80 bits the format allows.

    Same remote change -> same ULID on every machine, forever.
    """
    digest = hashlib.sha256(f"{system}|{key}|{rev}".encode("utf-8")).digest()
    return encode(rev_timestamp_ms, digest[:10])


def timestamp_ms(ulid: str) -> int:
    value = 0
    for ch in ulid[:10]:
        value = (value << 5) | CROCKFORD.index(ch)
    return value


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print(new())
    else:
        print(deterministic(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])))
