# LangChain Deep Agents / Deep Agents Code

How to use **worklog** with LangChain Deep Agents and Deep Agents Code (`dcode`).

This package follows the open **Agent Skills** layout (`plugin/skills/*/SKILL.md`).
Deep Agents loads the same format.

> Knowledge-tree writes used to ship in this plugin (`brain_session.py`,
> `okf_write.py`). They do not anymore. Use
> [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin) and
> [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core).
> See [ISOLATION.md](ISOLATION.md).

## Privacy

Never hard-code a remote URL or clone command for a private knowledge tree.
Public samples use only in-repo fiction.

## Install / discovery

### Filesystem skills source

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

agent = create_deep_agent(
    model="...",
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    skills=["./path/to/wiki_ticket_sdd/plugin/skills/"],
)
```

Or with SkillsMiddleware:

```python
from deepagents.middleware import SkillsMiddleware

SkillsMiddleware(
    backend=backend,
    sources=["/skills/", "/path/to/wiki_ticket_sdd/plugin/skills/"],
)
```

```bash
npx skills add SpillwaveSolutions/wiki_ticket_sdd --skill '*' --yes
```

This repo ships a root `plugin.json` conforming to https://agent-plugins.org.

Thin host wrapper: `plugin/hosts/deep-agents/SKILL.md`.

## Isolation

Deep Agents on one project worktree must not share that checkout with a second
session. Give each session its own `git worktree`. See [ISOLATION.md](ISOLATION.md).

## Deterministic ops

```bash
export SECOND_BRAIN_IDENTITY="deep-agents/wiki-ticket-sdd"
bin/worklog --actor "$SECOND_BRAIN_IDENTITY" add --level story --kind feature "…"
```

Wrap `bin/worklog` as a tool or shell. The model proposes. The CLI appends.

## Progressive disclosure

Startup sees skill frontmatter only.

## Related

- Agent Skills spec
- Agent Plugins 1.0
- [ISOLATION.md](ISOLATION.md), [GROK_BOT.md](GROK_BOT.md), [ONBOARDING.md](ONBOARDING.md)
- [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin) / [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core)
