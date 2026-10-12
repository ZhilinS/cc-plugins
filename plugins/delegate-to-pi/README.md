# Delegate to pi

Claude plans, [pi](https://github.com/badlogic/pi-mono) executes. A Haiku subagent (`pi-runner`) drives the pi CLI on opencode-go models one stateless call at a time and returns a compact report, so the heavy tokens burn on the OpenCode Go subscription instead of Anthropic.

## Install

```bash
/plugin marketplace add ZhilinS/cc-plugins
/plugin install delegate-to-pi@zhilin-cc-plugins
```

Needs `pi` on `PATH`, an opencode-go provider with a Go subscription, `jq` and `perl`.

## What's inside

- `skills/delegate-to-pi` — when and how to write task packets, model routing, verify packets.
- `agents/pi-runner` — the Haiku runner (`delegate-to-pi:pi-runner`).
- `hooks/hooks.json` — `SessionEnd` runs reflection, `SessionStart` surfaces what it drafted.

## Lessons

Each user grows their own lessons in `~/.claude/delegate-to-pi/lessons/`; the plugin ships none. `pi-runner` appends what it learned to `inbox.md`, and after a session that used it, reflection asks pi to fold the inbox and the session into a new `rules.md`.

The new rules arrive as `rules.pending.md` and are applied only after you approve the diff, because `pi-runner` follows `rules.md` with a shell and reflection reads untrusted text (web pages, repo files, pi output).

## Before you install

- **Data leaves the machine.** After every session that spawned `pi-runner`, a compacted transcript (up to 120 KB, the first 300 characters of every message and tool result) goes to opencode-go. If such a session read a `.env`, its beginning goes too. Sessions without `pi-runner` are not sent.
- **pi gets a shell.** `pi-runner` calls pi with write access, bash and web search. How far that reaches depends on your Claude Code permission mode.
- `PI_RW=write` is set on every call for a pi extension that starts pi read-only; without that extension it does nothing.
