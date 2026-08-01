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


GIT_STAMP_LEN = 5
_git_stamp_cache = []   # one-element memo; `worklog` mints many ids per run


def git_stamp() -> str:
    """First GIT_STAMP_LEN characters of HEAD, as Crockford base32.

    Git hashes are hex, and 0-9/A-F are all valid Crockford, so uppercasing
    is the whole conversion. Outside a git repo, or before the first commit,
    this is "" and ULIDs keep their full random entropy.

    Memoised per process. HEAD does not move underneath a single command, and
    `worklog` mints an id per event -- shelling out each time would put a
    subprocess in the hot path of the only writer.
    """
    if _git_stamp_cache:
        return _git_stamp_cache[0]
    stamp = ""
    if not os.environ.get("WORKLOG_NO_GIT_ULID"):
        try:
            import subprocess
            p = subprocess.run(["git", "rev-parse", "--short=%d" % GIT_STAMP_LEN,
                                "HEAD"], capture_output=True, text=True)
            raw = p.stdout.strip().upper()
            if p.returncode == 0 and len(raw) >= GIT_STAMP_LEN:
                candidate = raw[:GIT_STAMP_LEN]
                if all(c in CROCKFORD for c in candidate):
                    stamp = candidate
        except (OSError, ValueError):
            stamp = ""
    _git_stamp_cache.append(stamp)
    return stamp


def new(timestamp_ms: int = None, git: str = None) -> str:
    """A fresh ULID for a locally-originated event.

    Five characters of the entropy carry the short git hash of HEAD, so two
    agents in different worktrees or on different branches mint visibly
    different ids and events can be traced back to the branch that wrote
    them. The 26-character format, the 48-bit time prefix and therefore
    lexicographic-sort-equals-time-sort are all unchanged; only entropy is
    spent, 80 bits down to 55, which is still far more than this log will
    ever need to stay collision-free.

    It REPLACES entropy rather than appending: a 31-character id would not be
    a ULID, and every reader here (ULID_RE, timestamp_ms, the fold's string
    sort) is written against the fixed width.

    Deliberately NOT applied to deterministic() -- see that docstring. Two
    machines ingesting the same remote change must produce byte-identical
    ids, and a per-clone git hash is the one thing guaranteed to differ.
    """
    ms = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    out = encode(ms, os.urandom(10))
    stamp = git_stamp() if git is None else git
    if not stamp:
        return out
    # Entropy occupies characters 10..25; overwrite its first five.
    return out[:10] + stamp[:GIT_STAMP_LEN] + out[10 + GIT_STAMP_LEN:]


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
