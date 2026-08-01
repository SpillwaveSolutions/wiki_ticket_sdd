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


class TestCloseNeverPushed(Sandbox):
    def test_closed_item_forced_into_scope_creates_then_closes(self):
        # worklog 01KYAKH3: an item created and closed locally without ever
        # being pushed has no external key. Forcing it into scope via
        # --keys crashed with KeyError('key') in the closed-item branch,
        # which assumed a key already existed. It must create the ticket
        # first, then close it.
        item = self.wl("add", "Closed before ever pushed", "--priority", "P1").strip()
        self.wl("close", item, "--resolution", "fixed")
        out = self.sync("--push-only", "--keys", item)
        self.assertNotIn("Traceback", out)
        self.assertEqual(self.fake("_count"), "1", out)
        shown = self.show(item)
        self.assertEqual(shown["external"]["system"], "fake")
        self.assertIn("key", shown["external"])
        with open(self.fake_state, encoding="utf-8") as fh:
            (ticket,) = json.load(fh)["tickets"].values()
        self.assertTrue(ticket["closed"])


class TestOrphanNeverPushed(Sandbox):
    def test_orphan_and_titleless_items_are_drift_not_tickets(self):
        # A fold orphan is an event whose item has no create. The CLI can no
        # longer mint one (worklog 01KYA99TVC gave update/close prefix
        # resolution), but a git merge still can: an update event arriving
        # from another machine ahead of its create. Write that event raw.
        with open(os.path.join(self.dir, ".work", "todo.jsonl"), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ev": "01ZZZZZZZZZZZZZZZZZZZZZZZY", "ts": "2026-07-27T00:00:00Z",
                "actor": "other-machine", "item": "01ZZZZZZZZZZZZZZZZZZZZZZZZ",
                "op": "update", "add": {"labels": ["oops"]}}) + "\n")
        out = self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "0", out)
        self.assertIn("orphan/untitled item skipped", out)


class TestOneOwnerPerKey(Sandbox):
    """github#226: two items owned one ticket, sync pushed both, and the
    cancelled duplicate marked a live P0 ticket Done. Hand-repairing the
    ticket did not hold because the next sync rewrote the damage."""

    def link_dup(self, item, key, system="fake"):
        """Manufacture the duplicate. `link` refuses it now, so go through
        --force — which is also how a git union merge of two branches that
        each linked the same key ends up looking.

        Deliberately NOT a hand-written JSONL line with a fabricated `ev`:
        the fold orders by `ev`, so a synthetic high one sorts after a real
        later `unlink` and silently swallows it."""
        self.wl("link", item, "--system", system, "--key", key, "--force")

    def tickets(self):
        with open(self.fake_state, encoding="utf-8") as fh:
            return json.load(fh)["tickets"]

    def contested(self):
        """Item A owns a real ticket; B is then pointed at the same key.

        B is added AFTER the sync so it never files a ticket of its own —
        that is the reported shape: a plan-capture phantom that someone
        'fixes' by linking it to the ticket it appears to duplicate."""
        a = self.wl("add", "The real ticket", "--priority", "P1").strip()
        self.sync("--push-only")                       # A creates FAKE#1
        b = self.wl("add", "The phantom duplicate", "--priority", "P1").strip()
        self.link_dup(b, "FAKE#1")
        return a, b

    def test_contested_ticket_is_never_pushed(self):
        a, b = self.contested()
        # B's title would otherwise overwrite the ticket's.
        self.wl("update", b, "--priority", "P0")
        p = self.run_wl("sync", "--retry-base-delay", "0", "--push-only")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        out = p.stdout + p.stderr
        self.assertIn(a, out)
        self.assertIn(b, out)
        self.assertIn("worklog unlink", out)
        self.assertEqual(json.loads(self.fake("_counters"))["updates"], 0)
        self.assertEqual(self.tickets()["FAKE#1"]["item"]["title"],
                         "The real ticket")

    def test_contested_ticket_is_not_closed_by_a_cancelled_claimant(self):
        """The exact #226 damage. The closed branch is separate code from the
        create/update path, so a guard at the discriminator would miss it."""
        a, b = self.contested()
        self.wl("close", b, "--status", "cancelled", "--resolution", "duplicate")
        p = self.run_wl("sync", "--retry-base-delay", "0", "--push-only")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertFalse(self.tickets()["FAKE#1"]["closed"],
                         "a cancelled duplicate closed the real ticket")
        self.assertEqual(json.loads(self.fake("_counters"))["closes"], 0)

    def test_healthy_items_in_the_same_run_still_push(self):
        # Skip-the-colliders, not refuse-the-run: a repo with one bad pair is
        # not hard-blocked.
        self.contested()
        self.wl("add", "Unrelated work", "--priority", "P1")
        p = self.run_wl("sync", "--retry-base-delay", "0", "--push-only")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(self.fake("_count"), "2", p.stdout + p.stderr)

    def test_dry_run_also_fails(self):
        # `--dry-run` reporting 0 creates is the documented migration
        # acceptance gate; a gate that cannot see a duplicate is not a gate.
        self.contested()
        p = self.run_wl("sync", "--retry-base-delay", "0", "--push-only",
                        "--dry-run")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("claimed by more than one item", p.stdout + p.stderr)

    def test_unlink_frees_the_ticket_and_the_survivor_repushes(self):
        """The repair, end to end — and the reason last_pushed_key exists:
        `external` is not in HASH_FIELDS, so nothing here is content-dirty."""
        a, b = self.contested()
        self.wl("close", b, "--status", "cancelled", "--resolution", "duplicate")
        self.wl("unlink", b)
        out = self.sync("--push-only")            # exits 0 again
        self.assertEqual(self.fake("_count"), "1", out)   # b filed no ticket
        self.assertFalse(self.tickets()["FAKE#1"]["closed"])

    def test_unlinked_open_item_re_enters_scope(self):
        """Without last_pushed_key an unlink is a silent no-op at sync time:
        the content hash is unchanged, so the item stays out of scope."""
        item = self.wl("add", "Mislinked", "--priority", "P1").strip()
        self.sync("--push-only")
        self.assertEqual(self.fake("_count"), "1")
        self.wl("unlink", item)
        out = self.sync("--push-only")            # no field edits at all
        self.assertEqual(self.fake("_count"), "2", out)

    def test_auto_link_after_create_is_never_blocked(self):
        """The dispatcher records a key the tracker just minted. If the guard
        could stop it, sync would die between "remote created" and "link
        recorded" — and the next run would file a SECOND live ticket."""
        squatter = self.wl("add", "Squatting on FAKE#1", "--priority", "P1").strip()
        self.link_dup(squatter, "FAKE#1")
        self.wl("add", "Files the real FAKE#1", "--priority", "P1")
        p = self.run_wl("sync", "--retry-base-delay", "0", "--push-only")
        self.assertNotIn("Traceback", p.stdout + p.stderr)
        self.assertEqual(self.fake("_count"), "1", p.stdout + p.stderr)
        # The link was recorded, so the next run updates rather than
        # re-creating. Two owners now, which the next run refuses — loudly.
        linked = [i for i in json.loads(self.wl("fold"))
                  if (i.get("external") or {}).get("key") == "FAKE#1"]
        self.assertEqual(len(linked), 2, "created a ticket without recording it")


if __name__ == "__main__":
    unittest.main(verbosity=2)



class TestOverwriteReporting(Sandbox):
    """#238: 'updated 2' said nothing about a live ticket's title or state
    being replaced. In the reported incident that line would have caught the
    damage on the first run instead of the third."""

    def _linked_item(self, title="Original title"):
        iid = self.wl("add", title, "--priority", "P1").strip()
        self.sync("--push-only")          # creates + links the ticket
        return iid

    def test_a_replaced_title_is_named_before_and_after(self):
        iid = self._linked_item("Original title")
        self.wl("update", iid, "--title", "Replacement title")
        out = self.sync("--push-only")
        self.assertIn("overwrote live ticket fields", out)
        self.assertIn("Original title", out)
        self.assertIn("Replacement title", out)

    def test_the_report_names_the_field_that_changed(self):
        iid = self._linked_item()
        self.wl("update", iid, "--priority", "P3")
        out = self.sync("--push-only")
        self.assertIn("priority", out)

    def test_an_unchanged_ticket_reports_no_overwrite(self):
        """Must not cry wolf: a push that changes nothing a reader sees."""
        self._linked_item()
        out = self.sync("--push-only")
        self.assertNotIn("overwrote live ticket fields", out)

    def test_dry_run_shows_what_would_be_replaced(self):
        """The most valuable case — visible while still hypothetical."""
        iid = self._linked_item("Before")
        self.wl("update", iid, "--title", "After")
        out = self.sync("--push-only", "--dry-run")
        self.assertIn("overwrote live ticket fields", out)
        self.assertIn("Before", out)
        self.assertIn("After", out)

    def test_the_read_cost_is_reported(self):
        """The ticket called the extra read 'a real cost worth measuring'."""
        iid = self._linked_item()
        self.wl("update", iid, "--title", "Changed")
        out = self.sync("--push-only")
        self.assertRegex(out, r"read \d+ ticket.* in \d+\.\d+s")

    def test_one_batched_read_covers_many_tickets(self):
        """Not one read per updated ticket: the cost the ticket flagged is
        per RUN, which is what makes it affordable."""
        ids = [self._linked_item(f"Item {n}") for n in range(3)]
        for n, iid in enumerate(ids):
            self.wl("update", iid, "--title", f"Renamed {n}")
        out = self.sync("--push-only")
        self.assertIn("read 3 tickets", out)
        for n in range(3):
            self.assertIn(f"Renamed {n}", out)

    def test_close_that_also_rewrites_fields_is_reported(self):
        """The update-then-close path is the one that marked the reported
        ticket Done."""
        iid = self._linked_item("Live work")
        self.wl("update", iid, "--title", "Renamed then closed")
        self.wl("close", iid, "--status", "done")
        out = self.sync("--push-only")
        self.assertIn("Live work", out)
