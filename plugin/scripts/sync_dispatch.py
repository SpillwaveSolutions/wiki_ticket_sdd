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


def forward_ticket_env(config_path=".work/config.yml"):
    """Copy ticketing.project / ticketing.system into the adapter env.

    The contract (typed-adapter-contract §3) says connection details arrive
    via WORKLOG_TICKET_PROJECT; nothing was producing that variable. GitHub
    papers over the gap with `gh repo view`; a Jira adapter cannot.
    """
    if (os.environ.get("WORKLOG_TICKET_PROJECT")
            and os.environ.get("WORKLOG_TICKET_SYSTEM")):
        return
    try:
        with open(config_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return
    project = system = None
    inside = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line[:1] not in " \t":
            inside = line.strip().startswith("ticketing:")
            continue
        if not inside or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip().strip("\"'")
        if key == "project" and val:
            project = val
        elif key == "system" and val:
            system = val
    if project and not os.environ.get("WORKLOG_TICKET_PROJECT"):
        os.environ["WORKLOG_TICKET_PROJECT"] = project
    if system and system != "none" and not os.environ.get("WORKLOG_TICKET_SYSTEM"):
        os.environ["WORKLOG_TICKET_SYSTEM"] = system


class Dispatcher:
    COUNT_KEYS = ("created", "updated", "closed", "skipped", "pulled",
                  "conflicts", "deferred")
    # How many not-founds, with nothing succeeding, before we stop believing
    # the tickets and start suspecting the project. Three rather than one so a
    # genuinely-deleted first ticket does not abort a healthy run; low enough
    # that a bad project setting cannot walk the whole log (ADR-0004).
    GONE_ABORT = 3

    def __init__(self, adapter, retry_base_delay=0.5, dry_run=False, actor="sync"):
        self.adapter = adapter
        self.base_delay = retry_base_delay
        self.dry_run = dry_run
        self.actor = actor
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
        # #385: first-class drift, reported even on --push-only.
        self.unmarked = []          # (key, title, system)
        self.remote_closed = []     # (iid, key, title)
        self.skip_push_ids = set()  # do not push; would rewrite a closed remote

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

    def remembered_key(self, iid, ext=None):
        """The remote key this item should update against.

        Folded `external.key` wins. When a checkout has thrown the link
        event away (#382), fall back to last_pushed_key in the gitignored
        state file so the next run updates the ticket that already exists
        instead of minting a second one.
        """
        if ext is None:
            ext = {}
        if ext.get("key"):
            return str(ext["key"])
        prev = self.state.get("items", {}).get(iid, {}).get("last_pushed_key")
        return str(prev) if prev else None

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
        forward_ticket_env()
        p = subprocess.run([self.adapter, *args], input=stdin,
                           capture_output=True, text=True)
        if p.stderr:
            sys.stderr.write(p.stderr)
        return p

    def worklog(self, *args, fatal=True):
        p = subprocess.run([sys.executable, os.path.join(BIN, "worklog"),
                            "--actor", self.actor, *args],
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

        The ticket already exists remotely at this point. Create-vs-update
        is decided by remembered_key (folded `external.key`, else
        last_pushed_key) — so exiting here leaves a live ticket with no
        local link, and a clone that has also forgotten last_pushed_key
        files a second one. Hence --force (the one-owner check cannot apply
        to a key the remote just handed us) and fatal=False (no link
        failure may kill a run mid-create). A failure is real drift, not a
        reason to stop.
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
            if not key:
                key = self.remembered_key(iid)
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
            if iid in self.skip_push_ids:
                continue
            # A ticket reported gone (rc 3) on a prior run: don't retry it
            # every run (worklog#241) -- surface the remedy again so it isn't
            # forgotten. `worklog unlink` clears `external`, so ext["key"]
            # then mismatches gone_key and the item re-enters scope normally.
            gone_key = self.state.get("items", {}).get(iid, {}).get("gone_key")
            if gone_key is not None and gone_key == self.remembered_key(iid, ext):
                self.note("%s: ticket %s reported gone remotely — not "
                          "retried automatically; run `worklog unlink %s` "
                          "to clear the link and file a fresh one"
                          % (iid[:8], gone_key, iid))
                continue
            closed = item.get("status") in CLOSED_STATUSES
            payload_item = self.outbound(item, caps)
            h = canonical_hash(payload_item)
            key = self.remembered_key(iid, ext)
            relink = bool(key) and not ext.get("key")
            forced = bool(keys) and (iid in keys or ext.get("key") in keys
                                     or (key in keys if key else False))
            dirty = self.is_dirty(iid, h, ext)
            # Scope (spec §10.5): open ∪ hash-dirty ∪ --keys. A closed item
            # that never went remote is inert — pushing it would file tickets
            # for long-dead work. last_pushed_key counts as "went remote"
            # even when the log lost the link (#382).
            if closed and not key and not forced:
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
                        # A close is not always only a close: a dirty item
                        # pushes its final shape first (see below), and that
                        # push can rewrite fields on a ticket somebody else
                        # filed. Reporting overwrites only on the update path
                        # left this one silent -- the path where an operator
                        # reading "would close" is least expecting a field
                        # write. Same call, same condition, so the dry run now
                        # predicts exactly what the real run does.
                        if dirty:
                            self.note_overwrite(iid, key, payload_item)
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
                        if relink:
                            try:
                                resp = json.loads(p.stdout)
                            except json.JSONDecodeError:
                                resp = {}
                            self.record_link(iid, caps["system"], key, resp)
                p = self.run_adapter("close", str(key),
                                     item.get("resolution") or item["status"])
                if self.handle_exit(item, p):
                    if relink and ext.get("key") != key:
                        # Lost-link close of an already-pushed ticket: restore
                        # the folded key so the next run does not create (#382).
                        try:
                            resp = json.loads(p.stdout)
                        except json.JSONDecodeError:
                            resp = {}
                        self.record_link(iid, caps["system"], key, resp)
                    self.record_push(iid, h, key)
                    self.counts["closed"] += 1
                continue

            op = "update" if key else "create"
            payload = {"op": op, "key": key,
                       "marker": caps["marker"]["template"].replace("{ulid}", iid),
                       "item": payload_item}
            if self.dry_run:
                print("would %s %s%s" % (op, iid[:8],
                                         " -> %s" % key if key else ""))
                # The most useful place for this: see what would be replaced
                # while it is still hypothetical.
                if op == "update":
                    self.note_overwrite(iid, key, payload_item)
                continue
            p = self.call_push(payload)
            if not self.handle_exit(item, p):
                continue
            try:
                resp = json.loads(p.stdout)
            except json.JSONDecodeError:
                self.note("push %s: adapter returned non-JSON; not recorded" % iid[:8])
                continue
            pushed_key = key
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
                if relink:
                    self.record_link(iid, caps["system"], pushed_key, resp)
            self.record_push(iid, h, pushed_key)
        # The push loop is over, so the abort can no longer fire: whatever is
        # still buffered is what this run really means to record.
        self.commit_gone()

    # --- pull side ---

    def _adapter_keys(self, keys, by_id):
        """Resolve --keys (item ULIDs or ticket numbers) to adapter keys."""
        out = []
        for k in keys:
            item = by_id.get(k)
            if item is not None:
                remembered = self.remembered_key(k, item.get("external") or {})
                if remembered:
                    out.append(str(remembered))
            else:
                out.append(k)
        # Preserve order, drop empties/dupes.
        seen = set()
        unique = []
        for k in out:
            if k and k not in seen:
                seen.add(k)
                unique.append(k)
        return unique

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
        by_id = {i["id"]: i for i in items}
        adapter_keys = self._adapter_keys(keys, by_id) if keys else []
        keyed = bool(adapter_keys)
        if keyed:
            args = ["pull", "--keys", ",".join(adapter_keys)]
        else:
            args = ["pull", "--since", cursor]
        p = self.run_adapter(*args)
        if p.returncode == 2:
            sys.exit("worklog sync: adapter auth failure on pull — "
                     "re-authenticate with the tracker and re-run.")
        if p.returncode != 0:
            self.note("pull failed (exit %d); cursor not advanced" % p.returncode)
            return
        self.adapter_ok = True   # a clean pull proves the project is reachable
        max_rev = cursor
        ingest_failed = False
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
                # Unmarked tickets are not "new work arriving" — they are
                # tracker-only orphans (#385). Observe already classified
                # them when it could; this is the backstop for a pull that
                # sees one observe missed.
                key = ext.get("key")
                if key and not any(k == str(key) for k, _, _ in self.unmarked):
                    self.unmarked.append(
                        (str(key), line.get("title") or "", system))
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
                wrote = True
                for f in changed:
                    if self.worklog("conflict", iid, "--field", f,
                                    "--local", str(local.get(f)),
                                    "--remote", str(line[f]),
                                    "--remote-rev", rev or "",
                                    fatal=False) is None:
                        wrote = False
                        ingest_failed = True
                    else:
                        self.counts["conflicts"] += 1
                if not wrote:
                    self.note("pull: conflict record failed on %s; "
                              "cursor held" % iid[:8])
            else:
                ing = ["ingest", iid, "--system", system,
                       "--key", str(ext.get("key")), "--rev", rev or "",
                       "--rev-ts-ms", str(rev_to_ms(rev))]
                for f in changed:
                    ing += ["--set", "%s=%s" % (f, line[f])]
                if self.worklog(*ing, fatal=False) is not None:
                    self.counts["pulled"] += 1
                else:
                    ingest_failed = True
                    self.note("pull: ingest failed on %s; cursor held"
                              % iid[:8])
        # A --keys pull is a point query: do not move the since cursor.
        # A failed ingest must not advance it either, or that remote edit
        # is skipped until the ticket changes again.
        if keyed or self.dry_run:
            return
        if ingest_failed:
            self.note("pull: cursor not advanced past failed ingest")
            return
        if max_rev:
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

    # --- dedupe (#383): inverse of github#226, one item many remote keys ---

    def fetch_remote_tickets(self, caps, fatal=True):
        """Every ticket the adapter will name. Cursor-less on purpose.

        GitHub's pull requires --since or --keys; the fake does not. EPOCH
        satisfies both and is the whole board, not the delta since last sync.

        `fatal=False` (observe on push-only, #385) reports and returns None
        instead of aborting the run — a listing failure must not block a
        push that can still proceed.
        """
        if "pull" not in caps.get("supports", []):
            if not fatal:
                return None
            raise ContractError("adapter does not support pull; cannot dedupe")
        p = self.run_adapter("pull", "--since", EPOCH)
        if p.returncode == 2:
            if not fatal:
                self.note("could not list remote tickets (auth); "
                          "unmarked and closed-on-remote drift not reported")
                return None
            sys.exit("worklog dedupe: adapter auth failure on pull — "
                     "re-authenticate with the tracker and re-run.")
        if p.returncode != 0:
            if not fatal:
                self.note("could not list remote tickets (exit %d); "
                          "unmarked and closed-on-remote drift not reported"
                          % p.returncode)
                return None
            sys.exit("worklog dedupe: pull failed (exit %d)" % p.returncode)
        tickets = []
        for raw in p.stdout.splitlines():
            if not raw.strip():
                continue
            try:
                tickets.append(json.loads(raw))
            except json.JSONDecodeError:
                self.note("dedupe: unparseable NDJSON line skipped")
        # A clean board listing proves the project is reachable (ADR-0004),
        # including on --push-only where pull() never runs.
        self.adapter_ok = True
        return tickets

    def historical_keys_by_item(self):
        """item ULID -> keys that a `link` event ever recorded.

        Compaction drops these, so the join decays. Marker grouping is the
        durable one; this only fills gaps when a copy lost its marker but
        the log still remembers the key.
        """
        found = {}
        for path in LOG_PATHS:
            try:
                fh = open(path, encoding="utf-8")
            except FileNotFoundError:
                continue
            with fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if ev.get("op") != "link":
                        continue
                    iid = ev.get("item")
                    key = ((ev.get("set") or {}).get("external") or {}).get("key")
                    if iid and key:
                        found.setdefault(iid, []).append(str(key))
        return found

    @staticmethod
    def _ticket_key(ticket):
        key = (ticket.get("external") or {}).get("key")
        return str(key) if key is not None else None

    @staticmethod
    def _ticket_closed(ticket):
        return ticket.get("status") in CLOSED_STATUSES

    @staticmethod
    def _key_sort(key):
        """Earliest-wins: numeric suffix if present, else the string."""
        digits = []
        for ch in reversed(str(key)):
            if ch.isdigit():
                digits.append(ch)
            else:
                break
        n = int("".join(reversed(digits))) if digits else 0
        return (n, str(key))

    def group_duplicates(self, tickets, items):
        """Split remote tickets into marker groups and low-confidence titles.

        Marker ULID is the join that #382 extras share. Historical link
        events attach extra keys to an already-known item (they do not
        start a collapse on their own — an intentional unlink would look
        the same). Same title, different markers: low-confidence, never
        auto-collapsed.
        """
        by_marker = {}
        for t in tickets:
            iid = t.get("id")
            if iid:
                by_marker.setdefault(iid, []).append(t)
        by_key = {}
        for t in tickets:
            k = self._ticket_key(t)
            if k is not None:
                by_key[k] = t
        hist = self.historical_keys_by_item()
        for iid, keys in hist.items():
            # History may attach a marker-stripped extra to a group that
            # already has two copies. It must not start a collapse on its
            # own: an intentional unlink + re-file looks the same.
            if iid not in by_marker or len(by_marker[iid]) < 2:
                continue
            group = list(by_marker[iid])
            have = {self._ticket_key(t) for t in group}
            for k in keys:
                if k in have or k not in by_key:
                    continue
                group.append(by_key[k])
                have.add(k)
            by_marker[iid] = group
        marker_dupes = {k: v for k, v in by_marker.items() if len(v) > 1}

        in_marker = {id(t) for group in marker_dupes.values() for t in group}
        by_title = {}
        for t in tickets:
            if id(t) in in_marker:
                continue
            title = (t.get("title") or "").strip()
            if not title:
                continue
            by_title.setdefault(title, []).append(t)
        title_dupes = {k: v for k, v in by_title.items() if len(v) > 1}
        return marker_dupes, title_dupes

    def pick_survivor(self, iid, group, items):
        """Fold key, else last_pushed_key, else earliest key."""
        keys = [k for k in (self._ticket_key(t) for t in group) if k]
        if not keys:
            return None, []
        item = items.get(iid) or {}
        ext = item.get("external") or {}
        if ext.get("key") and str(ext["key"]) in keys:
            survivor = str(ext["key"])
        else:
            remembered = self.remembered_key(iid, ext)
            if remembered and remembered in keys:
                survivor = remembered
            else:
                survivor = sorted(keys, key=self._key_sort)[0]
        losers = [k for k in keys if k != survivor]
        return survivor, losers

    def collapse_group(self, iid, group, items, caps):
        survivor, losers = self.pick_survivor(iid, group, items)
        if not survivor:
            self.note("%s: duplicate group has no keys; skipped" % iid[:8])
            return
        pointer = "duplicate of %s (worklog dedupe of %s)" % (survivor, iid)
        for key in losers:
            p = self.run_adapter("close", str(key), pointer)
            if p.returncode != 0:
                self.note("%s: could not close extra %s (exit %d)"
                          % (iid[:8], key, p.returncode))
                continue
            print("closed extra %s -> %s" % (key, survivor))
        resp = {}
        for t in group:
            if self._ticket_key(t) == survivor:
                ext = t.get("external") or {}
                resp = {"url": ext.get("url"), "rev": ext.get("rev")}
                break
        item = items.get(iid) or {}
        if (item.get("external") or {}).get("key") != survivor:
            self.record_link(iid, caps["system"], survivor, resp)
        # Keep the last content hash if we have one; only the key changes.
        h = self.last_pushed(iid)
        self.record_push(iid, h, survivor)

    def dedupe(self, collapse_agreed=False, show_conflicts=False, dry_run=True):
        caps = self.capabilities()
        tickets = self.fetch_remote_tickets(caps)
        items = {i["id"]: i for i in self.fold_items()}
        marker_dupes, title_dupes = self.group_duplicates(tickets, items)

        agreed, conflicts = [], []
        for iid, group in sorted(marker_dupes.items()):
            flags = [self._ticket_closed(t) for t in group]
            entry = (iid, group)
            if flags and (all(flags) or not any(flags)):
                agreed.append(entry)
            else:
                conflicts.append(entry)

        if agreed:
            print("%d agreed duplicate group(s):" % len(agreed))
            for iid, group in agreed:
                keys = " ".join(self._ticket_key(t) or "?" for t in group)
                print("  agreed  %s  %s" % (iid, keys))
        if conflicts:
            print("%d conflict group(s):" % len(conflicts))
            for iid, group in conflicts:
                bits = []
                for t in group:
                    k = self._ticket_key(t) or "?"
                    bits.append("%s:%s" % (k, t.get("status") or "open"))
                print("  conflict  %s  %s" % (iid, " ".join(bits)))
        elif show_conflicts:
            print("no conflict groups")
        if title_dupes:
            print("%d low-confidence title group(s) (never auto-collapsed):"
                  % len(title_dupes))
            for title, group in sorted(title_dupes.items()):
                keys = " ".join(self._ticket_key(t) or "?" for t in group)
                print("  low-confidence  %r  %s" % (title, keys))
        if not (agreed or conflicts or title_dupes):
            print("dedupe: no duplicate groups")

        if collapse_agreed and not dry_run:
            for iid, group in agreed:
                self.collapse_group(iid, group, items, caps)
            self._save_state()
        elif collapse_agreed and dry_run:
            for iid, group in agreed:
                survivor, losers = self.pick_survivor(iid, group, items)
                print("would collapse %s keep %s close %s"
                      % (iid, survivor, " ".join(losers)))
        return 0

    # --- observe (#385): unmarked remotes + closed-on-remote, even push-only ---

    def observe_remote(self, caps, items):
        """Classify tracker-only orphans and closed-on-remote linked items.

        Push-only treats the log as source of truth, so these two drifts are
        otherwise invisible: an issue filed with `gh issue create` never
        carries a marker, and a GitHub close never writes a log event.
        This is not full pull-sync — title/body are not ingested.
        """
        tickets = self.fetch_remote_tickets(caps, fatal=False)
        if not tickets:
            return
        owned = {}
        for item in items:
            key = self.remembered_key(item["id"], item.get("external") or {})
            if key:
                owned[str(key)] = item
        system = caps["system"]
        for t in tickets:
            key = self._ticket_key(t)
            if key is None:
                continue
            owner = owned.get(key)
            iid = t.get("id")
            if owner is None and not iid:
                self.unmarked.append((key, t.get("title") or "", system))
                continue
            if owner is None:
                continue
            if (self._ticket_closed(t)
                    and owner.get("status") not in CLOSED_STATUSES):
                self.remote_closed.append(
                    (owner["id"], key, owner.get("title") or ""))
                self.skip_push_ids.add(owner["id"])

    def apply_remote_closes(self, caps):
        """Close local items whose linked ticket is already closed remotely.

        Skip the subsequent push of those items (skip_push_ids): an update
        would rewrite a closed ticket from stale open-log state. After the
        close, record last_pushed_hash against the closed shape so the next
        run does not treat the status change as dirty.
        """
        if not self.remote_closed:
            return
        if self.dry_run:
            return
        closed = []
        for iid, key, title in self.remote_closed:
            if self.worklog("close", iid, "--resolution",
                            "closed remotely (%s)" % key, fatal=False) is None:
                self.note("%s: remote %s is closed but could not close "
                          "locally — run `worklog close %s`"
                          % (iid[:8], key, iid))
                continue
            closed.append((iid, key, title))
        self.remote_closed = closed
        by_id = {i["id"]: i for i in self.fold_items()}
        for iid, key, title in closed:
            item = by_id.get(iid)
            if not item:
                continue
            h = canonical_hash(self.outbound(item, caps))
            self.record_push(iid, h, key)

    def adopt(self, key, system=None, dry_run=False):
        """Create a log item from an existing remote ticket and stamp the
        ULID marker so the next push updates instead of ignoring (#385).
        """
        caps = self.capabilities()
        system = system or caps["system"]
        if system != caps["system"]:
            print("worklog adopt: --system %s does not match adapter %s"
                  % (system, caps["system"]), file=sys.stderr)
            return 1
        if "get" not in caps.get("supports", []):
            print("worklog adopt: adapter does not support get", file=sys.stderr)
            return 1
        p = self.run_adapter("get", str(key))
        if p.returncode == 2:
            print("worklog adopt: adapter auth failure — re-authenticate "
                  "with the tracker and re-run.", file=sys.stderr)
            return 2
        if p.returncode == 3:
            print("worklog adopt: no ticket %s:%s" % (system, key),
                  file=sys.stderr)
            return 1
        if p.returncode != 0:
            print("worklog adopt: get failed (exit %d)" % p.returncode,
                  file=sys.stderr)
            return 1
        try:
            ticket = json.loads(p.stdout)
        except json.JSONDecodeError:
            print("worklog adopt: adapter returned non-JSON", file=sys.stderr)
            return 1
        items = self.fold_items()
        owners = [i for i in items
                  if str((i.get("external") or {}).get("key") or "") == str(key)]
        if owners:
            print("worklog adopt: %s:%s already belongs to %s"
                  % (system, key, owners[0]["id"]), file=sys.stderr)
            return 1
        existing = ticket.get("id")
        by_id = {i["id"]: i for i in items}
        title = ticket.get("title") or "(untitled)"
        if existing and existing in by_id:
            iid = existing
            if dry_run:
                print("would link %s -> %s:%s" % (iid, system, key))
                return 0
            ext = ticket.get("external") or {}
            self.record_link(iid, system, key,
                             {"url": ext.get("url"), "rev": ext.get("rev")})
            print(iid)
            return 0
        if dry_run:
            print("would create item from %s:%s (%r)" % (system, key, title))
            print("would link and stamp the worklog marker")
            return 0
        add = ["add", title]
        level = ticket.get("level") or "task"
        kind = ticket.get("kind")
        if level == "epic" and kind not in ("feature", "ops"):
            kind = "feature"
        add += ["--level", level]
        if kind:
            add += ["--kind", kind]
        if ticket.get("priority") in ("P0", "P1", "P2", "P3"):
            add += ["--priority", ticket["priority"]]
        if ticket.get("milestone"):
            add += ["--milestone", str(ticket["milestone"])]
        body = ticket.get("body") or ""
        if body:
            add += ["--body", body[:2048]]
        out = self.worklog(*add, fatal=False)
        if out is None:
            print("worklog adopt: could not create local item", file=sys.stderr)
            return 1
        iid = out.strip().splitlines()[-1].strip()
        if self._ticket_closed(ticket):
            self.worklog("close", iid, "--resolution",
                         "adopted already-closed ticket", fatal=False)
        ext = ticket.get("external") or {}
        self.record_link(iid, system, key,
                         {"url": ext.get("url"), "rev": ext.get("rev")})
        # Stamp the marker so the next sync updates this ticket.
        item = next((i for i in self.fold_items() if i["id"] == iid), None)
        if item is None:
            print("worklog adopt: created %s but could not re-fold it"
                  % iid, file=sys.stderr)
            return 1
        payload_item = self.outbound(item, caps)
        marker = caps["marker"]["template"].replace("{ulid}", iid)
        p = self.call_push({"op": "update", "key": str(key),
                            "marker": marker, "item": payload_item})
        if p.returncode != 0:
            self.note("%s: adopted locally but could not stamp marker on "
                      "%s:%s (exit %d) — next sync still updates by key"
                      % (iid[:8], system, key, p.returncode))
        else:
            try:
                resp = json.loads(p.stdout)
            except json.JSONDecodeError:
                resp = {}
            if resp.get("url") or resp.get("rev"):
                self.record_link(iid, system, key, resp)
        self.record_push(iid, canonical_hash(payload_item), key)
        self._save_state()
        print(iid)
        return 0

    # --- the run ---

    def sync(self, keys=None, push=True, pull=True):
        caps = self.capabilities()  # gate: nothing runs on a broken contract
        unsupported = sorted(f for f, m in caps["fields"].items()
                             if m == "unsupported")
        if unsupported:
            self.note("fields not synced on %s: %s"
                      % (caps["system"], ", ".join(unsupported)))
        items = self.fold_items()
        # Observe even on --push-only: unmarked remotes and closed-on-remote
        # linked items are the gaps push-only cannot see (#385).
        self.observe_remote(caps, items)
        self.apply_remote_closes(caps)
        if self.remote_closed and not self.dry_run:
            items = self.fold_items()
        if push:
            self.push_items(items, caps, keys or [])
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
        if self.unmarked:
            print("unmarked remote tickets (no worklog marker):")
            for key, title, system in self.unmarked:
                print("  - %s:%s  %s" % (system, key, title))
                print("    adopt with: worklog adopt --system %s --key %s"
                      % (system, key))
        if self.remote_closed:
            print("closed on remote, still open in the log:")
            for iid, key, title in self.remote_closed:
                if self.dry_run:
                    print("  - %s (%s)  %s — run `worklog close %s`"
                          % (iid[:8], key, title, iid))
                else:
                    print("  - %s (%s)  %s — closed locally"
                          % (iid[:8], key, title))
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
                    help="comma-separated item ULIDs or external keys to ADD "
                         "to the scope. This widens a run; it cannot narrow "
                         "one. Everything open or hash-dirty still syncs. To "
                         "see what a run will touch, use --dry-run.")
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
