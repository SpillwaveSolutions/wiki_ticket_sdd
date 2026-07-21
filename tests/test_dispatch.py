#!/usr/bin/env python3
"""Dispatcher invariant tests (typed-adapter-contract plan §7.1–7.5), run
against the fake adapter in sandbox repos — no network, no live tracker.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FUTURE_REV = "2030-01-01T00:00:00.000000Z"


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-dispatch-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(self.dir, "bin"))
        shutil.copytree(os.path.join(ROOT, "adapters"),
                        os.path.join(self.dir, "adapters"))
        os.makedirs(os.path.join(self.dir, ".work"))
        self.adapter = os.path.join(self.dir, "adapters", "fake", "adapter")
        self.fake_state = os.path.join(self.dir, ".fake-tracker.json")
        self.env = dict(os.environ,
                        WORKLOG_TICKET_ADAPTER=self.adapter,
                        WORKLOG_FAKE_STATE=self.fake_state)

    def run_wl(self, *args, env=None):
        return subprocess.run(
            [sys.executable, os.path.join(self.dir, "bin", "worklog"), *args],
            cwd=self.dir, capture_output=True, text=True, env=env or self.env)

    def wl(self, *args):
        p = self.run_wl(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def sync(self, *args):
        return self.wl("sync", "--retry-base-delay", "0", *args)

    def fake(self, *args):
        p = subprocess.run([sys.executable, self.adapter, *args],
                           cwd=self.dir, capture_output=True, text=True,
                           env=self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def edit_remote(self, mutate):
        """Direct state-file edit of the single fake ticket + rev bump —
        a change made 'in the tracker', invisible to the dispatcher."""
        with open(self.fake_state, encoding="utf-8") as fh:
            state = json.load(fh)
        (key,) = state["tickets"]
        mutate(state["tickets"][key])
        state["tickets"][key]["rev"] = FUTURE_REV
        with open(self.fake_state, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        return key

    def log_events(self):
        with open(os.path.join(self.dir, ".work", "todo.jsonl"),
                  encoding="utf-8") as fh:
            return [json.loads(l) for l in fh.read().splitlines() if l.strip()]

    def ingest_events(self):
        return [e for e in self.log_events() if "src" in e]

    def show(self, item):
        return json.loads(self.wl("show", item))


class TestIdempotency(Sandbox):
    def test_push_twice_same_ulid_is_one_ticket(self):
        self.wl("add", "Sync me", "--priority", "P1")
        self.sync("--push-only")
        self.sync("--push-only")  # hash unchanged -> skipped, never a 2nd create
        self.assertEqual(self.fake("_count"), "1")
        self.assertEqual(json.loads(self.fake("_counters"))["creates"], 1)

    def test_retry_after_transient_does_not_duplicate(self):
        self.wl("add", "Rate limited", "--priority", "P1")
        self.fake("_fail_next", "4")
        self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "1")
        self.assertEqual(json.loads(self.fake("_counters"))["creates"], 1)


class TestCapabilitiesGate(Sandbox):
    def test_malformed_capabilities_rejected_before_push(self):
        self.wl("add", "Never pushed", "--priority", "P1")
        bad = os.path.join(self.dir, "bad-adapter")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write('#!/bin/sh\n'
                     'if [ "$1" = capabilities ]; then\n'
                     '  echo \'{"system":"x"}\'\n  exit 0\nfi\nexit 1\n')
        os.chmod(bad, 0o755)
        p = self.run_wl("sync", "--retry-base-delay", "0",
                        env=dict(self.env, WORKLOG_TICKET_ADAPTER=bad))
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("supports", p.stderr)
        self.assertEqual(self.fake("_count"), "0")  # nothing pushed


class TestTypeDegrade(Sandbox):
    def test_no_epic_type_degrades(self):
        item = self.wl("add", "Big rock", "--type", "epic", "--priority", "P1").strip()
        out = self.sync("--push-only")
        self.assertIn("epic mapped to story", out)
        with open(self.fake_state, encoding="utf-8") as fh:
            (ticket,) = json.load(fh)["tickets"].values()
        self.assertEqual(ticket["item"]["type"], "story")
        self.assertEqual(self.show(item)["level"], "epic")  # local item untouched


class TestConflict(Sandbox):
    def test_both_sides_changed_records_conflict(self):
        item = self.wl("add", "Contested", "--priority", "P1").strip()
        self.sync("--push-only")
        self.edit_remote(lambda t: t["item"].__setitem__("title", "Remote title"))
        self.wl("update", item, "--title", "Local title")
        self.sync("--pull-only")
        conflicts = [e for e in self.log_events() if e["op"] == "conflict"]
        self.assertEqual(len(conflicts), 1, self.log_events())
        self.assertEqual(conflicts[0]["set"]["field"], "title")
        self.assertEqual(conflicts[0]["set"]["remote"], "Remote title")
        self.assertEqual(self.show(item)["title"], "Local title")  # report policy


class TestLocalOnly(Sandbox):
    def test_missing_adapter_is_local_only(self):
        env = {k: v for k, v in self.env.items() if k != "WORKLOG_TICKET_ADAPTER"}
        p = self.run_wl("sync", env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("local-only", p.stdout)


class TestPull(Sandbox):
    def test_echo_suppression(self):
        self.wl("add", "Echo", "--priority", "P1")
        self.sync("--push-only")
        self.sync("--pull-only")  # no remote change: our own push comes back
        self.assertEqual(self.ingest_events(), [])
        self.assertEqual([e for e in self.log_events() if e["op"] == "conflict"], [])

    def test_pull_ingests_remote_taxonomy_change(self):
        # worklog 01KXY8V5WZ: level/kind/milestone missing from the
        # dispatcher's INGEST_FIELDS silently dropped remote taxonomy edits.
        item = self.wl("add", "Retagged remotely", "--level", "task",
                       "--priority", "P1").strip()
        self.sync("--push-only")
        self.edit_remote(lambda t: t["item"].update(
            {"level": "story", "kind": "bug", "milestone": "v9.9.9"}))
        self.sync("--pull-only")
        shown = self.show(item)
        self.assertEqual(shown["level"], "story")
        self.assertEqual(shown["kind"], "bug")
        self.assertEqual(shown["milestone"], "v9.9.9")

    def test_pull_ingests_remote_change_with_deterministic_ev(self):
        item = self.wl("add", "Renamed remotely", "--priority", "P1").strip()
        self.sync("--push-only")
        self.edit_remote(lambda t: t["item"].__setitem__("title", "Remote title"))
        self.sync("--pull-only")
        self.sync("--pull-only")  # same remote change again, e.g. another poll
        evs = {e["ev"] for e in self.ingest_events()}
        self.assertEqual(len(evs), 1, self.ingest_events())
        self.assertEqual(self.show(item)["title"], "Remote title")


class TestCloseSyncsFields(Sandbox):
    def test_reclassify_then_close_survives_pull(self):
        # worklog 01KY129S: close pushed only key+resolution, leaving remote
        # taxonomy labels stale; the close echo then re-ingested the stale
        # kind over the local reclassify. Dirty close now updates first.
        item = self.wl("add", "Reclass then close", "--level", "task",
                       "--priority", "P1").strip()
        self.sync("--push-only")
        self.wl("update", item, "--kind", "bug")
        self.wl("close", item, "--resolution", "fixed")
        self.sync("--push-only")
        self.sync("--pull-only")
        shown = self.show(item)
        self.assertEqual(shown["kind"], "bug")
        self.assertEqual(shown["status"], "done")
        self.assertEqual(self.ingest_events(), [])  # echo, not a remote edit


class TestSchemaMirror(unittest.TestCase):
    def test_embedded_capabilities_schema_matches_file(self):
        sys.path.insert(0, os.path.join(ROOT, "bin"))
        import sync_dispatch
        with open(os.path.join(ROOT, "schema", "capabilities.schema.json"),
                  encoding="utf-8") as fh:
            self.assertEqual(sync_dispatch.CAPABILITIES_SCHEMA, json.load(fh),
                             "bin/sync_dispatch.py CAPABILITIES_SCHEMA must "
                             "mirror schema/capabilities.schema.json")


class TestOrphanNeverPushed(Sandbox):
    def test_orphan_and_titleless_items_are_drift_not_tickets(self):
        # a typo'd update creates a fold orphan: an event whose item has no create
        self.wl("update", "01ZZZZZZZZZZZZZZZZZZZZZZZZ", "--add-label", "oops")
        out = self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "0", out)
        self.assertIn("orphan/untitled item skipped", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

