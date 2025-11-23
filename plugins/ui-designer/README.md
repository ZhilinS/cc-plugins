# UI Designer Plugin

Create beautiful, distinctive UIs that avoid generic AI aesthetics.

## Overview

This plugin helps non-UI developers create exceptional user interfaces by:
- Auto-triggering creative design guidance when working on UI
- Providing curated font and design references
- Reviewing and testing UI with Playwright visual inspection
- Detecting and fixing generic AI patterns

## Features

### Auto-Triggering Skill
The `creative-ui-design` skill automatically loads when you mention UI work, providing:
- Anti-generic aesthetic guidance
- Distinctive font recommendations
- Curated screenshot examples
- Platform-specific considerations (web, mobile, desktop)

### Commands

**`/ui:review [path]`** - Review UI code and visuals
- Analyzes current UI file or specified path
- Renders with Playwright for visual inspection
- Compares against reference screenshots
- Provides specific improvement suggestions

**`/ui:test [path]`** - Test UI functionality
- Visual regression testing
- Interaction testing (forms, buttons, navigation)
- Generates visual diff reports

### Agent

**ui-quality-reviewer** - Automatically reviews UI code
- Triggers when >50 lines of UI code changed
- Detects generic patterns (overused fonts, clichéd colors)
- Auto-fixes obvious issues with confirmation
- References screenshot examples

## Installation

```bash
# Install plugin
cc plugin install /path/to/ui-designer

# Or link for development
ln -s /path/to/ui-designer ~/.claude/plugins/ui-designer
```

## Configuration

Create `.claude/ui-designer.local.md` in your project to customize:

```yaml
---
favorite_fonts:
  - "Authentic Sans"
  - "Departure Mono"
  - "GT Flexa"

color_preferences:
  - "Bold primaries with sharp accents"
  - "Dark mode with vibrant highlights"

screenshot_references:
  - path: "design-refs/example1.png"
    notes: "Love the bold color usage and geometric patterns"
  - path: "design-refs/example2.png"
    notes: "Excellent typography hierarchy"

framework_preference: "React"
---

Additional context about your design preferences...
```

All fields are optional. The plugin provides sensible defaults.

## Usage

### Creating UI
Just start working on UI naturally - the skill auto-triggers:
```
You: "Create a landing page for a developer tool"
Claude: [creative-ui-design skill loads automatically]
```

### Reviewing UI
```bash
/ui:review                    # Review current file
/ui:review src/components/    # Review directory
```

### Testing UI
```bash
/ui:test                      # Test current UI
/ui:test src/App.tsx         # Test specific file
```

## What Makes This Different

This plugin actively fights against:
- Generic AI aesthetics ("AI slop")
- Overused fonts (Inter, Roboto, system fonts)
- Clichéd color schemes (purple gradients everywhere)
- Cookie-cutter layouts
- Predictable component patterns

Instead, it promotes:
- Distinctive typography choices
- Cohesive, bold color palettes
- Thoughtful animations and micro-interactions
- Atmospheric backgrounds (not just solid colors)
- Context-specific, genuinely designed UIs

## Requirements

- Node.js (for Playwright MCP)
- Claude Code with MCP support

## License

MIT
