---
name: prepare-refactor
description: Use when refactoring code, improving code quality, cleaning up code, writing production-quality code, or applying coding standards. Provides methodology and reference materials for systematic refactoring.
---

# Refactoring Guru

Methodology-driven refactoring with curated code standards. Works in three stages: review, plan, execute.

## Flow

```dot
digraph refactor_flow {
    rankdir=TB;
    node [shape=box];

    subgraph cluster_explore {
        label="Stage 1a: Exploration (sub-agent)";
        explore [label="Spawn: Exploration Agent\n→ language, file list,\n   detected arch pattern,\n   reference paths"];
    }

    subgraph cluster_arch {
        label="Stage 1b: Architecture Check (sub-agent)";
        arch_agent [label="Spawn: Architecture Agent\n→ violation report"];
        arch_check [label="Arch violations?" shape=diamond];
        save_arch [label="Save arch-only plan\nFix violations\n(in-place or parallel-execution)"];
    }

    subgraph cluster_elements {
        label="Stage 1c: Elements + Polish (parallel sub-agents)";
        elem_agents [label="Spawn: Elements Agents (parallel)\nBatch references evenly across agents\n→ violation reports"];
    }

    subgraph cluster_plan {
        label="Stage 2: Save Plan";
        merge [label="Merge violation reports"];
        save_full [label="Save full plan\n(see plan-full-example.md)"];
    }

    subgraph cluster_exec {
        label="Stage 3: Execution";
        exec_choice [label="User chooses" shape=diamond];
        in_place [label="In-place\n(small changeset)"];
        subagent [label="Subagent-driven\n(refactoring-guru:parallel-execution)"];
    }

    reeval [label="Re-evaluation:\nSpawn arch + ALL elements agents\n(parallel, fresh check)" shape=box];
    new_violations [label="New violations?" shape=diamond];
    followup [label="Create follow-up plan\nExecute, re-evaluate again"];
    done [label="Done" shape=doublecircle];

    explore -> arch_agent;
    arch_agent -> arch_check;
    arch_check -> save_arch [label="yes"];
    save_arch -> arch_agent [label="re-check after fixes"];
    arch_check -> elem_agents [label="no"];
    elem_agents -> merge;
    merge -> save_full;
    save_full -> exec_choice;
    exec_choice -> in_place;
    exec_choice -> subagent;
    in_place -> reeval;
    subagent -> reeval;
    reeval -> new_violations;
    new_violations -> followup [label="yes"];
    followup -> reeval [label="after fixes"];
    new_violations -> done [label="no"];
}
```

## Layered References

Reference files are resolved from three layers (highest priority first):

1. **Project:** `$PROJECT_ROOT/.claude/refactoring-guru/references/`
2. **User:**    `$HOME/.claude/refactoring-guru/references/`
3. **Plugin:**  `${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references/`
   (fallback if env var missing: `ls -d $HOME/.claude/plugins/cache/*/refactoring-guru/*/skills/prepare-refactor/references/ | sort -V | tail -1`)

**Resolution rule — directory-replace, per category.** For each logical path, walk the layers top-down. The first layer that contains the path owns it fully. If the path is a directory, ALL files inside belong to that layer — contents of the same directory in lower-priority layers are ignored. Resolution happens per category (`principles.md`, `elements/`, `architecture/`), not per language: project can override `python/elements/` without touching `python/architecture/`.

**Adding a new language or custom rules** — create `<layer>/<language>/{principles.md,elements/*.md,architecture/*.md}` at the user or project layer. The exploration agent picks it up automatically; no plugin edits needed.

## Stage 1: Review (sub-agent driven)

Stage 1 is split into three sub-stages. The main agent orchestrates — it does NOT read project code files directly. All codebase reading happens inside sub-agents.

### Read User Context

Before doing anything else, extract from the user's message:
- **Scope** — which files, directories, or service to refactor
- **Steering** — any constraints, exclusions, or priorities (e.g. "don't touch error handling", "focus only on naming", "skip architecture fixes")

Carry both through to every sub-agent prompt you spawn. If scope is vague, ask the user to clarify before proceeding.

### Pre-check: Tests

Before spawning any sub-agents, verify:
- Tests exist for the code being refactored
- Run the test suite and confirm all tests pass (`pytest` for Python, `./gradlew test` or `mvn test` for Java)
- Check coverage — aim for >= 80% on files being refactored

If tests need work, record this in the plan and address it before proceeding with sub-agents.

### Stage 1a: Exploration Agent

> **Prefer Agent Teams when available.** If the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` setting is enabled, use Claude Code's native agent teams (`TeamCreate` + `SendMessage` + shared task list) instead of `Task` tool subagents. Create a team, add one task per element batch, and let teammates self-claim and coordinate through the shared task list. See https://code.claude.com/docs/en/agent-teams for details.
>
> **Fallback:** If agent teams are not enabled, use `Task` tool subagents as described below.

Spawn a sub-agent with this prompt:

```
You are a lightweight codebase explorer. Do NOT read any reference files. Do NOT check rules.

User context:
[SCOPE AND STEERING FROM USER — paste verbatim]

Your job:

1. Identify the programming language of the code being refactored (python, java, or other name).
2. List all files in scope (the files the user wants refactored).
3. Detect the architecture pattern. Look at directory structure, imports, class/module names:
   - hexagonal_ddd (ports & adapters: domain, application, infrastructure/adapters)
   - fastapi_web (FastAPI routes as primary entry point)
   - grpc_proxy (gRPC client/server, proto files)
   - spring_web (Spring Boot REST controllers)
   - unknown (cannot determine)

4. Resolve reference files from the layered reference stack.

   Layer roots, priority high → low:
   a) Project: "$(pwd)/.claude/refactoring-guru/references"
   b) User:    "$HOME/.claude/refactoring-guru/references"
   c) Plugin:  "${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references"
      (if CLAUDE_PLUGIN_ROOT is empty, fall back to:
       ls -d $HOME/.claude/plugins/cache/*/refactoring-guru/*/skills/prepare-refactor/references 2>/dev/null | sort -V | tail -1)

   Resolution rule — directory-replace, per category: walk layers top-down; the first layer that contains the path owns it fully. If the path is a directory, ALL files inside come from that layer only (lower layers' contents at the same path are ignored). Resolution is per category — project can own `<lang>/elements/` without affecting `<lang>/architecture/`.

   Discovery convention for the detected `<language>`:
   - `<language>/principles.md` — include if found
   - `<language>/elements/` — include ALL *.md files from the owning layer
   - `<language>/architecture/<detected_pattern>.md` — include if found and pattern ≠ unknown
   - `<language>/architecture/hexagonal_ddd.md` — include if found (baseline architecture)
   - Pattern = unknown → include ALL *.md files in `<language>/architecture/` from the owning layer

   Procedure:
   a) For each layer (project, user, plugin in order), check whether the root exists and whether `<language>/` exists inside it.
   b) Resolve `principles.md`: first layer whose `<language>/principles.md` exists wins.
   c) Resolve `elements/`: first layer whose `<language>/elements/` directory exists wins; list every *.md file inside it.
   d) Resolve `architecture/`: first layer whose `<language>/architecture/` directory exists wins; filter by detected pattern per convention above.
   e) Output ABSOLUTE paths only. If a category is not found in any layer, omit it (no placeholders).

Return an Exploration Report in this format:

## Exploration Report

**Language:** [python | java | other]
**Detected pattern:** [hexagonal_ddd | fastapi_web | grpc_proxy | spring_web | unknown]
**Files in scope:**
- path/to/file1.py
- path/to/file2.py

**Reference paths (principles):**
- /abs/path/to/<language>/principles.md  [layer: plugin|user|project]

**Reference paths (architecture):**
- /abs/path/to/<language>/architecture/<file>.md  [layer: ...]

**Reference paths (elements):**
- /abs/path/to/<language>/elements/<file>.md  [layer: ...]
- ... (every file in the owning elements dir)
```

Receive the Exploration Report. Use it to configure the next sub-agents.

### Stage 1b: Architecture Agent

Spawn a sub-agent with this prompt (fill in values from the Exploration Report):

```
You are an architecture code reviewer.

User context:
[SCOPE AND STEERING FROM USER — paste verbatim]

Files in scope:
[LIST FILES FROM EXPLORATION REPORT]

Reference files to check (read each one):
[LIST ARCHITECTURE + PRINCIPLES REFERENCE PATHS FROM EXPLORATION REPORT]

For EACH reference file:
1. Read the file.
2. Extract every ## heading — each heading is a separate rule.
3. For each rule: check ALL files in scope against that rule.
4. Record violations: which file, which lines, what is wrong.
5. If a file follows the rule, skip it — only report violations.

Do NOT fix anything. Read-only review only.

Return an Architecture Violation Report in this format:

## Architecture Violation Report

### [Rule Name — exact ## heading from reference]
**Reference:** /abs/path/to/<language>/architecture/<file>.md
**Files:** path/to/file.py:10-30
**Violation:** [What is wrong]

(Repeat for each violation. If no violations found, write: "No architecture violations found.")
```

**After receiving the report:**
- If violations found → see "Architecture Violations" below
- If no violations → proceed to Stage 1c

#### Architecture Violations: Save Plan and Fix

If the Architecture Agent reports violations:

1. Read [plan-arch-example.md](plan-arch-example.md) for the plan format.
2. Save a plan to `docs/plans/YYYY-MM-DD-refactor-<scope>.md` with Stage 1b (Architecture) violations only.
3. Commit the plan file.
4. Offer execution (in-place or `refactoring-guru:parallel-execution`).
5. After fixes are applied, re-spawn the Architecture Agent with the same prompt on the updated files.
6. Repeat until the Architecture Agent reports no violations.
7. Then proceed to Stage 1c.

### Stage 1c: Elements Agents (parallel)

Spawn sub-agents **in parallel** using the Task tool. Each covers a subset of element references. Decide the number of agents and how to batch references based on which reference files exist for the detected language (from the Exploration Report). Aim to balance work evenly across agents.

**Per-agent prompt template** (fill in values from the Exploration Report):

```
You are a code elements reviewer.

User context:
[SCOPE AND STEERING FROM USER — paste verbatim]

Files in scope:
[LIST FILES FROM EXPLORATION REPORT]

Reference files to check (read each one):
[LIST THIS AGENT'S REFERENCE FILE PATHS]

For EACH reference file:
1. Read the file.
2. Extract every ## heading — each heading is a separate rule.
3. For each rule: check ALL files in scope against that rule.
4. Record violations: which file, which lines, what is wrong.
5. If a file follows the rule, skip it — only report violations.

Do NOT fix anything. Read-only review only.

Return a Violation Report in this format:

## Violation Report: [Agent N]

### [Rule Name — exact ## heading from reference]
**Reference:** /abs/path/to/<language>/elements/<file>.md
**Files:** path/to/file.py:10-30
**Violation:** [What is wrong]

(Repeat for each violation. If no violations found for a rule, skip it.)
```

Wait for all agents to complete, then collect all violation reports.

## Stage 2: Save Plan

### Merge Violation Reports

Collect all violation reports from the Stage 1c elements agents. Merge them into a single violation list.

Phase labels come from [plan-full-example.md](plan-full-example.md) — read it to confirm the exact headings before grouping:
- Phase 3 covers structural element rules (class body, method structure, method signature, error handling)
- Phase 4 covers polish rules (naming, logging, documentation)

Group each agent's output into the appropriate phase based on which references it reviewed.

Then save the plan using the merged list. Read [plan-full-example.md](plan-full-example.md) for the full format.

**Save to:** `docs/plans/YYYY-MM-DD-refactor-<scope>.md`

### Architecture Changes Invalidate Later Phases

Architecture changes (moving files between packages, restructuring layers, changing DI wiring, splitting/merging classes) change the file layout. File paths and line numbers recorded during review for Stages 1c and 4 become unresolvable after architecture fixes.

**Rule:** If Stage 1b (Architecture) has any violations, do NOT include element or polish violations in the plan. Instead, add a **Stage 4 (Re-evaluate)** step that re-runs the review after architecture fixes are applied. See the flow diagram above for the complete decision path.

### Plan File Examples

The digraph above shows which phases to include. Read the matching example before writing the plan:

- **No architecture violations:** Read [plan-full-example.md](plan-full-example.md)
- **Has architecture violations:** Read [plan-arch-example.md](plan-arch-example.md)

**After saving:** Commit the plan file.

## Stage 3: Offer Execution

See flow diagram for the decision path. Present the user with:

| Option | When | How |
|--------|------|-----|
| **In-place** | Small changeset (user decides) | Work through plan phase by phase, commit after each |
| **Subagent-driven** | Larger changeset or >3 files | **REQUIRED:** Use refactoring-guru:parallel-execution |

## Stage 4: Re-evaluation

After all fixes from the plan are applied, re-run a full review to verify the codebase is clean.

Spawn all agents **in parallel** (same prompts as Stage 1b and 1c, same files in scope from the Exploration Report):
- Architecture Agent (Stage 1b prompt)
- Elements Agents (Stage 1c prompt, same batching as the original run)

**After collecting all reports:**

- **No violations** → done. Codebase is clean.
- **New violations found** → create a follow-up plan:
  1. Mark all current plan tasks as completed.
  2. Save a new plan file (`docs/plans/YYYY-MM-DD-refactor-<scope>-followup.md`) with the new violations.
  3. Offer execution.
  4. After fixes, re-run Stage 4 again.

The loop continues until re-evaluation finds zero violations.

## Writing Code (In-place Execution Only)

After writing or editing code, verify it against the relevant references using the same rule-by-rule process:

1. Read each relevant reference file
2. Create a checklist item for every `##` heading
3. Verify the code against each rule individually
4. Fix any deviations before moving on

If you haven't read the relevant reference yet, read it now.

## Embedding References

**Every plan step, TaskCreate task, and sub-agent prompt MUST include full reference paths.** Sub-agents don't inherit skill context — without explicit paths, they skip rules.

Use the ABSOLUTE paths from the Exploration Report verbatim. Sub-agents must never resolve layers themselves.

```
Step 2: Refactor the UserService class
References: /abs/path/to/<language>/elements/class_body.md
```

## Quick Reference

| Stage | What happens | Who does it |
|-------|-------------|-------------|
| Pre-check | Tests exist, coverage ≥ 80%, all passing | Main agent |
| 1a: Exploration | Language, files, arch pattern, reference paths | Exploration sub-agent |
| 1b: Architecture | Check arch refs rule-by-rule, report violations | Architecture sub-agent |
| 1c: Elements | Check element refs rule-by-rule, report violations | 3 parallel sub-agents |
| 2: Save Plan | Merge reports, save plan file, commit | Main agent |
| 3: Execute | In-place or `refactoring-guru:parallel-execution` | Main agent + user |
| 4: Re-evaluate | Re-run 1b + 1c in parallel, loop until clean | Main agent |
