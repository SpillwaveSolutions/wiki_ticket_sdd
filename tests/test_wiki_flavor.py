#!/usr/bin/env python3
"""Item #271: one seam for page naming and link syntax.

Two things have to be true for this to have been worth doing:

  1. Nothing changes for the platform that has a user. Gollum output must be
     byte-identical, or the seam is a rewrite wearing a refactor's clothes.
  2. A second platform really is a new class. The proof is a flavor defined
     HERE, in the tests -- deliberately not shipped, because the ticket said
     platforms get filed when they have a user, not before.
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
sys.path.insert(0, BIN)
import wiki_flavor  # noqa: E402
import ia_render  # noqa: E402


class Markdown:
    """A second platform, defined only in this test file. If the seam is real,
    this is all it takes -- no edit to ia_render.py."""

    name = "test-markdown"

    def link(self, page, text=None):
        return "[%s](%s)" % (text or page, page)

    def sanitize(self, name):
        return name.replace(" ", "_").lower()


class TestGollumIsUnchanged(unittest.TestCase):
    def setUp(self):
        self.f = wiki_flavor.Gollum()

    def test_plain_link_is_the_canonical_form(self):
        self.assertEqual(self.f.link("Index-Releases"), "[[Index-Releases]]")

    def test_translation_is_the_identity_for_gollum(self):
        """Why the refactor cannot change published output: for the one
        platform that ships, translating is a no-op."""
        text = ("See [[Index-Releases]] and [[Roadmap]], plus "
                "[[Design-Doc]] · [[Code-Walkthrough]].")
        self.assertEqual(wiki_flavor.render_links(text, self.f), text)

    def test_piped_link_puts_display_first(self):
        self.assertEqual(self.f.link("Roadmap", "the roadmap"),
                         "[[the roadmap|Roadmap]]")

    def test_spaces_become_dashes(self):
        self.assertEqual(self.f.sanitize("Some Page Name"), "Some-Page-Name")


class TestSecondPlatformNeedsNoRendererEdit(unittest.TestCase):
    def test_links_translate(self):
        out = wiki_flavor.render_links(
            "See [[Index-Releases]] now.", Markdown())
        self.assertEqual(out, "See [Index-Releases](Index-Releases) now.")

    def test_piped_link_translates_display_and_target(self):
        out = wiki_flavor.render_links("[[the roadmap|Roadmap]]", Markdown())
        self.assertEqual(out, "[the roadmap](Roadmap)")

    def test_several_links_in_one_line(self):
        out = wiki_flavor.render_links("[[A]] · [[B]] · [[C]]", Markdown())
        self.assertEqual(out, "[A](A) · [B](B) · [C](C)")

    def test_naming_differs_too(self):
        self.assertEqual(Markdown().sanitize("Some Page Name"),
                         "some_page_name")

    def test_the_renderer_picks_it_up_through_use_flavor(self):
        """The whole claim: swapping the flavor changes rendered links with
        no change to ia_render.py."""
        original = ia_render.FLAVOR
        try:
            wiki_flavor.FLAVORS["test-markdown"] = Markdown
            ia_render.use_flavor("test-markdown")
            self.assertEqual(ia_render._links("[[Roadmap]]"),
                             "[Roadmap](Roadmap)")
        finally:
            wiki_flavor.FLAVORS.pop("test-markdown", None)
            ia_render.FLAVOR = original
        self.assertEqual(ia_render._links("[[Roadmap]]"), "[[Roadmap]]")


class TestNonLinkTextIsUntouched(unittest.TestCase):
    def test_markdown_link_is_not_a_wikilink(self):
        text = "[a link](http://example.com) and `code[[x]]`"
        out = wiki_flavor.render_links(text, Markdown())
        self.assertIn("[a link](http://example.com)", out)

    def test_empty_brackets_are_left_alone(self):
        self.assertEqual(wiki_flavor.render_links("[[]]", Markdown()), "[[]]")

    def test_text_with_no_links_is_returned_unchanged(self):
        self.assertEqual(wiki_flavor.render_links("plain", Markdown()), "plain")


class TestConfig(unittest.TestCase):
    """The ticket's actual complaint: the renderer never read the wiki system
    from config."""

    def _cfg(self, text):
        fh = tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False)
        fh.write(text)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_reads_wiki_system(self):
        path = self._cfg("wiki:\n  system: github-wiki\n  root_url: x\n")
        self.assertEqual(wiki_flavor.configured_system(path), "github-wiki")

    def test_does_not_confuse_another_block_s_system_key(self):
        """ticketing: also has a `system:` -- reading the wrong one would
        silently pick a flavor from the tracker's name."""
        path = self._cfg("ticketing:\n  system: github\n"
                         "wiki:\n  system: github-wiki\n")
        self.assertEqual(wiki_flavor.configured_system(path), "github-wiki")

    def test_ticketing_only_config_yields_none(self):
        path = self._cfg("ticketing:\n  system: jira\n")
        self.assertIsNone(wiki_flavor.configured_system(path))

    def test_comments_are_ignored(self):
        path = self._cfg("wiki:\n  system: github-wiki   # github-wiki | none\n")
        self.assertEqual(wiki_flavor.configured_system(path), "github-wiki")

    def test_missing_file_is_not_an_error(self):
        self.assertIsNone(wiki_flavor.configured_system("/nonexistent/c.yml"))

    def test_unknown_system_falls_back_rather_than_failing(self):
        """`other` and `none` are valid config values. A repo naming a
        platform nobody implemented must still render its docs."""
        path = self._cfg("wiki:\n  system: confluence\n")
        self.assertIsInstance(wiki_flavor.get(path=path), wiki_flavor.Gollum)

    def test_none_configured_falls_back_to_default(self):
        path = self._cfg("wiki:\n  system: none\n")
        self.assertIsInstance(wiki_flavor.get(path=path), wiki_flavor.Gollum)

    def test_env_var_overrides_config(self):
        path = self._cfg("wiki:\n  system: github-wiki\n")
        os.environ["WORKLOG_WIKI_SYSTEM"] = "nope"
        self.addCleanup(os.environ.pop, "WORKLOG_WIKI_SYSTEM", None)
        self.assertIsInstance(wiki_flavor.get(path=path), wiki_flavor.Gollum)


class TestSeamStaysSmall(unittest.TestCase):
    """The ticket set its own limit: 'if it grows past a naming/link
    interface, stop and wait for a real second consumer.' This test is that
    limit, written down where it will actually be noticed."""

    def test_a_flavor_has_exactly_two_methods(self):
        public = {n for n in vars(wiki_flavor.Gollum)
                  if not n.startswith("_") and callable(
                      getattr(wiki_flavor.Gollum, n))}
        self.assertEqual(public, {"link", "sanitize"},
                         "the seam grew past naming and links — the ticket "
                         "says stop and wait for a real second platform")

    def test_only_one_platform_ships(self):
        self.assertEqual(list(wiki_flavor.FLAVORS), ["github-wiki"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
