#!/usr/bin/env python3
# Statusline for Claude Code. Reads the session JSON on stdin. No external deps,
# no transcript parsing, no subprocesses.
import sys, json, os

BLOCK = " │ "

# ANSI colors (tokyo-night-ish)
def c(code, s): return f"\033[{code}m{s}\033[0m"
BLUE, GREEN, YELLOW, MAG, GRAY, RED = "38;5;111", "38;5;150", "38;5;179", "38;5;176", "38;5;244", "38;5;174"
SEP = c(GRAY, BLOCK)

# Emoji icons (render without a Nerd Font). Change them here if you like.
IC_DIR, IC_BRANCH, IC_MODEL = "📁", "🌿", "🤖"
IC_COST, IC_CTX, IC_QUOTA = "💲", "🧠", "🔋"
IC_CACHE_WARM, IC_CACHE_COLD = "🔥", "🧊"

# Fallback only: used when the client does not send context_window.context_window_size.
CTX_LIMIT_FALLBACK = 200_000


def kfmt(n):
    n = int(n or 0)
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def pct_color(remaining):
    # remaining is what you still have, so low is bad
    return RED if remaining < 10 else YELLOW if remaining < 30 else GREEN


def git_branch(start):
    # walk up until a .git is found and read the branch, without calling git
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


def context_used(data):
    """(tokens, percent) in the context window. Prefers the client's own numbers."""
    cw = data.get("context_window") or {}
    size = cw.get("context_window_size") or CTX_LIMIT_FALLBACK
    tokens = (cw.get("total_input_tokens") or 0) + (cw.get("total_output_tokens") or 0)
    if tokens:
        pct = cw.get("used_percentage")
        return tokens, (pct if pct is not None else tokens / size * 100)
    return None, None


def quota(data):
    """Remaining share of each rate-limit window, in a fixed order so the
    status line does not reshuffle as the numbers move. rate_limits is absent
    for non-subscribers and before the first API response."""
    rl = data.get("rate_limits") or {}
    out = []
    for key, label in (("five_hour", "5h"), ("seven_day", "7d"), ("spend_limit", "$")):
        used = (rl.get(key) or {}).get("used_percentage")
        if used is None:
            continue
        out.append((label, max(0.0, 100.0 - used)))
    return out


def cache(data):
    """(icon, text, color) for the prompt cache, or None.

    Two states in one slot so the line does not change width: warm shows how
    much of the input came from cache, cold shows what the next request will
    re-cache. prompt_cache needs Claude Code 2.1.251+ and appears only after
    the main conversation's first API response."""
    pc = data.get("prompt_cache") or {}
    if not pc.get("caching_observed"):
        return None
    if pc.get("warm"):
        hr = pc.get("hit_ratio")
        if hr is None:
            return None
        pct = hr * 100
        col = GREEN if pct >= 80 else YELLOW if pct >= 50 else RED
        return IC_CACHE_WARM, f"cache {pct:.0f}%", col
    # cold: the prefix left its TTL, so the next request pays to rebuild it
    tok = pc.get("recache_tokens_if_cold")
    return IC_CACHE_COLD, ("cache " + kfmt(tok) if tok else "cache cold"), RED


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    parts = []

    cwd = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or ""
    if cwd:
        parts.append(c(GRAY, f"{IC_DIR} {os.path.basename(cwd)}"))

    br = git_branch(cwd) if cwd else None
    if br:
        parts.append(c(GREEN, f"{IC_BRANCH} {br}"))

    model = (data.get("model") or {}).get("display_name") or "?"
    # effort is only sent for models that take the reasoning-effort parameter
    effort = (data.get("effort") or {}).get("level")
    parts.append(c(BLUE, f"{IC_MODEL} {model}" + (f" ({effort})" if effort else "")))

    cost = (data.get("cost") or {}).get("total_cost_usd")
    if cost is not None:
        parts.append(c(GREEN, f"{IC_COST} {cost:.2f}"))

    ctx, pct = context_used(data)
    if ctx is not None:
        col = RED if pct >= 90 else YELLOW if pct >= 70 else MAG
        parts.append(c(col, f"{IC_CTX} {kfmt(ctx)} ({pct:.0f}%)"))

    ch = cache(data)
    if ch:
        icon, text, col = ch
        parts.append(c(col, f"{icon} {text}"))

    q = quota(data)
    if q:
        body = " ".join(f"{label} {rem:.0f}%" for label, rem in q)
        parts.append(c(pct_color(min(rem for _, rem in q)), f"{IC_QUOTA} {body}"))

    sys.stdout.write(SEP.join(parts))


if __name__ == "__main__":
    main()
