# CC Plugins Marketplace

Personal marketplace for Claude Code plugins and skills.

## Setup

Add this marketplace:

```bash
/plugin marketplace add <your-username>/cc-plugins
```

## Usage

Browse and install:

```bash
/plugin
```

Install specific plugin:

```bash
/plugin add <plugin-name>
```

## Adding Plugins

### Plugin Structure

```
plugins/
└── your-plugin/
    ├── plugin.json
    ├── README.md
    └── .claude/
        ├── commands/
        ├── skills/
        ├── subagents/
        └── hooks/
```

### Register in Marketplace

Add to `.claude-plugin/marketplace.json`:

```json
{
  "plugins": [
    {
      "name": "your-plugin",
      "path": "plugins/your-plugin",
      "displayName": "Your Plugin",
      "description": "What it does",
      "version": "1.0.0",
      "author": "Your Name",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

## Resources

- [Plugins Documentation](https://code.claude.com/docs/en/plugins)
- [Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Marketplace Guide](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
