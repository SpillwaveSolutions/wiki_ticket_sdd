# Changelog

## 0.24.0 — 2026-08-15

- **Multi-host bindings + isolation notes.** Agent Plugins 1.0 `plugin.json`, Grok Bot / Deep Agents / isolation / onboarding docs, host wrappers, vendored `plugin/scripts/brain_session.py`, and `worklog-session`.
- Documents the two merge models: append-only worklog (`.work/todo.jsonl`) vs knowledge-tree worktree + PR.
- Isolation tests use fictional **lumenfield-detector** / **northstar-console** only.

## 0.23.1 — unreleased

- **Fix**: `worklog doc-verify --strict` was un-passable. It exited 1 on a
  fabricated citation wherever it lived, and the only way to clear one is to
  edit the document — which the freeze rule forbids for exactly the documents
  that hold them. 48 fabrications sit in this repo's dated design pairs with no
  legal fix, so the release gate had been red since the verifier shipped and the
  remedy in every case was to not run it.

  The gate now follows **editability**, not freeze state: fabrication fails in a
  document that can still be corrected, and the commit that *creates* a frozen
  document is scoped by `--staged`, so its citations are still checked strictly
  — that is the only moment they could have been fixed anyway. Afterwards the
  errors stay, printed on every run tagged `[frozen record — reported, not
  gated]` with an explicit count, so silence never reads as absence. Reasoning
  and the two rejected alternatives: **ADR-0009**. (#345)

- **Fix**: `worklog doc-verify --staged` treated "cannot read the staged set"
  and "this commit touches no documents" as the same thing and exited 0 for
  both — a pass a check that never ran had not earned. It now says which
  happened, and checks everything when the staged set is unavailable.

## 0.23.0 — 2026-08-07

Four correctness fixes. Three of them are the same shape, and it is worth
naming: **a check that reported success while the answer was wrong.**

- **Fix**: `worklog doc-verify` now checks that a cited range *begins* where
  the symbol is defined. It used to ask only whether the symbol appeared
  somewhere inside the cited window, so a range starting in the wrong place
  passed — `compact()` was cited at lines 165–173 when it begins at 143, and
  read as fine for three releases. Six citations were wrong this way and
  every one was reported `ok`.

  Only the start is judged. The end is where the author chose to stop
  quoting, and citing a slice of a long function is legitimate; nine of the
  ranges measured overshot by exactly one line — the blank after the body,
  which is how people write citations and not a defect. Falls back to the old
  check when the syntax tree cannot say which definition is meant, because a
  wrong accusation costs more here than a missed one.

- **Fix**: the weekly status report lost work to compaction. It counted an
  item as shipped only when a `close` event fell inside the window, and
  compaction folds an item's history into a single snapshot — so the close
  event stops existing and the item vanishes from the report even though it
  closed in the window. Nightly compaction runs on the default branch, so
  **everything closed more than a day earlier disappeared** from the artifact
  whose whole job is to span a week. This repo's window read **9 items before
  the fix and 63 after**.

  The time was never lost: a snapshot carries the highest event it folded,
  which for a closed item is the close. **If you keep weekly reports, the
  older ones under-count.** No equivalent rescue exists for *opened* — a
  watermark is the last event folded, never the first — so figures derived
  from opened-in-window still under-report after a compaction.

- **New**: `worklog doc-verify --staged` checks only the documents a commit
  touches, and `hooks/pre-commit` now uses it. Every citation finding in a
  mature repo tends to live in a **frozen** document that policy says stays
  frozen, so the unscoped check warned on every commit forever regardless of
  what the commit contained — and a warning that always fires is one people
  learn to scroll past. The repo-wide run is still what the release gate
  uses, where the whole corpus is the subject rather than the commit.


- **Fix**: `_require_item` now rejects an item id containing whitespace.
  `item` is a single positional, so `close "$id1 $id2"` puts both ids in one
  string. `_resolve` already refuses to act on that, but two commands —
  `ingest` and `conflict` — call `_require_item` and then `append()` **without
  resolving**, so the event was written against a composite key matching no
  item: exit 0, no output, nothing changed. Both are sync-path commands, so the
  id can arrive from a remote system.

  The cost is not the no-op. The sidecar path rendered from that key grows with
  every id, and a downstream log carried a 10-ULID key whose 273-byte filename
  exceeded the filesystem limit and crashed `ia-render`, leaving the doc index
  stale behind a "soon a hard gate" warning. Four such records reached one log
  between 2026-07-23 and 2026-08-04; the older three survived only by staying
  under the limit.

  A real id never contains whitespace, so the same guard catches an error
  message captured into an id by mistake, which is how one of the four arose.
  On `close` the message now names the quoting mistake rather than reporting
  "no item matching &lt;two ULIDs&gt;", which reads as a missing item.

  Written downstream in a consuming repo and never sent here, so `init.sh`
  silently deleted it on upgrade — twice in one day, at 0.16.1 and again at
  0.22.2. That is how it surfaced. **A fix that lives only downstream has an
  expiry date.**

## 0.22.2 — 2026-08-06

- **Fix**: fifteen tests were never running. 0.22.0 found a run-as-a-script
  block sitting in the *middle* of one test file — everything defined below it
  is never registered — and fixed that one file without checking the other
  forty. Three were still hiding tests: `test_ulid.py` (11 of 20 running),
  `test_bug_merge.py` (15 of 19), `test_link.py` (15 of 17).

  Among the dead was the whole conflict-marker guard suite: the regression
  test for the check that stops an unresolved merge marker reaching the
  default branch, which the design documents cite as the enforcement. It had
  never run in CI.

  The two runners disagreed in silence — pytest imports the module and sees
  every class, CI runs the file as a script and sees only what precedes the
  block. **Worth checking your own suites for the same shape**; neither
  runner warns you.

  Fixing the instance and not the class is what made a second discovery
  necessary, so the check now covers the class: no test file may define a
  class below its `if __name__` block. Suite: 615 → 630 tests.

- **Docs**: the design document and code walkthrough are regenerated against
  0.22.1 and the dated pair frozen. Six inherited line citations were wrong at
  the tag and were corrected; every citation in both files was re-derived from
  the code rather than carried forward, and the pair verifies clean.

  The user guide, CLI reference, plugin guide and README are refreshed for
  0.22.0 and 0.22.1 — the Codex install path, the `merge-rescue`
  state-inversion repair (**if an item looks reopened, re-closing it is a
  complete repair**), the close-path overwrite report, and the plain statement
  that plugin hooks never fired before 0.22.1 and will start firing after you
  upgrade.

  Both defects in this release were found by the regeneration itself. That is
  twice in three releases that reading the code closely enough to describe it
  has surfaced something nothing else was looking for.

## 0.22.1 — 2026-08-06

One fix, and it is the kind worth reading: **if you installed this plugin,
none of its hooks have ever fired.**

- **Fix**: the hook manifest declared its events at the top level; the loader
  reads them from under a top-level `hooks` key. The file was valid JSON, so
  nothing failed, nothing warned, and the loader simply found no events —
  including the plan-capture hook this plugin is partly built around. Every
  other installed plugin we could compare against (superpowers, i-have-adhd,
  okf-graph-eng, explanatory-output-style) uses the wrapper; ours did not.

  **After upgrading, expect hooks to start firing that never did.** The
  prompt reminder on every message, the session doctor at start, the stop
  check on a dirty tree, and the plan-capture prompt on leaving plan mode are
  not new features in this release — they are the features you already
  installed, working for the first time.

  Found by [#329](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/pull/329)
  against a real installation, by noticing that no hook fired during a live
  plan-mode session. It could not be found from inside this repository, whose
  own sessions wire the same scripts through settings rather than through the
  plugin loader — so the tooling worked for the people building it and not for
  the people installing it.

  Three checks now cover the class rather than the instance: both manifests
  must be wrapped, every hook command must point at a file that exists and is
  executable, and every skill must declare `name` and `description` with no
  unquoted `": "` in its frontmatter — because a skill whose frontmatter fails
  to parse is not rejected, it loads with empty metadata and can never be
  matched. Installed and invisible.

## 0.22.0 — 2026-08-05

- **New**: a native Codex plugin. `plugin/.codex-plugin/plugin.json` packages
  the same skills the Claude plugin ships, installed the same way
  (`codex plugin marketplace add ...`, then `/plugins`). The shared `plugin/`
  tree stays canonical; each host gets a small manifest beside it.

- **New**: the Codex package carries lifecycle hooks, not just skills.
  `plugin/hooks/codex-hooks.json` wires the same prompt-submit, stop and
  session-start scripts the Claude plugin uses. They needed no porting: Codex
  sets `CLAUDE_PLUGIN_ROOT` for plugin-sourced hooks, and the scripts already
  emit the `hookSpecificOutput` / `additionalContext` shape Codex reads. Only
  the wrapper differs — Codex nests the event map under a `hooks` key.

  The plan-capture hook is the one that does not port, and for a real reason:
  it fires on `PostToolUse` with a matcher for the `ExitPlanMode` tool, and
  Codex has the event but not that tool. On Codex, plan capture stays what the
  policy file says it is. The other three are the ones that enforce work
  tracking, and they now work on both hosts.

- **Fix**: `worklog merge-rescue` could hand back an item in an older state
  than it went in with. When a compaction lands mid-branch, the rescue
  re-issues the branch's sub-watermark events under fresh ids so the fold
  cannot drop them. Fresh ids are stamped at *now*, so they sorted above every
  event that kept its original id — **including later events of the same
  item**, which sat above the watermark and were left alone. An item whose
  create and update moved but whose close did not folded back to the pre-close
  state. Nothing was lost, every guard was green, and the answer was wrong.
  Seen for real merging into a live branch: a `done` item came back
  `in_progress`.

  Re-issuing is now contagious forward within an item — once one event moves,
  every later event of that item moves with it — and a second, independent
  check verifies the whole log: sorting by the new ids must give each item the
  same sequence its original ids did, or the rescue refuses and leaves the
  logs untouched. **If you ran `merge-rescue` on 0.21.0 or earlier and an item
  looks reopened, that is this bug**; the close event is still in your log, so
  re-closing the item is a safe and complete repair.

- **Fix**: `worklog sync --dry-run` now reports the fields a *close* would
  overwrite. A close is not always only a close — a dirty item pushes its
  final shape first, and that push can rewrite a ticket somebody else filed.
  The dry run returned early on the close path and printed only
  `would close #123`, staying silent in exactly the case where a field write
  is least expected. This is the shape of the incident that renamed another
  reporter's issue; had that item been closing rather than updating, the dry
  run would have said nothing at all.

- **Fix**: seven dispatcher tests were never running. `tests/test_dispatch.py`
  carried its run-as-a-script block in the middle of the file, so every class
  defined below it was never registered — 20 tests executed where 27 existed,
  and CI runs these files as scripts. The hidden class covered overwrite
  reporting, **including the dry-run case fixed above**, so that defect sat
  underneath tests that could not fail. Worth checking your own suites for the
  same shape: pytest imports the module and sees all 27, running it as a
  script sees 20, and neither runner warns you.

## 0.21.0 — 2026-08-04

Generated documents now carry the commit they were written against, and a new
gate reads it back. This closes #294 — design docs quoting code that no longer
exists — but the mechanism is general: any document that cites code can now be
checked against the tree its author actually had open.

- **New**: `worklog doc-verify` resolves every `path — symbol(), lines N–M`
  citation in `docs/` at the commit the document was stamped with, and reports
  one of five verdicts. The distinction it exists to draw is **fabricated**
  (the citation was already wrong in the tree the author had open — a defect)
  versus **drift** (it was right when written and the code has since moved —
  not a defect, and expected in a frozen document). Before this, the two were
  indistinguishable, so a hand audit of the 0.20.0 design docs found **12 of 26
  citations wrong** and nobody could tell which of the rest to trust.

  `--strict` exits non-zero on any fabrication, and on drift **only in the two
  `current_*` design files**, which are the only documents that claim to
  describe the tree as it is now. It runs warn-level in `hooks/pre-commit`
  beside `trace-check`, `--strict` in the release skill, and — the placement
  that actually prevents the bug — inside the design-docs skill, before an
  agent may report a regeneration complete. That is the moment the error is
  made and the only moment fixing it is free.

  **It never falls back to HEAD.** A document with no `git_hash`, or one
  pinned to a commit absent from your clone, is reported `unstamped` or
  `unresolvable` and skipped. Re-checking against HEAD would be #294 with
  extra steps: it is precisely the assumption that produced the bad citations.

- **New**: `git_hash` is stamped on plans, status reports and ADRs as they are
  written, and on `docs/roadmap.md` and its snapshots — the roadmap taking it
  from the newest event's `git` field rather than shelling out, because the
  roadmap is regenerate-and-diffed in CI and a commit cannot know its own sha.
  `docs/.index/publish-manifest.json` carries one build-level `git_hash` rather
  than stamping 363 rendered pages with the same fact.

  `git_hash` means *the tree this document was written against*, which at
  generation time is the commit **before** the one the document lands in. That
  is the honest value and the one a reader diffing stale prose wants.

- **New**: `worklog provenance-backfill` adds `merged_in` — the merge commit
  that brought a frozen document to the default branch — after it lands. It
  runs from the release skill's post-release step, not a git hook, because
  `post-merge` fires on the default branch where committing is forbidden.
  73 documents carry it here. Both obvious recipes for computing that commit
  are wrong (`--merges | tail -1` returns merges *into* the branch;
  `--first-parent` alone returns nothing for a PR merge); the correct one is
  the oldest commit on the first-parent chain having the add-commit as an
  ancestor, and both wrong answers are pinned by tests.

- **Fix**: the publish manifest hashes a document **below its front matter**.
  Publishing strips front matter for Gollum-style wikis, so two files differing
  only there produce byte-identical pages — yet the old whole-file hash moved
  anyway, tripping the frozen-source guard on every metadata stamp the
  normalizer, `adr.mark_superseded`, or this release's provenance backfill
  writes. The guard now means *the prose changed*, which is the invariant it
  was always meant to protect. This is why stamping 73 documents moved the
  republish backlog by two pages instead of by 89.

- **Correction to the 0.20.0 notes.** Upgrading item 2 said your next
  `wiki-publish` would republish **every** frozen page. It does not. A page's
  `render_hash` moves only when its own banner text changes, and the 0.20.0
  banner fix changed plan banners alone — **18 pages republished here, not the
  whole site**. If you upgraded to 0.20.0 and saw a small publish, nothing
  failed. Released notes are frozen, so the correction lives here.

- **Docs**: ADR-0008 records that document provenance depends on this
  repository using merge commits. Under squash-merge the authoring commit never
  reaches the default branch, `git show <sha>:<path>` fails in a fresh clone,
  and the verifier loses its ground truth — at which point it must report
  `unresolvable` and refuse, never degrade to HEAD.

### Upgrading

**From 0.20.x** — `/worklog:init`, then read item 1 before you file a bug.

1. **`doc-verify` will report findings on your existing documents, and most of
   them are not yours to fix.** Documents written before this release have no
   `git_hash`, so they report `unstamped` — not a failure, just unverifiable;
   backfilling a guessed commit would be the exact error class #294 is about.
   Documents that *are* stamped may report fabrications inside **frozen**
   files — plans, ADRs, dated design pairs. Those stay. A frozen document is a
   record of what someone believed at a point in time, and editing it to
   silence a gate destroys the record and trips the publish ledger's
   frozen-source guard. Fix fabrications in live documents; name them in prose
   for frozen ones. Here that split is 45 frozen and 0 live.

2. **Nothing is required in front matter.** `merged_in` cannot be — a document
   on a branch has not merged, so requiring it would reject the commit that
   creates any plan — and `git_hash` is not, because documents predating this
   release cannot be honestly stamped.

## 0.20.0 — 2026-08-03

Two correctness fixes to the gates that judge your own repo, plus the release
doc sync 0.19.1 skipped. **Both fixes change what you see without changing any
of your data** — read "Upgrading" before you file a bug about the difference.

- **Fix**: `worklog trace-check --strict` now applies the scope it always
  claimed. The check is documented as covering *"every item in a released
  milestone"*, but it computed that scope as a label, printed it in every
  message, and filtered on nothing — so it swept every closed item in the log.
  In this repo that meant **401 gaps across 214 items, 80% of all closed work**,
  of which 323 were on items the check's own docstring excludes. The count grew
  with every item closed, which is how a gate becomes a number people scroll
  past.

  Scoping alone was not enough: release items carry milestones too, and every
  `Cut vX.Y.Z release` item was flagged for lacking the external ticket that
  the release skill explicitly says it must never have. So two exemptions come
  with it, each derived from a convention already documented elsewhere —
  `kind:ops` is exempt outright, and `unplanned` work is exempt from the *plan*
  check only (being discovered mid-flight excuses the plan, not the ticket and
  the PR). 401 gaps became 16, every one a real missing link.

- **Fix**: a plan's wiki banner now says which plan it is. Every plan page
  rendered the identical line — "the current plan" — whether the plan was
  finished, underway, or not yet started, even though the record carried
  `status` the whole time and nothing read it. The banner now takes the leading
  word of that status and names the state: *completed plan*, *plan in flight*,
  *plan not yet started*. Plan status is free prose, not an enum, so **prose
  the mapping does not recognise renders exactly as before rather than
  guessing** — inventing a label for text you cannot read is how this class of
  bug starts.

  Related: `banner()` no longer supplies a default for `kind` on a status
  record. `kind` is required there by schema; a record missing it now raises
  instead of rendering plausible prose over broken data.

  If you are on 0.18.0 or earlier, this fix also carries the 0.19.0 correction
  that stopped plan pages announcing themselves as *status reports*.

- **Fix**: `CLAUDE.md` and its `AGENTS.md` symlink are tracked in this
  repository. They never had been — not ignored, just never added — so a fresh
  clone got no work-tracking policy at all. **Check your own repo for this**;
  see Upgrading.

- **Docs**: the design document, code walkthrough, user guide and README are
  regenerated against 0.19.1 and the dated pair frozen. The user guide gains
  the four subcommands that shipped undocumented (`fields`, `merge-rescue`,
  `changelog-draft`, `find`), an operational page for `merge-rescue`, an
  environment-variable table, and the per-event `git` provenance rule. Two
  stale claims corrected: `pr-sync` has shipped, and `pre-merge-commit` runs
  more than checks 1–4.

  The regeneration also found the previous design docs quoting code that no
  longer exists — a merge-ordering tiebreak deleted in 0.19.0, a version
  constant three releases stale, an import `fold.py` does not have. The current
  pair is corrected; the frozen 0.18.0 pair keeps its errors, as frozen records
  do, and the current walkthrough names them for readers. Filed as #294.

### Upgrading

**From 0.19.x** — `/worklog:init` and nothing else. Then expect three
differences, all of them the fixes landing:

1. **`trace-check` will report far fewer gaps.** On a mature repo the drop can
   be an order of magnitude. **No data was removed.** The graph is unchanged
   and every edge still exists; the gate simply stopped asking about items it
   was never scoped to ask about. Run `worklog trace-check --strict` before and
   after if you want the difference itemised — the survivors are the ones worth
   your time.

2. **Your next `wiki-publish` will republish every frozen page.** Banner text
   folds into `render_hash` by design, so changing any banner invalidates every
   frozen page's hash at once. This is a single one-time churn, not a loop; the
   publish after it will be normal-sized. Do not interpret the ledger volume as
   a bug or interrupt the run partway.

3. **A status record with no `kind` now raises** where it previously rendered
   `"status report"`. If a publish fails with `KeyError: 'kind'`, that record
   was already malformed and was being papered over. Fix the record; do not
   restore the default.

**From 0.18.0 or earlier** — read the 0.19.0 and 0.19.1 notes below in full
first; they carry the compaction-watermark fix (#284) and the ULID entropy
correction, and neither is optional. Then:

4. **Check whether your policy file is committed.** `worklog init` creates
   `CLAUDE.md` and the `AGENTS.md` symlink but does not commit them, and it is
   easy to have never noticed:

   ```
   git ls-files CLAUDE.md AGENTS.md
   ```

   Empty output means a fresh clone of your repo gets no policy, and any agent
   session started from that clone runs with none of your rules. Fix with:

   ```
   git add CLAUDE.md AGENTS.md && git commit -m "track the worklog policy file"
   ```

   Verify the symlink stored as a symlink, not a copy — `git ls-files -s
   AGENTS.md` should show mode `120000`.

5. **If a nightly compaction blocks your first merge after upgrading**, that is
   expected on a busy repo and is what `worklog merge-rescue` is for. Run it
   from *inside* the blocked merge, then `worklog roadmap-render`, `git add -A`,
   `git commit`. Do not recompact to clear the block — recompaction verifies
   against a fold that has already discarded the branch's events, which makes
   the loss permanent.

**Downgrading** is safe. Nothing in this release changes the event log format,
the graph, or any sidecar schema. Both fixes are read-side only: revert the
version and the old behaviour returns, wrong counts and all.

## 0.19.1 — 2026-08-01

A corrective release for one thing shipped in 0.19.0. Upgrading from 0.19.0
needs nothing beyond `/worklog:init`; the guidance in the 0.19.0 notes below
still applies in full if you are coming from 0.18.0 or earlier.

- **Fix**: locally-minted ULIDs are back to their **full 80 bits of entropy**.
  0.19.0 overwrote five entropy characters with the short git hash to make
  branches distinguishable. That was the wrong trade: an id is issued once and
  never changes, and the only thing it must guarantee is that it does not
  clash, so entropy is not currency to spend on metadata.
- **New**: git provenance now rides on **every event** as its own `git` field
  — the short HEAD sha the event was authored at. This traces strictly better
  than the id ever could: an item's id is minted once, so it could only name
  the branch the *item* was created on, whereas a per-event field names the
  commit each individual event came from. Two agents in different worktrees or
  branches still produce traceably different events, which was the original
  goal.

  Additive and safe in both directions: the fold ignores unknown event fields,
  and `canonical_hash` picks only from the *item*, so no sync re-push follows.
  Events written by 0.19.0 or earlier simply have no `git` field. Set
  `WORKLOG_NO_GIT_PROVENANCE=1` to omit it.

  **Ids minted by 0.19.0 remain valid and are not rewritten.** They are
  well-formed ULIDs with slightly less entropy; there is nothing to migrate.
- **Fix**: `worklog link-pr` resolves an id prefix before writing the sidecar.
  It used to file `docs/.index/item/<prefix>.yml`, so the PR edge never
  reached the graph and the release evidence gate still reported the item as
  unlinked — with no error, because the write succeeded.

## 0.19.0 — 2026-08-01

### Upgrading from 0.18.0 or earlier

**Run `/worklog:init` in each repo.** Init is the upgrade path: it re-copies
`bin/` and `hooks/`, and this release adds four new `bin/` modules
(`session.py`, `changelog.py`, `item_fields.py`, `wiki_flavor.py`) plus a new
harness hook. A repo that skips this keeps working on the old code — nothing
breaks — but none of the features below exist until it runs.

**The event-log format changed additively, and mixed versions are safe in
both directions.** Compaction now writes a per-item `through` on each
snapshot (see *Fix* below). You do **not** need to upgrade every clone before
the next nightly compaction:

- An **old** reader on a **new** log ignores the unknown `through` field and
  applies the previous global-watermark rule. That is strictly more
  conservative — it can drop a branch-local event, exactly as it did before,
  but it never invents state.
- A **new** reader on an **old** log finds no `through` and falls back to the
  global mark for ordering, while still applying the new "an item with no
  snapshot never loses events" rule — which can only *restore* data.

No migration, no backfill, no coordinated cutover. Existing snapshots gain
the field naturally at the next compaction.

**Three things to do by hand after init:**

1. **Wire the `SessionEnd` hook** if you keep a project `.claude/settings.json`:
   ```json
   "SessionEnd": [{"hooks": [{"type": "command",
     "command": "\"$CLAUDE_PROJECT_DIR\"/hooks/session-end.sh"}]}]
   ```
   Without it the concurrent-session advisory still works, but a finished
   session keeps looking alive for an hour and warns the next one.
2. **Add `.work/.sessions` to `.gitignore`.** It is local advisory state and
   must never be committed.
3. **Re-check `core.hooksPath`** points at this repo's `hooks/`
   (`worklog doctor` reports it). The pre-commit hook gained a
   conflict-marker check that only runs if the hooks are wired.

**Behaviour changes worth knowing before you upgrade:**

- **`worklog add` and `worklog update` gained flags** for the default-on
  optional fields (`--owner`, `--risk`, `--acceptance-criteria`). Nothing is
  required and nothing existing changed shape. `--estimate` moved into the
  same catalog; its behaviour is identical. Run `worklog fields` to see what
  is on, and switch fields on or off with a `work_item_fields:` block in
  `.work/config.yml`.
- **Generated ULIDs now embed the short git hash** in five characters of
  their entropy. The 26-character format, the time prefix and
  sort-order-equals-time-order are unchanged, and ids minted before the
  upgrade stay valid forever. Ingest ids (`ulid.deterministic`) are
  deliberately unaffected, so remote-change ids remain byte-identical across
  clones.
- **A blocked merge now names a command that works.** If the resurrection
  guard stops a merge commit, run `worklog merge-rescue`. The old advice —
  recompacting — could not be run from that state and would not have been
  safe if it could. See ADR-0005/0006/0007.
- **`pre-commit` refuses staged files containing conflict markers**, with no
  merge exemption. If you have been landing merges that carried markers into
  `tests/` or `plugin/`, this will now stop you.
- **Rendered wiki output is byte-identical** to 0.18.0 despite the renderer
  being re-plumbed for portability. Verified across all 319 rendered pages.

### Changes

- **New**: `worklog find` — search the generated inventory and graph from the
  CLI. Documents by text, type or truth state; a node's edges in **both**
  directions (`--links`); every edge of one type (`--edge supersedes`).
  Read-only, no network, no new index — it reads what was already generated.
  Answers "which plan decided this?" and "what is superseded?" (#272)
- **New**: configurable optional item fields. A `work_item_fields:` block in
  `.work/config.yml` switches fields on per team; `estimate`, `owner`, `risk`
  and `acceptance_criteria` default on, `value`, `confidence`, `due_date` and
  `severity` default off. A disabled field is **invisible** — its flag is
  never built, so it cannot appear in `--help` or anything an agent reads.
  The core (`priority`, `milestone`, `depends_on`, …) is deliberately not
  configurable: it is load-bearing for the roadmap and sync. `worklog fields`
  prints both populations with what each one means. (#108)
- **New**: `worklog changelog-draft` — drafts this section from git log since
  the last tag, grouped by commit type, excluding commits that touched only
  the log and generated files. Markdown on stdout, the commits it excluded on
  stderr. It never guesses the version. (#136)
- **New**: `worklog merge-rescue` — resolves a merge the resurrection guard
  blocked, by keeping the compacted side's log and re-emitting this branch's
  own events above the watermark. Uses the **merge base**, not the watermark,
  to decide what was genuinely already folded, and refuses to write if any
  item would disappear. (#269)
- **New**: one render seam for page naming and link syntax. `[[Page]]` is now
  the renderer's canonical notation, translated once at the output boundary,
  so a second wiki platform is a new class in `bin/wiki_flavor.py` rather
  than an edit to forty link sites. The renderer also reads `wiki.system`
  from config, which it never did. Only GitHub wiki ships. (#271)
- **New**: sync names the live ticket fields a push replaces, before and
  after, in its report and under `--dry-run`. One batched read per run rather
  than one per ticket, and it prints what that read cost. (#238)
- **Fix** (#284): the compaction watermark is now **per item**, and snapshots
  sort where their events were. The fold used to drop every event at or below
  one global mark computed as `max_ev` over the whole log — a time marker
  doing a content marker's job — so an event created on a branch before a
  compaction ran on main was discarded silently on merge. Two independent
  mechanisms caused it and both are fixed: the watermark is now recorded per
  item on each snapshot, and a snapshot sorts at that mark rather than at the
  moment the compactor wrote it, so a branch's later close applies on top of
  the snapshot instead of being erased by it. ADR-0007.
- **Fix** (#269): the merge guard's printed remedy could not be run from the
  state the guard creates, and the remedy it named would not have been safe.
  Recompacting mid-merge verifies `fold(new) == fold(old)` against a fold
  that has already discarded the branch's events — it would have passed, and
  made the loss permanent.
- **Fix**: `pre-commit` refuses any staged file containing a conflict marker,
  with no merge exemption. `commit-msg` exempts merge commits and nothing
  parsed `tests/` or `plugin/`, so a resolution that missed a hunk committed
  cleanly and was only found by running the suite.
- **Change**: `worklog` warns when two assistant sessions are active in one
  working directory, and the generated policy now says concurrent sessions
  belong in separate worktrees. Session identity comes from the harness,
  because the CLI is short-lived and has no stable pid. Advisory only — it
  never blocks a write. (#236)
- **Change**: locally-minted ULIDs carry the short git hash, so agents in
  different worktrees or branches mint visibly different, traceable ids.
- **Docs**: ADR-0005 (no custom merge driver), ADR-0006 (resurrected events
  are not always cosmetic) and ADR-0007 (the watermark is per item) record
  the merge-safety reasoning end to end, including where an earlier record
  was wrong and why.
- **Internal**: the plugin's harness-hook copies are now sync-checked
  (`HOOK_CANON`); that check immediately found real drift in
  `exit-plan-capture.sh`. Test suite 427 → 556.

## 0.18.0 — 2026-07-29

- **Fix** (github#226): two local items were allowed to own the same external
  ticket key, and `worklog sync` then overwrote that ticket with whichever item
  changed last — forever. The correctly linked item is hash-clean, so it is
  skipped and never repairs the damage, while the wrong one keeps re-pushing. In
  the reported case a cancelled duplicate marked a live P0 ticket **Done**, and
  hand-repairing the ticket did not hold because the next sync rewrote it. The
  failure was invisible from the log: `worklog fold` showed two items each with a
  perfectly valid `external` block. Three changes close it:
  - `worklog link` refuses a key another item already owns, naming that item and
    its title, and printing the two commands that move the ticket deliberately.
    The check is status-blind — a *cancelled* owner is among the most dangerous,
    because sync pushes a full update against its key and then closes the ticket.
    `--force` skips the check.
  - **New: `worklog unlink <item>`.** A mistaken `link` previously could not be
    undone through any supported command, which is a sharp edge in a log whose
    whole design is that mistakes are corrected by appending. It writes an empty
    `external` through the existing `link` op, so no fold change is needed and an
    un-upgraded clone applies it correctly too.
  - `worklog sync` refuses to push any ticket that more than one item claims. It
    skips just those items — corruption needs both pushed — so the rest of the
    run still syncs, prints the claimants and the repair as its own block rather
    than a `drift:` line, and exits non-zero. It fires under `--dry-run` too,
    since "0 creates on a dry run" is the documented migration acceptance gate.
- **Fix**: sync now records which ticket it last pushed an item to, not just the
  content hash. `external` is not part of that hash, so unlinking or re-pointing
  an item was previously a silent no-op at sync time and the damaged ticket was
  never repaired. Guarded so clones that predate the field do not re-push
  everything once.
- **Fix**: sync's automatic link after creating a ticket can no longer abort the
  run. It ran between "remote ticket created" and "link recorded", and since
  create-vs-update is decided purely by whether the item carries a key, dying
  there meant the next run filed a *second* live ticket.
- **Fix**: `worklog list` no longer raises on an item whose `external` is null,
  which a git merge or a hand edit can already produce.
- **Fix** (github#235): the GitHub adapter created an issue with `gh issue
  create`, which prints only the new URL, and then made a *second* call to read
  back the revision the contract requires. That read happens after the issue
  exists — so a rate limit there exited with the "transient, retry me" code, the
  dispatcher retried the whole push with `op` still `create`, and **each retry
  filed another issue**: one transient failure, up to four live duplicates.
  Create now goes through the REST endpoint, which returns the number, URL and
  revision together, leaving no window to fail in. The update path keeps its
  read-back deliberately — re-editing the same issue is idempotent, so a retry
  there costs a call, not a duplicate.

## 0.17.1 — 2026-07-28

- **Fix** (`bin/worklog`): `close`, `update` and `link` wrote their event under
  whatever id string the caller passed. Handed the 8-character prefix that
  `worklog show` and `worklog list` themselves print — the form the docs
  recommend — they appended an event under that short id, which folds into a
  brand-new phantom item while the real one goes untouched. `update` was worse:
  its current-state lookup returned `{}` for a prefix, so the taxonomy rules ran
  against `level=None` and the "closed items need `reopen`" guard never fired.
  All three now resolve through one shared `_resolve()` — the same lookup
  `reopen`/`resolve`/`show` already used — and an ambiguous prefix errors with
  the candidate ids instead of silently taking the first match. This repo's own
  log carries the scar: `01KYA8MD` is a ghost item minted exactly this way, and
  `trace-check`/`sync` have been skipping it as orphan drift ever since.
- **Fix**: the session-start doctor compared `core.hooksPath` against the
  literal string `hooks`, so a repo wired with the absolute path — the form that
  actually works from a git worktree, where a relative path resolves against the
  wrong CWD — was reported broken at the top of every session. Both doctors now
  accept any path resolving to the repo's own `hooks/`.

## 0.17.0 — 2026-07-27

- **New**: `docs/graph-engineering.md` — declares and evidences (real
  file:line citations, not marketing copy) that this repo already has the
  four "graph engineering" primitives: ULID node identity, `ia_graph.py`'s
  typed edges, `fold.py`'s event-sourced persistent state, and a modest
  inventory/publish-manifest index. Two diagrams, a short forward-looking
  section, and a matching README callout.
- **Fix** (`bin/worklog plan-capture`): the overwrite guard checked only
  `docs/plans/<today-UTC>-<slug>.md`, so it enforced "plans are never
  rewritten" only when the dates happened to line up — a plan captured in
  the evening from a timezone behind UTC could silently duplicate under
  tomorrow's date. The guard is now slug-scoped across all dates. Found and
  fixed upstream from a real incident in a downstream repo (PR #198).
- **Fix**: the slug-scoped guard's first pass used a bare `*-<slug>.md`
  glob, which matched by suffix rather than field boundary (a search for
  slug `migration` would also match `database-migration`) — caught in
  review before merging PR #198, now anchored on the fixed date shape.
- **Fix**: generated wiki Home linked `[[Design-Doc]]` but not its
  `[[Code-Walkthrough]]` pair, leaving walkthroughs unreachable from Home.

## 0.16.1 — 2026-07-26

Post-tag doc sync and a real bug fix for v0.16.0, landed on `main` after the
tag per the release process (docs and fixes never block a tag, they follow
it):

- **Fix**: `bin/sync_dispatch.py` crashed with `KeyError: 'key'` when a
  closed item that was never pushed to the tracker got forced into sync
  scope via `--keys` — the closed-item branch assumed a remote key already
  existed. It now creates the ticket first, links it, then closes, mirroring
  how the open-item branch already handles create-vs-update.
- Design doc and code walkthrough regenerated and frozen for v0.16.0.
- `docs/user_guide/plugin-guide.md` and `README.md` updated for the new
  `integration-guide` skill.

## 0.16.0 — 2026-07-26

Wiki-driven integration guides (plan
`docs/plans/2026-07-25-wiki-driven-integration-guides.md`, epic #164): a new
`integration-guide` skill points users at living, wiki-hosted setup guides
for tools this repo doesn't ship adapter code for, instead of hard-coding
that knowledge into the skill set.

- **New skill** `integration-guide`: on mention of Superpowers, GSD,
  SpecKit, OpenSpec, Jira, Confluence, GitHub, GitLab, Azure DevOps, AWS
  CodeCatalyst, or Google Cloud DevOps, fetches the matching
  `Integration-<Name>` wiki page, verifies it's the real page (a GitHub
  wiki redirects a missing slug to Home instead of 404ing — a naive
  fetch-succeeded check would be fooled by this), and falls back to a
  local copy under `docs/integrations/` if the fetch fails or fails
  verification. No new adapter or fetch code — built on `WebFetch` plus
  the existing `worklog wiki-add`/`wiki-publish` mechanism.
- **11 integration pages** (`docs/integrations/fallback-*.md`, published to
  the wiki): one fixed 10-section template per system. Only GitHub has a
  real, shipped adapter — the other six ticket/wiki systems are documented
  honestly as agent-researched-at-runtime, matching `ticket-sync`'s
  existing ADO-caveats tone; the four SDD tools are framed as
  compositional guidance, not technical integration, since nothing in this
  repo wires to them today. Jira and Confluence require reusing the
  existing `jira`/`confluence` skills rather than raw REST calls;
  Confluence additionally requires converting Mermaid/PlantUML diagrams to
  images before upload.
- **Meta index** at `docs/integrations/README.md` / wiki page
  `Integrations`, linking all 11 pages.

## 0.15.1 — 2026-07-25

- Doc fix: user-guide miscounted branch-discipline hook checks ("two more
  pre-commit checks" → "two more checks" — one is `pre-commit`, the other
  is the separate `commit-msg` hook). Found by `/code-review` (#160).

## 0.15.0 — 2026-07-25

Branch-discipline hooks (plan `docs/plans/2026-07-25-branch-discipline-hooks.md`):
main is now pull-only, and every commit must be traceable to a worklog item
or ticket.

- **Branch guard** (`hooks/pre-commit`): rejects a commit authored directly
  on `main`/`master`. Exempt for a real reconciliation merge (`git merge
  origin/main`) via `WORKLOG_MERGE_COMMIT`, set by `pre-merge-commit` before
  it exec's into `pre-commit` — `MERGE_HEAD` is not yet on disk at the point
  git invokes `pre-merge-commit` (only appearing later, before `commit-msg`
  fires), so a MERGE_HEAD-only check would have missed this case.
  `WORKLOG_SKIP_BRANCH_GUARD` covers the handful of existing bare
  (non-commit) invocations of this script (`worklog doctor`, CI's
  `--no-verify` backstop) that would otherwise false-positive on `main`.
- **`hooks/commit-msg`** (new): requires a 26-char Crockford ULID or a
  `#123` ticket reference in every commit message; exempt for merge
  commits.
- Wired end-to-end: `worklog init`'s hook-copy loop and CI template,
  `worklog uninstall`, `worklog doctor`'s health check, and a new
  PR-scoped CI step validating every commit message in the PR range.
- `release` skill's "direct-commit repos" landing mode removed — dead once
  this ships; releases land as a PR like everything else now.

## 0.14.0 — 2026-07-24

Artifact-pages epic (plan `docs/plans/2026-07-24-artifact-pages.md`): the IA
content model now covers tickets, PRs, and releases, not just docs.

- **Ticket pages** (`worklog ia-render` → one page per work item under
  `docs/.index/rendered/tickets/`): own description/status, upward hierarchy
  to the epic, downward children with an aggregate progress rollup, linked
  PRs, linked release — `render_item_page()`, branching by level rather than
  four near-duplicate renderers. New `worklog ia-ticket <ULID>` preview
  command.
- **Release pages**: a Change Log section derived from the graph
  (milestone-tagged closed items plus their linked PRs), not a
  `CHANGELOG.md` parser — this file stays human-authored prose. Plus a
  Release Tree, Related PRs/Tickets, and Dependencies & Risks.
- **PR pages**: linked tickets, related release, traceability back to the
  root epic. Files-changed/review/CI status render as "not tracked" —
  fetching live PR metadata is scoped out to a separate follow-up
  (`worklog pr-sync`, not built in this release).
- Published-page manifest grew from 51 to 252 entries.
- Two bugs found while building this, filed but not yet fixed: `worklog
  close`/`update` don't resolve item-id prefixes the way `reopen` does
  (a short, valid prefix silently creates an orphan item instead of
  resolving to the real one); the reader-plane `banner()` mislabels every
  frozen "current" doc as a status report regardless of its actual
  `doc_type` (verified live on 12 of 14 published plan pages).

## 0.13.0 — 2026-07-23

IA & content model wave (plan `docs/plans/2026-07-22-ia-content-model.md`,
PR #104) plus follow-on schema and reliability fixes. Wiki-ticket UI tracking
moved to `wiki_ticket_sdd_ui` and is not shipped in this plugin.

- **Doc identity & schema (Phase 0):** unified `schema/doc.schema.json`,
  `worklog wiki-key`, `worklog ia-inventory`, migration helpers for stable
  `wiki_key` / `truth_state` frontmatter.
- **Normalize + warn gates (Phase 1):** `worklog ia-normalize` writes sidecars
  for frozen docs and in-place frontmatter for live ones; CI/hooks warn on
  missing/duplicate `wiki_key` and invalid frontmatter (hard-fail deferred to
  Phase 5).
- **Reader plane (Phase 2):** `worklog ia-render` + `ia-manifest` generate
  Home, Sidebar, and `publish-manifest.json`; wiki-publish consumes the
  manifest and strips YAML frontmatter at publish time so GitHub Wiki pages
  stay clean.
- **Indexes (Phase 3):** generated Decisions / Releases / Status Archive
  indexes wired into release and plan-capture flows.
- **Traceability (Phase 4):** typed-edge graph (`ia-graph`), `worklog link-pr`,
  `worklog trace-check` (warn by default, `--strict` pre-release), rich
  ticket bodies via `worklog ticket-body`.
- **Schema boundary (PR #112):** split document schema from entity/item
  schema — documents vs work items no longer share one overloaded schema.
- **Skills:** new `issue-description` and `pr-description` skills for
  durable ticket and PR prose.
- **Fixes:** pre-commit no longer dirties the tree with `bin/__pycache__`
  (`PYTHONDONTWRITEBYTECODE`); compaction snapshot writes folded state
  verbatim so closed orphans no longer abort verify; ticket bodies required
  and readable for junior devs/PMs (spec §13.4); `init.sh` installs IA
  modules; classify skips folder READMEs under plans/status/adr.

## 0.12.1 — 2026-07-21


- Dirty close syncs fields first: the dispatcher now pushes an `update`
  before the `close` verb when a closing item's hash is dirty, so remote
  labels/milestone/title match the final local state. Previously a
  reclassify-then-close left stale remote taxonomy labels that the next
  pull re-ingested over the local edit (#76).

## 0.12.0 — 2026-07-21

- Pull sync ingests taxonomy: the dispatcher's `INGEST_FIELDS` gains
  `level`/`kind`/`milestone`, so remote taxonomy edits (labels, milestone)
  land in the local log instead of being silently dropped. The GitHub
  adapter already round-tripped them; the dispatcher tuple was the gap.
- `worklog reopen <ulid>`: emits the `reopen` op the fold always supported —
  moves a closed item back to `todo` and drops the stale `resolution` in one
  event. `update --status` on a closed item is now refused with a pointer to
  `reopen` (the old path left the resolution behind).
- `sync.conflict_policy` descoped to `report` only: `local-wins` /
  `remote-wins` were documented but never read by the dispatcher, and
  `report` + `worklog resolve` covers the need without silent overwrites.
  Config and spec updated; auto-resolve returns only via a new plan.
- First release exercising the design-docs release-time doc sync
  (`release.sync_docs`) end to end.

## 0.11.0 — 2026-07-19

- System enums widened and documented as advisory (spec v1.8): ticketing
  `github | gitlab | jira | ado | linear | codecatalyst | other | none`, wiki
  gains `gitlab-wiki` and `other`. `bin/worklog` branches only on `none`;
  every other value is a name the edge skills resolve to available tooling,
  and `other` is the sanctioned value for unlisted systems (real name in
  `options:`).
- Caveats ride with the names in ticket-sync: AWS CodeCatalyst (ADO's AWS
  equivalent) closed to new customers 2025-11-07; Linear detected via
  CLI/MCP, not git remotes; GCP has no native tracker — no `gcp` value.
- Azure DevOps field-tested caveats in ticket-sync + adapters/README: tag
  markers (ADO strips HTML comments), merge-never-overwrite updates,
  link-first migration with the `sync --dry-run` 0-creates gate.
- /worklog:init: detection knows codecatalyst.aws and CLI/MCP-only trackers;
  pick-and-mix lists gain Linear, CodeCatalyst, and `other`.

## 0.10.0 — 2026-07-19

- Stop hook: untracked files no longer count as unrecorded work (-uno) — the
  actual root cause of the false blocks; #46's settle guard kept as hardening.
- Stop hook: settle-and-recheck + branch-stability guard — no more false blocks
  when a background merge chain flips branches mid-invocation (observed 3x).

## 0.9.0 — 2026-07-19

- Mermaid visual roadmap: `roadmap-render --viz=deps,hierarchy,gantt|all|none`
  (default deps,hierarchy; `--no-viz` alias) appends a generated
  "## Visual roadmap" section — dependency graph, hierarchy, and an
  event-dated gantt whose bars come from create/first-in_progress/close ULID
  timestamps (historical fact, no invented dates; "now" = max event, never
  wall clock). `/worklog:viz` regenerates with `--viz=all` in a background
  subagent and republishes the roadmap.
- Grok Build: PORTS.md/README/plugin-guide upgraded to full native
  compatibility, zero configuration, per the xAI docs (verification under
  Grok Build pending).
- features.auto_merge_on_green flag (default ON): advisory mode polls, reports
  green, and leaves the merge to a human; --auto/--advisory and
  WORKLOG_AUTO_MERGE override per run; doctor reports it.
- CLI rejects empty item ids (update/close/link/ingest/conflict/resolve/show).

## 0.8.0 — 2026-07-19

- Architecture Decision Records: schema-validated docs/adr/ (worklog adr
  new|list|check, pre-commit/CI guard), write-once bodies with sanctioned
  status/superseded_by mutation, wiki-synced with republish-on-change.
  Seeded with ADR-0001..0003 from the project's real decisions.
- Dispatcher: orphan/untitled items are drift-reported, never pushed.

## 0.7.0 — 2026-07-19

- Work taxonomy (plan 2026-07-18): four orthogonal axes — level (epic/story/task/
  subtask), kind (feature/bug/ops/triage, triage is the visible default), milestone
  (the release axis), planned/unplanned. Legacy `type` is a deprecated alias the
  fold normalizes and compaction migrates physically. Canonical hash gains the new
  fields (one-time sync churn).
- CLAUDE.md taxonomy block (marker-idempotent, consented at /worklog:init; AGENTS.md
  symlink carries it to every harness). Inline item proposals are the default path.
- Flag-gated classifier (off by default): Stop hook gains a propose-only mode, the
  classify skill stages suggestions in .work/suggestions.jsonl, `worklog promote`
  is the only path from suggestion to log.
- Roadmap: Needs-classification queue, kind mix per epic, milestone grouping with
  derived epic milestones. Adapters map kind→labels and milestone→GitHub milestones.
- Spec v1.7; migration doc; pre-commit/CI enforce taxonomy rules; README + user
  guide fully refreshed (no stub-era language remains).

## 0.6.0 — 2026-07-19

- Green-gates merge policy: /worklog:merge + merge-green skill + merge-when-green.sh
  poll loop (5-min default) — PRs merge only when every check passes; never bypass.
- Typed adapter contract (plan 2026-07-18): bin/sync_dispatch.py owns every sync
  invariant (capabilities gate, scope, create-vs-update, marker idempotency, echo
  suppression, §3.6 exit-code handling, conflicts, drift report); adapters are dumb
  translators — shipped fake (CI double) + github worked example; worklog adapter
  init|check; worklog sync is real — no stubs remain.
- Spec v1.6: §8.1 hosted-platform merge caveat + recovery; §9.5 typed contract layer.
- CI coverage gate: >=80% enforced on bin/*.py, target 95% (CLAUDE.md policy).
- ticket-sync skill delegates invariants to the dispatcher; per-system notes moved
  to adapters/README.md.

## 0.5.0 — 2026-07-18

- release skill: cutting a release is a wiki-ticket capability (stamp,
  snapshot, tag, platform release, publish, sync).
- Pull sync: `worklog ingest` (deterministic ev per spec §10.2 — identical polls
  dedupe across clones), `worklog conflict`, `worklog resolve --take local|remote`;
  fold clears conflicts when a later event writes the field. ticket-sync is now
  push AND pull with §10.3 echo suppression.
- Spec v1.5: adapter strays purged; pull CLI documented; §18 step 8 done.
- wiki-publish: per-system guidance (GitHub/GitLab/ADO/Confluence) + ledger field
  semantics across systems.
- Harness ports: /worklog:init scaffolds the AGENTS.md symlink; plugin/PORTS.md
  matrix — Codex/OpenCode work today with zero port.

## 0.4.0 — unreleased

- Compaction (`bin/compact.py`, `worklog compact --yes`) per spec §7 with fold-equality
  verification; nightly CI job commits `chore(worklog): compact through <watermark>`.
- `worklog status --kind daily|weekly` (`--emit-facts` / `--write`, frozen reports) +
  status-report skill. Timecard deferred on spec §17 open question 4.
- ticket-sync closes remote tickets when local items close (external.dirty scope).
- plan-capture publishes tickets + wiki via a background subagent — never blocks.
- Spec v1.4: §9 rewritten to skill-based edges.

## 0.3.0 — unreleased

- `worklog link`: attach external identities to work items via §5.3 link events.
- `worklog wiki-add`: register documents in the wiki publish set.
- ticket-sync skill: push-only sync to external trackers with ULID-marker
  idempotency; GitHub via `gh`, system-vague guidance elsewhere.
- /worklog:init system detection: confident yes/no path, multi-select
  pick-and-mix, upgrade skip.
- wiki-publish: default publish set + `source` field in the ledger.

## 0.2.0 — unreleased

- `worklog roadmap-snapshot` subcommand.
- `wiki-publish` skill: system-agnostic wiki publishing with a `published.json` ledger.
- Dogfood enforcement hooks: UserPromptSubmit reminder, Stop worklog check,
  SessionStart doctor-lite.
- Plugin installer/uninstaller scripts.
- User guide + README; docs live in the repo/wiki, deliberately NOT packaged
  in the plugin.

## 0.1.0 — unreleased

- Plugin scaffold: manifest, design captured as tracked work items
  (`docs/plans/2026-07-18-claude-plugin.md` in the source repo).
- `worklog --version`; version recorded in scaffolded repos and checked by `/worklog:doctor`.
