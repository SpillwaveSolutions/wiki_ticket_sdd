# Close both P1 epics, settle the merge-strategy and GONE questions

`01KYTJGK2WMX6PNMYQDFFFPGTP` · epic/feature · **open**

Follow-on session after the 2026-07-30 bug sweep cleared every defect in the tracker.

## Children

- [[Ticket-01KYTJGK2X700NYTZHB0JDE6Q1]] Expose the two item fields the specification already declares — Estimate and dependencies are normative in the specification, and the roadmap renderer
already reads dependencies to compute blockers, but neither can be set from the command
line. (open)
- [[Ticket-01KYTJGK2X7FC4PTAMH60ECY36]] Bring skill copies under the byte-for-byte sync check — Skills exist as two unlinked copies, shipped and development-local, and they have
already drifted in both directions: one carries a pre-release gate the other lacks, the
other carries a release note the first lacks. (open)
- [[Ticket-01KYTJGK2X7FFZC5BCYF2BPSSF]] Record the decision that clearing a dead ticket link stays manual — Write the architecture decision record explaining why automation is unsafe: the gone
signal is a substring match that cannot separate a deleted ticket from one you lack
permission to read, and clearing a link leaves the remote marker in place so a later
pull can re-attribute the old ticket. (done)
- [[Ticket-01KYTJGK2X98H9T7VVR879B0XC]] Remove the unreachable sort tiebreak in the fold — Deduplication by event id happens before the sort, so the secondary sort key can never
be reached. (open)
- [[Ticket-01KYTJGK2XDQVAZ85ZEH92NGGW]] Split the phase-five container into a new epic — Close the container on the gate promotion and refile what remains: the rendering
adapter seam, one item per wiki platform to be filed only when that platform has a
user, the document search command, and the optional glossary. (done)
- [[Ticket-01KYTJGK2XDTKNHGH8QTHBHCTY]] Add the merge-guard tests to the integration test list — The test file that covers both merge guards was never added to the workflow's test
list, so the protection built for them has no automated coverage. (done)
- [[Ticket-01KYTJGK2XJD516RXMZ52PDZP1]] Run the log merge guard in continuous integration — The guard added for the resurrection bug is gated on a merge being in progress, which
is never true in a continuous-integration checkout, so it protects only developer
machines today. (done)
- [[Ticket-01KYTJGK2XJSCMJ9K16YDXXMD2]] Fix the fused version fence in every shipped skill — Each shipped skill's front matter runs the version straight into the closing fence with
no newline between them, so the block is malformed. (open)
- [[Ticket-01KYTJGK2XMY73EJMZ026Q573G]] Forget the gone marker once a ticket answers again — The marker recording that a ticket was reported missing is written but never cleared;
it is only outgrown when the key itself changes. (done)
- [[Ticket-01KYTJGK2XSA2C4H72SKP8F34D]] Abort the run when the whole project is unreachable — A failure to resolve the project itself produces the same gone signal as a single
missing ticket, once per item, so one mistyped project setting would mark every linked
item gone in a single run. (done)
- [[Ticket-01KYTJGK2XYHW1BT3Y1XH1YNP7]] Record the decision not to build a custom merge driver — Supersede the existing record rather than editing it, since an accepted record's body
is written once. (done)

Progress: 7/11 done

## Related tickets

- [github #255](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/255)
