---
name: ui:test
description: Test UI with Playwright - visual regression and interaction testing
allowed-tools:
  - Read
  - Grep
  - Glob
  - mcp__playwright__*
argument-hint: "[optional: file path to test]"
---

# UI Test Command

Run visual regression and interaction tests on UI using Playwright.

## Process

1. **Identify UI files to test**:
   - If argument provided: Use specified file path
   - If no argument: Test current file in context or ask user

2. **Set up test environment**:
   - Determine UI type (HTML, React component, full page, etc.)
   - Prepare test harness if needed (for component testing)

3. **Run visual regression tests**:
   - Use Playwright to render UI
   - Take baseline screenshot (or compare to existing baseline)
   - Detect visual changes
   - Report any unintended visual regressions

4. **Run interaction tests**:
   - Identify interactive elements (buttons, forms, navigation)
   - Test user interactions:
     - Button clicks
     - Form submissions
     - Navigation flows
     - Hover states
     - Focus states
   - Verify expected behaviors

5. **Generate test report**:
   - Visual regression results (with screenshots if changes detected)
   - Interaction test results (pass/fail for each interaction)
   - Any accessibility issues discovered
   - Performance observations (if relevant)

6. **Ask about fixing issues**:
   - If tests fail, ask user if they want issues fixed
   - Provide specific recommendations for failures

## Test Types

**Visual Regression:**
- Compare current render against baseline
- Detect unintended visual changes
- Useful for catching CSS regressions

**Interaction Testing:**
- Forms: Can fields be filled? Do validations work?
- Buttons: Do they respond to clicks?
- Navigation: Do links work?
- Keyboard: Can UI be navigated with keyboard?

## Example Usage

```
/ui:test                        # Test current UI file
/ui:test src/App.tsx           # Test specific file
/ui:test src/components/Form.tsx  # Test component
```

## Tips

- Visual regression requires baseline screenshots - first run creates baseline
- Interaction tests work best with complete, rendered UIs
- For components, may need to render in test harness
- Ask user for clarification if test scope is unclear
