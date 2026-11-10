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


_git_commit_cache = {}   # {"short"|"full": sha}; many events per run


def _rev_parse(short: bool) -> str:
    """HEAD's sha, or "" outside a git repo / before the first commit.

    Memoised per process and per length. HEAD does not move underneath one
    command, and `worklog` writes an event per command -- shelling out per
    event would put a subprocess in the hot path of the only writer.

    Never raises. A missing git, a bare directory, or a repo with no commits
    all return "", and every caller is required to OMIT its field rather
    than write an empty one.
    """
    key = "short" if short else "full"
    if key in _git_commit_cache:
        return _git_commit_cache[key]
    sha = ""
    if not os.environ.get("WORKLOG_NO_GIT_PROVENANCE"):
        try:
            import subprocess
            argv = ["git", "rev-parse"] + (["--short"] if short else []) + ["HEAD"]
            p = subprocess.run(argv, capture_output=True, text=True)
            if p.returncode == 0:
                sha = p.stdout.strip()
        except OSError:
            sha = ""
    _git_commit_cache[key] = sha
    return sha


def git_commit() -> str:
    """Short HEAD sha for an EVENT's `git` field.

    Provenance, NOT identity: this goes in an event's own `git` field, never
    into the id. An id is issued once and must never collide, so spending its
    entropy to carry origin information weakens the single guarantee it
    exists to provide.

    Short is right here: the log carries one per event and the value is a
    hint for a human tracing origin, not a key anything resolves.
    """
    return _rev_parse(short=True)


def git_commit_full() -> str:
    """Full 40-hex HEAD sha for a DOCUMENT's front matter.

    Full length, and that is not a style preference. `ia._scalar` coerces an
    all-digit value to int before it considers quotes, so a 7-char short sha
    is all digits roughly one time in 27 and one with a leading zero reads
    back corrupted but still sha-shaped. Front matter writers should quote
    the value too -- belt and braces -- but the cheap structural fix is to
    make an all-digit sha vanishingly unlikely rather than routine.

    It also matches what design docs have carried since they were introduced,
    so there is one vocabulary for "the commit this doc was written against"
    rather than two.

    Caveat worth knowing at every call site: at stamping time HEAD is the
    commit BEFORE the one the doc lands in -- a commit cannot know its own
    sha. This means "the tree this document was written against", which is
    exactly what a reader diffing stale prose wants.
    """
    return _rev_parse(short=False)


_last_ms = -1
_last_entropy = None


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

    Same-millisecond calls are monotonic: the 80-bit entropy increments so
    create-then-update in one tick cannot fold out of order (merge-rescue
    already worked around this; the mint path does it too).
    """
    global _last_ms, _last_entropy
    ms = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    if ms == _last_ms and _last_entropy is not None:
        n = int.from_bytes(_last_entropy, "big") + 1
        if n >= (1 << 80):
            ms += 1
            entropy = os.urandom(10)
        else:
            entropy = n.to_bytes(10, "big")
    else:
        entropy = os.urandom(10)
    _last_ms = ms
    _last_entropy = entropy
    return encode(ms, entropy)


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
