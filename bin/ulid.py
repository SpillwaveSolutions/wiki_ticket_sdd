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


_git_commit_cache = []   # one-element memo; `worklog` mints many events per run


def git_commit() -> str:
    """Short HEAD sha, or "" outside a git repo / before the first commit.

    Provenance, NOT identity: this goes in an event's own `git` field, never
    into the id. An id is issued once and must never collide, so spending its
    entropy to carry origin information weakens the single guarantee it
    exists to provide.

    Memoised per process. HEAD does not move underneath one command, and
    `worklog` writes an event per command -- shelling out per event would put
    a subprocess in the hot path of the only writer.
    """
    if _git_commit_cache:
        return _git_commit_cache[0]
    sha = ""
    if not os.environ.get("WORKLOG_NO_GIT_PROVENANCE"):
        try:
            import subprocess
            p = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                               capture_output=True, text=True)
            if p.returncode == 0:
                sha = p.stdout.strip()
        except OSError:
            sha = ""
    _git_commit_cache.append(sha)
    return sha


def new(timestamp_ms: int = None) -> str:
    """A fresh ULID for a locally-originated event.

    Full 80 bits of entropy, always. v0.19.0 briefly overwrote five of those
    characters with the short git hash to make branches distinguishable; that
    was the wrong trade and is reverted. An id is issued once and never
    changes, and the only thing it must guarantee is that it does not clash,
    so entropy is not currency to spend on metadata. Provenance lives in the
    event's `git` field instead -- which also traces better, since an item's
    id is minted once and could only ever name the branch the ITEM was
    created on, while a field on every event names the origin of each one.
    """
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
