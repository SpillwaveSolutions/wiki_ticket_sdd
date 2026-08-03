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
import ia          # noqa: E402
import ia_render   # noqa: E402
import render_roadmap  # noqa: E402


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


class TestRoadmapRecordsItsSourceCommit(unittest.TestCase):
    """The roadmap is regenerated and byte-diffed by hooks/pre-commit and by
    CI, so its commit must come from the committed log -- every event has
    carried `git` since 0.19.1 -- and never from `git rev-parse`."""

    def log(self, events):
        import json
        p = os.path.join(self.d, "todo.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            for e in events:
                fh.write(json.dumps(e) + "\n")
        return p

    @staticmethod
    def ev(n, git=None):
        e = {"ev": "01J8X%04dA0" % n, "ts": "t", "actor": "t", "item": "I%d" % n,
             "op": "create", "set": {"title": "t", "status": "todo"}}
        if git:
            e["git"] = git
        return e

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-prov-rm-")
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_it_records_the_newest_events_commit(self):
        out = render_roadmap.render([self.log(
            [self.ev(1, "aaaaaaa"), self.ev(2, "bbbbbbb")])])
        self.assertIn('git_hash: "bbbbbbb"', out)
        self.assertNotIn("aaaaaaa", out)

    def test_an_older_event_carrying_git_does_not_win(self):
        """Ordering is by ULID, not by file order or by which line has a sha."""
        out = render_roadmap.render([self.log(
            [self.ev(9, "newest0"), self.ev(1, "oldest0")])])
        self.assertIn('git_hash: "newest0"', out)

    def test_the_key_is_omitted_when_no_event_carries_one(self):
        """Pre-0.19.1 logs must degrade to ABSENT, never to an empty value:
        `git_hash: ` opens a block list in ia.parse_front_matter and would
        swallow the `---` fence and everything after it."""
        out = render_roadmap.render([self.log([self.ev(1), self.ev(2)])])
        self.assertNotIn("git_hash", out)

    def test_the_newest_event_wins_even_if_it_lacks_a_sha(self):
        """Don't scan backwards for the newest event that happens to have
        git -- that would name a commit the data does not come from."""
        out = render_roadmap.render([self.log(
            [self.ev(1, "aaaaaaa"), self.ev(2)])])
        self.assertNotIn("git_hash", out)

    def test_an_all_digit_sha_survives_the_round_trip(self):
        """ia._scalar coerces an all-digit value to int BEFORE it considers
        quotes. Events carry the short sha, so ~1 in 27 is all digits and a
        leading zero would come back corrupted but still sha-shaped."""
        out = render_roadmap.render([self.log([self.ev(1, "0123456")])])
        fm, _ = ia.parse_front_matter(out)
        self.assertEqual(fm["git_hash"], "0123456")

    def test_max_ev_still_agrees_with_top_event(self):
        """max_ev's signature and return are unchanged -- six callers depend
        on it, including compact.py's watermark."""
        p = self.log([self.ev(1, "aaaaaaa"), self.ev(7, "ggggggg")])
        self.assertEqual(render_roadmap.max_ev([p]),
                         render_roadmap.top_event([p])["ev"])

    def test_both_return_none_on_an_empty_log(self):
        self.assertIsNone(render_roadmap.max_ev([os.path.join(self.d, "nope")]))
        self.assertIsNone(render_roadmap.top_event([os.path.join(self.d, "no")]))


class TestNoGitOnTheRegenerateAndDiffPath(unittest.TestCase):
    """The guard that actually protects the determinism contract.

    hooks/pre-commit regenerates docs/roadmap.md and diffs it, and CI runs
    the whole hook on a ref the developer never committed from. A commit
    cannot know its own sha, so a git call here fails EVERY commit -- and on
    pull_request the checkout is a synthetic refs/pull/N/merge sha that
    exists in no local clone, so no stored value could ever match.

    This test fails loudly the day someone "fixes" provenance with a
    subprocess call, which is the obvious wrong turn.
    """

    def test_rendering_the_roadmap_shells_out_to_nothing(self):
        import json
        d = tempfile.mkdtemp(prefix="worklog-prov-det-")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "todo.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"ev": "01J8X0001A0", "ts": "t", "actor": "t",
                                 "item": "I1", "op": "create", "git": "abc1234",
                                 "set": {"title": "t", "status": "todo"}}) + "\n")

        def explode(*a, **k):
            raise AssertionError("render_roadmap shelled out: %r" % (a,))

        real = subprocess.run
        subprocess.run = explode
        try:
            out = render_roadmap.render([p])
        finally:
            subprocess.run = real
        self.assertIn('git_hash: "abc1234"', out)


def _manifest():
    import json
    with open(os.path.join(ROOT, "docs/.index/publish-manifest.json")) as fh:
        return json.load(fh)


if __name__ == "__main__":
    os.chdir(ROOT)
    unittest.main(verbosity=2)
