# Isolation — WikiTicket SDD

> Knowledge-tree (OKF) isolation used to ship in this plugin. It does not
> anymore. That protocol lives in
> [second-brain-core docs/ISOLATION.md](https://github.com/SpillwaveSolutions/second-brain-core/blob/main/docs/ISOLATION.md)
> and the writer in
> [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin).
> `plugin/scripts/brain_session.py` and `bin/okf_write.py` are gone from
> this repo.

WikiTicket SDD tracks work as an append-only event log. Isolation here is
about **sessions sharing a checkout**, not knowledge-tree writes.

## One session per working directory

Two assistants in one checkout switch branches under each other and
independently "fix" the same problem in different ways. Give each session
its own `git worktree`. `bin/session.py` is an advisory registry of harness
sessions in this checkout; it never blocks a write.

```bash
git worktree add ../wiki-ticket-other feat/other-work
```

## Two merge models (must stay distinct)

| Surface | Merge model |
|---------|-------------|
| Worklog (`.work/todo.jsonl`) | Append-only ULID events. Fold produces current state. Union-merge is usually safe. |
| Knowledge tree (OKF Markdown) | Worktree + PR. Read `main`. Write `brain/<actor>/<session-id>`. Owned by okf-plugin / second-brain-core. |

Worklog appends do **not** require a knowledge worktree.

```bash
bin/worklog --actor grok-bot/wiki-ticket-sdd add "Example" --unplanned
```

## Related

- [ONBOARDING.md](ONBOARDING.md)
- [GROK_BOT.md](GROK_BOT.md)
- [second-brain-core docs/ISOLATION.md](https://github.com/SpillwaveSolutions/second-brain-core/blob/main/docs/ISOLATION.md)
