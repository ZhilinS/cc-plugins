---
name: Creative UI Design
description: This skill should be used when the user asks to "create UI", "build interface", "design frontend", "make a page", "build component", "create landing page", "design dashboard", "style this component", "improve UI design", "make this look better", "avoid generic design", or mentions UI/UX work. Provides anti-generic aesthetic guidance to avoid "AI slop" design patterns with distinctive typography, bold color palettes, and creative layouts.
version: 0.1.0
---

# Creative UI Design

## Purpose

This skill provides aesthetic guidance for creating distinctive, beautiful user interfaces that avoid generic AI design patterns. Use this when building any UI to ensure creative, context-specific design choices.

## Core Anti-Generic Aesthetic Guidance

You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight. Focus on:

### Typography

Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.

**Avoid these overused fonts:**
- Inter, Roboto, Arial, system fonts
- Space Grotesk (becoming overused)
- Any default system font stack

**Use distinctive fonts from bundled collection** (see Using Bundled Fonts below)

### Color & Theme

Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.

**Avoid clichéd color schemes:**
- Purple gradients on white backgrounds
- Generic blues and grays
- Predictable pastel palettes

**Create bold, cohesive palettes:**
- Dominant color with 1-2 sharp accents
- Draw from IDE themes (Tokyo Night, Nord, Dracula)
- Match context and audience

### Motion

Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.

### Backgrounds

Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

**Avoid:**
- Plain white backgrounds
- Plain solid colors without texture
- Generic linear gradients

**Create:**
- Layered CSS gradients
- Geometric patterns
- Noise textures
- Context-specific atmospheric effects

### Critical: Avoid Generic AI-Generated Aesthetics

- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. **You still tend to converge on common choices across generations. Avoid this: it is critical that you think outside the box!**

## Using Bundled Resources

### Bundled Fonts

Examine font files in `fonts/` directory within this skill. Each font has been selected for its distinctive character. When creating UI:

1. Check available fonts in `${CLAUDE_PLUGIN_ROOT}/skills/creative-ui-design/fonts/`
2. Select fonts appropriate for the context
3. Include font files in your UI implementation
4. Vary font choices across different projects - don't default to the same fonts

### Screenshot Examples

Analyze screenshot images in `examples/` directory to understand exceptional UI design. Each screenshot demonstrates specific aesthetic principles:

1. Check `${CLAUDE_PLUGIN_ROOT}/skills/creative-ui-design/examples/` for reference images
2. Use Read tool to view screenshots
3. Analyze for: typography choices, color palettes, layouts, backgrounds, animations
4. Extract principles, don't copy literally
5. Adapt inspiration to current context

## Reading User Settings

Check for `.claude/ui-designer.local.md` in the project root. If present:

1. Read the file with Read tool
2. Parse YAML frontmatter for:
   - `favorite_fonts` - Prioritize these fonts
   - `color_preferences` - Use as palette inspiration
   - `screenshot_references` - Paths to user's reference screenshots (relative to project root)
   - `framework_preference` - Target framework

3. If `screenshot_references` provided:
   - Read each screenshot image (paths relative to project root)
   - Analyze with vision capabilities
   - Extract aesthetic principles
   - Apply contextually to current UI task

4. If settings file doesn't exist, use bundled fonts and examples as defaults

## Workflow

When creating UI:

1. **Check user settings** - Read `.claude/ui-designer.local.md` if present
2. **Understand context** - What is this UI for? Who uses it? What's the mood?
3. **Choose aesthetic direction**:
   - Review user's screenshot references (if provided)
   - Examine bundled examples for inspiration
   - Select distinctive fonts (bundled or user favorites)
   - Define bold, cohesive color palette
4. **Create with principles**:
   - Distinctive typography (never Inter/Roboto/generic)
   - Bold colors with sharp accents
   - Atmospheric backgrounds
   - Thoughtful animations at key moments
   - Context-specific character
5. **Vary across projects** - Don't converge on same choices repeatedly

## Screenshot Analysis Process

When analyzing screenshots (bundled examples or user references):

1. **Visual inspection** - Examine typography, colors, layout, spacing, backgrounds
2. **Extract principles** - What creates visual interest? How does color guide attention?
3. **Apply contextually** - Adapt principles to current UI task, don't copy literally
4. **Combine inspirations** - Mix multiple references creatively

## Quality Checklist

Before finalizing UI:

- [ ] Typography is distinctive (not generic system fonts)
- [ ] Color palette is bold and cohesive (not clichéd)
- [ ] Background has atmosphere (not plain solid color)
- [ ] Animations enhance key moments (not scattered)
- [ ] Layout is context-appropriate (not cookie-cutter)
- [ ] Design has unique character (not generic AI aesthetic)
- [ ] Varied from previous generations (not converged on same choices)

## Platform Considerations

- **Web**: Modern CSS, responsive, semantic HTML
- **Mobile**: Platform conventions with custom aesthetics
- **Desktop**: Native patterns with personality

Adapt aesthetic principles to platform requirements while maintaining distinctive character.

---

Apply these principles to create UIs that are beautiful, distinctive, and genuinely designed for their context. Think outside the box and avoid converging on generic AI aesthetics.
