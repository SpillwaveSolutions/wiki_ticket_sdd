#!/usr/bin/env python3
"""
wiki_flavor.py -- the renderer's one platform seam. Item #271.

The renderer never read the wiki system from config: page naming and every
cross-page link were written for Gollum, the GitHub wiki engine. Roughly forty
wikilink sites and five naming helpers assumed its conventions, so porting to
any other platform meant editing all of them.

The seam is deliberately two things, and only two:

    link(page, text=None) -> the platform's cross-page link syntax
    sanitize(name)        -> what the platform allows in a page name

A second platform is a new class in FLAVORS, not a rewrite.

The design point that keeps it small: `[[Page]]` is treated as the renderer's
CANONICAL link notation, not as Gollum output. Every prose string in
ia_render.py keeps writing `[[Index-Releases]]` -- readable, greppable,
unchanged -- and render_links() translates the whole page once at the output
boundary. So a second platform implements one method instead of editing forty
call sites, and Gollum stays byte-identical because for Gollum the
translation is the identity.

The ticket that asked for this set its own limit: doing the seam without a
second consumer is only worth it if it stays small, and if it grows past a
naming/link interface, stop and wait for a real second platform. So there is
no page-layout hook, no frontmatter hook, no directory-structure hook, and no
`filename()` -- those would be guesses about a platform nobody has asked for.
Only ONE flavor ships, because only one platform has a user
(`wiki.system: github-wiki`).
"""
import os
import re

CONFIG = ".work/config.yml"

# Gollum's own syntax, reused as the canonical notation: [[Page]] or the
# piped [[Display|Page]] -- display FIRST, which is the order that bites
# people, and the reason translation lives in one place.
CANONICAL_LINK = re.compile(r"\[\[([^\[\]|]+?)(?:\|([^\[\]|]+?))?\]\]")


class Gollum:
    """GitHub wiki. Flat namespace, `[[Page]]` links, spaces become dashes."""

    name = "github-wiki"

    def link(self, page, text=None):
        return "[[%s|%s]]" % (text, page) if text else "[[%s]]" % page

    def sanitize(self, name):
        # Gollum maps spaces to dashes in URLs; writing the dash keeps a page
        # name and its published URL identical.
        return name.replace(" ", "-")


FLAVORS = {f.name: f for f in (Gollum,)}
DEFAULT = Gollum.name


def render_links(text, flavor):
    """Translate canonical [[...]] notation in `text` into `flavor` syntax."""
    def one(m):
        first, second = m.group(1), m.group(2)
        # [[Page]] -> page only; [[Display|Page]] -> display first (Gollum).
        return flavor.link(second, first) if second else flavor.link(first)
    return CANONICAL_LINK.sub(one, text)


def configured_system(path=CONFIG):
    """`wiki.system` from .work/config.yml, or None.

    A targeted read rather than a YAML dependency: this needs one value from
    one known block, and the installer already reads config.yml the same way
    with awk. Anything malformed reads as "not configured", which falls back
    to the default rather than failing a render.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    in_wiki = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line[0].isspace():
            in_wiki = line.strip().startswith("wiki:")
            continue
        if in_wiki:
            m = re.match(r"\s+system:\s*(\S+)", line)
            if m:
                return m.group(1).strip("\"'")
    return None


def get(system=None, path=CONFIG):
    """The flavor to render with.

    An unknown system is NOT an error: the config legitimately carries
    `other` and `none`, and a repo naming a platform nobody has implemented
    should still render its docs in the one format that exists rather than
    refusing to build.
    """
    system = (system or os.environ.get("WORKLOG_WIKI_SYSTEM")
              or configured_system(path) or DEFAULT)
    return FLAVORS.get(system, FLAVORS[DEFAULT])()
