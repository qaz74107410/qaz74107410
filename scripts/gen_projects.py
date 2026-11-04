#!/usr/bin/env python3
"""Render one SVG project card per entry in projects.json.

Data (stars, language, last push) comes from the GitHub REST API; the title and
hook line are authored in projects.json so the copy stays human.

Usage:
    GITHUB_TOKEN=... python3 scripts/gen_projects.py [login]
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
PROJECTS = os.path.join(ROOT, "projects.json")

EMERALD = "#34D399"
TEAL = "#2DD4BF"
CYAN = "#22D3EE"
TEXT = "#E6EDF3"
MUTED = "#9BA7B4"
DIM = "#6E7681"
PANEL = "#101820"
STROKE = "#1E2A33"
FONT = "'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"
MONO = "'SF Mono','JetBrains Mono',ui-monospace,Menlo,Consolas,monospace"

W, H = 440, 176


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def api(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": "bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-project-cards",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ago(iso):
    then = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - then).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return "%dd ago" % days
    if days < 365:
        return "%dmo ago" % (days // 30)
    return "%dy ago" % (days // 365)


def card(p, meta):
    stars = meta.get("stargazers_count", 0)
    lang = meta.get("language") or "—"
    pushed = ago(meta["pushed_at"]) if meta.get("pushed_at") else ""
    featured = p.get("featured", False)

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="{esc(p["title"])}">',
        "  <defs>",
        '    <linearGradient id="ac" x1="0" y1="0" x2="1" y2="0">',
        f'      <stop offset="0%" stop-color="{EMERALD}"/>',
        f'      <stop offset="60%" stop-color="{TEAL}"/>',
        f'      <stop offset="100%" stop-color="{CYAN}"/>',
        "    </linearGradient>",
        "  </defs>",
        f'  <rect width="{W}" height="{H}" rx="16" fill="#0B0F14"/>',
        f'  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="15.25" '
        f'fill="none" stroke="{STROKE}" stroke-width="1.5"/>',
    ]
    if featured:
        s.append(f'  <rect x="0" y="0" width="{W}" height="3" rx="1.5" fill="url(#ac)"/>')

    # index + stars
    s.append(f'  <text x="26" y="36" font-family="{MONO}" font-size="12" letter-spacing="1.6" '
             f'fill="{DIM}">{esc(p["index"])}</text>')
    star_txt = f'★ {stars}' if stars else '☆ 0'
    s.append(f'  <text x="{W - 26}" y="36" text-anchor="end" font-family="{FONT}" font-size="13" '
             f'fill="{EMERALD if stars else DIM}">{esc(star_txt)}</text>')

    # title
    s.append(f'  <text x="26" y="78" font-family="{FONT}" font-size="21" font-weight="700" '
             f'fill="{TEXT}">{esc(p["title"])}</text>')

    # authored hook, two lines
    for i, line in enumerate(p["hook"][:2]):
        s.append(f'  <text x="26" y="{106 + i * 19}" font-family="{FONT}" font-size="14" '
                 f'fill="{MUTED}">{esc(line)}</text>')

    # divider
    s.append(f'  <line x1="26" y1="140" x2="{W - 26}" y2="140" stroke="{STROKE}" stroke-width="1"/>')

    # tag chip
    tag = p["tag"]
    tw = 14 + len(tag) * 6.6 + 14
    s.append(f'  <rect x="26" y="150" width="{tw:.1f}" height="20" rx="10" fill="{PANEL}" '
             f'stroke="{STROKE}" stroke-width="1"/>')
    s.append(f'  <text x="{26 + tw / 2:.1f}" y="164" text-anchor="middle" font-family="{FONT}" '
             f'font-size="11" fill="{EMERALD}">{esc(tag)}</text>')

    # language + pushed
    right = f"{lang}  ·  {pushed}" if pushed else lang
    s.append(f'  <text x="{W - 26}" y="164" text-anchor="end" font-family="{FONT}" font-size="11.5" '
             f'fill="{DIM}">{esc(right)}</text>')
    s.append("</svg>\n")
    return "".join(s)


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "qaz74107410"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set")
    data = json.load(open(PROJECTS))["projects"]
    os.makedirs(ASSETS, exist_ok=True)

    out = []
    for p in data:
        meta = api(f"https://api.github.com/repos/{login}/{p['repo']}", token)
        svg = card(p, meta)
        name = f"project-{p['index']}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(svg)
        out.append({"card": name, "repo": p["repo"], "stars": meta.get("stargazers_count", 0),
                    "language": meta.get("language"), "pushed": meta.get("pushed_at")})
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
