#!/usr/bin/env python3
"""Git provenance on generated docs, and the guarantees it rests on (#294).

A test that merely asserts a provenance field EXISTS is worth nothing here —
the failure mode being guarded against is a field that is present and wrong.
Every case below fails when the recorded value is incorrect, not merely
absent.

Design record: docs/plans/2026-08-03-doc-provenance-and-verification.md
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import ia_render   # noqa: E402


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class TestBodyHashIgnoresFrontMatter(unittest.TestCase):
    """The publisher strips front matter, so two files differing only there
    publish identically. Hashing the body is what stops a metadata stamp
    from looking like a frozen-doc edit."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-prov-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "doc.md")

    def test_a_front_matter_only_edit_does_not_move_the_hash(self):
        write(self.p, "---\nwiki_key: a\n---\n\n# Title\n\nThe prose.\n")
        before = ia_render._body_hash(self.p)
        write(self.p, "---\nwiki_key: a\nmerged_in: abc123\n---\n\n"
                      "# Title\n\nThe prose.\n")
        self.assertEqual(ia_render._body_hash(self.p), before)

    def test_a_body_edit_does_move_the_hash(self):
        write(self.p, "---\nwiki_key: a\n---\n\n# Title\n\nThe prose.\n")
        before = ia_render._body_hash(self.p)
        write(self.p, "---\nwiki_key: a\n---\n\n# Title\n\nDifferent prose.\n")
        self.assertNotEqual(ia_render._body_hash(self.p), before)

    def test_reordering_front_matter_keys_does_not_move_the_hash(self):
        write(self.p, "---\na: 1\nb: 2\n---\n\nbody\n")
        before = ia_render._body_hash(self.p)
        write(self.p, "---\nb: 2\na: 1\n---\n\nbody\n")
        self.assertEqual(ia_render._body_hash(self.p), before)

    def test_a_file_with_no_front_matter_hashes_its_whole_content(self):
        """parse_front_matter returns (({}, text)) with no fence, so the
        body IS the file. A doc that never had front matter must not hash
        differently once one is added by the normalizer."""
        write(self.p, "# Title\n\nThe prose.\n")
        bare = ia_render._body_hash(self.p)
        write(self.p, "---\nwiki_key: a\n---\n# Title\n\nThe prose.\n")
        self.assertEqual(ia_render._body_hash(self.p), bare)

    def test_it_differs_from_the_whole_file_hash_when_front_matter_exists(self):
        """Guards against _body_hash silently degrading to _file_hash."""
        write(self.p, "---\nwiki_key: a\n---\n\nbody\n")
        self.assertNotEqual(ia_render._body_hash(self.p),
                            ia_render._file_hash(self.p))


class TestManifestCarriesTheGuardsInput(unittest.TestCase):
    """The publisher must never hash files itself: it reads source_hash from
    the manifest. If the manifest stopped carrying it, the skill would
    silently fall back to whole-file hashing and the guard would fire on
    every metadata stamp again."""

    def test_every_doc_page_carries_a_body_source_hash(self):
        docs = [p for p in _manifest()["pages"] if p["render"] == "doc+banner"]
        self.assertTrue(docs, "no doc+banner pages — fixture is wrong")
        for p in docs:
            self.assertIn("source_hash", p, p["wiki_key"])
            self.assertEqual(p["source_hash"],
                             ia_render._body_hash(p["source"]), p["wiki_key"])

    def test_rendered_pages_have_no_source_hash(self):
        """`as-is` pages have no source doc — their bytes ARE the render.
        A source_hash there would be meaningless and invite the publisher to
        guard something that cannot change independently."""
        for p in _manifest()["pages"]:
            if p["render"] == "as-is":
                self.assertNotIn("source_hash", p, p["wiki_key"])


def _manifest():
    import json
    with open(os.path.join(ROOT, "docs/.index/publish-manifest.json")) as fh:
        return json.load(fh)


if __name__ == "__main__":
    os.chdir(ROOT)
    unittest.main(verbosity=2)
