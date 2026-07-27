# simple-claude-code-statusline

A tiny, dependency-free status line for [Claude Code](https://claude.com/claude-code).
Single Python file, emoji icons (no Nerd Font required).

```
📁 my-project │ 🌿 main │ 🤖 Opus 4.8 │ 💲 0.42 │ 🔢 1.8M │ 🧠 240.6k (24%) │ ⏳ 18:00
```

## What it shows

| Field | Icon | Source |
|-------|------|--------|
| Current directory | 📁 | stdin JSON (`workspace.current_dir`) |
| Git branch | 🌿 | reads `.git/HEAD` (no `git` call; supports worktrees) |
| Model | 🤖 | stdin JSON (`model.display_name`) |
| Session cost (USD) | 💲 | stdin JSON (`cost.total_cost_usd`) |
| Session tokens | 🔢 | transcript (input + cache-creation + output) |
| Context tokens | 🧠 | transcript (last message); color turns yellow ≥70%, red ≥90% |
| Usage-window reset | ⏳ | **estimate**, 5h block aligned to first-use hour |

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

- `CTX_LIMIT` — context window size for the `%`. Default `1_000_000`; set `200_000` for the standard context.
- `BLOCK_HOURS` — usage-window length for the reset estimate (default `5`).
- `IC_*` — swap any icon (emoji or your own glyph).

## Notes

- **The reset time is an estimate.** Claude Code does not persist the real quota
  reset locally (it arrives in API headers at runtime), so this uses the
  ccusage-style 5-hour block heuristic from message timestamps. The `⏳` value is
  approximate and computed per session.
- Colors are ANSI 256; adjust the color constants to taste.

## License

MIT
