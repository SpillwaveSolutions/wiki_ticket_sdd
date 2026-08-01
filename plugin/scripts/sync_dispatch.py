#!/usr/bin/env python3
"""sync_dispatch.py — the ticket-sync dispatcher.

Owns every invariant in docs/plans/2026-07-18-typed-adapter-contract.md §4:
scope, canonical hash, create-vs-update, the idempotency marker, echo
suppression, conflict detection, capabilities validation, and building
`worklog ingest` calls from pull output. The adapter is a dumb translator;
if any of this logic appears in an adapter, the design has failed.

Adapter resolution: $WORKLOG_TICKET_ADAPTER, else `adapter_path` in
.work/sync-state.json, else none → local-only mode (a mode, not an error;
spec §15.10).
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canonical import HASH_FIELDS, canonical_hash
from fold import external_owners

BIN = os.path.dirname(os.path.abspath(__file__))
SYNC_STATE = ".work/sync-state.json"
INGEST_FIELDS = ("title", "body", "status", "priority", "assignee", "type",
                 "level", "kind", "milestone")
CLOSED_STATUSES = ("done", "cancelled")
LOCAL_ONLY = ("worklog sync: no adapter configured — local-only "
              "(set WORKLOG_TICKET_ADAPTER or run worklog adapter check)")
LOG_PATHS = (".work/todo.jsonl", ".work/done.jsonl")
EPOCH = "1970-01-01T00:00:00Z"  # ponytail: fallback --since for an empty log

# Mirror of schema/capabilities.schema.json — embedded because installed repos
# ship bin/ without schema/. tests/test_dispatch.py asserts the two are identical.
CAPABILITIES_SCHEMA = {
    "description": "Adapter `capabilities` output (typed-adapter-contract spec section 3.1). Restricted to the subset {type, required, properties, enum, items, additionalProperties} so a stdlib mini-validator can enforce it.",
    "type": "object",
    "required": ["system", "supports", "types", "marker", "fields", "max_title"],
    "properties": {
        "system": {"type": "string"},
        "supports": {
            "type": "array",
            "items": {"enum": ["push", "pull", "get", "close"]}
        },
        "types": {
            "description": "Canonical type -> platform type name, or null if the platform has no equivalent (triggers the documented degrade path).",
            "type": "object"
        },
        "marker": {
            "type": "object",
            "required": ["style", "template"],
            "properties": {
                "style": {"type": "string"},
                "template": {
                    "type": "string",
                    "description": "MUST contain the literal substring {ulid}. The mini-validator subset cannot express substring containment; the dispatcher checks it explicitly."
                }
            }
        },
        "fields": {
            "description": "Canonical field -> platform mapping, or the string \"unsupported\" (dispatcher reports drift, never errors).",
            "type": "object"
        },
        "max_title": {"type": "integer"}
    }
}


class ContractError(Exception):
    """An adapter broke the typed contract; the message names the field."""


TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
}


def validate(instance, schema, path="$"):
    """Mini JSON Schema validator for the subset
    {type, required, properties, enum, items, additionalProperties}.
    Raises ContractError naming the offending field path.

    tests/test_adapter_contract.py carries its own copy — deliberately no
    import coupling between the test suite and the dispatcher.
    """
    if "enum" in schema and instance not in schema["enum"]:
        raise ContractError("%s: %r not in enum %r" % (path, instance, schema["enum"]))
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(TYPE_CHECKS[t](instance) for t in types):
            raise ContractError("%s: expected %s, got %r"
                                % (path, "/".join(types), instance))
    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                raise ContractError("%s: missing required field %r" % (path, req))
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], "%s.%s" % (path, key))
            elif schema.get("additionalProperties") is False:
                raise ContractError("%s: unexpected field %r" % (path, key))
    if isinstance(instance, list) and "items" in schema:
        for i, value in enumerate(instance):
            validate(value, schema["items"], "%s[%d]" % (path, i))


def rev_to_ms(rev):
    """Remote revision stamp -> epoch ms for the deterministic ingest ev."""
    try:
        return int(datetime.datetime.fromisoformat(
            rev.replace("Z", "+00:00")).timestamp() * 1000)
    except (ValueError, AttributeError):
        return int(time.time() * 1000)  # ponytail: unparseable rev -> now


def earliest_event_ts(paths=LOG_PATHS):
    """Earliest `ts` across the local event log.

    Seeds --since on a cursor-less first pull (worklog#141): the adapter
    contract requires one of --since/--keys, so a repo that has never pulled
    before must not call it with neither. Bad JSON or a missing file is
    skipped, same leniency as fold.py's own log reader.
    """
    earliest = None
    for path in paths:
        try:
            fh = open(path, encoding="utf-8")
        except FileNotFoundError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ts = json.loads(line).get("ts")
                except json.JSONDecodeError:
                    continue
                if ts and (earliest is None or ts < earliest):
                    earliest = ts
    return earliest


def resolve_adapter():
    path = os.environ.get("WORKLOG_TICKET_ADAPTER")
    if path:
        return path
    try:
        with open(SYNC_STATE, encoding="utf-8") as fh:
            return json.load(fh).get("adapter_path")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


class Dispatcher:
    COUNT_KEYS = ("created", "updated", "closed", "skipped", "pulled",
                  "conflicts", "deferred")
    # How many not-founds, with nothing succeeding, before we stop believing
    # the tickets and start suspecting the project. Three rather than one so a
    # genuinely-deleted first ticket does not abort a healthy run; low enough
    # that a bad project setting cannot walk the whole log (ADR-0004).
    GONE_ABORT = 3

    def __init__(self, adapter, retry_base_delay=0.5, dry_run=False):
        self.adapter = adapter
        self.base_delay = retry_base_delay
        self.dry_run = dry_run
        self.counts = dict.fromkeys(self.COUNT_KEYS, 0)
        self.drift = []
        self.collisions = {}
        # #238: what this run replaced on live tickets, and what the one
        # batched read to find that out cost.
        self.overwrites = []
        self.remote_before = {}
        self.snapshot_cost = None
        self.state = self._load_state()
        # GONE bookkeeping (ADR-0004). Exit code 3 cannot separate a deleted
        # ticket from an unreachable project — both are 404 — so the guard is
        # on SCALE, not on any per-ticket judgement: a run that has proved
        # nothing may condemn at most GONE_ABORT-1 items before it aborts.
        # `adapter_ok` is what disarms that, and the marks are buffered so the
        # abort can leave nothing behind.
        self.adapter_ok = False
        self.pending_gone = {}

    # --- state (.work/sync-state.json, per-clone) ---

    def _load_state(self):
        try:
            with open(SYNC_STATE, encoding="utf-8") as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_state(self):
        if self.dry_run:
            return
        os.makedirs(".work", exist_ok=True)
        with open(SYNC_STATE, "w", encoding="utf-8") as fh:
            json.dump(self.state, fh, indent=2, sort_keys=True)
            fh.write("\n")

    def item_state(self, iid):
        return self.state.setdefault("items", {}).setdefault(iid, {})

    def last_pushed(self, iid):
        return self.state.get("items", {}).get(iid, {}).get("last_pushed_hash")

    def is_dirty(self, iid, h, ext):
        """Content changed, OR the ticket this item points at changed.

        `external` is not in HASH_FIELDS, so the content hash alone can never
        notice an unlink or a re-link — which made `worklog unlink` a silent
        no-op at sync time and left github#226's damaged ticket unrepaired.

        Only compares when a key was actually recorded before: clones that
        predate last_pushed_key must not see every item go dirty at once.
        """
        st = self.state.get("items", {}).get(iid, {})
        if h != st.get("last_pushed_hash"):
            return True
        prev = st.get("last_pushed_key")
        now = str(ext["key"]) if ext.get("key") else None
        return prev is not None and prev != now

    def record_push(self, iid, h, key):
        self.item_state(iid).update({"last_pushed_hash": h,
                                     "last_pushed_key": str(key) if key else None})

    # --- process seams ---

    def run_adapter(self, *args, stdin=None):
        p = subprocess.run([self.adapter, *args], input=stdin,
                           capture_output=True, text=True)
        if p.stderr:
            sys.stderr.write(p.stderr)
        return p

    def worklog(self, *args, fatal=True):
        p = subprocess.run([sys.executable, os.path.join(BIN, "worklog"),
                            "--actor", "sync", *args],
                           capture_output=True, text=True)
        if p.returncode != 0:
            if fatal:
                sys.exit("worklog sync: `worklog %s` failed: %s"
                         % (args[0], p.stderr.strip()))
            self.note("worklog %s failed: %s" % (args[0], p.stderr.strip()))
            return None
        return p.stdout

    def record_link(self, iid, system, key, resp):
        """Record the key the tracker just minted. Must never abort the run.

        The ticket already exists remotely at this point, and create-vs-update
        is decided purely by `external.key` presence — so exiting here leaves a
        live ticket with no local link, and the NEXT run files a second one.
        Hence --force (the one-owner check cannot apply to a key the remote
        just handed us) and fatal=False (no link failure may kill a run
        mid-create). A failure is real drift, not a reason to stop.
        """
        link = ["link", iid, "--system", system, "--key", str(key), "--force"]
        if resp.get("url"):
            link += ["--url", resp["url"]]
        if resp.get("rev"):
            link += ["--rev", resp["rev"]]
        if self.worklog(*link, fatal=False) is None:
            self.note("%s: created %s:%s but could not record the link — "
                      "link it by hand before the next sync, or it will be "
                      "created again" % (iid[:8], system, key))

    def fold_items(self):
        return json.loads(self.worklog("fold"))

    def note(self, line):
        self.drift.append(line)

    # --- capabilities gate (plan §4.6): first, every run, before any push ---

    def capabilities(self):
        p = self.run_adapter("capabilities")
        if p.returncode != 0:
            raise ContractError("capabilities exited %d" % p.returncode)
        try:
            caps = json.loads(p.stdout)
        except json.JSONDecodeError as e:
            raise ContractError("capabilities: not valid JSON: %s" % e)
        validate(caps, CAPABILITIES_SCHEMA)
        if "{ulid}" not in caps["marker"]["template"]:
            raise ContractError("$.marker.template: must contain '{ulid}'")
        return caps

    # --- mapping ---

    def outbound(self, item, caps):
        """The item as pushed: HASH_FIELDS only, type degraded per
        capabilities (null platform type -> story, else task; plan §6.3).
        last_pushed_hash is the canonical hash of THIS shape, so the degraded
        echo coming back on pull still suppresses."""
        out = {"id": item["id"]}
        for f in HASH_FIELDS:
            if item.get(f) is not None:
                out[f] = item[f]
        # Taxonomy compat (handoff to edges agent): folded items carry
        # level/kind/milestone, not `type`. HASH_FIELDS above already copies
        # them; the adapter contract still speaks `type`, so derive it from
        # level (falling back to a raw legacy `type` if one is present).
        out.setdefault("type", item.get("level", item.get("type")) or "task")
        if caps["types"].get(out["type"]) is None:
            out["type"] = "story" if caps["types"].get("story") is not None else "task"
        return out

    # --- push side ---

    def call_push(self, payload):
        """push with retry-on-4: base_delay, x2, x2 (3 retries), then give up."""
        delay = self.base_delay
        p = None
        for attempt in range(4):
            p = self.run_adapter("push", stdin=json.dumps(payload))
            if p.returncode != 4:
                break
            if attempt < 3:
                time.sleep(delay)
                delay *= 2
        return p

    def handle_exit(self, item, p):
        """§3.6 exit-code table. True = success, carry on with the item."""
        rc = p.returncode
        if rc == 0:
            # Reachability is proven, and this key answers — so any gone mark
            # from an earlier run is stale. Without this, a ticket restored
            # from the tracker's trash stays skipped forever, because the mark
            # is only outgrown when the key itself changes (ADR-0004).
            self.adapter_ok = True
            self.item_state(item["id"]).pop("gone_key", None)
            return True
        iid = item["id"]
        if rc == 2:
            self._save_state()
            sys.exit("worklog sync: adapter auth failure — re-authenticate "
                     "with the tracker and re-run. Nothing further was pushed.")
        if rc == 3:
            # GONE (definite not-found), not a transient failure. The adapter
            # contract says to clear `external` so the item files afresh, but
            # doing that automatically here cannot tell a real deletion from
            # a flaky 404 -- and auto-clearing on a transient error would
            # file a duplicate. Deliberately conservative (worklog#241): stop
            # retrying this item every run and hand the decision to a human,
            # instead of popping last_pushed_hash and hammering the same
            # dead key forever.
            key = (item.get("external") or {}).get("key")
            self.pending_gone[iid] = key
            if not self.adapter_ok and len(self.pending_gone) >= self.GONE_ABORT:
                self._save_state()   # deliberately WITHOUT the pending marks
                sys.exit(
                    "worklog sync: %d tickets reported gone and not one "
                    "adapter call has succeeded — the project itself is "
                    "probably unreachable, not the tickets. Nothing was "
                    "changed. Check WORKLOG_TICKET_PROJECT and the tracker "
                    "credentials, then re-run." % len(self.pending_gone))
            self.note("%s: ticket %s reported gone remotely — not retried "
                      "automatically; run `worklog unlink %s` to clear the "
                      "link and file a fresh one" % (iid[:8], key, iid))
            self.counts["deferred"] += 1
        elif rc == 4:
            self.note("rate limited on %s; deferred after 3 retries" % iid[:8])
            self.counts["deferred"] += 1
        elif rc == 5:
            self.remote_conflict(item)
        else:
            self.note("adapter error (exit %d) on %s; continuing" % (rc, iid[:8]))
        return False

    def remote_conflict(self, item):
        """Push refused with exit 5: fetch the remote and record per-field
        conflicts (report policy — never auto-resolve, plan §4.5)."""
        key = (item.get("external") or {}).get("key")
        p = self.run_adapter("get", str(key)) if key else None
        line = None
        if p and p.returncode == 0:
            try:
                line = json.loads(p.stdout)
            except json.JSONDecodeError:
                line = None
        if not line:
            self.note("remote conflict on %s (key %s); could not fetch detail"
                      % (item["id"][:8], key))
            self.counts["conflicts"] += 1
            return
        rev = (line.get("external") or {}).get("rev", "")
        for f in INGEST_FIELDS:
            if f in line and line[f] != item.get(f):
                self.worklog("conflict", item["id"], "--field", f,
                             "--local", str(item.get(f)), "--remote", str(line[f]),
                             "--remote-rev", rev, fatal=False)
                self.counts["conflicts"] += 1

    def report_collisions(self, items):
        """Print the contested tickets as their own block, not a drift line.

        Drift is what operators skim — burying a live-data-corruption warning
        there would reproduce github#226's silent-failure mode in a new
        costume. The report ends with the full repair including the step
        people otherwise miss: `external` is not in HASH_FIELDS, so unlinking
        the impostor does NOT make the surviving owner dirty, and the damaged
        ticket stays wrong until it is forced back into scope.
        """
        titles = {i["id"]: i.get("title", "") for i in items}
        print("sync: %d ticket(s) claimed by more than one item — NOT pushed "
              "(github#226)" % len(self.collisions), file=sys.stderr)
        for (system, key), ids in sorted(self.collisions.items(),
                                         key=lambda kv: (str(kv[0][0]), kv[0][1])):
            print("  %s:%s" % (system, key), file=sys.stderr)
            for i in ids:
                print("    <- %s  %s" % (i, titles.get(i, "")), file=sys.stderr)
            # ids are ULID-sorted, so the last is the newest link — usually the
            # mistake. Said as a heuristic, not asserted as fact.
            print("  the later link is usually the mistake:", file=sys.stderr)
            print("    worklog unlink %s" % ids[-1], file=sys.stderr)
            print("    worklog sync --keys %s   # re-push the surviving owner "
                  "over the damage" % key, file=sys.stderr)

    def refuse_ambiguous_keys(self, items, keys):
        """--keys accepts a ticket number as well as an item ULID. A number
        more than one item claims must be refused outright, not drag every
        claimant into scope -- that is exactly the reflex an operator reaches
        for while repairing a duplicate (github#226), and precisely wrong
        then (worklog#239). Unlike the collision guard below (which skips the
        colliders and keeps the rest of the run going), an ambiguous forced
        key stops the run before anything is pushed -- the operator asked for
        one specific ticket and got a fork in the road instead.
        """
        for key in keys:
            owners = sorted(i["id"] for i in items
                            if (i.get("external") or {}).get("key") == key)
            if len(owners) > 1:
                sys.exit("worklog sync: --keys %r is ambiguous — claimed by "
                         "%d items: %s (worklog unlink the wrong one first)"
                         % (key, len(owners), ", ".join(owners)))

    # --- overwrite reporting (#238) ---

    # What a reader would notice being replaced on a live ticket. Deliberately
    # not every ingest field: `body` is long enough to bury the line that
    # matters, and this exists to make damage visible at a glance.
    OVERWRITE_FIELDS = ("title", "status", "priority", "milestone", "assignee")

    def _keys_at_risk(self, items, caps, keys, blocked):
        """Keys of tickets this run may overwrite.

        Approximate on purpose. It does not re-derive the push loop's exact
        scope rules -- over-fetching costs nothing (the read is batched) and
        under-fetching only means one ticket reports no before/after. Cloning
        that logic to be exact would put the delicate part in two places.
        """
        at_risk = []
        for item in items:
            ext = item.get("external") or {}
            key = ext.get("key")
            if (not key or item["id"] in blocked or item.get("_orphan")
                    or not item.get("title")):
                continue
            h = canonical_hash(self.outbound(item, caps))
            forced = bool(keys) and (item["id"] in keys or key in keys)
            if self.is_dirty(item["id"], h, ext) or forced:
                at_risk.append(str(key))
        return at_risk

    def snapshot_remote(self, caps, at_risk):
        """{key: remote fields} as they stand BEFORE this run pushes.

        ONE batched `pull --keys` for the whole run. The ticket that asked for
        this flagged "one extra read per updated ticket" as a real cost worth
        measuring -- so it is a read per RUN instead, and the run reports how
        long it took and how many tickets it covered. The adapter contract
        already accepts a key list, so no new verb was needed.

        Degrades to {}: no pull support, a failed read, or unparseable output
        all mean "report the fields without before/after", never a failed sync.
        """
        if not at_risk or "pull" not in caps["supports"]:
            return {}
        started = time.time()
        p = self.run_adapter("pull", "--keys", ",".join(sorted(set(at_risk))))
        self.snapshot_cost = (len(set(at_risk)), time.time() - started)
        if p.returncode != 0:
            self.note("could not read current ticket state (exit %d); "
                      "overwrites reported without before/after" % p.returncode)
            return {}
        snap = {}
        for raw in p.stdout.splitlines():
            if not raw.strip():
                continue
            try:
                line = json.loads(raw)
            except json.JSONDecodeError:
                continue
            key = (line.get("external") or {}).get("key")
            if key is not None:
                snap[str(key)] = line
        return snap

    def note_overwrite(self, iid, key, payload_item):
        """Record which live fields this push replaced, before -> after."""
        before = self.remote_before.get(str(key))
        if before is None:
            return
        changed = []
        for f in self.OVERWRITE_FIELDS:
            if f not in before:
                continue
            old, new = before.get(f), payload_item.get(f)
            if old != new:
                changed.append("%s: %r -> %r" % (f, old, new))
        if changed:
            self.overwrites.append("%s (%s): %s"
                                   % (key, iid[:8], "; ".join(changed)))

    def push_items(self, items, caps, keys):
        if keys:
            self.refuse_ambiguous_keys(items, keys)
        # Collection-level gate: inside the loop every item looks perfectly
        # valid, which is exactly why github#226 was invisible from the log.
        self.collisions = {k: v for k, v in external_owners(items).items()
                           if len(v) > 1}
        if self.collisions:
            self.report_collisions(items)
        blocked = {i for ids in self.collisions.values() for i in ids}
        # Read the live tickets BEFORE anything is pushed -- after the push
        # there is no "before" left to report (#238).
        self.remote_before = self.snapshot_remote(
            caps, self._keys_at_risk(items, caps, keys, blocked))
        for item in items:
            iid = item["id"]
            ext = item.get("external") or {}
            # Orphans (events for an unknown item, e.g. a typo'd id) and
            # titleless items are fold debris, not work — report, never push.
            # Pushing one files an "(untitled)" ticket remotely.
            if item.get("_orphan") or not item.get("title"):
                # Once it is closed the debris is settled: it can never be
                # pushed and there is nothing to act on, so repeating it every
                # run only teaches readers to skim drift (01KYTGNS76).
                if item.get("status") not in CLOSED_STATUSES:
                    self.drift.append(
                        f"{iid[:8]}: orphan/untitled item skipped — not pushed")
                continue
            # Before `closed` is computed, so the update-then-close branch is
            # covered too — that is the path that marked the reported ticket
            # Done. Corruption needs BOTH claimants pushed, so skipping the
            # set removes it entirely; the rest of the run proceeds.
            if iid in blocked:
                continue
            # A ticket reported gone (rc 3) on a prior run: don't retry it
            # every run (worklog#241) -- surface the remedy again so it isn't
            # forgotten. `worklog unlink` clears `external`, so ext["key"]
            # then mismatches gone_key and the item re-enters scope normally.
            gone_key = self.state.get("items", {}).get(iid, {}).get("gone_key")
            if gone_key is not None and gone_key == ext.get("key"):
                self.note("%s: ticket %s reported gone remotely — not "
                          "retried automatically; run `worklog unlink %s` "
                          "to clear the link and file a fresh one"
                          % (iid[:8], gone_key, iid))
                continue
            closed = item.get("status") in CLOSED_STATUSES
            payload_item = self.outbound(item, caps)
            h = canonical_hash(payload_item)
            forced = bool(keys) and (iid in keys or ext.get("key") in keys)
            dirty = self.is_dirty(iid, h, ext)
            # Scope (spec §10.5): open ∪ hash-dirty ∪ --keys. A closed item
            # that never went remote is inert — pushing it would file tickets
            # for long-dead work.
            if closed and not ext.get("key") and not forced:
                continue
            if not (dirty or forced):
                if not closed:
                    self.counts["skipped"] += 1
                continue

            # Taxonomy compat (handoff to edges agent): degrade note reads
            # `level` now that folded items no longer carry `type`.
            local_type = item.get("level", item.get("type")) or "task"
            if payload_item["type"] != local_type:
                self.note("%s: %s mapped to %s (no %s type in %s)"
                          % (iid[:8], local_type, payload_item["type"],
                             local_type, caps["system"]))

            if closed:
                key = ext.get("key")
                if not key:
                    # Forced into scope (--keys) but never went remote: no
                    # key to update-then-close against, so create first,
                    # link it, then close immediately.
                    if self.dry_run:
                        print("would create+close %s (%s)"
                              % (iid[:8], item.get("status")))
                        continue
                    p = self.call_push({
                        "op": "create",
                        "marker": caps["marker"]["template"].replace("{ulid}", iid),
                        "item": payload_item})
                    if not self.handle_exit(item, p):
                        continue
                    try:
                        resp = json.loads(p.stdout)
                    except json.JSONDecodeError:
                        self.note("push %s: adapter returned non-JSON; not recorded"
                                  % iid[:8])
                        continue
                    key = resp.get("key")
                    if not key:
                        self.note("push %s: response missing key; not linked"
                                  % iid[:8])
                        continue
                    self.record_link(iid, caps["system"], key, resp)
                    self.counts["created"] += 1
                else:
                    if self.dry_run:
                        print("would close %s (%s)" % (key, item.get("status")))
                        continue
                    if dirty:
                        # Close alone never syncs fields (adapter close is
                        # key+resolution only), so reclassify-then-close left
                        # stale remote labels the next pull re-ingested over
                        # the local edit (worklog 01KY129S). Push the final
                        # shape first; the close echo then hash-suppresses.
                        p = self.call_push({
                            "op": "update", "key": key,
                            "marker": caps["marker"]["template"].replace("{ulid}", iid),
                            "item": payload_item})
                        if not self.handle_exit(item, p):
                            continue
                        # This is the path that marked the reported ticket
                        # Done -- the one most worth naming out loud.
                        self.note_overwrite(iid, key, payload_item)
                p = self.run_adapter("close", str(key),
                                     item.get("resolution") or item["status"])
                if self.handle_exit(item, p):
                    self.record_push(iid, h, key)
                    self.counts["closed"] += 1
                continue

            op = "update" if ext.get("key") else "create"
            payload = {"op": op, "key": ext.get("key"),
                       "marker": caps["marker"]["template"].replace("{ulid}", iid),
                       "item": payload_item}
            if self.dry_run:
                print("would %s %s%s" % (op, iid[:8],
                                         " -> %s" % ext["key"] if ext.get("key") else ""))
                # The most useful place for this: see what would be replaced
                # while it is still hypothetical.
                if op == "update":
                    self.note_overwrite(iid, ext["key"], payload_item)
                continue
            p = self.call_push(payload)
            if not self.handle_exit(item, p):
                continue
            try:
                resp = json.loads(p.stdout)
            except json.JSONDecodeError:
                self.note("push %s: adapter returned non-JSON; not recorded" % iid[:8])
                continue
            pushed_key = ext.get("key")
            if op == "create":
                if not resp.get("key"):
                    self.note("push %s: response missing key; not linked" % iid[:8])
                    continue
                pushed_key = resp["key"]
                self.record_link(iid, caps["system"], pushed_key, resp)
                self.counts["created"] += 1
            else:
                self.counts["updated"] += 1
                self.note_overwrite(iid, pushed_key, payload_item)
            self.record_push(iid, h, pushed_key)
        # The push loop is over, so the abort can no longer fire: whatever is
        # still buffered is what this run really means to record.
        self.commit_gone()

    # --- pull side ---

    def pull(self, caps, items, keys):
        if "pull" not in caps["supports"]:
            self.note("adapter does not support pull; local log may lag remote")
            return
        system = caps["system"]
        # No cursor yet (first pull for this system) -> the adapter contract
        # still requires --since or --keys, so seed one from the earliest
        # local event instead of calling with neither (worklog#141).
        cursor = (self.state.get("cursors", {}).get(system)
                 or earliest_event_ts() or EPOCH)
        args = ["pull", "--since", cursor]
        p = self.run_adapter(*args)
        if p.returncode == 2:
            sys.exit("worklog sync: adapter auth failure on pull — "
                     "re-authenticate with the tracker and re-run.")
        if p.returncode != 0:
            self.note("pull failed (exit %d); cursor not advanced" % p.returncode)
            return
        self.adapter_ok = True   # a clean pull proves the project is reachable
        by_id = {i["id"]: i for i in items}
        max_rev = cursor
        for raw in p.stdout.splitlines():
            if not raw.strip():
                continue
            try:
                line = json.loads(raw)
            except json.JSONDecodeError:
                self.note("pull: unparseable NDJSON line skipped")
                continue
            ext = line.get("external") or {}
            rev = ext.get("rev")
            if rev and (max_rev is None or rev > max_rev):
                max_rev = rev
            iid = line.get("id")
            if not iid:
                # Creating local items from remote-origin tickets is future
                # work — report, don't act, keep this run read-safe.
                self.note("remote-origin ticket %s: no local item created"
                          % ext.get("key"))
                continue
            local = by_id.get(iid)
            if local is None:
                self.note("pull: key %s carries unknown item %s"
                          % (ext.get("key"), iid[:8]))
                continue
            last = self.last_pushed(iid)
            if canonical_hash(line) == last:
                continue  # echo of our own push (spec §10.3)
            mapped_local = self.outbound(local, caps)
            # ponytail: field-diff against the outbound shape, so a degraded
            # type echo never reads as a remote edit. Labels sync via
            # add/del is future work; INGEST_FIELDS only.
            changed = [f for f in INGEST_FIELDS
                       if f in line and line[f] != mapped_local.get(f)]
            if not changed:
                continue
            both = last is not None and canonical_hash(mapped_local) != last
            if self.dry_run:
                print("would %s %s: %s"
                      % ("record conflict on" if both else "ingest", iid[:8],
                         ",".join(changed)))
                continue
            if both:
                # Both sides moved since last push (spec §10.6): record,
                # never overwrite under the default report policy.
                for f in changed:
                    self.worklog("conflict", iid, "--field", f,
                                 "--local", str(local.get(f)),
                                 "--remote", str(line[f]),
                                 "--remote-rev", rev or "", fatal=False)
                    self.counts["conflicts"] += 1
            else:
                ing = ["ingest", iid, "--system", system,
                       "--key", str(ext.get("key")), "--rev", rev or "",
                       "--rev-ts-ms", str(rev_to_ms(rev))]
                for f in changed:
                    ing += ["--set", "%s=%s" % (f, line[f])]
                if self.worklog(*ing, fatal=False) is not None:
                    self.counts["pulled"] += 1
        if max_rev and not self.dry_run:
            self.state.setdefault("cursors", {})[system] = max_rev

    def commit_gone(self):
        """Flush the run's buffered gone marks into state.

        Buffering is not a second safety rule — GONE_ABORT is the rule, and it
        has already fired if this run was going to condemn items at scale. What
        buffering buys is that the abort leaves nothing behind: marks written
        item-by-item would survive the exit that was supposed to change
        nothing (ADR-0004).
        """
        for iid, key in self.pending_gone.items():
            self.item_state(iid)["gone_key"] = key
        self.pending_gone.clear()

    # --- the run ---

    def sync(self, keys=None, push=True, pull=True):
        caps = self.capabilities()  # gate: nothing runs on a broken contract
        unsupported = sorted(f for f, m in caps["fields"].items()
                             if m == "unsupported")
        if unsupported:
            self.note("fields not synced on %s: %s"
                      % (caps["system"], ", ".join(unsupported)))
        if push:
            self.push_items(self.fold_items(), caps, keys or [])
        if pull:
            self.pull(caps, self.fold_items(), keys or [])
        self._save_state()
        self.report()
        # Non-zero so a contested ticket cannot pass unnoticed in CI. The run
        # still did everything that was safe to do.
        return 1 if self.collisions else 0

    def report(self):
        print("sync report: " + " ".join("%s=%d" % (k, self.counts[k])
                                         for k in self.COUNT_KEYS))
        # Before drift: "updated 2" is not the line that catches damage --
        # naming the field that changed on a live ticket is (#238).
        if self.overwrites:
            print("overwrote live ticket fields:")
            for line in self.overwrites:
                print("  - " + line)
        if self.snapshot_cost:
            n, secs = self.snapshot_cost
            print("  (read %d ticket%s in %.2fs to report the above)"
                  % (n, "" if n == 1 else "s", secs))
        if self.drift:
            print("drift:")
            for line in self.drift:
                print("  - " + line)


def build_parser():
    ap = argparse.ArgumentParser(
        prog="sync_dispatch.py",
        description="Ticket-sync dispatcher (typed adapter contract).")
    ap.add_argument("--dry-run", action="store_true",
                    help="print decisions; call no mutating verbs")
    ap.add_argument("--keys",
                    help="comma-separated item ULIDs or external keys to force into scope")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--push-only", action="store_true")
    g.add_argument("--pull-only", action="store_true")
    ap.add_argument("--retry-base-delay", type=float, default=0.5,
                    metavar="SECONDS", help="first backoff delay for exit-4 retries")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    adapter = resolve_adapter()
    if not adapter or not os.path.exists(adapter):
        print(LOCAL_ONLY)
        return 0
    d = Dispatcher(adapter, retry_base_delay=a.retry_base_delay, dry_run=a.dry_run)
    try:
        return d.sync(keys=[k for k in (a.keys or "").split(",") if k] or None,
                      push=not a.pull_only, pull=not a.push_only)
    except ContractError as e:
        print("worklog sync: contract violation: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
