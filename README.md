# cc-plugins

Personal marketplace of Claude Code plugins, `zhilin-cc-plugins`.

## Install

```bash
/plugin marketplace add ZhilinS/cc-plugins
/plugin install <plugin>@zhilin-cc-plugins
```

Pull later changes with `/plugin marketplace update zhilin-cc-plugins`, then `/plugin update <plugin>@zhilin-cc-plugins`. New skills, agents and hooks load at the next session start.

## Plugins

| Plugin | What it does |
|---|---|
| [delegate-to-pi](plugins/delegate-to-pi) | Claude plans, a Haiku subagent drives the pi CLI on opencode-go models; learns rules from each run, applied after your approval |
| [style](plugins/style) | A classifier grades every prompt and tells Claude how to answer it; liked and disliked answers become few-shot examples. Backends: claude -p, opencode, pi, Jev |
| [agterm-visuals](plugins/agterm-visuals) | Diagrams and interactive walkthroughs as HTML pages in agterm's right pane, with comments sent back to the chat |

Each plugin's README covers setup, requirements and where it keeps its data.

## Layout

```
.claude-plugin/marketplace.json     # the plugin list
plugins/<name>/
  .claude-plugin/plugin.json        # name, version, description, author
  README.md                         # install line, what it does, requirements
  skills/<skill>/SKILL.md
  agents/<agent>.md                 # optional
  commands/<command>.md             # optional
  hooks/hooks.json                  # optional; scripts via ${CLAUDE_PLUGIN_ROOT}
  scripts/                          # optional
```

A plugin's skills and agents are namespaced by the plugin: `delegate-to-pi:pi-runner`. Per-user data (lessons, feedback) lives outside the plugin, in `~/.claude/<plugin>/`, because the installed copy is replaced on every update.

## Changing a plugin

1. Work on a branch, one PR per change.
2. **Bump `version` in the plugin's `plugin.json` in every PR that changes the plugin.** Claude Code caches installs by version: without a bump, `/plugin update` reports "already at the latest version" and users keep the old copy.
3. Run `claude plugin validate .` (the marketplace) and `claude plugin validate plugins/<name>` before pushing.

## Adding a plugin

1. Create `plugins/<name>/` with the layout above. The README starts with an install line: `/plugin install <name>@zhilin-cc-plugins`.
2. Add it to `.claude-plugin/marketplace.json`:

   ```json
   { "name": "<name>", "description": "One line", "source": "./plugins/<name>", "category": "development" }
   ```

3. Validate as above.

## Docs

- [Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Skills](https://code.claude.com/docs/en/skills)
