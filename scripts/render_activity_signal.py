#!/usr/bin/env python3
"""Render the "Activity Signal" section of the profile README as a static SVG.

Output style: contribution line/area chart (last 52 weeks) + 2x2 stats grid +
language bar. Data sources are public HTTP endpoints; no third-party image
service is involved, so the picture cannot break when someone's Vercel
instance dies. The committed SVG is refreshed by .github/workflows/activity-signal.yml.

Usage:
    render_activity_signal.py --username lska367 --lang en --out assets/activity-signal.svg

Exit code is non-zero when the data needed for the chart is unavailable, which
keeps the previous (still correct) SVG in place instead of publishing a blank one.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from collections import OrderedDict

API = "https://api.github.com"
CONTRIB_API = "https://github-contributions-api.jogruber.de/v4/{user}?y=1"

# GitHub Linguist colors for the language bar / legend dots.
LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "HTML": "#e34c26", "CSS": "#663399", "Vue": "#41B883", "C": "#555555",
    "C++": "#f34b7d", "Go": "#00ADD8", "Rust": "#dea584", "Java": "#b07219",
    "Shell": "#89e051", "TeX": "#008060", "Dockerfile": "#384d54",
    "Makefile": "#427819", "Jupyter Notebook": "#DA5B0B", "Lua": "#000080",
    "CUDA": "#3A4E6A", "PowerShell": "#012456", "Ruby": "#701516",
    "PHP": "#4F5D95", "Swift": "#F05138", "Kotlin": "#A97BFF", "R": "#358a7b",
    "MATLAB": "#e16737", "Perl": "#0298c3", "Scala": "#c22d40",
}
FALLBACK_COLORS = ["#8b949e", "#a5d6ff", "#d2a8ff", "#ffa657", "#7ee787", "#ff7b72"]

ACCENT = "#36BCF7"
BG = "#0d1117"
BORDER = "#21262d"
TEXT = "#e6edf3"
MUTED = "#8b949e"

UI_FONT = ("'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',"
           "'Noto Sans CJK SC','Source Han Sans SC','Droid Sans Fallback',"
           "Helvetica,Arial,sans-serif")

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_ZH = ["1月", "2月", "3月", "4月", "5月", "6月",
             "7月", "8月", "9月", "10月", "11月", "12月"]

I18N = {
    "en": {
        "chart_title": "Contribution Signal",
        "chart_sub": "{n} contributions in the last 52 weeks",
        "stats_title": "{user}'s GitHub Stats",
        "stats_title_short": "GitHub Stats",
        "langs_title": "Most Used Languages",
        "stars": "Total Stars", "repos": "Public Repos",
        "followers": "Followers", "following": "Following",
    },
    "zh": {
        "chart_title": "贡献信号",
        "chart_sub": "近 52 周共 {n} 次贡献",
        "stats_title": "{user} 的 GitHub 统计",
        "stats_title_short": "GitHub 统计",
        "langs_title": "常用语言",
        "stars": "Star 总数", "repos": "公开仓库",
        "followers": "关注者", "following": "正在关注",
    },
}


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def http_json(url: str, *, timeout: int = 25, payload=None, attempts: int = 3):
    """Fetch JSON with backoff.

    GitHub answers 403 once the rate budget is spent. That has to fail loudly: a
    silently truncated response would be baked into the committed chart.
    """
    last: Exception = RuntimeError(f"no attempt made for {url}")
    for i in range(attempts):
        headers = {
            "User-Agent": "activity-signal-renderer",
            "Accept": "application/vnd.github+json",
        }
        token = github_token()
        if token and url.startswith(API):
            headers["Authorization"] = f"Bearer {token}"
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, headers=headers, data=body)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read()[:160].decode("utf-8", "replace").strip()
            except Exception:
                detail = ""
            last = RuntimeError(f"HTTP {exc.code} {url.split('?')[0]} {detail}".strip())
            if exc.code not in (403, 408, 429, 500, 502, 503, 504) or i == attempts - 1:
                raise last from None
            wait = int(exc.headers.get("Retry-After") or 0) or min(30, 3 * 2 ** i)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = RuntimeError(f"{url.split('?')[0]}: {exc}")
            if i == attempts - 1:
                raise last from None
            wait = 3 * (i + 1)
        time.sleep(wait)
    raise last


def github_token():
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def _bucket_weeks(days, weeks):
    """[(date, count)] -> (Monday-aligned week starts, weekly totals, window total)."""
    buckets: "OrderedDict[dt.date, int]" = OrderedDict()
    for d, c in days:
        monday = d - dt.timedelta(days=d.weekday())
        buckets[monday] = buckets.get(monday, 0) + c
    ordered = sorted(buckets)[-weeks:]
    return ordered, [buckets[m] for m in ordered], sum(buckets[m] for m in ordered)


def _weekly_graphql(user: str, weeks: int):
    """Official source: needs any valid token (public data, no special scope)."""
    now = dt.datetime.now(dt.timezone.utc)
    data = http_json(f"{API}/graphql", payload={
        "query": (
            "query($login:String!,$from:DateTime!,$to:DateTime!){"
            "user(login:$login){contributionsCollection(from:$from,to:$to){"
            "contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"
        ),
        "variables": {
            "login": user,
            "from": (now - dt.timedelta(days=364)).strftime("%Y-%m-%dT00:00:00Z"),
            "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    })
    if data.get("errors"):
        raise RuntimeError(data["errors"][0].get("message", "graphql error"))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for item in week["contributionDays"]:
            days.append((dt.date.fromisoformat(item["date"]),
                         int(item.get("contributionCount", 0) or 0)))
    if not days:
        raise RuntimeError("graphql returned an empty calendar")
    return _bucket_weeks(days, weeks)


def _weekly_jogruber(user: str, weeks: int):
    """Token-free fallback: public mirror of the contribution calendar."""
    payload = http_json(CONTRIB_API.format(user=user))
    days = []
    for item in payload.get("contributions", []):
        try:
            d = dt.date.fromisoformat(item["date"])
        except (KeyError, ValueError):
            continue
        days.append((d, int(item.get("count", 0) or 0)))
    if not days:
        raise RuntimeError("contribution API returned no data")
    return _bucket_weeks(days, weeks)


def fetch_weekly(user: str, weeks: int = 52):
    sources = ([] if not github_token() else [("graphql", _weekly_graphql)]) + \
              [("contributions-api", _weekly_jogruber)]
    problems = []
    for name, fn in sources:
        try:
            mondays, series, total = fn(user, weeks)
            print(f"contributions from {name}: {len(series)} weeks, {total} total")
            return mondays, series, total
        except (urllib.error.URLError, RuntimeError, KeyError, ValueError, TypeError) as exc:
            problems.append(f"{name}: {exc}")
    raise RuntimeError("all contribution sources failed -> " + " | ".join(problems))


def fetch_stats(user: str):
    me = http_json(f"{API}/users/{user}")
    repos, page = [], 1
    while True:
        chunk = http_json(f"{API}/users/{user}/repos?per_page=100&page={page}&sort=updated")
        if not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
        if page > 10:
            break

    stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
    langs: "dict[str, int]" = {}
    for r in repos:
        # Deliberately not swallowed: a missing repo would skew the language bar.
        for name, size in http_json(r["languages_url"]).items():
            langs[name] = langs.get(name, 0) + int(size)
    return {
        "public_repos": int(me.get("public_repos", len(repos))),
        "followers": int(me.get("followers", 0)),
        "following": int(me.get("following", 0)),
        "stars": stars,
        "langs": sorted(langs.items(), key=lambda kv: -kv[1])[:8],
    }


# --------------------------------------------------------------------------- #
# SVG helpers
# --------------------------------------------------------------------------- #
def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def fmt_int(n: int) -> str:
    return f"{n:,}"


def nice_max(v: int):
    """Axis ceiling that splits into exactly two halves (0 / mid / max)."""
    if v <= 0:
        return 4
    for cand in (4, 6, 10, 20, 30, 50, 100, 150, 200, 300, 500, 1000,
                 1500, 2000, 3000, 5000, 10000):
        if v <= cand:
            return cand
    return int(math.ceil(v / 5000.0) * 5000)


def card(x, y, w, h) -> str:
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
            f'fill="{BG}" stroke="{BORDER}" stroke-width="1"/>')


def title(x, y, text, size=19) -> str:
    return (f'<text x="{x}" y="{y}" font-family="{UI_FONT}" font-size="{size}" '
            f'font-weight="700" fill="{ACCENT}">{esc(text)}</text>')


def small(x, y, text, anchor="start", fill=MUTED, size=12) -> str:
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{UI_FONT}" '
            f'font-size="{size}" fill="{fill}">{esc(text)}</text>')


def text_w(s: str, size: float) -> float:
    """Rough advance width: CJK glyphs ~1em, latin ~0.56em (good enough to avoid overlap)."""
    return sum(size * (1.0 if ord(c) > 0x2E80 else 0.56) for c in s)


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def build_chart(x, y, w, h, mondays, series, total, lang):
    months = MONTHS_ZH if lang == "zh" else MONTHS_EN
    out = [card(x, y, w, h)]
    pad = 20
    out.append(title(x + pad, y + 36, CTX["chart_title"]))
    out.append(small(x + pad, y + 58, CTX["chart_sub"].format(n=fmt_int(total)), size=13))
    out.append(small(x + w - pad, y + 36, STAMP, anchor="end"))

    pl, pr = x + 62, x + w - pad
    pt, pb = y + 82, y + h - 46
    ymax = nice_max(max(series) if series else 0)
    ticks = 2

    def px(i):
        n = max(1, len(series) - 1)
        return pl + (pr - pl) * i / n

    def py(v):
        return pb - (pb - pt) * (v / ymax)

    for t in range(ticks + 1):
        val = ymax * t / ticks
        yy = py(val)
        out.append(f'<line x1="{pl}" y1="{yy:.1f}" x2="{pr}" y2="{yy:.1f}" '
                   f'stroke="{BORDER}" stroke-width="1" opacity="{0.55 if t else 1}"/>')
        out.append(small(pl - 10, yy + 4, f"{val:g}", anchor="end", size=11))

    pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(series))
    out.append(
        f'<path d="M {pl},{pb} L ' + " L ".join(pts.split()) + f' L {pr},{pb} Z" '
        f'fill="url(#areaGrad)" opacity="0.45"/>'
    )
    out.append(f'<polyline points="{pts}" fill="none" stroke="{ACCENT}" stroke-width="2" '
               f'stroke-dasharray="5 4" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, v in enumerate(series):
        out.append(f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="2.6" fill="{ACCENT}"/>')

    last_key = None
    for i, m in enumerate(mondays):
        key = (m.year, m.month)
        if key == last_key:
            continue
        last_key = key
        lab = months[m.month - 1]
        if m.month == 1 or i == 0:
            lab = f"{lab} {m.year}"
        out.append(small(min(px(i), pr - 14), pb + 22, lab, size=11))
    return "".join(out)


def build_stats(x, y, w, h, stats, user):
    out = [card(x, y, w, h)]
    pad = 20
    full = CTX["stats_title"].format(user=user)
    short = CTX["stats_title_short"]
    # Narrow cards: the timestamp wins, so drop the username rather than collide.
    head = full if text_w(full, 18) + text_w(STAMP, 11) + 24 <= w - 2 * pad else short
    out.append(title(x + pad, y + 36, head, size=18))
    out.append(small(x + w - pad, y + 35, STAMP, anchor="end", size=11))
    out.append(f'<line x1="{x + pad}" y1="{y + 50}" x2="{x + w - pad}" y2="{y + 50}" '
               f'stroke="{BORDER}" stroke-width="1"/>')

    cells = [
        (CTX["stars"], fmt_int(stats["stars"])),
        (CTX["repos"], fmt_int(stats["public_repos"])),
        (CTX["followers"], fmt_int(stats["followers"])),
        (CTX["following"], fmt_int(stats["following"])),
    ]
    col_w = (w - 2 * pad) / 2
    for i, (lab, val) in enumerate(cells):
        cx = x + pad + (i % 2) * col_w
        cy = y + 84 + (i // 2) * 84
        out.append(f'<circle cx="{cx + 6}" cy="{cy - 5}" r="5" fill="{ACCENT}"/>')
        out.append(small(cx + 20, cy, lab, fill=MUTED, size=13))
        out.append(f'<text x="{cx + 20}" y="{cy + 36}" font-family="{UI_FONT}" '
                   f'font-size="28" font-weight="700" fill="{TEXT}">{esc(val)}</text>')
    return "".join(out)


def build_langs(x, y, w, h, langs):
    out = [card(x, y, w, h)]
    pad = 20
    out.append(title(x + pad, y + 36, CTX["langs_title"], size=18))
    out.append(small(x + w - pad, y + 35, STAMP, anchor="end", size=11))
    out.append(f'<line x1="{x + pad}" y1="{y + 50}" x2="{x + w - pad}" y2="{y + 50}" '
               f'stroke="{BORDER}" stroke-width="1"/>')

    bar_y, bar_h = y + 68, 14
    total = sum(sz for _, sz in langs) or 1
    clip = f"langClip{int(x)}"
    out.append(f'<defs><clipPath id="{clip}"><rect x="{x + pad}" y="{bar_y}" '
               f'width="{w - 2 * pad}" height="{bar_h}" rx="7"/></clipPath></defs>')
    out.append(f'<rect x="{x + pad}" y="{bar_y}" width="{w - 2 * pad}" height="{bar_h}" '
               f'rx="7" fill="{BORDER}"/>')
    segs, cursor = [], float(x + pad)
    for i, (name, size) in enumerate(langs):
        width = (w - 2 * pad) * size / total
        color = LANG_COLORS.get(name) or FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
        segs.append(f'<rect x="{cursor:.2f}" y="{bar_y}" width="{width + 0.6:.2f}" '
                    f'height="{bar_h}" fill="{color}"/>')
        cursor += width
    out.append(f'<g clip-path="url(#{clip})">{"".join(segs)}</g>')

    col_w = (w - 2 * pad) / 2
    for i, (name, size) in enumerate(langs):
        color = LANG_COLORS.get(name) or FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
        cx = x + pad + (i % 2) * col_w
        cy = y + 118 + (i // 2) * 34
        pct = size * 100.0 / total
        out.append(f'<circle cx="{cx + 6}" cy="{cy - 4}" r="5.5" fill="{color}"/>')
        out.append(f'<text x="{cx + 20}" y="{cy}" font-family="{UI_FONT}" font-size="13" '
                   f'font-weight="700" fill="{TEXT}">{esc(name)}</text>')
        out.append(small(cx + col_w - 14, cy, f"{pct:.1f}%", anchor="end", size=12))
    return "".join(out)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", default="lska367")
    ap.add_argument("--lang", choices=["en", "zh"], default="en")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=900)
    args = ap.parse_args()

    global CTX, STAMP
    CTX = I18N[args.lang]
    STAMP = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    mondays, series, total = fetch_weekly(args.username)
    stats = fetch_stats(args.username)

    W, pad = args.width, 16
    inner = W - 2 * pad
    left_w = inner * 0.5 - 6
    right_w = inner - left_w - 12
    chart_h, cards_h = 300, 250
    H = pad + chart_h + 16 + cards_h + pad

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Activity signal">',
        "<defs><linearGradient id=\"areaGrad\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">"
        f'<stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.75"/>'
        f'<stop offset="100%" stop-color="{ACCENT}" stop-opacity="0.05"/>'
        "</linearGradient></defs>",
        build_chart(pad, pad, inner, chart_h, mondays, series, total, args.lang),
        build_stats(pad, pad + chart_h + 16, left_w, cards_h, stats, args.username),
        build_langs(pad + left_w + 12, pad + chart_h + 16, right_w, cards_h,
                    stats["langs"]),
        "</svg>",
    ]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("".join(svg))
    print(f"wrote {args.out}: {len(series)} weeks, {total} contributions, "
          f"{fmt_int(stats['stars'])} stars, {len(stats['langs'])} languages")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (urllib.error.URLError, RuntimeError, TimeoutError, KeyError, ValueError) as exc:
        # Keep the previously committed SVG rather than publishing an empty card.
        print(f"error: data unavailable, previous image kept ({exc})", file=sys.stderr)
        sys.exit(1)
