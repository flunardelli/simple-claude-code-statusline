# simple-claude-code-statusline

A tiny, dependency-free status line for [Claude Code](https://claude.com/claude-code).
Single Python file, emoji icons, no Nerd Font required. It reads only the session JSON
on stdin: no transcript parsing, no subprocesses, nothing that gets slower as a session
grows.

```
📁 my-project │ 🌿 main │ 🤖 Opus 5 (high) │ 💲 106.00 │ 🧠 599.5k (60%) │ 🔥 cache 98% │ 📈 5h 21% 7d 68%
```

## What it shows

| Field | Icon | Source |
|-------|------|--------|
| Current directory | 📁 | `workspace.current_dir` |
| Git branch | 🌿 | reads `.git/HEAD` directly; no `git` call, supports worktrees |
| Model and effort | 🤖 | `model.display_name`, `effort.level` |
| Session cost (USD) | 💲 | `cost.total_cost_usd` |
| Context window | 🧠 | `context_window`; yellow ≥70% used, red ≥90% |
| Prompt cache | 🔥 / 🧊 | `prompt_cache`; green ≥80% hit, red when cold |
| Rate-limit usage | 📈 | `rate_limits`; yellow ≥50% used, red ≥80% |

**🔥 and 🧊 share one slot**, so the line keeps its width. Warm shows the share of input
served from cache, which is what explains the bill. Cold shows the tokens the next
request has to re-cache, which is the cost spike you would otherwise notice only after
it happened.

**📈 is what you have spent**, the same direction the `/usage` command reports, so the
two always agree. `5h` and `7d` are the rolling rate-limit windows, `$` is the spend
limit when one applies to you. The field takes its colour from the window closest to
its ceiling, so one glance says whether you can keep going.

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

Needs `python3` (standard library only), and Claude Code 2.1.251 or later for the cache
and spend-limit fields. Older versions still work: whatever they do not send is simply
left out.

## Configure

At the top of `statusline.py`:

- `IC_*` — swap any icon, emoji or your own glyph.
- Colour constants are ANSI 256; adjust to taste.
- `CTX_LIMIT_FALLBACK` — used only by clients too old to send `context_window`.
  Current versions report the real window size, the 1M extended context included,
  so there is nothing to set by hand.

## Fields that can be missing

The status line drops a field rather than guessing when its data is absent:

- `rate_limits` reaches only claude.ai Pro and Max subscribers, or sessions behind a
  gateway that sets a spend limit, and only after the session's first API response.
  Each of the three windows can be absent on its own.
- `prompt_cache` appears after the main conversation's first API response.
- `effort` is sent only for models that take the reasoning-effort parameter.
- `context_window` percentages can be `null` early in a session.

## What changed since the first version

- **The usage-window countdown is gone.** It guessed the reset time from a 5-hour
  block heuristic, because the client did not expose the real one. It does now, so
  the guess gave way to `rate_limits`, which carries the true reset instant. Claude
  Code re-runs the status line when a window actually resets.
- **The cache field arrived**, for the same reason: a cold cache is the largest
  invisible cost in a long session, and the client reports exactly what a rebuild
  will cost.
- **Reasoning effort** now sits beside the model name.
- **The session-token counter was removed.** It summed cumulative expensive tokens,
  which the cost field already states in the unit that matters, and it sat next to the
  context figure in the same `k` notation, so the two read as comparable when one is a
  running total and the other a snapshot. Dropping it also removed the only reason the
  script opened the transcript at all.
- **`CTX_LIMIT` is no longer a setting**, since the client reports the real window size.
- **The rate-limit field shows usage, not headroom.** It first displayed what was left,
  which read backwards next to `/usage`: the same window showed 79 in one place and 21 in
  the other. A number the product already publishes should not be inverted without saying
  so, and the battery icon that went with it made the inversion look deliberate. The
  rising chart replaced it because it climbs as you spend, the way the number does.

## License

MIT
