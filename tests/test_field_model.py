#!/usr/bin/env python3
"""Item #108: configurable optional fields, so a lightweight and a heavyweight
process can share one log.

(tests/test_item_fields.py covers the two fields the spec already declared,
#256/#259; this covers the model that now carries them.)

The load-bearing claims, in order of how badly they'd hurt if wrong:
  1. The core cannot be switched off -- a config that disables `priority` is a
     config that breaks the roadmap renderer.
  2. A disabled field is INVISIBLE, not merely rejected. For a CLI whose
     --help is what an agent reads, "never appears in prompts, forms, or
     validation" means the flag must not exist.
  3. Enabling a field is a config edit and nothing else.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
sys.path.insert(0, BIN)
import item_fields  # noqa: E402


class TestCatalog(unittest.TestCase):
    def _cfg(self, text):
        fh = tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False)
        fh.write(text)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_defaults_match_the_ticket(self):
        on = set(item_fields.enabled(self._cfg("")))
        self.assertEqual(on, {"estimate", "owner", "risk",
                              "acceptance_criteria"})

    def test_default_off_fields_are_off(self):
        on = item_fields.enabled(self._cfg(""))
        for name in ("value", "confidence", "due_date", "severity"):
            self.assertNotIn(name, on)

    def test_config_can_switch_one_on(self):
        path = self._cfg("work_item_fields:\n  severity: on\n")
        self.assertIn("severity", item_fields.enabled(path))

    def test_config_can_switch_one_off(self):
        path = self._cfg("work_item_fields:\n  risk: off\n")
        self.assertNotIn("risk", item_fields.enabled(path))

    def test_various_truthy_spellings(self):
        for value in ("true", "yes", "on", "1", "TRUE"):
            path = self._cfg("work_item_fields:\n  value: %s\n" % value)
            self.assertIn("value", item_fields.enabled(path), value)

    def test_unreadable_value_falls_back_to_the_documented_default(self):
        """Not to 'off', and not to a crash: a typo must not silently drop a
        field the team relies on."""
        path = self._cfg("work_item_fields:\n  risk: maybe\n")
        self.assertIn("risk", item_fields.enabled(path))

    def test_another_block_is_not_read_as_field_config(self):
        path = self._cfg("wiki:\n  system: github-wiki\n"
                         "work_item_fields:\n  severity: on\n")
        on = item_fields.enabled(path)
        self.assertIn("severity", on)
        self.assertNotIn("system", on)

    def test_missing_config_is_not_an_error(self):
        self.assertTrue(item_fields.enabled("/nonexistent/config.yml"))

    def test_every_catalog_field_carries_a_description(self):
        """Agents read these to decide what to write; a field without one
        gets guessed differently by two people."""
        for name, (_d, _c, desc) in item_fields.CATALOG.items():
            self.assertTrue(desc and len(desc) > 30, name)

    def test_no_optional_field_shadows_a_core_field(self):
        self.assertEqual(set(item_fields.CATALOG) & set(item_fields.CORE),
                         set())

    def test_due_date_shape_is_validated(self):
        self.assertIsNone(item_fields.validate("due_date", "2026-08-01"))
        self.assertIn("YYYY-MM-DD",
                      item_fields.validate("due_date", "next tuesday"))

    def test_flag_name_uses_dashes(self):
        self.assertEqual(item_fields.flag("acceptance_criteria"),
                         "--acceptance-criteria")


class TestCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-fieldmodel-")
        self.addCleanup(shutil.rmtree, self.d, True)
        for f in os.listdir(BIN):
            src = os.path.join(BIN, f)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(self.d, f))
        os.makedirs(os.path.join(self.d, ".work"))
        for f in ("todo.jsonl", "done.jsonl"):
            open(os.path.join(self.d, ".work", f), "w").close()

    def config(self, text):
        with open(os.path.join(self.d, ".work", "config.yml"), "w") as fh:
            fh.write(text)

    def wl(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.d, "worklog"), *args],
            cwd=self.d, capture_output=True, text=True)

    def events(self):
        with open(os.path.join(self.d, ".work", "todo.jsonl")) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_enabled_field_is_written_to_the_log(self):
        p = self.wl("add", "T", "--body", "b", "--level", "task",
                    "--kind", "feature", "--risk", "high", "--owner", "rick")
        self.assertEqual(p.returncode, 0, p.stderr)
        s = self.events()[0]["set"]
        self.assertEqual(s["risk"], "high")
        self.assertEqual(s["owner"], "rick")

    def test_disabled_field_has_no_flag_at_all(self):
        """Invisible, not rejected — the difference the ticket asked for."""
        p = self.wl("add", "T", "--body", "b", "--severity", "sev1")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("unrecognized arguments", p.stderr)

    def test_disabled_field_is_absent_from_help(self):
        out = self.wl("add", "--help").stdout
        self.assertNotIn("--severity", out)
        self.assertIn("--risk", out)

    def test_enabling_in_config_is_the_only_step_needed(self):
        self.config("work_item_fields:\n  severity: on\n")
        self.assertIn("--severity", self.wl("add", "--help").stdout)
        p = self.wl("add", "T", "--body", "b", "--severity", "sev1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.events()[0]["set"]["severity"], "sev1")

    def test_disabling_in_config_removes_the_flag(self):
        self.config("work_item_fields:\n  risk: off\n")
        self.assertNotIn("--risk", self.wl("add", "--help").stdout)

    def test_core_field_cannot_be_switched_off(self):
        """The safety property: priority is load-bearing for the roadmap."""
        self.config("work_item_fields:\n  priority: off\n")
        out = self.wl("add", "--help").stdout
        self.assertIn("--priority", out)
        p = self.wl("add", "T", "--body", "b", "--priority", "P1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.events()[0]["set"]["priority"], "P1")

    def test_update_carries_optional_fields_too(self):
        iid = self.wl("add", "T", "--body", "b").stdout.strip()
        p = self.wl("update", iid, "--risk", "low")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.events()[-1]["set"]["risk"], "low")

    def test_estimate_still_works_through_the_catalog(self):
        """It used to be hardcoded in two places; it must not regress."""
        p = self.wl("add", "T", "--body", "b", "--estimate", "L")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.events()[0]["set"]["estimate"], "L")

    def test_bad_choice_is_rejected(self):
        p = self.wl("add", "T", "--body", "b", "--risk", "enormous")
        self.assertNotEqual(p.returncode, 0)

    def test_bad_due_date_shape_never_reaches_the_log(self):
        self.config("work_item_fields:\n  due_date: on\n")
        p = self.wl("add", "T", "--body", "b", "--due-date", "soon")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("YYYY-MM-DD", p.stdout + p.stderr)
        self.assertEqual(self.events(), [])

    def test_fields_command_reports_both_populations(self):
        out = self.wl("fields").stdout
        self.assertIn("core (always on", out)
        self.assertIn("[on ] --risk", out)
        self.assertIn("[off] --severity", out)
        self.assertIn("work_item_fields:", out)   # how to change it

    def test_unset_optional_fields_are_not_written(self):
        """A field nobody filled must be absent, not null: an empty value
        looks like an answer."""
        self.wl("add", "T", "--body", "b")
        s = self.events()[0]["set"]
        for name in item_fields.CATALOG:
            self.assertNotIn(name, s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
