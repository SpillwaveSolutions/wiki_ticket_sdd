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

BIN = os.path.dirname(os.path.abspath(__file__))
SYNC_STATE = ".work/sync-state.json"
INGEST_FIELDS = ("title", "body", "status", "priority", "assignee", "type")
CLOSED_STATUSES = ("done", "cancelled")
LOCAL_ONLY = ("worklog sync: no adapter configured — local-only "
              "(set WORKLOG_TICKET_ADAPTER or run worklog adapter check)")

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

    def __init__(self, adapter, retry_base_delay=0.5, dry_run=False):
        self.adapter = adapter
        self.base_delay = retry_base_delay
        self.dry_run = dry_run
        self.counts = dict.fromkeys(self.COUNT_KEYS, 0)
        self.drift = []
        self.state = self._load_state()

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
        out.setdefault("type", "task")
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
            return True
        iid = item["id"]
        if rc == 2:
            self._save_state()
            sys.exit("worklog sync: adapter auth failure — re-authenticate "
                     "with the tracker and re-run. Nothing further was pushed.")
        if rc == 3:
            key = (item.get("external") or {}).get("key")
            self.note("key %s gone remotely; will re-push %s next run"
                      % (key, iid[:8]))
            self.item_state(iid).pop("last_pushed_hash", None)
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

    def push_items(self, items, caps, keys):
        for item in items:
            iid = item["id"]
            ext = item.get("external") or {}
            closed = item.get("status") in CLOSED_STATUSES
            payload_item = self.outbound(item, caps)
            h = canonical_hash(payload_item)
            forced = bool(keys) and (iid in keys or ext.get("key") in keys)
            dirty = h != self.last_pushed(iid)
            # Scope (spec §10.5): open ∪ hash-dirty ∪ --keys. A closed item
            # that never went remote is inert — pushing it would file tickets
            # for long-dead work.
            if closed and not ext.get("key") and not forced:
                continue
            if not (dirty or forced):
                if not closed:
                    self.counts["skipped"] += 1
                continue

            if payload_item["type"] != (item.get("type") or "task"):
                self.note("%s: %s mapped to %s (no %s type in %s)"
                          % (iid[:8], item["type"], payload_item["type"],
                             item["type"], caps["system"]))

            if closed:
                if self.dry_run:
                    print("would close %s (%s)" % (ext["key"], item.get("status")))
                    continue
                p = self.run_adapter("close", str(ext["key"]),
                                     item.get("resolution") or item["status"])
                if self.handle_exit(item, p):
                    self.item_state(iid)["last_pushed_hash"] = h
                    self.counts["closed"] += 1
                continue

            op = "update" if ext.get("key") else "create"
            payload = {"op": op, "key": ext.get("key"),
                       "marker": caps["marker"]["template"].replace("{ulid}", iid),
                       "item": payload_item}
            if self.dry_run:
                print("would %s %s%s" % (op, iid[:8],
                                         " -> %s" % ext["key"] if ext.get("key") else ""))
                continue
            p = self.call_push(payload)
            if not self.handle_exit(item, p):
                continue
            try:
                resp = json.loads(p.stdout)
            except json.JSONDecodeError:
                self.note("push %s: adapter returned non-JSON; not recorded" % iid[:8])
                continue
            if op == "create":
                if not resp.get("key"):
                    self.note("push %s: response missing key; not linked" % iid[:8])
                    continue
                link = ["link", iid, "--system", caps["system"],
                        "--key", str(resp["key"])]
                if resp.get("url"):
                    link += ["--url", resp["url"]]
                if resp.get("rev"):
                    link += ["--rev", resp["rev"]]
                self.worklog(*link)
                self.counts["created"] += 1
            else:
                self.counts["updated"] += 1
            self.item_state(iid)["last_pushed_hash"] = h

    # --- pull side ---

    def pull(self, caps, items, keys):
        if "pull" not in caps["supports"]:
            self.note("adapter does not support pull; local log may lag remote")
            return
        system = caps["system"]
        cursor = self.state.get("cursors", {}).get(system)
        args = ["pull"] + (["--since", cursor] if cursor else [])
        p = self.run_adapter(*args)
        if p.returncode == 2:
            sys.exit("worklog sync: adapter auth failure on pull — "
                     "re-authenticate with the tracker and re-run.")
        if p.returncode != 0:
            self.note("pull failed (exit %d); cursor not advanced" % p.returncode)
            return
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
        return 0

    def report(self):
        print("sync report: " + " ".join("%s=%d" % (k, self.counts[k])
                                         for k in self.COUNT_KEYS))
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
