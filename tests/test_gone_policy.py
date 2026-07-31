#!/usr/bin/env python3
"""ADR-0004: a gone mark is only meaningful relative to a reachable project.

Exit code 3 cannot separate a deleted ticket from one in a project the caller
cannot reach — GitHub returns 404 for both, on purpose. So the dispatcher does
not try. It asks a different question, one the signal CAN answer: has anything
at all succeeded this run? If not, the run has learned nothing about any
individual ticket and must not record anything about them.
"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import sync_dispatch                                            # noqa: E402


class _Result:
    def __init__(self, rc):
        self.returncode, self.stdout, self.stderr = rc, "{}", ""


class _Probe(sync_dispatch.Dispatcher):
    """A dispatcher with no adapter and no state file behind it."""

    def __init__(self):
        self.counts = dict.fromkeys(self.COUNT_KEYS, 0)
        self.drift = []
        self.collisions = {}
        self.state = {"items": {}, "cursors": {}}
        self.dry_run = False
        self.adapter_ok = False
        self.pending_gone = {}

    def _save_state(self):
        pass


def _item(iid, key):
    return {"id": iid, "title": "t", "status": "todo",
            "external": {"system": "github", "key": key}}


class TestGoneMarksAreBuffered(unittest.TestCase):
    """Buffering is not a second safety rule — GONE_ABORT is the rule. What
    buffering buys is that the abort leaves nothing behind."""

    def test_a_mark_is_buffered_before_it_is_committed(self):
        d = _Probe()
        d.handle_exit(_item("01AAA", "1"), _Result(3))
        self.assertEqual(d.pending_gone, {"01AAA": "1"})
        self.assertNotIn("01AAA", d.state["items"])

    def test_commit_moves_buffered_marks_into_state(self):
        d = _Probe()
        d.handle_exit(_item("01AAA", "1"), _Result(3))
        d.commit_gone()
        self.assertEqual(d.state["items"]["01AAA"]["gone_key"], "1")
        self.assertEqual(d.pending_gone, {})

    def test_a_lone_deleted_ticket_is_still_marked(self):
        """The rule deliberately does NOT require proof of reachability. It
        would make a one-item, push-only repo retry a genuinely deleted
        ticket forever, and the damage it would prevent is already bounded
        by the abort threshold."""
        d = _Probe()
        d.handle_exit(_item("01AAA", "1"), _Result(3))
        d.commit_gone()
        self.assertEqual(d.state["items"]["01AAA"]["gone_key"], "1")
        self.assertFalse(d.adapter_ok)

    def test_at_most_two_items_can_be_wrongly_condemned(self):
        """The bound that makes the above safe: a run that proves nothing
        cannot mark more than GONE_ABORT-1 items, because reaching the
        threshold aborts instead."""
        d = _Probe()
        for i in range(sync_dispatch.Dispatcher.GONE_ABORT - 1):
            d.handle_exit(_item("01ITEM%d" % i, str(i)), _Result(3))
        d.commit_gone()
        self.assertEqual(len(d.state["items"]),
                         sync_dispatch.Dispatcher.GONE_ABORT - 1)


class TestWholeProjectUnreachableAborts(unittest.TestCase):
    """The failure this exists to prevent: one mistyped project setting
    reports every ticket gone, identically, on every attempt."""

    def _run_gone(self, n, succeed_first=False):
        d = _Probe()
        if succeed_first:
            d.handle_exit(_item("01OK", "0"), _Result(0))
        for i in range(n):
            d.handle_exit(_item("01ITEM%d" % i, str(i)), _Result(3))
        return d

    def test_aborts_before_walking_the_whole_log(self):
        with self.assertRaises(SystemExit) as cm:
            self._run_gone(sync_dispatch.Dispatcher.GONE_ABORT)
        self.assertIn("probably unreachable", str(cm.exception))
        self.assertIn("Nothing was changed", str(cm.exception))

    def test_below_the_threshold_it_keeps_going(self):
        d = self._run_gone(sync_dispatch.Dispatcher.GONE_ABORT - 1)
        self.assertEqual(len(d.pending_gone),
                         sync_dispatch.Dispatcher.GONE_ABORT - 1)

    def test_a_successful_call_disarms_the_abort(self):
        """Many genuinely-deleted tickets in a healthy run is legitimate and
        must not look like an outage."""
        d = self._run_gone(sync_dispatch.Dispatcher.GONE_ABORT + 5,
                           succeed_first=True)
        self.assertEqual(len(d.pending_gone),
                         sync_dispatch.Dispatcher.GONE_ABORT + 5)

    def test_abort_persists_no_gone_marks(self):
        with self.assertRaises(SystemExit):
            self._run_gone(sync_dispatch.Dispatcher.GONE_ABORT)
        # the marks were buffered, never committed — nothing reached state


class TestGoneMarkIsForgotten(unittest.TestCase):
    """A ticket restored from the tracker's trash used to stay skipped
    forever: the mark was only outgrown when the key itself changed, and the
    only way to change it was the manual unlink the mark was telling you to
    do."""

    def test_a_later_success_on_the_same_key_clears_it(self):
        d = _Probe()
        d.state["items"]["01AAA"] = {"gone_key": "1"}
        d.handle_exit(_item("01AAA", "1"), _Result(0))
        self.assertNotIn("gone_key", d.state["items"]["01AAA"])

    def test_clearing_does_not_disturb_other_state(self):
        d = _Probe()
        d.state["items"]["01AAA"] = {"gone_key": "1", "last_pushed_hash": "h"}
        d.handle_exit(_item("01AAA", "1"), _Result(0))
        self.assertEqual(d.state["items"]["01AAA"]["last_pushed_hash"], "h")

    def test_clearing_an_absent_mark_is_harmless(self):
        d = _Probe()
        d.handle_exit(_item("01AAA", "1"), _Result(0))  # must not raise


class TestUnchangedContractBehaviour(unittest.TestCase):
    """ADR-0004 changes when a mark is written, never what the exit codes
    mean. The rc 3 / rc 4 distinction #241 established stays exactly as it
    was."""

    def test_auth_failure_still_aborts_immediately(self):
        d = _Probe()
        with self.assertRaises(SystemExit) as cm:
            d.handle_exit(_item("01AAA", "1"), _Result(2))
        self.assertIn("auth failure", str(cm.exception))

    def test_rate_limit_is_deferred_not_marked_gone(self):
        d = _Probe()
        d.handle_exit(_item("01AAA", "1"), _Result(4))
        self.assertEqual(d.pending_gone, {})
        self.assertEqual(d.counts["deferred"], 1)

    def test_gone_still_counts_as_deferred(self):
        d = _Probe()
        d.handle_exit(_item("01OK", "0"), _Result(0))
        d.handle_exit(_item("01AAA", "1"), _Result(3))
        self.assertEqual(d.counts["deferred"], 1)

    def test_gone_still_prints_the_manual_remedy(self):
        d = _Probe()
        d.handle_exit(_item("01OK", "0"), _Result(0))
        d.handle_exit(_item("01AAA", "1"), _Result(3))
        self.assertTrue(any("worklog unlink" in n for n in d.drift),
                        "the human remedy must stay visible — ADR-0004 "
                        "leaves unlinking to a person")


if __name__ == "__main__":
    unittest.main()
