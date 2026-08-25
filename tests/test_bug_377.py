#!/usr/bin/env python3
"""Bug #377: ia.py classified design docs by docs/designs/ (plural) only.

Consumer repos, including ones scaffolded from the documented convention,
store them in docs/design/ (singular). classify() returned None, doc_paths()
never listed them, and ia-inventory reported a healthy count with design:0
and no warning.

Follow-ons the path fix surfaces:
  1. REQUIRED_BY_TYPE['design'] demands git_hash, and the sidecar
     normalizer never wrote one.
  2. docs/project_notes/ was not classified at all.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import ia  # noqa: E402


class TestSingularDesignPathIsDesign(unittest.TestCase):
    def test_classify_accepts_both_spellings(self):
        self.assertEqual(ia.classify("docs/designs/current_design_doc.md"),
                         "design")
        self.assertEqual(ia.classify("docs/design/current_design_doc.md"),
                         "design")
        self.assertEqual(
            ia.classify("docs/design/2026-08-01_foo_design_doc.md"), "design")
        self.assertEqual(
            ia.classify("docs/designs/2026-08-01_foo_design_doc.md"), "design")

    def test_canonical_key_is_the_same_for_both_spellings(self):
        self.assertEqual(
            ia.derive_canonical_key("docs/design/current_design_doc.md"),
            "design/current-design-doc")
        self.assertEqual(
            ia.derive_canonical_key("docs/designs/current_design_doc.md"),
            "design/current-design-doc")
        self.assertEqual(
            ia.derive_canonical_key(
                "docs/design/2026-08-01_foo_design_doc.md"),
            "design/2026-08-01_foo-design-doc")

    def test_a_neighbouring_path_is_not_design(self):
        self.assertIsNone(ia.classify("docs/design-notes/foo.md"))
        self.assertIsNone(ia.classify("docs/designed.md"))


class TestProjectNotesAreGuides(unittest.TestCase):
    def test_classify_project_notes_as_guide(self):
        self.assertEqual(
            ia.classify("docs/project_notes/2026-08-01-cut.md"), "guide")
        self.assertEqual(
            ia.derive_canonical_key("docs/project_notes/2026-08-01-cut.md"),
            "guide/2026-08-01-cut")

    def test_folder_readme_is_still_navigation(self):
        self.assertIsNone(ia.classify("docs/project_notes/README.md"))


class TestDocPathsListsBothDesignDirs(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-377-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.cwd = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.cwd)

    def test_singular_and_plural_and_notes_are_listed(self):
        for rel in ("docs/design/one.md", "docs/designs/two.md",
                    "docs/project_notes/cut.md", "docs/plans/p.md"):
            os.makedirs(os.path.dirname(rel), exist_ok=True)
            open(rel, "w").write("# x\n")
        paths = ia.doc_paths()
        self.assertIn("docs/design/one.md", paths)
        self.assertIn("docs/designs/two.md", paths)
        self.assertIn("docs/project_notes/cut.md", paths)
        self.assertIn("docs/plans/p.md", paths)


class TestDesignSidecarGetsGitHash(unittest.TestCase):
    """#377 follow-on: after the path fix, frozen designs fail
    ia-inventory --check with missing git_hash because the normalizer
    never wrote one. Stamp the commit that last touched the file."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-377-hash-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.cwd = os.getcwd()
        os.chdir(self.d)
        shutil.copytree(os.path.join(ROOT, "bin"), "bin")
        for sub in ("docs/design", ".work"):
            os.makedirs(sub)
        open(".work/todo.jsonl", "w").close()
        open(".work/done.jsonl", "w").close()
        open("docs/design/foo_design_doc.md", "w").write(
            "---\ntitle: Foo\n---\n# Foo\n")
        subprocess.run(["git", "init", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "config", "user.email", "t@test.invalid"],
                       check=True)
        subprocess.run(["git", "config", "user.name", "t"], check=True)
        subprocess.run(["git", "add", "docs/design/foo_design_doc.md"],
                       check=True)
        subprocess.run(["git", "commit", "-qm", "add design"], check=True)
        self.sha = subprocess.run(
            ["git", "log", "-1", "--format=%H"],
            capture_output=True, text=True, check=True).stdout.strip()

    def tearDown(self):
        os.chdir(self.cwd)

    def test_normalize_stamps_last_touch_sha(self):
        changes = ia.normalize()
        self.assertTrue(any("sidecar" in c for c in changes), changes)
        side = ia.read_sidecar("design/foo-design-doc")
        self.assertEqual(side.get("git_hash"), self.sha)
        recs = ia.build_records()
        rec = recs["design/foo-design-doc"]
        self.assertEqual(ia.validate_record(rec), [])

    def test_existing_frontmatter_hash_is_not_overwritten(self):
        with open("docs/design/foo_design_doc.md", "w") as fh:
            fh.write("---\ntitle: Foo\ngit_hash: "
                     "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n---\n# Foo\n")
        ia.normalize()
        side = ia.read_sidecar("design/foo-design-doc")
        self.assertEqual(side.get("git_hash"),
                         "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    def test_inventory_sees_the_singular_path(self):
        ia.normalize()
        ia.write_inventory()
        inv = json.load(open(ia.INVENTORY))
        sources = [d["source"] for d in inv["docs"]]
        self.assertIn("docs/design/foo_design_doc.md", sources)
        types = [d["doc_type"] for d in inv["docs"]]
        self.assertIn("design", types)


class TestSessionEndReadsThePayload(unittest.TestCase):
    """session-end.sh used a python heredoc as stdin, so json.load saw
    the script itself and session.end() always got no session_id."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-377-end-")
        self.addCleanup(shutil.rmtree, self.d, True)
        os.makedirs(os.path.join(self.d, "bin"))
        os.makedirs(os.path.join(self.d, ".work"))
        shutil.copy2(os.path.join(ROOT, "bin", "session.py"),
                     os.path.join(self.d, "bin", "session.py"))
        shutil.copy2(os.path.join(ROOT, "bin", "worklog"),
                     os.path.join(self.d, "bin", "worklog"))
        os.chmod(os.path.join(self.d, "bin", "worklog"), 0o755)
        open(os.path.join(self.d, ".work", "todo.jsonl"), "w").close()
        self.hook = os.path.join(ROOT, "hooks", "session-end.sh")

    def test_session_end_drops_the_named_session(self):
        import time
        import session as sess
        reg = os.path.join(self.d, ".work", ".sessions")
        sess.touch("keep", path=reg, now=time.time(), branch_name="main",
                   base_sha="a" * 40)
        sess.touch("drop-me", path=reg, now=time.time(), branch_name="main",
                   base_sha="b" * 40)
        payload = json.dumps({"session_id": "drop-me"})
        r = subprocess.run(["bash", self.hook], cwd=self.d, input=payload,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.load(open(reg))
        self.assertIn("keep", data)
        self.assertNotIn("drop-me", data)


if __name__ == "__main__":
    unittest.main()
