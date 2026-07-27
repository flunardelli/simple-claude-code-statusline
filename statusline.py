#!/usr/bin/env python3
# Statusline for Claude Code. Reads JSON from stdin (model/cost) and the
# transcript JSONL (tokens/context). No external deps.
import sys, json, os
from datetime import datetime, timedelta, timezone

CTX_LIMIT = 1_000_000  # context window. Use 200_000 for the standard context.
BLOCK_HOURS = 5        # usage window (ccusage-style estimate).

# ANSI colors (tokyo-night-ish)
def c(code, s): return f"\033[{code}m{s}\033[0m"
BLUE, GREEN, YELLOW, MAG, GRAY, RED = "38;5;111", "38;5;150", "38;5;179", "38;5;176", "38;5;244", "38;5;174"
SEP = c(GRAY, " │ ")

# Emoji icons (render without a Nerd Font). Change them here if you like.
IC_DIR, IC_BRANCH, IC_MODEL = "📁", "🌿", "🤖"
IC_COST, IC_TOKENS, IC_CTX, IC_RESET = "💲", "🔢", "🧠", "⏳"

def kfmt(n):
    n = int(n or 0)
    if n >= 1000: return f"{n/1000:.1f}k"
    return str(n)

def git_branch(start):
    # walk up until a .git is found and read the current branch, without calling git
    d = start
    while d and d != "/":
        g = os.path.join(d, ".git")
        head = None
        if os.path.isfile(g):  # worktree: .git is a file pointing to the gitdir
            try:
                gd = open(g).read().strip()
                if gd.startswith("gitdir:"):
                    head = os.path.join(gd.split(":", 1)[1].strip(), "HEAD")
            except Exception:
                pass
        elif os.path.isdir(g):
            head = os.path.join(g, "HEAD")
        if head and os.path.exists(head):
            try:
                ref = open(head).read().strip()
                return ref.split("/", 2)[-1] if ref.startswith("ref:") else ref[:7]
            except Exception:
                return None
        d = os.path.dirname(d)
    return None

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    model = (data.get("model") or {}).get("display_name") or "?"
    cost = (data.get("cost") or {}).get("total_cost_usd")
    tpath = data.get("transcript_path")
    cwd = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or ""

    sess_tokens = 0
    ctx_tokens = 0
    first_ts = None
    with_tp = False
    if tpath:
        try:
            with open(tpath) as fh:
                for line in fh:
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    ts = o.get("timestamp")
                    if ts and first_ts is None:
                        try:
                            first_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        except Exception:
                            pass
                    u = (o.get("message") or {}).get("usage")
                    if not u:
                        continue
                    with_tp = True
                    it = u.get("input_tokens", 0) or 0
                    cc = u.get("cache_creation_input_tokens", 0) or 0
                    cr = u.get("cache_read_input_tokens", 0) or 0
                    ot = u.get("output_tokens", 0) or 0
                    sess_tokens += it + cc + ot            # new tokens processed
                    ctx_tokens = it + cc + cr + ot          # live context (last message)
        except Exception:
            pass

    # estimate the usage-window reset (5h block aligned to the hour of first use)
    reset_str = None
    if first_ts is not None:
        try:
            start = first_ts.replace(minute=0, second=0, microsecond=0)
            now = datetime.now(timezone.utc)
            block = timedelta(hours=BLOCK_HOURS)
            while now - start >= block:
                start += block
            reset_local = (start + block).astimezone()
            reset_str = reset_local.strftime("%H:%M")
        except Exception:
            pass

    parts = []
    if cwd:
        parts.append(c(GRAY, f"{IC_DIR} {os.path.basename(cwd)}"))
    br = git_branch(cwd) if cwd else None
    if br:
        parts.append(c(GREEN, f"{IC_BRANCH} {br}"))
    parts.append(c(BLUE, f"{IC_MODEL} {model}"))
    if cost is not None:
        parts.append(c(GREEN, f"{IC_COST} {cost:.2f}"))
    if with_tp:
        parts.append(c(YELLOW, f"{IC_TOKENS} {kfmt(sess_tokens)}"))
        pct = (ctx_tokens / CTX_LIMIT * 100) if CTX_LIMIT else 0
        ctx_color = RED if pct >= 90 else YELLOW if pct >= 70 else MAG
        parts.append(c(ctx_color, f"{IC_CTX} {kfmt(ctx_tokens)} ({pct:.0f}%)"))
    if reset_str:
        parts.append(c(GRAY, f"{IC_RESET} {reset_str}"))

    sys.stdout.write(SEP.join(parts))

if __name__ == "__main__":
    main()
