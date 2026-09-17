# simple-claude-code-statusline

A tiny, dependency-free status line for [Claude Code](https://claude.com/claude-code).
Single Python file, emoji icons (no Nerd Font required). Reads only the session
JSON on stdin: no transcript parsing, no subprocesses, nothing to slow down a long
session.

```
📁 my-project │ 🌿 main │ 🤖 Opus 5 (high) │ 💲 76.81 │ 🧠 565.9k (57%) │ 🔥 cache 98% │ 🔋 5h 76% 7d 59% $ 37%
```

## What it shows

| Field | Icon | Source |
|-------|------|--------|
| Current directory | 📁 | stdin JSON (`workspace.current_dir`) |
| Git branch | 🌿 | reads `.git/HEAD` (no `git` call; supports worktrees) |
| Model and effort | 🤖 | stdin JSON (`model.display_name`, `effort.level`) |
| Session cost (USD) | 💲 | stdin JSON (`cost.total_cost_usd`) |
| Context window | 🧠 | stdin JSON (`context_window`); yellow ≥70% used, red ≥90% |
| Prompt cache | 🔥 / 🧊 | stdin JSON (`prompt_cache`); 🔥 is the share of input served from cache, 🧊 means the cache went cold and shows what the next request re-caches |
| Quota remaining | 🔋 | stdin JSON (`rate_limits`); yellow <30% left, red <10% |

🔥 and 🧊 share one slot, so the line keeps its width. Warm shows the share of input
served from cache, which is what explains the bill; cold shows the tokens the next
request re-caches, which is the cost spike you would otherwise only notice afterwards.

The 🔋 field is what you have left, not what you have spent: `5h` and `7d` are the
rolling rate-limit windows, `$` is the spend limit when one applies to you. The whole
field turns yellow or red on the tightest of the three, so a single glance tells you
whether you can keep going.

## Install

1. Save `statusline.py` to `~/.claude/statusline.py`.
2. Add to `~/.claude/settings.json`:

   ```json
   "statusLine": {
     "type": "command",
     "command": "python3 ~/.claude/statusline.py"
   }
   ```
3. Restart Claude Code.

Requires `python3` (standard library only).

## Configure

Top of `statusline.py`:

- `IC_*` — swap any icon (emoji or your own glyph).
- Color constants are ANSI 256; adjust to taste.
- `CTX_LIMIT_FALLBACK` — only used by old clients that do not send
  `context_window`. Current versions report the real window size, including the
  1M extended context, so there is nothing to configure.

## Fields that can be missing

The status line drops a field rather than guessing when its data is absent:

- `rate_limits` is sent only to claude.ai Pro and Max subscribers, or behind a
  gateway with a spend limit, and only after the first API response of the session.
  Each of the three windows can be absent on its own. Needs Claude Code 2.1.251+
  for `spend_limit`.
- `prompt_cache` needs Claude Code 2.1.251+ and appears only after the first
  API response of the main conversation.
- `effort` is sent only for models that take the reasoning-effort parameter.
- `context_window` percentages can be `null` early in a session.

## License

MIT
