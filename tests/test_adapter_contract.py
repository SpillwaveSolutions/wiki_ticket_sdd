#!/usr/bin/env python3
"""Contract tests for adapters (typed-adapter-contract spec sections 3, 7.6).

Runs the fake adapter against schema/*.json with a stdlib mini-validator, and
enforces adapter dumbness: no invariant logic in ANY adapters/*/adapter.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE = os.path.join(ROOT, "adapters", "fake", "adapter")


def load_schema(name):
    with open(os.path.join(ROOT, "schema", name), encoding="utf-8") as fh:
        return json.load(fh)


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
    Raises AssertionError naming the offending field.

    NOTE: bin/sync_dispatch.py ships its own copy of this — deliberately no
    import coupling between the test suite and the dispatcher.
    """
    if "enum" in schema:
        assert instance in schema["enum"], \
            "%s: %r not in enum %r" % (path, instance, schema["enum"])
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        assert any(TYPE_CHECKS[t](instance) for t in types), \
            "%s: expected %s, got %r" % (path, "/".join(types), instance)
    if isinstance(instance, dict):
        for req in schema.get("required", []):
            assert req in instance, "%s: missing required field %r" % (path, req)
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], "%s.%s" % (path, key))
            elif schema.get("additionalProperties") is False:
                raise AssertionError("%s: unexpected field %r" % (path, key))
    if isinstance(instance, list) and "items" in schema:
        for i, value in enumerate(instance):
            validate(value, schema["items"], "%s[%d]" % (path, i))


ULID_A = "01FAKEULIDAAAAAAAAAAAAAAAA"
ULID_B = "01FAKEULIDBBBBBBBBBBBBBBBB"


def marker_for(ulid):
    return "<!-- worklog:%s -->" % ulid


def item_for(ulid, title="First title"):
    return {"id": ulid, "type": "task", "title": title, "status": "todo",
            "priority": "P1", "labels": ["backend"]}


class FakeSandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="adapter-contract-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.env = dict(os.environ,
                        WORKLOG_FAKE_STATE=os.path.join(self.dir, "state.json"))

    def run_fake(self, *args, stdin=None):
        return subprocess.run([sys.executable, FAKE, *args], input=stdin,
                              capture_output=True, text=True,
                              env=self.env, cwd=self.dir)

    def fake(self, *args, stdin=None):
        p = self.run_fake(*args, stdin=stdin)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def push(self, op, key, item, marker):
        payload = {"op": op, "key": key, "marker": marker, "item": item}
        validate(payload, load_schema("adapter-io.schema.json")["properties"]["push_request"])
        return json.loads(self.fake("push", stdin=json.dumps(payload)))


class TestCapabilities(FakeSandbox):
    def test_capabilities_validates_against_schema(self):
        caps = json.loads(self.fake("capabilities"))
        validate(caps, load_schema("capabilities.schema.json"))
        # The containment rule the schema subset cannot express (see its description).
        self.assertIn("{ulid}", caps["marker"]["template"])
        # Honest fake: the degrade path must stay testable.
        self.assertIsNone(caps["types"]["epic"])
        self.assertEqual(caps["fields"]["depends_on"], "unsupported")


class TestPush(FakeSandbox):
    def test_create_then_update_round_trip(self):
        resp = self.push("create", None, item_for(ULID_A), marker_for(ULID_A))
        validate(resp, load_schema("adapter-io.schema.json")["properties"]["push_response"])
        key = resp["key"]
        self.assertTrue(key.startswith("FAKE#"))

        self.push("update", key, item_for(ULID_A, title="Renamed"), marker_for(ULID_A))
        shown = json.loads(self.fake("get", key))
        self.assertEqual(shown["title"], "Renamed")

        self.assertEqual(self.fake("_count").strip(), "1")
        counters = json.loads(self.fake("_counters"))
        self.assertEqual(counters["creates"], 1)
        self.assertEqual(counters["updates"], 1)

    def test_update_unknown_key_exits_3(self):
        payload = {"op": "update", "key": "FAKE#999",
                   "marker": marker_for(ULID_A), "item": item_for(ULID_A)}
        p = self.run_fake("push", stdin=json.dumps(payload))
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr)

    def test_fail_next_fails_once_then_clears(self):
        self.fake("_fail_next", "4")
        payload = json.dumps({"op": "create", "key": None,
                              "marker": marker_for(ULID_A), "item": item_for(ULID_A)})
        p = self.run_fake("push", stdin=payload)
        self.assertEqual(p.returncode, 4, p.stdout + p.stderr)
        # Consumed: the retry succeeds.
        p = self.run_fake("push", stdin=payload)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.fake("_count").strip(), "1")


class TestPull(FakeSandbox):
    def test_pull_emits_valid_ndjson_and_ids_round_trip(self):
        self.push("create", None, item_for(ULID_A), marker_for(ULID_A))
        self.push("create", None, item_for(ULID_B, title="Second"), marker_for(ULID_B))

        out = self.fake("pull")
        lines = [json.loads(l) for l in out.splitlines() if l.strip()]
        self.assertEqual(len(lines), 2)
        schema = load_schema("adapter-io.schema.json")["properties"]["pull_line"]
        for line in lines:
            validate(line, schema)
        self.assertEqual({l["id"] for l in lines}, {ULID_A, ULID_B})


class TestAdapterDumbness(unittest.TestCase):
    """Spec section 7.6: the invariants live in the dispatcher, never in an
    adapter. This scans EVERY adapters/*/adapter, so it automatically covers
    new adapters (including the github one) the day they appear."""

    BANNED = ("sha256", "last_pushed_hash", "canonical_json", "search",
              "sync-state")

    def test_adapters_contain_no_invariant_logic(self):
        paths = sorted(glob.glob(os.path.join(ROOT, "adapters", "*", "adapter")))
        self.assertTrue(paths, "no adapters found under adapters/*/")
        for path in paths:
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
            for banned in self.BANNED:
                self.assertNotIn(
                    banned, src,
                    "%s contains %r — invariant logic belongs in the "
                    "dispatcher, not an adapter (spec section 7.6)" % (path, banned))


if __name__ == "__main__":
    unittest.main()
