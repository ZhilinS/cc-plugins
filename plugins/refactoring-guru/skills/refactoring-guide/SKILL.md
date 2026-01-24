---
name: refactoring-guide
description: This skill should be used when the user asks to "refactor code", "improve code quality", "clean up code", "write production-quality code", "apply coding standards", or when planning significant code changes. Provides systematic refactoring guidance using company code standards.
allowed-tools: Glob, Read
---

# Code Refactoring Guide

Systematic approach to refactoring using company code standards.

## Step 1: Read the Navigation Map

Start by reading the navigation map to understand available rules:

```
Read ${CLAUDE_PLUGIN_ROOT}/skills/refactoring-guide/references/navigation-map.md
```

This file describes:
- All available rule files and their purposes
- Which files to read for which refactoring type
- Quick reference table for common scenarios

## Step 2: Assess the Code

Before reading any rules, analyze the code:
- What language?
- What needs fixing? (structure, error handling, naming, async patterns?)
- Is this architectural (multiple files, layers) or localized (single method/class)?

## Step 3: Read Only Relevant Files

Based on assessment and navigation map guidance, read 1-3 relevant files:

```
Read ${CLAUDE_PLUGIN_ROOT}/skills/refactoring-guide/references/{language}/{path}
```

**Do NOT read all files.** The navigation map tells you exactly which files match your needs.

## Step 4: Build Refactoring Plan

Order changes:
1. Architectural restructuring (if needed)
2. Apply principles
3. Fix element-specific issues
4. Verify nothing breaks

## Key Rules

1. **Navigation map first** - Always read it to understand what's available
2. **Read minimally** - Load only files relevant to this specific refactoring
3. **Think before reading** - Know what you need before you fetch it
