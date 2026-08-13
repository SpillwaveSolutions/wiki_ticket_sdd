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

    def test_build_provenance_is_recorded_once_at_the_top(self):
        """One fact about one build. Recording it per page would be ~344
        copies, would move every render_hash at once, and would be stripped
        before any reader saw it."""
        man = _manifest()
        self.assertIn("git_hash", man)
        self.assertEqual(
            man["git_hash"],
            render_roadmap.top_event(render_roadmap.PATHS)["git"])
        for p in man["pages"]:
            self.assertNotIn("git_hash", p, p["wiki_key"])


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

    def test_building_the_manifest_shells_out_to_nothing(self):
        """render_all() is byte-compared by write_all(check=True) from
        hooks/pre-commit and from CI. A git call anywhere under it makes the
        freshness gate unpassable."""
        real = subprocess.run

        def explode(*a, **k):
            raise AssertionError("ia_render shelled out: %r" % (a,))

        subprocess.run = explode
        try:
            _, manifest, _, _ = ia_render.render_all()
        finally:
            subprocess.run = real
        self.assertIn("git_hash", manifest)

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


class TestTheStampNamesTheRightTree(unittest.TestCase):
    """The test that matters: it fails when the recorded sha is WRONG.

    Asserting a git_hash exists proves nothing — a stamp naming the wrong
    commit is present, plausible, and useless, which is precisely the #294
    failure class. So: build a real repo, stamp, change the file, and assert
    the recorded sha still resolves to what the doc was written against.
    """

    def git(self, *args, **kw):
        return subprocess.run(["git", *args], cwd=self.d, capture_output=True,
                              text=True, **kw)

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-prov-tree-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.git("init", "-q", ".")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")

    def commit(self, name, text):
        write(os.path.join(self.d, name), text)
        self.git("add", "-A")
        self.git("commit", "-qm", "x")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def stamp(self):
        """What a writer records: full HEAD sha, taken in this repo."""
        p = self.git("rev-parse", "HEAD")
        return p.stdout.strip() if p.returncode == 0 else ""

    def test_the_recorded_sha_resolves_to_the_tree_the_doc_was_written_against(self):
        c0 = self.commit("foo.py", "ORIGINAL\n")
        recorded = self.stamp()
        self.assertEqual(recorded, c0)
        # the code moves on
        self.commit("foo.py", "REWRITTEN\n")
        # the stamp still names the tree the doc described
        at_stamp = self.git("show", "%s:foo.py" % recorded).stdout
        self.assertEqual(at_stamp, "ORIGINAL\n")
        # ...and HEAD does not, which is the whole point of pinning
        self.assertEqual(self.git("show", "HEAD:foo.py").stdout, "REWRITTEN\n")

    def test_the_recorded_sha_is_full_length(self):
        """Short shas are all digits ~1 time in 27, and ia._scalar coerces
        an all-digit value to int. Full length makes that ~7e-9."""
        self.commit("foo.py", "x\n")
        self.assertEqual(len(self.stamp()), 40)

    def test_a_stamp_is_the_parent_of_the_commit_that_carries_the_doc(self):
        """Documents the off-by-one honestly rather than pretending it away:
        a commit cannot know its own sha, so `git_hash` means "the tree this
        was written against", not "the commit containing this file"."""
        c0 = self.commit("foo.py", "x\n")
        recorded = self.stamp()          # what a writer would stamp now
        c1 = self.commit("doc.md", '---\ngit_hash: "%s"\n---\nbody\n' % recorded)
        self.assertEqual(recorded, c0)
        self.assertNotEqual(recorded, c1)
        parent = self.git("rev-parse", "%s^" % c1).stdout.strip()
        self.assertEqual(recorded, parent)


class TestWritersDegradeWithoutGit(unittest.TestCase):
    """Absent means "not verifiable, skip and say so". Empty would corrupt
    the parse of every line after it."""

    def test_plan_front_matter_omits_the_key_when_there_is_no_sha(self):
        import plan_capture
        for missing in ("", None):
            fm = plan_capture.front_matter("2026-08-03", "s", "T", "01E",
                                           ["01A"], missing)
            self.assertNotIn("git_hash", fm)
            self.assertTrue(fm.startswith("---\n"))

    def test_plan_front_matter_quotes_the_sha(self):
        fm = _plan_fm("0123456")
        self.assertIn('git_hash: "0123456"', fm)
        self.assertEqual(ia.parse_front_matter(fm)[0]["git_hash"], "0123456")

    def test_adr_scaffold_omits_and_quotes_the_same_way(self):
        import adr
        _, bare = adr.scaffold("T", 1, "s", "2026-08-03")
        self.assertNotIn("git_hash", bare)
        _, stamped = adr.scaffold("T", 1, "s", "2026-08-03", git_hash="0123456")
        self.assertEqual(ia.parse_front_matter(stamped)[0]["git_hash"], "0123456")

    def test_the_env_kill_switch_silences_both_helpers(self):
        import ulid
        ulid._git_commit_cache.clear()
        os.environ["WORKLOG_NO_GIT_PROVENANCE"] = "1"
        try:
            self.assertEqual(ulid.git_commit(), "")
            self.assertEqual(ulid.git_commit_full(), "")
        finally:
            del os.environ["WORKLOG_NO_GIT_PROVENANCE"]
            ulid._git_commit_cache.clear()


class RepoFixture(unittest.TestCase):
    """A throwaway repo with real history — merges included, because the
    whole merged_in derivation is about which merge landed what."""

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.d, capture_output=True,
                              text=True)

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="worklog-prov-repo-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.git("init", "-q", "-b", "main", ".")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        self.commit("seed.txt", "seed\n")

    def commit(self, name, text):
        path = os.path.join(self.d, name)
        os.makedirs(os.path.dirname(path), exist_ok=True) if "/" in name else None
        write(path, text)
        self.git("add", "-A")
        self.git("commit", "-qm", name)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def run_in_repo(self, fn):
        cwd = os.getcwd()
        os.chdir(self.d)
        try:
            return fn()
        finally:
            os.chdir(cwd)


class TestMergedInNamesTheCommitThatLandedIt(RepoFixture):
    """Both obvious one-liners are wrong, and quietly. These pin the right
    answer against the exact histories that break them."""

    def landed(self, path):
        import provenance
        return self.run_in_repo(lambda: provenance.merged_in(path, "main"))

    def test_it_finds_the_merge_that_brought_the_file_to_main(self):
        self.git("checkout", "-q", "-b", "feature")
        self.commit("doc.md", "body\n")
        self.git("checkout", "-q", "main")
        self.commit("other.txt", "x\n")
        self.git("merge", "-q", "--no-ff", "-m", "Merge feature", "feature")
        self.assertEqual(self.landed("doc.md"), self.head())

    def test_a_merge_of_main_INTO_the_branch_is_not_the_answer(self):
        """`rev-list --ancestry-path --merges A..main | tail -1` returns THIS
        merge — the earliest on the path — and it is wrong. Verified wrong on
        the real repo before this test existed."""
        self.git("checkout", "-q", "-b", "feature")
        self.commit("doc.md", "body\n")
        self.git("checkout", "-q", "main")
        self.commit("other.txt", "x\n")
        self.git("checkout", "-q", "feature")
        self.git("merge", "-q", "--no-ff", "-m", "Merge main into feature", "main")
        incoming = self.head()
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "Merge feature", "feature")
        landing = self.head()
        got = self.landed("doc.md")
        self.assertEqual(got, landing)
        self.assertNotEqual(got, incoming)

    def test_a_later_merge_does_not_displace_the_first(self):
        self.git("checkout", "-q", "-b", "feature")
        self.commit("doc.md", "body\n")
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "Merge feature", "feature")
        landing = self.head()
        self.git("checkout", "-q", "-b", "second")
        self.commit("later.txt", "y\n")
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "Merge second", "second")
        self.assertEqual(self.landed("doc.md"), landing)

    def test_a_file_still_on_a_branch_has_no_answer(self):
        self.git("checkout", "-q", "-b", "feature")
        self.commit("doc.md", "body\n")
        self.assertIsNone(self.landed("doc.md"))

    def test_a_file_committed_straight_to_main_landed_as_itself(self):
        sha = self.commit("doc.md", "body\n")
        self.assertEqual(self.landed("doc.md"), sha)


class TestVerifierReadsThePinnedCommit(RepoFixture):
    """The #294 regression test.

    A citation that was correct when written, whose code has since moved,
    must read as DRIFT — not as a defect — because the verifier resolves it
    at the document's own commit. Checking against HEAD would call it
    fabricated, which is the failure this whole feature exists to end.
    """

    def verify_one(self, doc_rel, cite_text, sha):
        import doc_verify
        write(os.path.join(self.d, doc_rel),
              '---\ngit_hash: "%s"\n---\n\n%s\n' % (sha, cite_text))
        self.git("add", "-A")
        self.git("commit", "-qm", "doc")
        rec = {"k": {"source": doc_rel, "git_hash": sha}}
        return self.run_in_repo(lambda: doc_verify.verify(records=rec))

    def test_a_citation_correct_when_written_reads_as_drift_not_a_defect(self):
        self.commit("bin/thing.py", "\n".join(
            ["# 1", "# 2", "def target():", "    pass", "# 5"]) + "\n")
        sha = self.head()
        # the code moves: target() is deleted
        self.commit("bin/thing.py", "\n".join(["# 1", "# 2", "# 3"]) + "\n")
        findings, summary = self.verify_one(
            "doc.md", "`bin/thing.py — target(), lines 3–4`", sha)
        self.assertEqual(summary["fabricated"], 0, findings)
        self.assertEqual(summary["drift"], 1, findings)

    def test_a_citation_wrong_when_written_reads_as_fabricated(self):
        self.commit("bin/thing.py", "\n".join(
            ["# 1", "# 2", "def target():", "    pass", "# 5"]) + "\n")
        sha = self.head()
        findings, summary = self.verify_one(
            "doc.md", "`bin/thing.py — target(), lines 1–2`", sha)
        self.assertEqual(summary["fabricated"], 1, findings)

    def test_a_range_that_merely_CONTAINS_the_symbol_is_not_good_enough(self):
        """01KZCC0F: the check used to ask only whether the symbol appeared
        somewhere inside the cited window, so a range starting in the wrong
        place passed. `compact()` was cited at 165-173 when it begins at 143
        and read as fine for three releases; the v0.22.1 regeneration found
        six such citations, every one reported ok.

        Here the window contains `target` (in the call on line 2) but the
        definition starts at 4, so the reader lands two lines above it.
        """
        self.commit("bin/thing.py", "\n".join(
            ["# 1", "target()", "# 3", "def target():", "    pass"]) + "\n")
        sha = self.head()
        findings, summary = self.verify_one(
            "doc.md", "`bin/thing.py — target(), lines 2–5`", sha)
        self.assertEqual(summary["fabricated"], 1, findings)
        self.assertIn("begins at line 4", findings[0]["detail"])

    def test_the_END_of_a_range_is_deliberately_not_judged(self):
        """Citing a SLICE of a long function is legitimate, and nine of the
        ranges measured overshot by exactly one line -- the blank after the
        body -- which is how people write citations, not an error worth a
        finding. Only the start is judged; pinned so nobody 'tightens' this
        into a source of noise."""
        self.commit("bin/thing.py", "\n".join(
            ["# 1", "def target():", "    a = 1", "    b = 2", "    return a + b",
             "", "# 7"]) + "\n")
        sha = self.head()
        for rng in ("2–3", "2–6", "2–7"):     # short slice, +1 blank, overshoot
            findings, summary = self.verify_one(
                "doc-%s.md" % rng.replace("–", "-"),
                "`bin/thing.py — target(), lines %s`" % rng, sha)
            self.assertEqual(summary["fabricated"], 0,
                             "range %s should not be a finding: %s" % (rng, findings))

    def test_an_ambiguous_symbol_falls_back_rather_than_accusing(self):
        """Two definitions of one name -- a method on two classes, or a
        redefinition under a version guard -- means the AST cannot say which
        one is meant. Judge nothing: a wrong accusation is worse than a missed
        one, because this tool's value is that a finding is worth acting on."""
        self.commit("bin/thing.py", "\n".join(
            ["class A:", "    def target(self):", "        pass",
             "class B:", "    def target(self):", "        pass"]) + "\n")
        sha = self.head()
        findings, summary = self.verify_one(
            "doc.md", "`bin/thing.py — target(), lines 4–6`", sha)
        self.assertEqual(summary["fabricated"], 0, findings)

    def test_a_non_python_file_still_uses_the_substring_check(self):
        """The AST rule cannot apply, and must not silently pass everything
        either -- a symbol genuinely absent from the window is still wrong."""
        self.commit("hooks/pre-commit", "\n".join(
            ["#!/bin/sh", "# nothing here", "# nor here"]) + "\n")
        sha = self.head()
        findings, summary = self.verify_one(
            "doc.md", "`hooks/pre-commit — target(), lines 1–3`", sha)
        self.assertEqual(summary["fabricated"], 1, findings)

    def test_staged_scope_hides_a_finding_in_a_doc_this_commit_never_saw(self):
        """01KZCZQ2: the hook ran repo-wide, and every finding in this repo
        lives in a FROZEN document that policy says stays frozen -- so it
        warned on every commit forever regardless of what the commit touched.
        A warning that always fires is one people learn to scroll past, which
        costs more than it catches.

        Here two documents both cite the same wrong lines. Scoped to one, the
        other's finding must not appear.
        """
        self.commit("bin/thing.py", "\n".join(
            ["# 1", "# 2", "def target():", "    pass"]) + "\n")
        sha = self.head()
        cite = "`bin/thing.py — target(), lines 1–2`"
        for name in ("mine.md", "theirs.md"):
            write(os.path.join(self.d, name),
                  '---\ngit_hash: "%s"\n---\n\n%s\n' % (sha, cite))
        self.git("add", "-A")
        self.git("commit", "-qm", "two docs")
        import doc_verify
        recs = {"mine": {"source": "mine.md", "git_hash": sha},
                "theirs": {"source": "theirs.md", "git_hash": sha}}

        both = self.run_in_repo(lambda: doc_verify.verify(records=recs))
        self.assertEqual(both[1]["fabricated"], 2, both[0])

        one = self.run_in_repo(
            lambda: doc_verify.verify(records=recs, only={"mine.md"}))
        self.assertEqual(one[1]["fabricated"], 1, one[0])
        self.assertEqual(one[0][0]["source"], "mine.md")

    def test_an_empty_staged_set_is_not_the_same_as_no_scope(self):
        """`only=set()` must check nothing, not everything. Conflating the
        two would make a commit that touches no documents silently run the
        repo-wide check again -- the exact behaviour being removed."""
        self.commit("bin/thing.py", "def target():\n    pass\n")
        sha = self.head()
        write(os.path.join(self.d, "doc.md"),
              '---\ngit_hash: "%s"\n---\n\n`bin/thing.py — target(), lines 90–99`\n'
              % sha)
        self.git("add", "-A")
        self.git("commit", "-qm", "doc")
        import doc_verify
        recs = {"k": {"source": "doc.md", "git_hash": sha}}
        _, summary = self.run_in_repo(
            lambda: doc_verify.verify(records=recs, only=set()))
        self.assertEqual(summary["docs"], 0)
        self.assertEqual(summary["fabricated"], 0)

    def test_a_range_past_the_end_of_the_file_is_fabricated(self):
        self.commit("bin/thing.py", "one\ntwo\n")
        sha = self.head()
        findings, summary = self.verify_one(
            "doc.md", "`bin/thing.py — x(), lines 90–99`", sha)
        self.assertEqual(summary["fabricated"], 1, findings)

    def test_an_accurate_citation_is_just_ok(self):
        self.commit("bin/thing.py", "\n".join(
            ["# 1", "# 2", "def target():", "    pass"]) + "\n")
        sha = self.head()
        findings, summary = self.verify_one(
            "doc.md", "`bin/thing.py — target(), lines 3–4`", sha)
        self.assertEqual((summary["ok"], summary["fabricated"]), (1, 0), findings)


class TestVerifierNeverFallsBackToHead(unittest.TestCase):
    """Falling back is bug #294 with extra steps: it would report drift as
    fabrication while looking like it worked."""

    def setUp(self):
        """A document with a citation that WOULD resolve against HEAD, so a
        fallback would silently produce a verdict. That is the whole point:
        these tests fail if the verifier ever starts answering."""
        self.d = tempfile.mkdtemp(prefix="worklog-prov-nofb-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.doc = os.path.join(self.d, "doc.md")
        write(self.doc, "`bin/fold.py — fold(), lines 1–400`\n")

    def test_an_unstamped_document_is_skipped_not_checked(self):
        import doc_verify
        _, summary = doc_verify.verify(records={"k": {"source": self.doc}})
        self.assertEqual(summary["unstamped"], 1)
        self.assertEqual((summary["ok"], summary["fabricated"],
                          summary["drift"]), (0, 0, 0))

    def test_an_unresolvable_commit_is_skipped_not_checked(self):
        import doc_verify
        _, summary = doc_verify.verify(
            records={"k": {"source": self.doc, "git_hash": "0" * 40}})
        self.assertEqual(summary["unresolvable"], 1)
        self.assertEqual((summary["ok"], summary["fabricated"],
                          summary["drift"]), (0, 0, 0))

    def test_strict_fails_on_fabrication_but_tolerates_frozen_drift(self):
        import doc_verify
        frozen_drift = {"verdict": "drift", "live": False}
        live_drift = {"verdict": "drift", "live": True}
        fabricated = {"verdict": "fabricated", "live": False, "editable": True}
        self.assertEqual(doc_verify.failing([frozen_drift]), [])
        self.assertEqual(len(doc_verify.failing([live_drift])), 1)
        self.assertEqual(len(doc_verify.failing([fabricated])), 1)


class TestStrictIsPassable(unittest.TestCase):
    """#345 / ADR-0009. Gating fabrication ANYWHERE was un-passable: the only
    way to clear one is to edit the document, and for a frozen document the
    freeze rule forbids exactly that. 48 of them sat in this repo's dated
    design pairs with no legal fix, so the release gate could never go green.

    The gate now follows editability, and these tests pin both halves --
    dropping the gate for landed frozen docs is only defensible because the
    commit that WRITES one still gets checked.
    """

    def finding(self, **kw):
        f = {"verdict": "fabricated", "live": False, "editable": False}
        f.update(kw)
        return f

    def test_a_landed_frozen_fabrication_does_not_fail_the_gate(self):
        import doc_verify
        self.assertEqual(doc_verify.failing([self.finding()]), [])

    def test_the_commit_that_writes_that_same_document_still_fails(self):
        """The whole justification for the line above. A repo-wide run marks
        a frozen doc uneditable; a --staged run is scoped to documents the
        commit is writing, so every finding in it is still fixable."""
        import doc_verify
        self.assertEqual(
            len(doc_verify.failing([self.finding(editable=True)])), 1)

    def test_a_doc_that_is_neither_live_nor_frozen_is_still_gated(self):
        """docs/user_guide/ and README.md are neither. Scoping the gate to
        LIVE_DOCS instead of to editability -- the obvious one-line fix --
        would stop gating a fabrication there, which IS fixable."""
        import doc_verify
        rec = {"source": "docs/user_guide/x.md", "doc_type": "guide"}
        self.assertFalse(ia.is_frozen(rec))
        self.assertEqual(len(doc_verify.failing(
            [self.finding(editable=True)])), 1)

    def verdicts_for(self, name, scoped=False):
        """A fabrication through verify(), which is where `editable` is
        computed -- failing() never sees a record. The cited path does not
        exist at any commit, so the verdict does not depend on this repo's
        contents. `scoped` mimics --staged: the run is restricted to this
        document, i.e. the commit is writing it."""
        import doc_verify
        d = tempfile.mkdtemp(prefix="worklog-345-")
        self.addCleanup(shutil.rmtree, d, True)
        doc = os.path.join(d, name)
        write(doc, "`bin/no-such-module.py — target(), lines 1–2`\n")
        rec = {"source": doc, "doc_type": "design", "git_hash": "HEAD"}
        findings, _ = doc_verify.verify(records={"k": rec},
                                        only={doc} if scoped else None)
        self.assertTrue(findings, "expected a fabrication to work with")
        return findings

    def test_verify_marks_a_landed_frozen_design_uneditable(self):
        import doc_verify
        f = self.verdicts_for("2026-07-19_v0.11.0-release_design_doc.md")
        self.assertFalse(any(x.get("editable") for x in f), f)
        self.assertEqual(doc_verify.failing(f), [])

    def test_verify_marks_the_current_pair_editable(self):
        f = self.verdicts_for("current_design_doc.md")
        self.assertTrue(all(x.get("editable") for x in f), f)

    def test_a_commit_scoped_run_makes_even_a_frozen_design_editable(self):
        """The load-bearing case: the commit that creates a dated design pair
        is the last moment its citations can be corrected, so --staged must
        gate them. If this ever stops holding, a new frozen document can land
        fabricated and nothing will ever fail on it."""
        import doc_verify
        name = "2026-07-19_v0.11.0-release_design_doc.md"
        f = self.verdicts_for(name)
        scoped = self.verdicts_for(name, scoped=True)
        self.assertFalse(any(x.get("editable") for x in f))
        self.assertTrue(all(x.get("editable") for x in scoped), scoped)
        self.assertEqual(len(doc_verify.failing(scoped)), 1)


class TestCitationParsing(unittest.TestCase):
    """All four forms that actually occur in this repo's design docs."""

    def test_it_reads_the_four_real_forms(self):
        import doc_verify
        text = ("`bin/fold.py — apply_watermark(), lines 210–267`\n"
                "(`bin/worklog`, lines 528–595)\n"
                "(`ia_graph.ticket_body()`, lines 302–357)\n"
                "`bin/canonical.py:17`\n")
        got = {(c["path"], c["symbol"], c["start"], c["end"])
               for c in doc_verify.citations(text)}
        self.assertIn(("bin/fold.py", "apply_watermark", 210, 267), got)
        self.assertIn(("bin/worklog", None, 528, 595), got)
        self.assertIn(("bin/ia_graph.py", "ticket_body", 302, 357), got)
        self.assertIn(("bin/canonical.py", None, 17, 17), got)

    def test_an_en_dash_range_is_not_missed(self):
        """A regex written for a hyphen matches nothing in these docs."""
        import doc_verify
        self.assertTrue(doc_verify.citations("`bin/fold.py`, lines 1–2"))


def _plan_fm(sha):
    import plan_capture
    return plan_capture.front_matter("2026-08-03", "s", "T", "01E", ["01A"], sha)


def _manifest():
    import json
    with open(os.path.join(ROOT, "docs/.index/publish-manifest.json")) as fh:
        return json.load(fh)


if __name__ == "__main__":
    os.chdir(ROOT)
    unittest.main(verbosity=2)
