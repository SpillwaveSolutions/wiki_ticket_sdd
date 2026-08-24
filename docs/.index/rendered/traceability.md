# Traceability

_The evidence chain: plan → item → ticket → code → release, forward and backward. Generated from `docs/.index/_graph.json`; do not edit._

### Release v0.24.5 mermaid-first design docs
`01M0TQ90FYZXRJ637E58FCT5WJ` · status: in_progress
- targets: release/v0.24.5

### Phase 2-3 style plugins + AGER polish
`01M0KCDVAYS67SPN8FHAYY4DWX` · status: in_progress
- belongs-to: multi-host plugin matrix + three-host hooks

### Phase 1 ContentPack three-host hooks
`01M0KCDV94P4YPBXJXQZNNGQTM` · status: in_progress
- belongs-to: multi-host plugin matrix + three-host hooks

### Phase 1 foundation + wiki_ticket_sdd hosts
`01M0KCDV7AQEQ61TA2MYN3M5C3` · status: in_progress
- belongs-to: multi-host plugin matrix + three-host hooks

### Phase 0 shared three-host hook template
`01M0KCDV5GP8BMZT142MMAPAG7` · status: in_progress
- belongs-to: multi-host plugin matrix + three-host hooks

### multi-host plugin matrix + three-host hooks
`01M0KCDKJRAZYMWDD9PFGHC6XY` · status: in_progress
- contains: Phase 0 shared three-host hook template
- contains: Phase 1 foundation + wiki_ticket_sdd hosts
- contains: Phase 1 ContentPack three-host hooks
- contains: Phase 2-3 style plugins + AGER polish

### Release v0.24.3
`01M0B004MDMSVF1VT3F4PCCPKV` · status: done

### No way to restrict a sync to specific items -- --keys widens scope, it cannot narrow it
`01M09DV3XKWJV5VVNYPJC9PRVF` · status: done

### Bot pushes to main skip CI, so a broken main goes unnoticed
`01M09DEB5YMZRHRBZB8GADMKY0` · status: done
- references: [github#361](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/361)

### Scheduled compaction pushes a stale IA manifest and roadmap to main
`01M095WZRZC0J94D3FDZV9Q7V0` · status: done

### Wave C: require identity on knowledge-tree writes
`01M06BRQPQ8408XTDYTMY2JYFE` · status: done
- references: [github#356](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/356)
- targets: release/v0.24.1

### Stop hook cannot see work that was recorded and then committed
`01M032YRXR61XAJBBNP355AVQW` · status: done
- references: [github#352](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/352)

### Stop hook accuses a correctly-logged worktree session of skipping the log
`01KZY2EVJMFERMM4PGPKM0QE58` · status: done
- references: [github#349](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/349)

### Fix TestStrictIsPassable dependency on ambient git clone depth
`01KZY0B9KQBKH6NFGBA0YFSYQA` · status: done

### doc-verify --strict is un-passable once a frozen doc carries a fabricated citation
`01KZWHQN8AHWFBC7JV4N6XPVNK` · status: done

### Cut v0.23.0 release
`01KZD8FBVV2AP9JKMMCX1YWDEP` · status: done
- targets: release/v0.23.0

### The citation warning fires on every commit and can never clear
`01KZCZQ2561TW1BPT3Z9AM75SZ` · status: done
- targets: release/v0.23.0

### Composite item ids write junk events on the non-resolving sync commands
`01KZCYXC49J4M5NECS620EFXNB` · status: done
- targets: release/v0.23.0

### Compaction hides shipped work from the status report
`01KZCCG7010S0Q0Y6PF6NN27C2` · status: done
- targets: release/v0.23.0

### doc-verify accepts a citation whose range is merely close
`01KZCC0F3QYFX9QAKTYVZ01TFK` · status: done
- targets: release/v0.23.0

### Cut v0.22.2 release
`01KZC9JZTS96R2VSNDYBHR2NVF` · status: done
- targets: release/v0.22.2

### Sweep every test file for the mid-file runner block
`01KZC9CB5VY2YDCNDYN3W3QK6Y` · status: done
- targets: release/v0.22.2

### Three test suites still hide 15 tests behind a mid-file __main__ block
`01KZC83EFJV7S63VAXTPRB2YH3` · status: done

### v0.22.1 doc sync: user guide + README
`01KZC7BEN8HXMT90Q4P033YA0Q` · status: done
- targets: release/v0.22.1

### v0.22.1 doc sync: design doc + code walkthrough
`01KZC7BEFK020YSGQSBB1Z70PX` · status: done
- targets: release/v0.22.1

### Cut v0.22.1 release
`01KZC4C33K1X5T6K79B9E4D3XY` · status: done
- targets: release/v0.22.1

### A test asserted the broken hook manifest shape
`01KZC47J5M7K96TRWY0X5X53P6` · status: done
- targets: release/v0.22.1

### Plugin hooks never fired: the manifest was not wrapped
`01KZC47J0FF1EBGD1JH3GP28RQ` · status: done
- targets: release/v0.22.1

### Cut v0.22.0 release
`01KZ9N0EX7AE9HMYZ84NRMAESP` · status: done
- targets: release/v0.22.0

### A stray main block hides seven dispatcher tests
`01KZ9MD733ZEBNT3B2X1672FB0` · status: done
- targets: release/v0.22.0

### merge-rescue can invert an item's state
`01KZ9KGE49EAS3VEFDNFTVM1PV` · status: done
- targets: release/v0.22.0

### Restore the file patterns in two skill descriptions
`01KZ9JTCGG2QJYXW973RJCWDR2` · status: done
- belongs-to: Add native Codex plugin compatibility
- targets: release/v0.22.0

### Open the 0.22.0 changelog section and bump the version lockstep
`01KZ9JTCBS4W06FVSHZPZMQHCE` · status: done
- belongs-to: Add native Codex plugin compatibility
- targets: release/v0.22.0

### Ship the worklog hooks to Codex, not just the skills
`01KZ9JTC6VAC8105JAGT0WRYVH` · status: done
- belongs-to: Add native Codex plugin compatibility
- targets: release/v0.22.0

### Codex PR: regenerate the index so CI goes green
`01KZ9JTC1SPC6PHXHE6RAGDW9G` · status: done
- belongs-to: Add native Codex plugin compatibility
- targets: release/v0.22.0

### Add native Codex plugin compatibility
`01KZ721Y7CM5Q0NTQC31QB2HGS` · status: done
- targets: release/v0.22.0
- contains: Codex PR: regenerate the index so CI goes green
- contains: Ship the worklog hooks to Codex, not just the skills
- contains: Open the 0.22.0 changelog section and bump the version lockstep
- contains: Restore the file patterns in two skill descriptions

### v0.21.0 doc sync: user guide + README
`01KZ70HNTMN1AQHSX32XZ1J2X9` · status: done
- targets: release/v0.21.0

### v0.21.0 doc sync: design doc + code walkthrough
`01KZ70HNMFKYY9KZ0VXVAMD7S5` · status: done
- targets: release/v0.21.0

### Cut v0.21.0 release
`01KZ5CZ2JGGGY1G6QBKFBXW4AW` · status: done
- targets: release/v0.21.0

### Design-docs regeneration does not verify its own citations
`01KZ4EETMXD1JQMDFA97HSZQM4` · status: done

### Sync's dry run does not report the field overwrites a close would make
`01KZ31DGAQ2YDP6RMEMVNAWABH` · status: done
- references: [github#320](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/320)

### Add a full-length commit helper that mirrors the existing environment contract
`01KZ30X6JEXH4TTKHDNV3ZW0Q2` · status: done
- belongs-to: Stamp the authoring commit onto plans, status reports and new decision records
- references: [github#316](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/316)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Separate a fabricated citation from one that merely drifted
`01KZ30X6JEWCD74E81Y555DAYP` · status: done
- belongs-to: Verify document citations against the commit the document was written against
- references: [github#315](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/315)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Document the two new fields in the document schema
`01KZ30X6JEH1Z7D5AC5ZAMM5V8` · status: done
- belongs-to: Stamp the authoring commit onto plans, status reports and new decision records
- references: [github#314](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/314)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Verify document citations against the commit the document was written against
`01KZ30X6JEF29Z5AEEWXBSJWHV` · status: done
- belongs-to: Git provenance on generated docs, and the verifier it enables
- references: [github#313](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/313)
- contains: Record that document provenance depends on merge commits, not squash merges
- contains: Refuse to fall back to the current checkout when the recorded commit cannot be resolved
- contains: Separate a fabricated citation from one that merely drifted
- produced-by: [[Plan-doc-provenance-and-verification]]

### Refuse to fall back to the current checkout when the recorded commit cannot be resolved
`01KZ30X6JEETVQZG7YYFM7B998` · status: done
- belongs-to: Verify document citations against the commit the document was written against
- references: [github#312](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/312)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Stamp the authoring commit onto plans, status reports and new decision records
`01KZ30X6JECK0M9G04ZHMS4SMA` · status: done
- belongs-to: Git provenance on generated docs, and the verifier it enables
- references: [github#311](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/311)
- contains: Document the two new fields in the document schema
- contains: Add a full-length commit helper that mirrors the existing environment contract
- produced-by: [[Plan-doc-provenance-and-verification]]

### Record that document provenance depends on merge commits, not squash merges
`01KZ30X6JEBXN08HQTQ77ESSTV` · status: done
- belongs-to: Verify document citations against the commit the document was written against
- references: [github#310](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/310)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Run the backfill from the release routine rather than a git hook
`01KZ30X6JE8542ERDW1B8A9P8H` · status: done
- belongs-to: Backfill the merge commit onto documents once they land on the default branch
- references: [github#309](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/309)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Record build provenance once on the publish manifest rather than on every rendered page
`01KZ30X6JE1ERVS43QVXEEGVXA` · status: done
- belongs-to: Git provenance on generated docs, and the verifier it enables
- references: [github#308](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/308)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Backfill the merge commit onto documents once they land on the default branch
`01KZ30X6JE0QSQF6BE8S0YRPBW` · status: done
- belongs-to: Git provenance on generated docs, and the verifier it enables
- references: [github#307](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/307)
- contains: Run the backfill from the release routine rather than a git hook
- produced-by: [[Plan-doc-provenance-and-verification]]

### Teach the wiki publisher's frozen-document guard to read it, in both skill trees
`01KZ30X6JDYF6YQWN6WYMVQ5Y4` · status: done
- belongs-to: Hash the document body, not the whole file, when deciding what to republish
- references: [github#306](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/306)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Add a body-only hash and use it for pages published with a banner
`01KZ30X6JDXDZ38RY6AQEYE7VY` · status: done
- belongs-to: Hash the document body, not the whole file, when deciding what to republish
- references: [github#305](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/305)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Keep the newest event object during the scan without changing the existing helper's signature
`01KZ30X6JDSYHB6FQB7RRCGKQQ` · status: done
- belongs-to: Record on the roadmap which commit its data came from
- references: [github#304](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/304)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Pin the rule that a roadmap snapshot inherits the roadmap's provenance
`01KZ30X6JDHPRBESZDQ2CSNJZ2` · status: done
- belongs-to: Record on the roadmap which commit its data came from
- references: [github#303](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/303)
- produced-by: [[Plan-doc-provenance-and-verification]]

### Hash the document body, not the whole file, when deciding what to republish
`01KZ30X6JD7M4XV6Y5194E1D32` · status: done
- belongs-to: Git provenance on generated docs, and the verifier it enables
- references: [github#302](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/302)
- contains: Add a body-only hash and use it for pages published with a banner
- contains: Teach the wiki publisher's frozen-document guard to read it, in both skill trees
- produced-by: [[Plan-doc-provenance-and-verification]]

### Record on the roadmap which commit its data came from
`01KZ30X6JD06D11ACPVF8Q5GMW` · status: done
- belongs-to: Git provenance on generated docs, and the verifier it enables
- references: [github#301](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/301)
- contains: Pin the rule that a roadmap snapshot inherits the roadmap's provenance
- contains: Keep the newest event object during the scan without changing the existing helper's signature
- produced-by: [[Plan-doc-provenance-and-verification]]

### Git provenance on generated docs, and the verifier it enables
`01KZ30X6HZ6FKJXJX386J44CB1` · status: done
- references: [github#300](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/300)
- contains: Record on the roadmap which commit its data came from
- contains: Hash the document body, not the whole file, when deciding what to republish
- contains: Backfill the merge commit onto documents once they land on the default branch
- contains: Record build provenance once on the publish manifest rather than on every rendered page
- contains: Stamp the authoring commit onto plans, status reports and new decision records
- contains: Verify document citations against the commit the document was written against
- produced-by: [[Plan-doc-provenance-and-verification]]

### Correct the v0.20.0 republish claim in the next release notes
`01KZ2PJZF067ZS4YW231C1FM28` · status: done
- references: [github#299](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/299)

### Cut release v0.20.0
`01KZ2MZ69SFQDHEXFBJTXTDNFX` · status: done
- targets: release/v0.20.0

### Generated design docs quote code that no longer exists; nothing verifies their claims
`01KZ2M75CEXBQHFN1AG1Z8A2YB` · status: done
- references: ticket/github#294

### Run the v0.19.1 release doc sync
`01KZ2M07FKC9AYK84B7AC91TVP` · status: done
- targets: release/v0.19.1

### Run the v0.19.1 release doc sync
`01KZ2M00NVDWJN795G7F8CWTRJ` · status: cancelled
- targets: release/v0.19.1

### Frozen plan pages render a status-report banner that ignores the plan's own status
`01KZ2KGPRMKG9B98Q6YVD3MZVJ` · status: done
- lands-in: pr/293
- references: ticket/github#292
- targets: release/v0.20.0
- produced-by: [[Plan-plan-banner-state]]

### CLAUDE.md and AGENTS.md are not tracked in the source repo
`01KZ2JRT7MAE0MJH7Y0SJ3ZJS3` · status: done

### trace-check --strict ignores its own released-milestone scope
`01KZ2JAT7PCV6B34W2RK34WBX7` · status: done
- lands-in: pr/293
- references: ticket/github#291
- targets: release/v0.20.0
- produced-by: [[Plan-trace-check-scope]]

### Cut release v0.19.1
`01KYZNRRNFBWHA8452CNFKH6XV` · status: done
- targets: release/v0.19.1

### Restore full ULID entropy; record git provenance as its own event field
`01KYZNG520D5E9AVN2X1C0BQ3E` · status: done

### link-pr and pr-sync accept an id prefix and write a phantom sidecar
`01KYZFMZ5CF79DAYHMNKXSAZ5K` · status: done

### Cut release v0.19.0
`01KYZFF99YF79DAN4V33HXC7AE` · status: done
- targets: release/v0.19.0

### Stamp generated ULIDs with the short git hash so concurrent branches diverge
`01KYZER08G7NSQ6CFQ9QWFZFTJ` · status: done
- lands-in: pr/286

### Conflict markers can reach a commit: the merge exemption plus unparsed tests
`01KYZEC0C1MGQXQSH61ZPDD0YZ` · status: done
- lands-in: pr/286

### Compaction watermark can silently drop branch-local events the snapshot never folded
`01KYZ5CY9PS60BYH1E07DF5C9P` · status: done
- lands-in: pr/286
- references: [github#284](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/284)

### Fix the thing from #98
`01KYWJ6YGQMMHQ58G9CNAF6F00` · status: cancelled

### worklog find: search the generated inventory and graph from the CLI
`01KYWGM3W958F3QK4HB52X1Q1X` · status: done
- belongs-to: IA reader plane: platform-portable rendering and document search
- lands-in: pr/281
- references: [github#272](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/272)

### Extract a render adapter seam so page naming is not hardcoded to Gollum
`01KYWGM3R13Q33YZ3PJA3V7QMD` · status: done
- belongs-to: IA reader plane: platform-portable rendering and document search
- lands-in: pr/282
- references: [github#271](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/271)

### IA reader plane: platform-portable rendering and document search
`01KYWGM3KPNQNSWV03FRG23ADB` · status: done
- lands-in: pr/283
- references: [github#270](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/270)
- contains: Extract a render adapter seam so page naming is not hardcoded to Gollum
- contains: worklog find: search the generated inventory and graph from the CLI

### Merge guard's printed remedy cannot be run from the state it creates
`01KYWGJD1QCQRM6V6S0MWN5SCW` · status: done
- lands-in: pr/277
- references: [github#269](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/269)

### Record the decision not to build a custom merge driver
`01KYTJGK2XYHW1BT3Y1XH1YNP7` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#266](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/266)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Abort the run when the whole project is unreachable
`01KYTJGK2XSA2C4H72SKP8F34D` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#265](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/265)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Forget the gone marker once a ticket answers again
`01KYTJGK2XMY73EJMZ026Q573G` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#264](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/264)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Fix the fused version fence in every shipped skill
`01KYTJGK2XJSCMJ9K16YDXXMD2` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#263](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/263)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Run the log merge guard in continuous integration
`01KYTJGK2XJD516RXMZ52PDZP1` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#262](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/262)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Add the merge-guard tests to the integration test list
`01KYTJGK2XDTKNHGH8QTHBHCTY` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#261](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/261)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Split the phase-five container into a new epic
`01KYTJGK2XDQVAZ85ZEH92NGGW` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#260](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/260)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Remove the unreachable sort tiebreak in the fold
`01KYTJGK2X98H9T7VVR879B0XC` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#259](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/259)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Record the decision that clearing a dead ticket link stays manual
`01KYTJGK2X7FFZC5BCYF2BPSSF` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#258](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/258)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Bring skill copies under the byte-for-byte sync check
`01KYTJGK2X7FC4PTAMH60ECY36` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#257](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/257)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Expose the two item fields the specification already declares
`01KYTJGK2X700NYTZHB0JDE6Q1` · status: done
- belongs-to: Close both P1 epics, settle the merge-strategy and GONE questions
- references: [github#256](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/256)
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Close both P1 epics, settle the merge-strategy and GONE questions
`01KYTJGK2WMX6PNMYQDFFFPGTP` · status: done
- references: [github#255](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/255)
- contains: Expose the two item fields the specification already declares
- contains: Bring skill copies under the byte-for-byte sync check
- contains: Record the decision that clearing a dead ticket link stays manual
- contains: Remove the unreachable sort tiebreak in the fold
- contains: Split the phase-five container into a new epic
- contains: Add the merge-guard tests to the integration test list
- contains: Run the log merge guard in continuous integration
- contains: Fix the fused version fence in every shipped skill
- contains: Forget the gone marker once a ticket answers again
- contains: Abort the run when the whole project is unreachable
- contains: Record the decision not to build a custom merge driver
- produced-by: [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]]

### Settled orphan debris is reported as drift on every sync run
`01KYTGNS76Z1YRA64QMARYSWJM` · status: done

### Priority change leaves the old priority label on the ticket
`01KYTDN3W67ZFFDE1F60M2ST6T` · status: done
- references: [github#253](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/253)

### Prune merged branches and orphaned worktrees after v0.18.0
`01KYT66K7YA68DB5WF3B0P625B` · status: done

### Release v0.18.0
`01KYNKBCNS8WY5BH2B7EDBHMF1` · status: done
- targets: release/v0.18.0

### Log compaction is silently undone by any branch that spans it
`01KYNHEW47G49CWZ9SS9ABQ2VG` · status: done
- references: [github#243](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/243)

### Warn at plan capture when a task title references a ticket number
`01KYNHEVZSBJ43P0CE2EBXT7Y0` · status: done
- references: [github#242](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/242)

### A ticket that no longer exists remotely retries forever
`01KYNHEVVG57D20ZG5EJ3F36J3` · status: done
- references: [github#241](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/241)

### Conflict and resolve accept any field name, including ones that break sync
`01KYNHEVPZJZFB9HPHA68K2XBZ` · status: done
- references: [github#240](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/240)

### Restrict a ticket to one item when forcing keys into scope
`01KYNHEVJNZTGEJ2EW5A9C9A7C` · status: done
- references: [github#239](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/239)

### Sync should say which ticket fields it is about to overwrite
`01KYNHEVDSD4BTASXCTV88Q80Q` · status: done
- lands-in: pr/280
- references: [github#238](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/238)

### Catch duplicate ticket ownership at merge time, not just at sync
`01KYNHEV9M01PQJZQ5QRZQ3C8J` · status: done
- references: [github#237](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/237)

### Concurrent sessions in one working directory corrupt each other's work
`01KYNHEV5GCR1MDNECAXFT0GK2` · status: done
- lands-in: pr/278
- references: [github#236](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/236)

### GitHub adapter can file duplicate issues when rate-limited mid-create
`01KYNHEV1BJ48RKWHTXCJYVRAF` · status: done
- references: [github#235](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/235)
- targets: release/v0.18.0

### Add a command to undo a link
`01KYND4SNPXVR1W4GQA453VB4G` · status: done
- belongs-to: One local owner per remote ticket (#226)
- references: [github#233](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/233)
- targets: release/v0.18.0
- produced-by: [[Plan-one-owner-per-external-key]]

### Make undoing or moving a link actually re-push
`01KYND4SNPH307DFDEE9BJ0ZZ4` · status: done
- belongs-to: One local owner per remote ticket (#226)
- references: [github#232](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/232)
- targets: release/v0.18.0
- produced-by: [[Plan-one-owner-per-external-key]]

### Keep sync's automatic linking from ever aborting a run
`01KYND4SNPG1HFE8E0P7F7K7PF` · status: done
- belongs-to: One local owner per remote ticket (#226)
- references: [github#231](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/231)
- targets: release/v0.18.0
- produced-by: [[Plan-one-owner-per-external-key]]

### Refuse a duplicate external key when linking
`01KYND4SNPF2DYKSMDG4NJ39CF` · status: done
- belongs-to: One local owner per remote ticket (#226)
- references: [github#230](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/230)
- targets: release/v0.18.0
- produced-by: [[Plan-one-owner-per-external-key]]

### Update the mirrored copies, the docs and the changelog
`01KYND4SNPBAW2A1H0GPHDGT0E` · status: done
- belongs-to: One local owner per remote ticket (#226)
- references: [github#229](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/229)
- targets: release/v0.18.0
- produced-by: [[Plan-one-owner-per-external-key]]

### Stop sync from pushing a ticket that two items claim
`01KYND4SNP68XAJ30Q4PY4VV11` · status: done
- belongs-to: One local owner per remote ticket (#226)
- references: [github#228](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/228)
- targets: release/v0.18.0
- produced-by: [[Plan-one-owner-per-external-key]]

### One local owner per remote ticket (#226)
`01KYND4SNNVYRAEQ958HK83W72` · status: done
- references: [github#226](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/226)
- contains: Add an external-key ownership map to the fold
- contains: Stop sync from pushing a ticket that two items claim
- contains: Update the mirrored copies, the docs and the changelog
- contains: Refuse a duplicate external key when linking
- contains: Keep sync's automatic linking from ever aborting a run
- contains: Make undoing or moving a link actually re-push
- contains: Add a command to undo a link
- produced-by: [[Plan-one-owner-per-external-key]]

### Add an external-key ownership map to the fold
`01KYND4SNNCPZ7R2NWFD7QXYTJ` · status: done
- belongs-to: One local owner per remote ticket (#226)
- references: [github#227](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/227)
- targets: release/v0.18.0
- produced-by: [[Plan-one-owner-per-external-key]]

### Release procedure omits the re-index required after publishing to the wiki
`01KYKDGW7HJMRQ2KKF02M8CAAW` · status: done
- references: [github#224](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/224)

### Version lockstep check does not cover the README version marker
`01KYKDGW3DFDEQ1DEDFR6N45SM` · status: done
- references: [github#223](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/223)

### Roadmap hides epics whose children are all closed but which are still open
`01KYKDGVZ4C7FSCY7GJNGPV0Q5` · status: done
- references: [github#222](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/222)

### roadmap-snapshot freezes whatever is on disk instead of rendering first
`01KYKDGVTYMZ0E84BVBC29FTJY` · status: done
- references: [github#221](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/221)

### Release v0.17.1
`01KYKATVGM10E5HVZHVPA1C5J0` · status: done
- targets: release/v0.17.1

### Remove two abandoned git worktrees
`01KYJYG4PYJRAFEHJCP51XVCRA` · status: done
- belongs-to: Clear post-v0.17.0 drift and fix the prefix-ULID log corruption
- references: [github#212](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/212)
- targets: release/v0.17.1
- produced-by: [[Plan-post-v017-drift-and-prefix-resolution]]

### Close out stale work-log bookkeeping
`01KYJYG4PYFFTK74AZ7RW90M7R` · status: done
- belongs-to: Clear post-v0.17.0 drift and fix the prefix-ULID log corruption
- references: [github#211](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/211)
- targets: release/v0.17.1
- produced-by: [[Plan-post-v017-drift-and-prefix-resolution]]

### Resolve work-item id prefixes in close and update
`01KYJYG4PYDA4H10JXXRDRCXPZ` · status: done
- belongs-to: Clear post-v0.17.0 drift and fix the prefix-ULID log corruption
- targets: release/v0.17.1
- produced-by: [[Plan-post-v017-drift-and-prefix-resolution]]

### Regression tests for id-prefix resolution
`01KYJYG4PY8S8RZNB9AYP3G8GW` · status: done
- belongs-to: Clear post-v0.17.0 drift and fix the prefix-ULID log corruption
- references: [github#210](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/210)
- targets: release/v0.17.1
- produced-by: [[Plan-post-v017-drift-and-prefix-resolution]]

### Accept an absolute core.hooksPath in the doctor checks
`01KYJYG4PY6TE6ZTZMF8CV2VFT` · status: done
- belongs-to: Clear post-v0.17.0 drift and fix the prefix-ULID log corruption
- references: [github#209](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/209)
- targets: release/v0.17.1
- produced-by: [[Plan-post-v017-drift-and-prefix-resolution]]

### Clear post-v0.17.0 drift and fix the prefix-ULID log corruption
`01KYJYG4PX7NVTS1CZQ8MPES7T` · status: done
- references: [github#208](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/208)
- contains: Accept an absolute core.hooksPath in the doctor checks
- contains: Regression tests for id-prefix resolution
- contains: Resolve work-item id prefixes in close and update
- contains: Close out stale work-log bookkeeping
- contains: Remove two abandoned git worktrees
- produced-by: [[Plan-post-v017-drift-and-prefix-resolution]]

### Release v0.17.0
`01KYJGF6GN93GA3FMP5EW5A7S2` · status: done
- references: [github#203](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/203)
- targets: release/v0.17.0

### Glob boundary bug in the new slug guard causes false-positive refusal
`01KYGVDTXNEER6AQNEVWVRDEY4` · status: done
- lands-in: pr/198
- references: [github#200](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/200)

### Fix plan-capture slug-scoped duplicate guard (PR #198)
`01KYGVDKEWT513AGM0ZTY3SZP0` · status: done
- lands-in: pr/198
- references: [github#199](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/199)

### Declare wiki_ticket_sdd as a Graph Engineering system
`01KYFSRNDMYCTQ1XTMXFWEVBWT` · status: done
- lands-in: pr/197
- references: [github#195](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/195)
- contains: Add a graph-engineering callout to README.md
- contains: Verify accuracy and scope boundaries
- contains: Write docs/graph-engineering.md
- produced-by: [[Plan-declare-graph-engineering]]

### Write docs/graph-engineering.md
`01KYFSRNDMYBVMWXJFEK2AJWJJ` · status: done
- belongs-to: Declare wiki_ticket_sdd as a Graph Engineering system
- lands-in: pr/197
- references: [github#194](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/194)
- produced-by: [[Plan-declare-graph-engineering]]

### Verify accuracy and scope boundaries
`01KYFSRNDMSMEXKT7PV0F9X54M` · status: done
- belongs-to: Declare wiki_ticket_sdd as a Graph Engineering system
- lands-in: pr/197
- references: [github#193](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/193)
- produced-by: [[Plan-declare-graph-engineering]]

### Add a graph-engineering callout to README.md
`01KYFSRNDMMPY0E54PQ9QSWJWK` · status: done
- belongs-to: Declare wiki_ticket_sdd as a Graph Engineering system
- lands-in: pr/197
- references: [github#192](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/192)
- produced-by: [[Plan-declare-graph-engineering]]

### Release v0.16.1
`01KYFRPNEQEVTFB6144W7A79BJ` · status: done
- targets: release/v0.16.1

### Backfill trace-check evidence gaps (311 historical items)
`01KYFJVN7Y30B50D8A9RG60CJS` · status: done
- references: [github#185](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/185)
- targets: release/v0.16.0

### Release v0.16.0
`01KYDZRVN5HAP73465JAM65EK7` · status: done
- references: [github#184](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/184)
- targets: release/v0.16.0

### fallback-gitlab.md
`01KYDP0BQHZHYH9CKM3D0ZM803` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#178](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/178)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### End-to-end verification
`01KYDP0BQHZAPBZPSSY38J33ZZ` · status: done
- belongs-to: Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems
- lands-in: pr/179
- references: [github#177](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/177)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-awscodecatalyst.md
`01KYDP0BQHXZCGTTM5PAV262RM` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#176](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/176)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-superpowers.md
`01KYDP0BQHXGEBEY40SC1Q4ST3` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#175](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/175)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-jira.md
`01KYDP0BQHW1A3235YSF16ZZAQ` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#174](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/174)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-googleclouddevops.md
`01KYDP0BQHV6MW1XX7H7JC1EN4` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#173](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/173)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-azuredevops.md
`01KYDP0BQHRM2Q3C5727FAZ7RD` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#172](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/172)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-github.md
`01KYDP0BQHPP0JZRK856QHN76S` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#171](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/171)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-openspec.md
`01KYDP0BQHDBJ50D8HZHWN3G4H` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#170](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/170)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-confluence.md
`01KYDP0BQHANV652NZVV8N7VX5` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#169](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/169)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### Write the Integrations meta index page
`01KYDP0BQHAMP5AC6AP7854N9H` · status: done
- belongs-to: Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems
- lands-in: pr/179
- references: [github#168](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/168)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-gsd.md
`01KYDP0BQHAE38H6VPDNVXV8JA` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#167](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/167)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### fallback-speckit.md
`01KYDP0BQH6389PTNGKXHSN2KR` · status: done
- belongs-to: Write the 11 fallback integration pages
- lands-in: pr/179
- references: [github#166](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/166)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### Register and publish the new pages
`01KYDP0BQH33AMR5ETPDF4V1M6` · status: done
- belongs-to: Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems
- lands-in: pr/179
- references: [github#165](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/165)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems
`01KYDP0BQGW4XAAGX68526C9ES` · status: done
- lands-in: pr/179
- references: [github#164](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/164)
- contains: Create the integration-guide skill
- contains: Write the 11 fallback integration pages
- contains: Register and publish the new pages
- contains: Write the Integrations meta index page
- contains: End-to-end verification
- produced-by: [[Plan-wiki-driven-integration-guides]]

### Write the 11 fallback integration pages
`01KYDP0BQGC8N7K1TE571K74JF` · status: done
- belongs-to: Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems
- lands-in: pr/179
- references: [github#163](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/163)
- contains: fallback-speckit.md
- contains: fallback-gsd.md
- contains: fallback-confluence.md
- contains: fallback-openspec.md
- contains: fallback-github.md
- contains: fallback-azuredevops.md
- contains: fallback-googleclouddevops.md
- contains: fallback-jira.md
- contains: fallback-superpowers.md
- contains: fallback-awscodecatalyst.md
- contains: fallback-gitlab.md
- produced-by: [[Plan-wiki-driven-integration-guides]]

### Create the integration-guide skill
`01KYDP0BQG59M8QGCQY72SC0G1` · status: done
- belongs-to: Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems
- lands-in: pr/179
- references: [github#162](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/162)
- produced-by: [[Plan-wiki-driven-integration-guides]]

### Cut v0.15.1 release
`01KYDMC6M6B2W8F48271TG0VEK` · status: done
- lands-in: pr/161
- references: [github#183](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/183)
- targets: release/v0.15.1

### user-guide.md miscounts branch-discipline hook checks (code-review finding)
`01KYDKDJFCJTDVFZJ27Q9Y08TV` · status: done
- lands-in: pr/160
- references: [github#182](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/182)

### Cut v0.15.0 release
`01KYBPP7619CBXN3ZTV9FZJMEJ` · status: done
- lands-in: pr/157
- references: [github#181](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/181)
- targets: release/v0.15.0

### Add a CI step validating commit messages on PRs
`01KYBD2HYKYBBNGDMCQSW4VE2T` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#154](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/154)
- produced-by: [[Plan-branch-discipline-hooks]]

### Create hooks/commit-msg requiring a ULID or ticket reference
`01KYBD2HYKKZM22DFM16ZJXYFG` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#153](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/153)
- contains: Mirror to plugin/scripts/commit-msg (byte-identical canon copy)
- produced-by: [[Plan-branch-discipline-hooks]]

### Add the branch-guard block to hooks/pre-commit
`01KYBD2HYKKC2G9NW4VA3RVC6G` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#152](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/152)
- produced-by: [[Plan-branch-discipline-hooks]]

### Add TestBranchGuard and TestCommitMsgReference test classes
`01KYBD2HYKJHS5M2PFZ78Y585C` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#151](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/151)
- produced-by: [[Plan-branch-discipline-hooks]]

### Update test fixtures for the new hooks
`01KYBD2HYKG0DW7QJX7XG561A8` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#150](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/150)
- produced-by: [[Plan-branch-discipline-hooks]]

### Remove the "direct-commit repos" mode from the release skill
`01KYBD2HYKET7WJARQFB2NVMFS` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#149](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/149)
- produced-by: [[Plan-branch-discipline-hooks]]

### Full test suite green + manual verification
`01KYBD2HYKB5E4JXNYYQ9BPDAE` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#148](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/148)
- produced-by: [[Plan-branch-discipline-hooks]]

### Wire commit-msg into install/uninstall/doctor/CANON
`01KYBD2HYK9XY02QHSVF1849BQ` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#147](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/147)
- produced-by: [[Plan-branch-discipline-hooks]]

### Mirror to plugin/scripts/commit-msg (byte-identical canon copy)
`01KYBD2HYK1AT1YCN3GW8Q3QQW` · status: done
- belongs-to: Create hooks/commit-msg requiring a ULID or ticket reference
- lands-in: pr/155
- references: [github#146](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/146)
- produced-by: [[Plan-branch-discipline-hooks]]

### Add WORKLOG_SKIP_BRANCH_GUARD to the three bare pre-commit call sites
`01KYBD2HYK196RQN7JNCMV6PDS` · status: done
- belongs-to: Branch-discipline hooks: never commit on main, always reference work
- lands-in: pr/155
- references: [github#145](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/145)
- produced-by: [[Plan-branch-discipline-hooks]]

### Branch-discipline hooks: never commit on main, always reference work
`01KYBD2HYJVNHX698WR1JD96YC` · status: done
- references: [github#144](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/144)
- contains: Add WORKLOG_SKIP_BRANCH_GUARD to the three bare pre-commit call sites
- contains: Wire commit-msg into install/uninstall/doctor/CANON
- contains: Full test suite green + manual verification
- contains: Remove the "direct-commit repos" mode from the release skill
- contains: Update test fixtures for the new hooks
- contains: Add TestBranchGuard and TestCommitMsgReference test classes
- contains: Add the branch-guard block to hooks/pre-commit
- contains: Create hooks/commit-msg requiring a ULID or ticket reference
- contains: Add a CI step validating commit messages on PRs
- produced-by: [[Plan-branch-discipline-hooks]]

### sync_dispatch push_items KeyError on ext['key'] when forcing a never-remote closed item into scope via --keys
`01KYAKH389T1ZKKBP94WH2HK94` · status: done
- lands-in: pr/188
- references: [github#143](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/143)

### ia_graph build_graph() ignores commit-only sidecar code links (lands-in only honors code.pr)
`01KYAHAB3T2QXGMN4SQT4ZNZGW` · status: done
- references: [github#142](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/142)

### Cut v0.14.0 release
`01KYAH3VHPSEK2RY63J7Y109FR` · status: done
- references: [github#140](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/140)
- targets: release/v0.14.0

### worklog sync --pull can never bootstrap: cursor-less pull calls the adapter with no --since, which it requires
`01KYAGZ8KK46SQF1MKHAHVCTJV` · status: done
- references: [github#141](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/141)

### worklog pr-sync: fetch live PR metadata (files, review/CI status)
`01KYADGT9Q48EKJZVQQSH4HXWZ` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: pr/268
- references: [github#138](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/138)

### banner() mislabels frozen 'current' plans as status reports
`01KYACFJA0SQSF4C83BJZXB5MY` · status: done
- references: [github#137](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/137)

### Auto-draft the release CHANGELOG unreleased section from git log
`01KYAC0AC01R4C6W7YY1X8NVRV` · status: done
- lands-in: pr/279
- references: [github#136](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/136)

### Phase 0: add item/release page-name helpers and extend build_manifest()
`01KYABYEQPXZAAY0VWF6Z8TQ27` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/cab8952
- references: [github#135](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/135)
- produced-by: [[Plan-artifact-pages]]

### Phase 2: render PR pages
`01KYABYEQPW8Q2RGGTNP71W88E` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/4ab20d3
- references: [github#134](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/134)
- produced-by: [[Plan-artifact-pages]]

### Aggregate progress rollup for Story/Feature/Epic pages
`01KYABYEQPRM8308SYFPR8X437` · status: done
- belongs-to: Phase 1: render ticket pages for all four levels
- lands-in: commit/dd6da53
- references: [github#133](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/133)
- produced-by: [[Plan-artifact-pages]]

### Phase 2: render release pages with graph-derived Change Log
`01KYABYEQPP82DJEN19F43YRAE` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/4ab20d3
- references: [github#132](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/132)
- produced-by: [[Plan-artifact-pages]]

### Phase 4: extend tests/test_ia.py for the new page shapes
`01KYABYEQPNK7HHH5CMAR2V1JG` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/5b21a0f
- references: [github#131](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/131)
- produced-by: [[Plan-artifact-pages]]

### Phase 1: render ticket pages for all four levels
`01KYABYEQPK6PV87WNZXEYRB12` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/dd6da53
- references: [github#130](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/130)
- contains: One-line summary derivation from body's first sentence (no cache)
- contains: `ia-ticket <ULID>` preview subcommand on `bin/worklog`
- contains: Aggregate progress rollup for Story/Feature/Epic pages
- produced-by: [[Plan-artifact-pages]]

### Phase 3: file PR live-metadata follow-up item
`01KYABYEQPF8N2K26ENRKREE0W` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/1b567da
- references: [github#129](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/129)
- produced-by: [[Plan-artifact-pages]]

### Phase 4: regenerate all pages and confirm coverage gate holds
`01KYABYEQPDS2VFQKQ7B6YXZVR` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/5b21a0f
- references: [github#128](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/128)
- produced-by: [[Plan-artifact-pages]]

### `ia-ticket <ULID>` preview subcommand on `bin/worklog`
`01KYABYEQPAFJM7WC3XZV6YY76` · status: done
- belongs-to: Phase 1: render ticket pages for all four levels
- lands-in: commit/dd6da53
- references: [github#127](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/127)
- produced-by: [[Plan-artifact-pages]]

### One-line summary derivation from body's first sentence (no cache)
`01KYABYEQP9FDY8THDV79F324G` · status: done
- belongs-to: Phase 1: render ticket pages for all four levels
- lands-in: commit/dd6da53
- references: [github#126](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/126)
- produced-by: [[Plan-artifact-pages]]

### Extend IA to tickets, PRs, and releases (artifact pages)
`01KYABYEQP8ANXGYPBCV2T20D8` · status: done
- lands-in: pr/268
- references: [github#125](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/125)
- contains: Phase 0: add item_links() graph helper
- contains: Phase 4: regenerate all pages and confirm coverage gate holds
- contains: Phase 3: file PR live-metadata follow-up item
- contains: Phase 1: render ticket pages for all four levels
- contains: Phase 4: extend tests/test_ia.py for the new page shapes
- contains: Phase 2: render release pages with graph-derived Change Log
- contains: Phase 2: render PR pages
- contains: Phase 0: add item/release page-name helpers and extend build_manifest()
- contains: worklog pr-sync: fetch live PR metadata (files, review/CI status)
- produced-by: [[Plan-artifact-pages]]

### Phase 0: add item_links() graph helper
`01KYABYEQP3YCB9AVHRPCTCMRS` · status: done
- belongs-to: Extend IA to tickets, PRs, and releases (artifact pages)
- lands-in: commit/cab8952
- references: [github#124](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/124)
- produced-by: [[Plan-artifact-pages]]

### close/update silently corrupt log when given an item-id prefix instead of the full ULID
`01KYA99TVCGX79HFNHN1DVT7Y6` · status: done
- references: [github#123](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/123)
- targets: release/v0.17.1

### Give kind:ops release items a GitHub issue going forward
`01KYA8MDY5HP9MC5KQMJX3BN84` · status: done

### 01KYA8MD
`01KYA8MD` · status: done

### Backfill missing 0.13.0 changelog entries (process gap)
`01KY8KQ923Q5DMVDACGK2S4EHD` · status: done
- targets: release/v0.13.0

### Cut v0.13.0 release
`01KY8KQ8WW4A4RJ07YC4QVE7HB` · status: done
- lands-in: pr/122
- targets: release/v0.13.0

### Add MIT LICENSE (repo was public with no license)
`01KY69K4ZJMYJ1HWMWXMQ4J7BA` · status: done
- lands-in: commit/4bf033c

### ia.classify treats README.md inside docs/plans|status|adr dirs as a doc of that type — generic repos with folder READMEs fail inventory
`01KY6037BN94086PR1QP0CM7XC` · status: done
- lands-in: commit/cb8d316

### init.sh copy list missing IA modules (ia.py, ia_render.py, ia_graph.py, canonical.py, sync_dispatch.py) — fresh repos get worklog with broken ia-* commands
`01KY5ZY3ZX2Z4F73Y0BT0M0NR5` · status: done
- lands-in: commit/cb8d316

### Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
`01KY5VY0TEWBMZK5W6YJN5FQ9D` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#117](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/117)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Server: Hono JSON API over any worklog repo — fold, events, docs, index plane, git, gh, ledger, sync state
`01KY5VY0TEW87KK6AW6FQTYGZ9` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#115](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/115)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Panels wave 2: Releases, Docs browser (inventory-driven), Publish plane (3-way drift), Sync health, Charts
`01KY5VY0TEKXBXK91S9ZFZTJZ5` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#118](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/118)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
`01KY5VY0TEK8XSGP2SG57GF0KT` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#116](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/116)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Traceability panel: interactive _graph.json explorer with trace-check integrity checklist
`01KY5VY0TE8EZPWNZPZWSPTSAR` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#119](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/119)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
`01KY5VY0TE8B6RXVX1MQYJZ0TH` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#120](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/120)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Tauri 2 desktop shell wrapping the same frontend
`01KY5VY0TE7G7ZC5W20T3KAXJ7` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#121](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/121)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
`01KY5VY0TDTD7PQDT6EVD5AG9N` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#114](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/114)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
`01KY5VY0TDSWJE6W80CNCWA8QA` · status: cancelled
- references: [github#113](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/113)
- contains: Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
- contains: Tauri 2 desktop shell wrapping the same frontend
- contains: Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
- contains: Traceability panel: interactive _graph.json explorer with trace-check integrity checklist
- contains: Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
- contains: Panels wave 2: Releases, Docs browser (inventory-driven), Publish plane (3-way drift), Sync health, Charts
- contains: Server: Hono JSON API over any worklog repo — fold, events, docs, index plane, git, gh, ledger, sync state
- contains: Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Author superseding UI plan: re-base wiki_ticket_sdd_ui design on the shipped IA & content model (manifest, wiki_key, truth_state, graph, sidecars)
`01KY5VRR3R4JEFSV3S9J6PFD7N` · status: done

### Schema boundary: split doc.schema.json (documents) from entity schema (items, releases, code-changes) — defer until a second graph entity needs validation
`01KY5QV5G05V77TKESCJVY62S3` · status: done
- lands-in: pr/112
- references: [github#111](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/111)

### Add schema drift test: schema/doc.schema.json must stay equivalent to bin/ia.py validator constants
`01KY5QJAY8C8G5C4FEBMRFKM51` · status: done
- lands-in: pr/112
- references: [github#110](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/110)

### Repair frozen-plan drift: restore grok-compat-and-mermaid-viz to published version, move background-subagent rule to amendment doc
`01KY5QJARJ0S9QHGRPAV8SFV9H` · status: done
- lands-in: pr/112
- references: [github#109](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/109)
- produced-by: [[Plan-grok-viz-background-execution]]

### pre-commit hook pollutes worktree with bin/__pycache__ after git add — merge aborts on tracked-vs-untracked pyc collision
`01KY5P9V0CMM86G43HH4Q28ZDD` · status: done
- lands-in: pr/104
- references: [github#107](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/107)

### Configurable work-item field model: optional fields (estimate, risk, effort, value, confidence, owner, due_date, acceptance_criteria, blocked_by/blocks) behind work_item_fields config
`01KY5NE0ZYGBWG44N0KPEBFCZ8` · status: done
- lands-in: pr/283
- references: [github#108](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/108)
- produced-by: [[Plan-configurable-item-fields]]

### issue-description skill + rich ticket bodies in ticket-sync (summary/context/outcome/scope/acceptance/traceability from the item graph)
`01KY5N7DF2YMR9E11G4W3HF6PY` · status: done
- references: [github#106](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/106)

### PR-description skill: 10-section high-context PR body spec (big picture, runtime context, scope, flow, testing honesty, out-of-scope, ticket glossary)
`01KY5N447CK55EXFHTQGWA9JZ9` · status: done
- references: [github#105](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/105)

### GitHub Wiki shows raw YAML frontmatter on published pages — strip at publish time
`01KY5JB9F9XKKD1RNS66J6DXHZ` · status: done
- lands-in: pr/102

### Compaction aborts on closed orphan item — snapshot must not inject taxonomy defaults
`01KY5HW7KSBAYS1RE95ZT8BYM4` · status: done
- lands-in: pr/103
- references: [github#101](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/101)

### Tickets unreadable: no junior-dev/PM description — add --body to add/update, plan-capture task descriptions, skill rule, backfill open items
`01KY5HGKCBKJA5A3ZJGMPASP3X` · status: done
- lands-in: pr/102

### Phase 4: ia-graph typed-edge taxonomy + link-pr + trace-check + Traceability Index; propose-only edge seeding via suggestions.jsonl
`01KY5G9ZW0Z6JFMVTAFC54RM36` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#100](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/100)
- produced-by: [[Plan-ia-content-model]]

### Phase 2: worklog ia-render + ia-manifest — generated Home, Sidebar, publish-time truth banners in docs/.index/rendered/
`01KY5G9ZW0X5F3K7KHP1SXFM3Q` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#99](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/99)
- produced-by: [[Plan-ia-content-model]]

### Phase 5: promote gates to hard fail; platform render adapters (GitLab/ADO/Confluence); /worklog:find + glossary
`01KY5G9ZW0RABXWHEMEP1FAV2G` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#98](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/98)
- produced-by: [[Plan-ia-content-model]]

### Phase 1: CI gates — wiki_key present/unique, schema-valid frontmatter (warn one cycle, then hard)
`01KY5G9ZW0PNKDDEK5TM8GS2J6` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#97](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/97)
- produced-by: [[Plan-ia-content-model]]

### Phase 2: extend wiki-publish to consume publish-manifest.json; replace hand-maintained wiki-home.md with generated Home
`01KY5G9ZW0PEZK9PTM3NG0PYX7` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#96](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/96)
- produced-by: [[Plan-ia-content-model]]

### Phase 0: schema/doc.schema.json unified frontmatter schema + stdlib validator (adr.schema.json pattern)
`01KY5G9ZW0PBXTBKRJJ70QHR5P` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#95](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/95)
- produced-by: [[Plan-ia-content-model]]

### Phase 3: generated indexes — Decisions, Releases, Status Archive; wire ia-index into release + plan-capture skills
`01KY5G9ZW0MQD9335S641DC7ZG` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#94](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/94)
- produced-by: [[Plan-ia-content-model]]

### IA & content model (supersedes wiki-information-architecture)
`01KY5G9ZW0H2YMNWDFJYGRPYE5` · status: done
- references: [github#93](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/93)
- contains: Phase 0: worklog wiki-key + worklog ia-inventory (read-only) + migration record docs/migrations/0002-ia-content-model.md
- contains: Phase 1: worklog ia-normalize — sidecars for frozen docs, in-place for sanctioned-live; backfill wiki_key (ledger-seeded) + truth_state
- contains: Phase 3: generated indexes — Decisions, Releases, Status Archive; wire ia-index into release + plan-capture skills
- contains: Phase 0: schema/doc.schema.json unified frontmatter schema + stdlib validator (adr.schema.json pattern)
- contains: Phase 2: extend wiki-publish to consume publish-manifest.json; replace hand-maintained wiki-home.md with generated Home
- contains: Phase 1: CI gates — wiki_key present/unique, schema-valid frontmatter (warn one cycle, then hard)
- contains: Phase 5: promote gates to hard fail; platform render adapters (GitLab/ADO/Confluence); /worklog:find + glossary
- contains: Phase 2: worklog ia-render + ia-manifest — generated Home, Sidebar, publish-time truth banners in docs/.index/rendered/
- contains: Phase 4: ia-graph typed-edge taxonomy + link-pr + trace-check + Traceability Index; propose-only edge seeding via suggestions.jsonl
- produced-by: [[Plan-ia-content-model]]

### Phase 1: worklog ia-normalize — sidecars for frozen docs, in-place for sanctioned-live; backfill wiki_key (ledger-seeded) + truth_state
`01KY5G9ZW0EYQ5T83RP46Z7952` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#92](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/92)
- produced-by: [[Plan-ia-content-model]]

### Phase 0: worklog wiki-key + worklog ia-inventory (read-only) + migration record docs/migrations/0002-ia-content-model.md
`01KY5G9ZW025TRGTHFAFSVEXSX` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- lands-in: pr/104
- references: [github#91](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/91)
- produced-by: [[Plan-ia-content-model]]

### Phase 1: content inventory — classify every existing doc and wiki page into the model
`01KY5F6QA4YVHE4ESMT3E2KYK9` · status: done
- belongs-to: Wiki information architecture
- references: [github#90](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/90)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 3 (coarse): traceability graph, worklog docs validate/index/health/trace, CI gates — explode via superseding plan
`01KY5F6QA4WWSSZVKE0YJ7YHXZ` · status: done
- belongs-to: Wiki information architecture
- references: [github#89](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/89)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 2 (coarse): frontmatter normalization + generated indexes incl. Traceability Index — explode via superseding plan
`01KY5F6QA43HN4CAMFBBD6MKSA` · status: done
- belongs-to: Wiki information architecture
- references: [github#88](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/88)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: _Sidebar.md mapped to the 9 target sections
`01KY5F6QA3YAAWKF4PC5VPM90A` · status: done
- belongs-to: Wiki information architecture
- references: [github#87](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/87)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: current-vs-historical banners + Wiki-Structure conventions page
`01KY5F6QA3Y05F7S3ZMWEQ5BB2` · status: done
- belongs-to: Wiki information architecture
- references: [github#86](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/86)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: redesign Home as question-oriented orientation hub with current-vs-history zones
`01KY5F6QA3G8VWG73VVD3AWDGE` · status: done
- belongs-to: Wiki information architecture
- references: [github#85](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/85)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 1: docs/navigation.yml + docs/publishing.yml publish manifest
`01KY5F6QA3AV0B9NGBBKTMJS7J` · status: done
- belongs-to: Wiki information architecture
- references: [github#84](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/84)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: index pages — Plans-Index, ADR-Index, Status-Index, Release-History
`01KY5F6QA35SKWEN7YGMVR16XS` · status: done
- belongs-to: Wiki information architecture
- references: [github#83](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/83)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 1: document templates (plan, adr, status, design) with required frontmatter
`01KY5F6QA32MWBKTYPVPTBPKQ7` · status: done
- belongs-to: Wiki information architecture
- references: [github#82](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/82)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 1: docs/information-architecture.md + docs/content-model.md
`01KY5F6QA32GH5RWA1BH42EVSQ` · status: done
- belongs-to: Wiki information architecture
- references: [github#81](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/81)
- produced-by: [[Plan-wiki-information-architecture]]

### Wiki information architecture
`01KY5F6QA220S0K7RRK2Q80XR8` · status: done
- references: [github#80](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/80)
- contains: Phase 1: docs/information-architecture.md + docs/content-model.md
- contains: Phase 1: document templates (plan, adr, status, design) with required frontmatter
- contains: Phase 0: index pages — Plans-Index, ADR-Index, Status-Index, Release-History
- contains: Phase 1: docs/navigation.yml + docs/publishing.yml publish manifest
- contains: Phase 0: redesign Home as question-oriented orientation hub with current-vs-history zones
- contains: Phase 0: current-vs-historical banners + Wiki-Structure conventions page
- contains: Phase 0: _Sidebar.md mapped to the 9 target sections
- contains: Phase 2 (coarse): frontmatter normalization + generated indexes incl. Traceability Index — explode via superseding plan
- contains: Phase 3 (coarse): traceability graph, worklog docs validate/index/health/trace, CI gates — explode via superseding plan
- contains: Phase 1: content inventory — classify every existing doc and wiki page into the model
- produced-by: [[Plan-wiki-information-architecture]]

### Ignore tmp/ scratch dir in .gitignore (onboarding notes live there untracked)
`01KY5D79CY0DPSDAQ09QZFW694` · status: done
- lands-in: commit/c7dca2b

### Scrub inputs/ from main history (drop d538d15 + revert f97626a via rebase, force-with-lease) and delete local copies
`01KY2KHHF43KAZ54F57BQW71TD` · status: done
- references: [github#79](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/79)

### Cut v0.12.1: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KY2J9WN6WN6A8TVMR1TNS6ZX` · status: done
- targets: release/v0.12.1

### Close verb leaves remote taxonomy labels stale; next pull re-ingests them, reverting local reclassify-then-close (LWW on remote rev)
`01KY129SGV3DEX5NVAP34VV9G2` · status: done
- references: [github#76](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/76)
- targets: release/v0.12.1

### Cut v0.12.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish (first release exercising design-docs doc-sync)
`01KY11HDR3A5SR342DHG1BH5AZ` · status: done
- references: [github#74](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/74)
- targets: release/v0.12.0

### Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
`01KY111BC8QJAS9KH7N368N6RF` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#72](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/72)
- produced-by: [[Plan-wiki-ticket-ui]]

### Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
`01KY111BC8F9BH0T3TERYEFC3C` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#71](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/71)
- produced-by: [[Plan-wiki-ticket-ui]]

### Panels wave 2: Releases, Docs browser, Wiki drift, Sync health, Charts
`01KY111BC88FS6QD49JADZ9CJ5` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#70](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/70)
- produced-by: [[Plan-wiki-ticket-ui]]

### Tauri 2 desktop shell wrapping the same frontend
`01KY111BC842N3J7Y7H85NHSEG` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#69](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/69)
- produced-by: [[Plan-wiki-ticket-ui]]

### WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
`01KY111BC7PABV8W6SDNVQACSN` · status: cancelled
- references: [github#68](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/68)
- contains: Server: Hono JSON API over any worklog repo (fold, events, docs, git, gh, wiki ledger, sync state)
- contains: Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
- contains: Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
- contains: Tauri 2 desktop shell wrapping the same frontend
- contains: Panels wave 2: Releases, Docs browser, Wiki drift, Sync health, Charts
- contains: Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
- contains: Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
- produced-by: [[Plan-wiki-ticket-ui]]

### Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
`01KY111BC7NJ4BE7JBDK2P6Y56` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#67](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/67)
- produced-by: [[Plan-wiki-ticket-ui]]

### Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
`01KY111BC7B70C7M2RF1E57G17` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#66](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/66)
- produced-by: [[Plan-wiki-ticket-ui]]

### Server: Hono JSON API over any worklog repo (fold, events, docs, git, gh, wiki ledger, sync state)
`01KY111BC71KJGNH55CB2DWMKN` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#65](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/65)
- produced-by: [[Plan-wiki-ticket-ui]]

### sync.conflict_policy local-wins/remote-wins documented in config but never read by dispatcher — implement or descope
`01KXY8V686YPK4ET2XFB2KW2RX` · status: done
- references: [github#64](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/64)
- targets: release/v0.12.0

### No reopen CLI: fold supports reopen but worklog has no subcommand; update --status todo leaks stale resolution
`01KXY8V62QH1H1V70M0Y08ARXX` · status: done
- references: [github#63](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/63)
- targets: release/v0.12.0

### Pull sync drops taxonomy: sync_dispatch INGEST_FIELDS lacks level/kind/milestone — remote taxonomy edits silently not ingested
`01KXY8V5WZJ4E76B3D39KW5DCE` · status: done
- references: [github#62](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/62)
- targets: release/v0.12.0

### Packaging guard matches 'docs/' as substring — skills/design-docs/ false-positive; match path segments
`01KXY85EAS6YSEH2EDFW3PXN22` · status: done

### wiki: Design-Doc + Code-Walkthrough live pages, frozen dated pages, Home links, published.json ledger keys
`01KXY7X0QJY4JZWYYF2CA46B9G` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#60](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/60)
- produced-by: [[Plan-design-docs-release-sync]]

### dogfood generation: current_design_doc + current_code_walkthrough + dated v0.11.0-release pair under docs/designs/ (background agent, grounded in actual repo, frontmatter tag/hash/branch/roadmap)
`01KXY7X0QJQHZBCSCR438RFFMM` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#59](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/59)
- produced-by: [[Plan-design-docs-release-sync]]

### design-docs skill: SKILL.md + references/design-doc-prompt.md (Rick's 35-section prompt, improved) + references/code-walkthrough-prompt.md; plugin mirror with version frontmatter
`01KXY7X0QJCEHRDABCXF6QKXF7` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#58](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/58)
- produced-by: [[Plan-design-docs-release-sync]]

### release skill gains background-agents doc-sync step (both copies); release.sync_docs list in .work/config.yml + init.sh scaffold
`01KXY7X0QJAE0QH2W30JKK39TA` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#57](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/57)
- produced-by: [[Plan-design-docs-release-sync]]

### suites green; PR; green-gates merge; item closeout
`01KXY7X0QJ79852RFK5Q8F6FZM` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#56](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/56)
- produced-by: [[Plan-design-docs-release-sync]]

### docs: user guide + plugin guide + README document design artifacts; CLAUDE.md policy bullet; wiki-publish default set gains designs
`01KXY7X0QJ2SBY6KTQ30AKASP7` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#55](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/55)
- produced-by: [[Plan-design-docs-release-sync]]

### Design docs + code walkthroughs with release-time doc sync
`01KXY7X0QH47Z6B5QZD5G052FJ` · status: done
- references: [github#54](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/54)
- contains: docs: user guide + plugin guide + README document design artifacts; CLAUDE.md policy bullet; wiki-publish default set gains designs
- contains: suites green; PR; green-gates merge; item closeout
- contains: release skill gains background-agents doc-sync step (both copies); release.sync_docs list in .work/config.yml + init.sh scaffold
- contains: design-docs skill: SKILL.md + references/design-doc-prompt.md (Rick's 35-section prompt, improved) + references/code-walkthrough-prompt.md; plugin mirror with version frontmatter
- contains: dogfood generation: current_design_doc + current_code_walkthrough + dated v0.11.0-release pair under docs/designs/ (background agent, grounded in actual repo, frontmatter tag/hash/branch/roadmap)
- contains: wiki: Design-Doc + Code-Walkthrough live pages, frozen dated pages, Home links, published.json ledger keys
- produced-by: [[Plan-design-docs-release-sync]]

### Cut v0.11.0: stamp lockstep versions + CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KXY449A7CEKMJXTQPZRC2WX9` · status: done
- targets: release/v0.11.0

### Widen system enums: linear, gitlab, codecatalyst (AWS), explicit other; GCP no-native-tracker note; enum-is-advisory semantics
`01KXY3CQY87WFM35ZECK5TMR4S` · status: done

### Daily status report 2026-07-19
`01KXY2N7XC0BWB2AFWDD9VAECJ` · status: done
- targets: release/v0.10.0

### Migration guide: adopting worklog with existing tickets — pre-seed external via worklog link (create-vs-update keys purely on external presence), pilot one epic, sync --dry-run acceptance gate = 0 creates
`01KXXY4QW2MR804KTV4RQ952DW` · status: done
- belongs-to: ADO migration feedback: tag markers, update-merge safety, link-first import

### Adapter update-merge safety rule: updates merge tags and touch only changed fields — never overwrite existing remote content; add to adapters/README authoring rules + fake adapter behavior + dumbness-compatible test
`01KXXY4QPE8RHA7D0TYN3VS0MY` · status: done
- belongs-to: ADO migration feedback: tag markers, update-merge safety, link-first import

### Marker style per system end-to-end: ADO strips HTML comments from Description — marker must be a tag (worklog:<ulid>); verify dispatcher honors capabilities.marker.style/template beyond html_comment; document in ticket-sync skill + adapters/README
`01KXXY4QH87BAJ0M7XBJH3Y0P7` · status: done
- belongs-to: ADO migration feedback: tag markers, update-merge safety, link-first import

### ADO migration feedback: tag markers, update-merge safety, link-first import
`01KXXY4QBSGEX3HPMPSENYFA5A` · status: done
- references: [github#49](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/49)
- contains: Marker style per system end-to-end: ADO strips HTML comments from Description — marker must be a tag (worklog:<ulid>); verify dispatcher honors capabilities.marker.style/template beyond html_comment; document in ticket-sync skill + adapters/README
- contains: Adapter update-merge safety rule: updates merge tags and touch only changed fields — never overwrite existing remote content; add to adapters/README authoring rules + fake adapter behavior + dumbness-compatible test
- contains: Migration guide: adopting worklog with existing tickets — pre-seed external via worklog link (create-vs-update keys purely on external presence), pilot one epic, sync --dry-run acceptance gate = 0 creates

### Cut v0.10.0
`01KXXT3XSWDX75JFJJ7DRPMX1Z` · status: done
- targets: release/v0.10.0

### Stop hook root cause was untracked files (inputs/) counted as dirty — race diagnosis in #46 was wrong; use status -uno
`01KXXRQVRNAC61JC4RPYRWH6R2` · status: done

### Stop hook false-positives during background merge-chain branch handoffs (2x on 2026-07-19): gate reads transient tree state
`01KXXPCNQDQG9YQSEJGFRHNE12` · status: done

### Cut v0.9.0
`01KXXP6PBPXCNHAQF6Z774VAHR` · status: done
- targets: release/v0.9.0

### CLI accepts empty item id: update/close/link/ingest append orphan events for ''
`01KXXMCG418TSDDKCEZ61ZSFMH` · status: done

### Feature flag for auto-merge-on-green (default on)
`01KXXM7MD5SRRZ19EM2QGWNBHJ` · status: done
- references: [github#39](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/39)

### Grok Build native compat statement + Mermaid roadmap viz (deps/hierarchy default, event-dated gantt)
`01KXXM1Z13NPYK1XBJ1EQFEKGT` · status: done
- produced-by: [[Plan-grok-compat-and-mermaid-viz]]

### Cut v0.8.0
`01KXXKWMV2Y6YGW2GY24YFZ9HY` · status: done
- targets: release/v0.8.0

### test_adr ran repo bin/ from sandbox cwd — invisible to subprocess coverage (caught by the green-gates loop refusing PR #36)
`01KXXKPNAHYJD2143G5VAB843C` · status: done

### Seed ADRs 0001-0003 from real decisions; wiki-publish default set gains ADRs; docs + Home section
`01KXXJYKGPV41JK02KX0X67Q0G` · status: done
- belongs-to: Architecture Decision Records: schema-validated docs/adr/, worklog adr new|list|check, wiki-synced
- produced-by: [[Plan-adr]]

### worklog adr subcommands + schema/adr.schema.json + pre-commit check + tests
`01KXXJYKB1B12WEXTS6FZZ7QH2` · status: done
- belongs-to: Architecture Decision Records: schema-validated docs/adr/, worklog adr new|list|check, wiki-synced
- produced-by: [[Plan-adr]]

### Architecture Decision Records: schema-validated docs/adr/, worklog adr new|list|check, wiki-synced
`01KXXJYK5KS3MQWRPGZ3WNA790` · status: done
- contains: worklog adr subcommands + schema/adr.schema.json + pre-commit check + tests
- contains: Seed ADRs 0001-0003 from real decisions; wiki-publish default set gains ADRs; docs + Home section
- produced-by: [[Plan-adr]]

### Dispatcher pushes orphan/untitled items: scope must skip _orphan and titleless items, drift-report instead
`01KXXJDW8XQ8S5MPST369MJQZT` · status: done

### Cut v0.7.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KXXHXHFY3RV0X4M92PQ3PCBZ` · status: done
- targets: release/v0.7.0

### Hook gap: pre-commit schema check does not enforce taxonomy §2 rules (spec §3.3) — CLI-only enforcement
`01KXXGET7PTBERR80PHA2XM7RN` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)

### Docs refresh: README + user guide cover taxonomy, classifier, promote, adapter contract, green-gates merge, coverage gate
`01KXXG2QPCE09N0V2Y1DKZDNSG` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### v0.7.0 CHANGELOG, full-suite + coverage verification, dogfood sync with new fields
`01KXXFKHVTZQZ371DF7Z5HQB8M` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Roadmap: Needs-classification section, kind-mix per epic, milestone grouping (derived epic milestone), tests
`01KXXFKHPHDANP7S4GKC20G8EV` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Edges+spec: dispatcher/adapters map kind+milestone, spec v1.7 field/hash updates, migration doc, work-track/plan-capture skill updates
`01KXXFKHH0VP73C2X6P9EX4616` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Policy: CLAUDE.md taxonomy block (markers, permissioned init step), classifier graduates Stop hook, classify skill, config block, tests
`01KXXFKHBMR218J218RNN7C07N` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Core: fold/canonical/CLI level+kind+milestone, triage default, type-alias migration, promote subcommand, tests
`01KXXFKH6438M5ZV8ZKM0CH9QN` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Cut v0.6.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KXXF29E1WHP41QPNX469DVDM` · status: done

### Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
`01KXV61H5BDS7TD99H0FF9FE11` · status: done
- references: [github#29](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/29)
- contains: Core: fold/canonical/CLI level+kind+milestone, triage default, type-alias migration, promote subcommand, tests
- contains: Policy: CLAUDE.md taxonomy block (markers, permissioned init step), classifier graduates Stop hook, classify skill, config block, tests
- contains: Edges+spec: dispatcher/adapters map kind+milestone, spec v1.7 field/hash updates, migration doc, work-track/plan-capture skill updates
- contains: Roadmap: Needs-classification section, kind-mix per epic, milestone grouping (derived epic milestone), tests
- contains: v0.7.0 CHANGELOG, full-suite + coverage verification, dogfood sync with new fields
- contains: Docs refresh: README + user guide cover taxonomy, classifier, promote, adapter contract, green-gates merge, coverage gate
- contains: Hook gap: pre-commit schema check does not enforce taxonomy §2 rules (spec §3.3) — CLI-only enforcement
- produced-by: [[Plan-work-taxonomy]]

### /worklog:merge command + merge-green skill + CLAUDE.md policy bullet
`01KXV5DQPRDD2W1QKCXRQ02A58` · status: done
- belongs-to: Green-gates merge policy: PRs merge only when all checks pass; /worklog:merge polls every 5 min until green

### plugin/scripts/merge-when-green.sh poll loop + fake-gh test suite
`01KXV5DQHGQ6EQZDRVR2MV92KZ` · status: done
- belongs-to: Green-gates merge policy: PRs merge only when all checks pass; /worklog:merge polls every 5 min until green

### Green-gates merge policy: PRs merge only when all checks pass; /worklog:merge polls every 5 min until green
`01KXV5DQC9M70PN3A4AS0VCBQH` · status: done
- contains: plugin/scripts/merge-when-green.sh poll loop + fake-gh test suite
- contains: /worklog:merge command + merge-green skill + CLAUDE.md policy bullet

### Coverage gate blind to subprocess-exercised modules: sync_dispatch tanks total to 54%; wire subprocess coverage + path aliasing
`01KXV2KQRXZBKE2V6ADNGMZX62` · status: done

### PR gate: test coverage >=80% enforced in CI (bin/ modules), target 95% stated in CLAUDE.md
`01KXV1TTAW8G80DWS7ZMNJX3XE` · status: done

### v0.6.0 + dogfood: adapter check green against fake and github example
`01KXV1J05APQR0DBP1840ZPVRM` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### adapters/github worked example over gh + ticket-sync skill delegates invariants to dispatcher + CI wiring
`01KXV1J0179NHDTP9K8FRVZGYP` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### sync_dispatch.py: dispatcher owns §4 invariants; worklog sync/adapter-check wiring (last stub falls); dispatch tests
`01KXV1HZX2B49T1PB0GA4H0YMS` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### spec v1.6: §8.1 GitHub-UI merge caveat + §9 typed-contract reconciliation; user-guide recovery section
`01KXV1HZS08M62Z5EZF4HTVB6G` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### canonical.py + capabilities/adapter-io schemas + fake adapter + contract tests
`01KXV1HZMTKQGJHX0VSETZJX4Z` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### GitHub server-side merges ignore merge=union — log/roadmap conflicts in PR UI
`01KXV1B3RY3G25WR0K2ZGYEH73` · status: done
- references: [github#25](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/25)

### Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
`01KXV0NQPPPK2K948CK20QJSS1` · status: done
- references: [github#23](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/23)
- contains: canonical.py + capabilities/adapter-io schemas + fake adapter + contract tests
- contains: spec v1.6: §8.1 GitHub-UI merge caveat + §9 typed-contract reconciliation; user-guide recovery section
- contains: sync_dispatch.py: dispatcher owns §4 invariants; worklog sync/adapter-check wiring (last stub falls); dispatch tests
- contains: adapters/github worked example over gh + ticket-sync skill delegates invariants to dispatcher + CI wiring
- contains: v0.6.0 + dogfood: adapter check green against fake and github example
- produced-by: [[Plan-typed-adapter-contract]]

### Fix: plugin release-skill copy missing version frontmatter (silent str.replace miss broke version-sync test)
`01KXTZ8134TGKGC1YC2PXYRV29` · status: done
- belongs-to: release skill: cutting a release is a wiki-ticket capability

### Cut v0.5.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish + sync
`01KXTZ5TEQV2J99CHPQNHJ1NA1` · status: done
- belongs-to: release skill: cutting a release is a wiki-ticket capability

### release skill: cutting a release is a wiki-ticket capability
`01KXTZ5TAPZBC06AG50KDJKEYF` · status: done
- contains: Cut v0.5.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish + sync
- contains: Fix: plugin release-skill copy missing version frontmatter (silent str.replace miss broke version-sync test)

### Timecard status kind — narrative only per Rick: a sentence or two per day (spec §17 Q4 closed)
`01KXT9W0Y40SDTZBB93XY5YXNT` · status: done
- references: [github#17](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/17)

### Spec cleanup: purge remaining adapter references (§4.2 config keys, §5.3, §13.3, §15.5, §15.10)
`01KXT9B43GA5B8AAT26W8A1VPJ` · status: done
- references: [github#16](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/16)

### Push-only sync: close the linked ticket when a local item closes (skill scope gap)
`01KXT8JG3RNE2YZVCYEBXW9EX6` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- references: [github#14](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/14)
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Version 0.3.0 + CHANGELOG
`01KXT88N4W1E78NY17DW65PJPX` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Rewrite /worklog:init command: detect systems, yes/no confirm or multi-select pick-and-mix, write config
`01KXT88N0Z4EHR2HKMHGAM0WB3` · status: done
- belongs-to: /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Pull + echo suppression + conflicts (spec 10.3-10.6), after living with push-only
`01KXT88MWVW63PA5698TFNYZ5E` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- references: [github#13](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/13)
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Dogfood: push open items to GitHub Issues; roadmap shows issue links
`01KXT88MRST1ZZSBFMFCXYEDA1` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- references: [github#12](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/12)
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Config: ticketing block -> github, project SpillwaveSolutions/wiki_ticket_sdd
`01KXT88MMR65W3CX1C37ECEEXG` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### ticket-sync skill (push-only): ULID idempotency marker, sync-state hash skip; gh for GitHub, others vague
`01KXT88MGRJB0ARA9CN7QX29GY` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### worklog link subcommand: record external identity after successful push (spec 5.3)
`01KXT88MCBB82VT84JT0PB53PG` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### worklog wiki-add <file>: register a file in .work/published.json for wiki publishing
`01KXSQJ3Z40QHSXEN6B4Y238AZ` · status: done
- belongs-to: /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area

### wiki-publish always includes plans and roadmaps by default
`01KXSQJ3SGWWEHDNK83CDNPT4S` · status: done
- belongs-to: /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area

### /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area
`01KXSQJ3K19QWBDX482FRT7ETR` · status: done
- contains: wiki-publish always includes plans and roadmaps by default
- contains: worklog wiki-add <file>: register a file in .work/published.json for wiki publishing
- contains: Rewrite /worklog:init command: detect systems, yes/no confirm or multi-select pick-and-mix, write config

### Background plan-publish: on plan-capture, subagent syncs tickets and publishes plan to wiki, non-blocking
`01KXSQ4JH8SCHQ94DYQ7YJ872P` · status: done
- references: [github#11](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/11)

### Multi-tracker: sync one worklog to two systems at once (external as array)
`01KXSP277AE68GPTJHC1QJV1NX` · status: done
- references: [github#10](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/10)

### 01KXSP277AE68GPTHC1QJV1NX
`01KXSP277AE68GPTHC1QJV1NX` · status: cancelled
- references: [github#34](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/34)

### Harness ports — OpenCode and Codex (Claude plugin format is canonical)
`01KXSP273B1649RGJ841PVSCF3` · status: done
- references: [github#9](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/9)

### Status reports (daily/weekly) + plan-next (spec §13.3)
`01KXSP26Z674RTTB6D8GQCM2A8` · status: done
- references: [github#8](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/8)

### Compaction + nightly CI job (spec §7)
`01KXSP26V19JX6VTH0EYGDV2Z0` · status: done
- references: [github#7](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/7)

### Wiki publish breadth — Confluence, ADO, GitLab via skills
`01KXSP26PS6A0WDHQ65Y4B1X94` · status: done
- references: [github#6](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/6)

### Spec v1.4 — revise §9 adapter contract to skill-based edges
`01KXSP26JP91E4508YST2WXPTD` · status: done
- references: [github#5](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/5)

### Ticket sync — skill-based, GitHub Issues first
`01KXSP26ENPKCT4APD4YE93MMV` · status: done
- references: [github#4](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/4)
- contains: worklog link subcommand: record external identity after successful push (spec 5.3)
- contains: ticket-sync skill (push-only): ULID idempotency marker, sync-state hash skip; gh for GitHub, others vague
- contains: Config: ticketing block -> github, project SpillwaveSolutions/wiki_ticket_sdd
- contains: Dogfood: push open items to GitHub Issues; roadmap shows issue links
- contains: Pull + echo suppression + conflicts (spec 10.3-10.6), after living with push-only
- contains: Version 0.3.0 + CHANGELOG
- contains: Push-only sync: close the linked ticket when a local item closes (skill scope gap)

### Bump version 0.2.0 (plugin.json, worklog VERSION, skills frontmatter incl. new skill) + CHANGELOG entry
`01KXSNNSWKTJX2QWW4PYFDEZHS` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Packaging guard in tests/test_plugin.py — plugin/ contains no docs/user_guide content; canon list still passes
`01KXSNNSWKPDG9Q4404RPTWZY9` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Render roadmap, snapshot as docs/roadmap/<date>_v0.2-roadmap.md
`01KXSNNSWKC64M1XX0Y7WVT67Z` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Plugin installer/uninstaller at repo root — install-plugin.sh (claude plugin marketplace add + install, graceful message if claude CLI absent), uninstall-plugin.sh (reverse)
`01KXSNNSWK2PPBHVJ21MBT65ER` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Publish wiki: Home, User-Guide, CLI-Reference, Plugin-Guide, Roadmap (current), dated snapshot page; record in .work/published.json; add .work/wiki-checkout/ to .gitignore
`01KXSNNSWK0HC96WQ3HV98DHT8` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Seed roadmap: future epics via worklog add (ticket-sync skill-based w/ GitHub Issues first P1; spec v1.4 skill-based edges P2; wiki breadth Confluence/ADO/GitLab P2; compaction+nightly CI P2; status reports + plan-next P2; OpenCode/Codex ports P2; multi-tracker simultaneous P3)
`01KXSNNSWJZMQQH7H68XVB654Y` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### SessionStart hook — doctor-lite on session open: verify CLAUDE.md carries the worklog policy block (marker or heading), core.hooksPath=hooks, and installed: version vs plugin version; emit additionalContext naming what's missing and pointing at /worklog:init or /worklog:doctor; silent when repo has no bin/worklog
`01KXSNNSWJWK58BS457Y2NG3JA` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Stop hook — if the working tree has non-.work changes but .work/todo.jsonl is unchanged vs HEAD, block once with "record the work items or explain" (honor stop_hook_active from stdin JSON to prevent loops)
`01KXSNNSWJVJW87EPCZXE6QDCA` · status: done
- belongs-to: Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Docs, wiki publishing & dogfood discipline
`01KXSNNSWJV2H5QS5CSTYASS6M` · status: done
- contains: Rewrite README.md — what/why: WikiTicket SDD ("wicked ticket"), fishbowled AI development, spec-driven (plans are the spec, tickets are the WIP), multi-team, system-agnostic edges (GitHub/GitLab/ADO/Jira/Confluence — they pick), epics/stories/tasks/bugs/subtasks, event-log history, generated roadmap/status. Keep quick-start + plugin sections, tightened.
- contains: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- contains: worklog roadmap-snapshot [--name] subcommand — copy docs/roadmap.md to docs/roadmap/<YYYY-MM-DD>_<name>.md, frozen (refuse overwrite), + tests; re-copy worklog to plugin/scripts (canon sync)
- contains: Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
- contains: wiki-publish skill (repo + plugin canonical copy) — system-vague: read .work/config.yml wiki block, publish named files using available tooling for that system (gh/git for GitHub wiki, MCP/CLI for Confluence/ADO/GitLab), research missing tooling, maintain .work/published.json ledger {key: {url, rev, source_hash}}, skip unchanged hashes, surface one-time init steps (e.g. GitHub wiki first page) to the human
- contains: Dogfood policy in CLAUDE.md — every request is broken into worklog items via work-track BEFORE work starts; mirror line in work-track skill
- contains: SessionStart hook — doctor-lite on session open: verify CLAUDE.md carries the worklog policy block (marker or heading), core.hooksPath=hooks, and installed: version vs plugin version; emit additionalContext naming what's missing and pointing at /worklog:init or /worklog:doctor; silent when repo has no bin/worklog
- contains: Seed roadmap: future epics via worklog add (ticket-sync skill-based w/ GitHub Issues first P1; spec v1.4 skill-based edges P2; wiki breadth Confluence/ADO/GitLab P2; compaction+nightly CI P2; status reports + plan-next P2; OpenCode/Codex ports P2; multi-tracker simultaneous P3)
- contains: Publish wiki: Home, User-Guide, CLI-Reference, Plugin-Guide, Roadmap (current), dated snapshot page; record in .work/published.json; add .work/wiki-checkout/ to .gitignore
- contains: Plugin installer/uninstaller at repo root — install-plugin.sh (claude plugin marketplace add + install, graceful message if claude CLI absent), uninstall-plugin.sh (reverse)
- contains: Render roadmap, snapshot as docs/roadmap/<date>_v0.2-roadmap.md
- contains: Packaging guard in tests/test_plugin.py — plugin/ contains no docs/user_guide content; canon list still passes
- contains: Bump version 0.2.0 (plugin.json, worklog VERSION, skills frontmatter incl. new skill) + CHANGELOG entry
- produced-by: [[Plan-docs-wiki-dogfood]]

### Write docs/user_guide/cli-reference.md — every worklog subcommand with examples, hooks, invariants
`01KXSNNSWJQ91JPN4QRVMJQ296` · status: done
- belongs-to: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Dogfood policy in CLAUDE.md — every request is broken into worklog items via work-track BEFORE work starts; mirror line in work-track skill
`01KXSNNSWJN9C584RF3NNJK0W9` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### wiki-publish skill (repo + plugin canonical copy) — system-vague: read .work/config.yml wiki block, publish named files using available tooling for that system (gh/git for GitHub wiki, MCP/CLI for Confluence/ADO/GitLab), research missing tooling, maintain .work/published.json ledger {key: {url, rev, source_hash}}, skip unchanged hashes, surface one-time init steps (e.g. GitHub wiki first page) to the human
`01KXSNNSWJMS2914A0JJYX3KEZ` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
`01KXSNNSWJKRR3BF33CBK3E4Q7` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- contains: UserPromptSubmit hook — inject a one-line reminder: requests that produce work get worklog items first (work-track), keep statuses moving
- contains: Stop hook — if the working tree has non-.work changes but .work/todo.jsonl is unchanged vs HEAD, block once with "record the work items or explain" (honor stop_hook_active from stdin JSON to prevent loops)
- produced-by: [[Plan-docs-wiki-dogfood]]

### worklog roadmap-snapshot [--name] subcommand — copy docs/roadmap.md to docs/roadmap/<YYYY-MM-DD>_<name>.md, frozen (refuse overwrite), + tests; re-copy worklog to plugin/scripts (canon sync)
`01KXSNNSWJEP1V1JMSXH2MQWYV` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
`01KXSNNSWJDK16TMR50CNR3T3V` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- contains: Write docs/user_guide/plugin-guide.md — plugin vs repo install levels, /worklog:* commands, skills, version/doctor, harness notes (Claude Code + Grok build now; OpenCode/Codex ports on roadmap)
- contains: Write docs/user_guide/user-guide.md — concepts (event log, fold, visible WIP), core workflows (plan→capture→work→close→sync, unplanned work, PR flow incl. roadmap merge recovery)
- contains: Write docs/user_guide/cli-reference.md — every worklog subcommand with examples, hooks, invariants
- produced-by: [[Plan-docs-wiki-dogfood]]

### Write docs/user_guide/user-guide.md — concepts (event log, fold, visible WIP), core workflows (plan→capture→work→close→sync, unplanned work, PR flow incl. roadmap merge recovery)
`01KXSNNSWJ8RHP53Z2VQJH4D9J` · status: done
- belongs-to: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Write docs/user_guide/plugin-guide.md — plugin vs repo install levels, /worklog:* commands, skills, version/doctor, harness notes (Claude Code + Grok build now; OpenCode/Codex ports on roadmap)
`01KXSNNSWJ72MM7XHEJBHM6A1Y` · status: done
- belongs-to: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Rewrite README.md — what/why: WikiTicket SDD ("wicked ticket"), fishbowled AI development, spec-driven (plans are the spec, tickets are the WIP), multi-team, system-agnostic edges (GitHub/GitLab/ADO/Jira/Confluence — they pick), epics/stories/tasks/bugs/subtasks, event-log history, generated roadmap/status. Keep quick-start + plugin sections, tightened.
`01KXSNNSWJ3QKFCRBB3A12H5GT` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### UserPromptSubmit hook — inject a one-line reminder: requests that produce work get worklog items first (work-track), keep statuses moving
`01KXSNNSWJ0P23QC3SYXRQ01WA` · status: done
- belongs-to: Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
- produced-by: [[Plan-docs-wiki-dogfood]]

### /worklog:init command — scaffold bin, hooks, .work, .gitattributes, CI into the current repo
`01KXSFEWNDZ55K8AQJBCN9MRD6` · status: done
- belongs-to: Worklog Claude plugin
- contains: Record installed plugin version in .work/config.yml
- produced-by: [[Plan-claude-plugin]]

### Scaffold plugin/ with .claude-plugin/plugin.json manifest v0.1.0
`01KXSFEWNDT1B5D0PRK16NX14T` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Record installed plugin version in .work/config.yml
`01KXSFEWNDR0ZDTHHGQVN3PG9Z` · status: done
- belongs-to: /worklog:init command — scaffold bin, hooks, .work, .gitattributes, CI into the current repo
- produced-by: [[Plan-claude-plugin]]

### /worklog:uninstall command — remove scaffolding, always preserve .work data and docs
`01KXSFEWNDM44B8A8RV30PF6X1` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### bin/worklog --version + plugin CHANGELOG.md
`01KXSFEWNDBM4RHBFMNYJWR9CE` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Plugin hooks.json ExitPlanMode hook with uninitialized-repo guard
`01KXSFEWND595MAFB1GMB9KECF` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Integration test: init, track, uninstall in a sandbox repo
`01KXSFEWND4TYQ2V26KRPFHW9M` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Marketplace manifest + README install docs
`01KXSFEWND3DGDF12DSWJEKVDF` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### /worklog:doctor — version skew report + invariant checks
`01KXSFEWND2PG3PQW8GMZ9B319` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Move the three skills into plugin/skills, canonical copies
`01KXSFEWND18ATDAPCWJXKV8C1` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Worklog Claude plugin
`01KXSFEWNCJMXPZDNT7RNYTG8X` · status: done
- contains: Move the three skills into plugin/skills, canonical copies
- contains: /worklog:doctor — version skew report + invariant checks
- contains: Marketplace manifest + README install docs
- contains: Integration test: init, track, uninstall in a sandbox repo
- contains: Plugin hooks.json ExitPlanMode hook with uninitialized-repo guard
- contains: bin/worklog --version + plugin CHANGELOG.md
- contains: /worklog:uninstall command — remove scaffolding, always preserve .work data and docs
- contains: Scaffold plugin/ with .claude-plugin/plugin.json manifest v0.1.0
- contains: /worklog:init command — scaffold bin, hooks, .work, .gitattributes, CI into the current repo
- produced-by: [[Plan-claude-plugin]]

### Smoke test item
`01KXS7W15SHYS5PSGGWHYMFKYM` · status: cancelled

