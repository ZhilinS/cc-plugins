---
name: ui:review
description: Review UI code and visuals for aesthetic quality. Renders with Playwright, compares against references, provides improvement suggestions.
allowed-tools:
  - Read
  - Grep
  - Glob
  - mcp__playwright__*
argument-hint: "[optional: file path or directory to review]"
---

# UI Review Command

Review UI code and rendered output for aesthetic quality against creative design principles.

## Process

1. **Identify UI files to review**:
   - If argument provided: Use specified file/directory path
   - If no argument: Review current file in context or ask user

2. **Read and analyze code**:
   - Read UI code (HTML, CSS, React, Vue, SwiftUI, etc.)
   - Check for generic patterns (Inter font, purple gradients, predictable layouts)
   - Identify areas lacking creative character

3. **Render with Playwright** (for web UIs):
   - Use Playwright MCP to render HTML/React/Vue code
   - Take screenshot of rendered output
   - Analyze screenshot visually with vision capabilities

4. **Compare against references**:
   - Check `.claude/ui-designer.local.md` for user's screenshot references
   - If present, read user's reference screenshots
   - Compare rendered output against reference aesthetics
   - Note what the references do well that the current UI lacks

5. **Provide specific feedback**:
   - List generic patterns found (with code locations)
   - Suggest specific improvements with alternatives
   - Reference bundled examples or user screenshots showing better approaches
   - Focus on: typography, color palette, backgrounds, animations

6. **Generate visual report** (if multiple issues):
   - Summary of issues found
   - Before/after comparison ideas
   - Specific code changes to implement

## Example Usage

```
/ui:review                           # Review current file
/ui:review src/components/Header.tsx # Review specific file
/ui:review src/pages/               # Review directory
```

## Tips

- For web UIs, always render with Playwright to see visual output
- Compare against user's references if provided in settings
- Be specific about what to change and why
- Provide code alternatives, not just criticism
- Reference visual examples when suggesting improvements
