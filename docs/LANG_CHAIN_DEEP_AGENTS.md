# LangChain Deep Agents / Deep Agents Code

How to use **worklog** with LangChain Deep Agents and Deep Agents Code (`dcode`).

This package follows the open **Agent Skills** layout (`skills/*/SKILL.md`). Deep Agents loads the same format.

## Privacy and knowledge root

The institutional second brain is a local or private OKF tree the human already owns.

- Point Deep Agents at that tree with `SECOND_BRAIN_ROOT`.
- Never hard-code a remote URL or clone command.
- Public samples use only the in-repo sample graph.

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
    sources=["/skills/", "/path/to/wiki_ticket_sdd/skills/"],
)
```

```bash
npx skills add SpillwaveSolutions/wiki_ticket_sdd --skill '*' --yes
```

This repo ships a root `plugin.json` conforming to https://agent-plugins.org.

Thin host wrapper: `plugin/hosts/deep-agents/SKILL.md`.

## Isolation

Deep Agents on one project worktree (for example **northstar-console**) must not write `main` of a shared brain directly.

```bash
python3 plugin/scripts/brain_session.py open \
  --repo "$BRAIN_REPO" \
  --bundle knowledge \
  --actor deep-agents/wiki-ticket-sdd \
  --plugin worklog \
  --host deep-agents
```

Then set `SECOND_BRAIN_ROOT` to the session bundle from the JSON. Close the session to PR. See [ISOLATION.md](ISOLATION.md).

## Deterministic ops

```bash
export SECOND_BRAIN_IDENTITY="deep-agents/wiki-ticket-sdd"
bin/worklog show --help
# Knowledge-tree writes only, after opening a session:
# write TicketLink / work-item Markdown into $SECOND_BRAIN_ROOT
```

Wrap the scripts as tools or shell. The model proposes. The scripts capture, pack, and validate.

## Progressive disclosure

Startup sees skill frontmatter only. Pack (2 hops) before answering or writing.

## Related

- Agent Skills spec
- Agent Plugins 1.0
- [ISOLATION.md](ISOLATION.md), [GROK_BOT.md](GROK_BOT.md), [ONBOARDING.md](ONBOARDING.md)
- [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core) session helpers
