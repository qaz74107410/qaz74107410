#!/usr/bin/env python3
"""Generate self-hosted profile cards (SVG) for a GitHub profile README.

No third-party image services: all data comes from the GitHub GraphQL API and
the cards are rendered here as plain SVG, so the profile keeps working even when
github-readme-stats / streak-stats are rate-limited or offline.

Usage:
    GITHUB_TOKEN=... python3 scripts/gen_cards.py [login]

Outputs (relative to repo root):
    assets/stats.svg          repos / stars / commits / streak
    assets/langs.svg          language mix across owned repos
    assets/contributions.svg  53-week contribution heatmap
"""
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

EMERALD = "#34D399"
TEAL = "#2DD4BF"
CYAN = "#22D3EE"
TEXT = "#E6EDF3"
MUTED = "#8B949E"
DIM = "#6E7681"
PANEL = "#101820"
STROKE = "#1E2A33"
FONT = "'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"

LEVEL_COLORS = ["#0E1620", "#0F3A2E", "#166B4E", "#1FA46F", "#34D399"]
LANG_COLORS = ["#34D399", "#22D3EE", "#3B82F6", "#A78BFA", "#FBBF24", "#F472B6", "#64748B"]

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    name
    followers { totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first:12, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection(from:$from, to:$to) {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def graphql(token, login):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": login,
            "from": start.isoformat() + "T00:00:00Z",
            "to": today.isoformat() + "T23:59:59Z",
        },
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "profile-card-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit("GraphQL error: %s" % json.dumps(body["errors"])[:400])
    return body["data"]["user"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def head(w, h, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">\n'
        '  <defs>\n'
        '    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">\n'
        f'      <stop offset="0%" stop-color="{EMERALD}"/>\n'
        f'      <stop offset="60%" stop-color="{TEAL}"/>\n'
        f'      <stop offset="100%" stop-color="{CYAN}"/>\n'
        "    </linearGradient>\n"
        '    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">\n'
        '      <path d="M32 0H0V32" fill="none" stroke="#8B949E" stroke-width="1" stroke-opacity="0.05"/>\n'
        "    </pattern>\n"
        '    <linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">\n'
        '      <stop offset="0%" stop-color="#34D399" stop-opacity="0"/>\n'
        '      <stop offset="50%" stop-color="#8FF7D6" stop-opacity="0.55"/>\n'
        '      <stop offset="100%" stop-color="#34D399" stop-opacity="0"/>\n'
        "    </linearGradient>\n"
        "  </defs>\n"
        f'  <rect width="{w}" height="{h}" rx="16" fill="#0B0F14"/>\n'
        f'  <rect width="{w}" height="{h}" rx="16" fill="url(#grid)"/>\n'
        f'  <rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="15.25" '
        f'fill="none" stroke="{STROKE}" stroke-width="1.5"/>\n'
    )


def title(x, y, text, size=11.5):
    return (
        f'  <text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'letter-spacing="2.6" fill="{MUTED}">{esc(text)}</text>\n'
        f'  <rect x="{x}" y="{y + 8}" width="26" height="2" rx="1" fill="url(#accent)"/>\n'
    )


def fmt(n):
    if n >= 1000:
        return "%.1fk" % (n / 1000.0) if n < 10000 else "%.0fk" % (n / 1000.0)
    return str(n)


def compute_streaks(days):
    longest = cur = 0
    best = 0
    for d in days:
        if d["contributionCount"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    # current streak: count back from the most recent day
    for d in reversed(days):
        if d["contributionCount"] > 0:
            cur += 1
            best = cur
        else:
            break
    return longest, best


def stats_svg(user):
    repos = user["repositories"]["totalCount"]
    stars = sum(n["stargazerCount"] for n in user["repositories"]["nodes"])
    cc = user["contributionsCollection"]
    commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    total = cc["contributionCalendar"]["totalContributions"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    longest, current = compute_streaks(days)

    tiles = [
        ("PUBLIC REPOS", fmt(repos), "owned, non-fork"),
        ("STARS EARNED", fmt(stars), "across public repos"),
        ("COMMITS · 12 MO", fmt(commits), f"{fmt(total)} contributions"),
        ("LONGEST STREAK", f"{longest}d", f"current {current}d"),
    ]
    W, H = 900, 150
    s = [head(W, H, "GitHub stats")]
    pad, gap = 26, 16
    tw = (W - 2 * pad - 3 * gap) / 4.0
    for i, (label, value, sub) in enumerate(tiles):
        x = pad + i * (tw + gap)
        s.append(f'  <g transform="translate({x:.1f},24)">\n')
        s.append(f'    <rect x="0" y="0" width="{tw:.1f}" height="102" rx="14" fill="{PANEL}" fill-opacity="0.85"/>\n')
        s.append(f'    <rect x="0.75" y="0.75" width="{tw - 1.5:.1f}" height="100.5" rx="13.25" fill="none" stroke="{STROKE}" stroke-width="1.5"/>\n')
        s.append(f'    <rect x="0" y="0" width="3" height="102" rx="1.5" fill="url(#accent)"/>\n')
        s.append(f'    <text x="18" y="30" font-family="{FONT}" font-size="10.5" letter-spacing="1.4" fill="{MUTED}">{esc(label)}</text>\n')
        s.append(f'    <text x="18" y="68" font-family="{FONT}" font-size="30" font-weight="700" fill="{TEXT}">{esc(value)}</text>\n')
        s.append(f'    <text x="18" y="88" font-family="{FONT}" font-size="11.5" fill="{DIM}">{esc(sub)}</text>\n')
        s.append("  </g>\n")
    s.append("</svg>\n")
    return "".join(s), dict(repos=repos, stars=stars, commits=commits, contribution_total=total,
                            longest_streak=longest, current_streak=current)


def langs_svg(user):
    totals = {}
    for n in user["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            totals[e["node"]["name"]] = totals.get(e["node"]["name"], 0) + e["size"]
    grand = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:6]
    rest = grand - sum(v for _, v in top)
    if rest > 0:
        top.append(("Other", rest))

    W, H = 900, 172
    s = [head(W, H, "Language mix")]
    s.append(title(26, 32, "LANGUAGE MIX · OWNED REPOS"))
    x0, barw, barh, y = 26, W - 52, 14, 58
    s.append(f'  <clipPath id="barclip"><rect x="{x0}" y="{y}" width="{barw}" height="{barh}" rx="7"/></clipPath>\n')
    cx = x0
    s.append('  <g clip-path="url(#barclip)">\n')
    for i, (name, size) in enumerate(top):
        w = barw * size / grand
        color = LANG_COLORS[i % len(LANG_COLORS)]
        s.append(f'    <rect x="{cx:.2f}" y="{y}" width="{w:.2f}" height="{barh}" fill="{color}" fill-opacity="0.92"/>\n')
        cx += w
    s.append("  </g>\n")
    # legend: two rows of up to four
    lx, ly = x0, y + 46
    per_row = 4
    for i, (name, size) in enumerate(top):
        col = i % per_row
        row = i // per_row
        px = lx + col * (barw / per_row)
        py = ly + row * 30
        color = LANG_COLORS[i % len(LANG_COLORS)]
        pct = 100.0 * size / grand
        s.append(f'  <circle cx="{px + 4:.1f}" cy="{py - 4}" r="4" fill="{color}"/>\n')
        s.append(f'  <text x="{px + 16:.1f}" y="{py}" font-family="{FONT}" font-size="12.5" fill="{TEXT}">{esc(name)}</text>\n')
        s.append(f'  <text x="{px + 16:.1f}" y="{py + 15}" font-family="{FONT}" font-size="11" fill="{DIM}">{pct:.1f}%</text>\n')
    s.append("</svg>\n")
    return "".join(s), dict(top=top, grand=grand)


def contributions_svg(user):
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    peak = max(counts) or 1

    cell, gap = 11, 3
    W = 52 + len(weeks) * (cell + gap)
    W = max(W, 760) + 26
    H = 200
    s = [head(W, H, "Contribution heatmap")]
    s.append(title(26, 32, "CONTRIBUTIONS · LAST 12 MONTHS"))
    s.append(
        f'  <text x="{W - 26}" y="32" text-anchor="end" font-family="{FONT}" font-size="12" '
        f'fill="{TEXT}">{cal["totalContributions"]:,} total</text>\n'
    )

    gx, gy = 52, 62
    # month labels
    last_month = None
    for wi, w in enumerate(weeks):
        d0 = w["contributionDays"][0]["date"]
        m = int(d0[5:7])
        if m != last_month and int(d0[8:10]) <= 14:
            s.append(
                f'  <text x="{gx + wi * (cell + gap)}" y="{gy - 8}" font-family="{FONT}" '
                f'font-size="10" fill="{DIM}">{"Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[m - 1]}</text>\n'
            )
            last_month = m

    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            di = int(datetime.strptime(d["date"], "%Y-%m-%d").strftime("%w"))
            # reorder so row 0 = Monday
            row = (di - 1) % 7
            c = d["contributionCount"]
            if c == 0:
                lvl = 0
            else:
                frac = c / peak
                lvl = 1 if frac <= 0.25 else 2 if frac <= 0.5 else 3 if frac <= 0.8 else 4
            x = gx + wi * (cell + gap)
            y = gy + row * (cell + gap)
            s.append(
                f'  <rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                f'fill="{LEVEL_COLORS[lvl]}"><title>{d["date"]}: {c}</title></rect>\n'
            )

    # day labels
    for row, name in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
        s.append(
            f'  <text x="26" y="{gy + row * (cell + gap) + 9}" font-family="{FONT}" font-size="10" '
            f'fill="{DIM}">{name}</text>\n'
        )

    # animated scan sweep across the grid (SMIL survives GitHub's <img> render)
    grid_w = len(weeks) * (cell + gap) - gap
    grid_h = 7 * (cell + gap) - gap
    s.append(f'  <clipPath id="hclip"><rect x="{gx}" y="{gy}" width="{grid_w}" height="{grid_h}" rx="3"/></clipPath>\n')
    s.append('  <g clip-path="url(#hclip)">\n')
    s.append(f'    <rect x="{gx - 100}" y="{gy}" width="100" height="{grid_h}" fill="url(#scan)">\n')
    s.append(f'      <animate attributeName="x" values="{gx - 100};{gx + grid_w}" dur="9s" repeatCount="indefinite"/>\n')
    s.append("    </rect>\n  </g>\n")

    # legend (right-aligned, fully inside the card)
    legend_w = 5 * (cell + 4)
    lx = W - 26 - 30 - legend_w - 6
    ly = gy + 7 * (cell + gap) + 16
    s.append(f'  <text x="{lx - 8:.1f}" y="{ly + 9}" text-anchor="end" font-family="{FONT}" font-size="10" fill="{DIM}">Less</text>\n')
    for i, color in enumerate(LEVEL_COLORS):
        s.append(f'  <rect x="{lx + i * (cell + 4):.1f}" y="{ly}" width="{cell}" height="{cell}" rx="2.5" fill="{color}"/>\n')
    s.append(f'  <text x="{lx + legend_w + 6:.1f}" y="{ly + 9}" font-family="{FONT}" font-size="10" fill="{DIM}">More</text>\n')
    s.append("</svg>\n")
    return "".join(s), dict(total=cal["totalContributions"], peak=peak)


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "qaz74107410"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set")
    user = graphql(token, login)
    os.makedirs(ASSETS, exist_ok=True)

    stats, sdata = stats_svg(user)
    langs, ldata = langs_svg(user)
    contrib, cdata = contributions_svg(user)

    written = {}
    for name, svg in (("stats.svg", stats), ("langs.svg", langs), ("contributions.svg", contrib)):
        path = os.path.join(ASSETS, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        written[name] = len(svg)

    print(json.dumps({"login": login, "stats": sdata,
                      "languages": [(n, round(100.0 * v / ldata["grand"], 1)) for n, v in ldata["top"]],
                      "contributions": cdata, "bytes": written}, indent=2))


if __name__ == "__main__":
    main()
