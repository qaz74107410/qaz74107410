#!/usr/bin/env python3
"""Render the last 12 months of contributions as a playable-looking shooter.

Every non-empty day on the contribution calendar becomes a target; a ship
sweeps the grid left to right, firing at each one in turn, then the wave
resets. Pure SVG + SMIL, so it animates inside GitHub's <img> render and
needs no third-party image service.

Usage:
    GITHUB_TOKEN=... python3 scripts/gen_shooter.py [login]

Output:
    assets/shooter.svg
"""
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_cards import (  # noqa: E402
    ASSETS, DIM, EMERALD, FONT, LEVEL_COLORS, MUTED, TEXT,
    esc, graphql, head, title,
)

CELL, GAP = 11, 3
STEP = CELL + GAP
GX, GY = 52, 70            # grid origin
SHIP_Y = GY + 7 * STEP + 92
FLIGHT = 0.16              # seconds a bullet is in the air
SPEED = 1500.0             # ship travel, px per second
MIN_MOVE = 0.05
OUTRO = 3.2                # "wave cleared" hold before reset
MAX_ROUND = 34.0           # cap so heavy years still loop in reasonable time


def level(c, peak):
    if c == 0:
        return 0
    f = c / peak
    return 1 if f <= 0.25 else 2 if f <= 0.5 else 3 if f <= 0.8 else 4


def build(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=1) or 1

    cells, targets = [], []
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            row = int(datetime.strptime(d["date"], "%Y-%m-%d").strftime("%w"))  # Sunday-first, like GitHub
            lvl = level(d["contributionCount"], peak)
            x, y = GX + wi * STEP, GY + row * STEP
            cells.append((x, y))
            if lvl:
                targets.append(dict(x=x, y=y, lvl=lvl, wi=wi, row=row,
                                    date=d["date"], count=d["contributionCount"]))
    # sweep columns left to right, bottom row first, like clearing a wave
    targets.sort(key=lambda t: (t["wi"], -t["row"]))

    grid_w = len(weeks) * STEP - GAP
    W = max(GX + grid_w + 26, 820)
    H = SHIP_Y + 52
    home = GX + grid_w / 2.0

    # --- timeline -----------------------------------------------------------
    scale = 1.0
    for _ in range(2):
        t, x = 0.6, home
        ship = [(0.0, home), (t, home)]
        for tg in targets:
            cx = tg["x"] + CELL / 2.0
            t += max(MIN_MOVE, abs(cx - x) / SPEED) * scale
            ship.append((t, cx))
            tg["fire"] = t
            t += FLIGHT * scale
            tg["hit"] = t
            ship.append((t, cx))
            x = cx
        end = t + 0.5
        T = end + 0.9 + OUTRO
        if T <= MAX_ROUND or scale < 1.0:
            break
        scale = (MAX_ROUND - 0.9 - OUTRO - 1.1) / (T - 0.9 - OUTRO - 1.1)
    ship.append((end + 0.9, home))
    ship.append((T, home))

    def kt(times):
        out, prev = [], 0.0
        for v in times:
            f = max(prev, min(1.0, round(v / T, 5)))
            out.append(f)
            prev = f
        out[0], out[-1] = 0.0, 1.0
        return ";".join("%g" % f for f in out)

    eps = 0.004
    ship_x = ";".join("%.1f" % px for _, px in ship)
    ship_k = kt([tt for tt, _ in ship])

    bullet_y, bullet_yt, bullet_o, bullet_ot = [SHIP_Y - 14], [0.0], [0], [0.0]
    for tg in targets:
        bullet_y += [SHIP_Y - 14, tg["y"] + CELL]
        bullet_yt += [tg["fire"], tg["hit"]]
        bullet_o += [0, 1, 1, 0]
        bullet_ot += [tg["fire"], tg["fire"] + eps, tg["hit"] - eps, tg["hit"]]
    bullet_y.append(SHIP_Y - 14)
    bullet_yt.append(T)
    bullet_o.append(0)
    bullet_ot.append(T)

    # --- svg ----------------------------------------------------------------
    total = cal["totalContributions"]
    s = [head(W, H, f"Space shooter: {len(targets)} contribution days, {total} contributions")]
    s.append(title(26, 32, "SPACE SHOOTER · LAST 12 MONTHS OF COMMITS AS INVADERS"))
    s.append(f'  <text x="{W - 26}" y="32" text-anchor="end" font-family="{FONT}" font-size="12" '
             f'fill="{TEXT}">SCORE <tspan fill="{EMERALD}" font-weight="700">{total:,}</tspan></text>\n')

    # starfield
    rnd = random.Random(7410)
    for _ in range(46):
        sx, sy = rnd.uniform(20, W - 20), rnd.uniform(48, H - 14)
        if GX - 6 < sx < GX + grid_w + 6 and GY - 6 < sy < GY + 7 * STEP + 6:
            continue
        r = rnd.choice((0.6, 0.8, 1.1))
        d = rnd.uniform(1.8, 4.5)
        s.append(f'  <circle cx="{sx:.0f}" cy="{sy:.0f}" r="{r}" fill="#CFE9DE">'
                 f'<animate attributeName="opacity" values="0.15;0.8;0.15" dur="{d:.1f}s" '
                 f'begin="{rnd.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>\n')

    # invader grid (bobs gently)
    s.append('  <g>\n')
    s.append('    <animateTransform attributeName="transform" type="translate" '
             'values="0,0;0,3;0,0" dur="2.4s" repeatCount="indefinite"/>\n')
    for x, y in cells:
        s.append(f'    <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVEL_COLORS[0]}"/>\n')
    for tg in targets:
        h = tg["hit"]
        s.append(
            f'    <rect x="{tg["x"]}" y="{tg["y"]}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{LEVEL_COLORS[tg["lvl"]]}"><title>{tg["date"]}: {tg["count"]}</title>'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="{kt([0, h, h + 0.1, T])}" '
            f'dur="{T:.2f}s" repeatCount="indefinite"/></rect>\n')
        cx, cy = tg["x"] + CELL / 2.0, tg["y"] + CELL / 2.0
        k = kt([0, h, h + eps, h + 0.38, T])
        s.append(
            f'    <circle cx="{cx}" cy="{cy}" r="2" fill="none" stroke="#B9FBE0" stroke-width="1.6" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{k}" dur="{T:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="2;2;2;11;11" keyTimes="{k}" dur="{T:.2f}s" repeatCount="indefinite"/>'
            '</circle>\n')
    s.append('  </g>\n')

    # bullet
    s.append(f'  <rect x="-1.5" y="0" width="3" height="9" rx="1.5" fill="#B9FBE0" opacity="0">\n'
             f'    <animate attributeName="x" values="{";".join("%.1f" % (px - 1.5) for _, px in ship)}" '
             f'keyTimes="{ship_k}" dur="{T:.2f}s" repeatCount="indefinite"/>\n'
             f'    <animate attributeName="y" values="{";".join("%.1f" % v for v in bullet_y)}" '
             f'keyTimes="{kt(bullet_yt)}" dur="{T:.2f}s" repeatCount="indefinite"/>\n'
             f'    <animate attributeName="opacity" values="{";".join(map(str, bullet_o))}" '
             f'keyTimes="{kt(bullet_ot)}" dur="{T:.2f}s" repeatCount="indefinite"/>\n'
             '  </rect>\n')

    # ship
    s.append(f'  <g transform="translate({home:.1f},{SHIP_Y})">\n'
             f'    <animateTransform attributeName="transform" type="translate" '
             f'values="{";".join("%.1f,%d" % (px, SHIP_Y) for _, px in ship)}" keyTimes="{ship_k}" '
             f'dur="{T:.2f}s" repeatCount="indefinite"/>\n'
             '    <path d="M-3 10h6l-3 7z" fill="#FBBF24">'
             '<animate attributeName="opacity" values="1;0.35;1" dur="0.18s" repeatCount="indefinite"/></path>\n'
             f'    <path d="M0 -13 L3 -6 L3 -2 L10 3 L10 8 L3 6 L2 10 L-2 10 L-3 6 L-10 8 L-10 3 L-3 -2 L-3 -6 Z" '
             f'fill="{EMERALD}"/>\n'
             '    <path d="M0 -8 L1.6 -3 L-1.6 -3 Z" fill="#0B0F14"/>\n'
             '  </g>\n')

    # ground line + hud
    s.append(f'  <rect x="26" y="{H - 22}" width="{W - 52}" height="1" fill="{MUTED}" fill-opacity="0.18"/>\n')
    s.append(f'  <text x="26" y="{H - 8}" font-family="{FONT}" font-size="10" fill="{DIM}">'
             f'{len(targets)} active days · peak {peak} in a day · one target per day, brighter = busier</text>\n')
    s.append(f'  <text x="{W - 26}" y="{H - 8}" text-anchor="end" font-family="{FONT}" font-size="10" fill="{DIM}">'
             'regenerated daily from the GitHub API</text>\n')

    # wave cleared banner
    ko = kt([0, end + 0.3, end + 0.6, T - 0.4, T])
    s.append(f'  <g opacity="0" font-family="{FONT}" text-anchor="middle">\n'
             f'    <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{ko}" dur="{T:.2f}s" repeatCount="indefinite"/>\n'
             f'    <text x="{home:.0f}" y="{GY + 3.5 * STEP}" font-size="22" font-weight="700" letter-spacing="6" fill="{EMERALD}">WAVE CLEARED</text>\n'
             f'    <text x="{home:.0f}" y="{GY + 3.5 * STEP + 22}" font-size="12" fill="{TEXT}">'
             f'{total:,} contributions · new wave tomorrow</text>\n'
             '  </g>\n')
    s.append("</svg>\n")
    return "".join(s), dict(targets=len(targets), seconds=round(T, 1), total=total)


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "qaz74107410"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set")
    svg, info = build(graphql(token, login))
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "shooter.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    info["bytes"] = len(svg)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
