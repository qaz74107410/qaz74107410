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
from gen_cards import graphql  # noqa: E402
from manifest_style import (  # noqa: E402
    ASSETS, FORM, FORM_SOFT, PAPER, PAPER_DEEP, RULE, STAMP, TYPED, TYPED_SOFT, Sheet,
)

# box fills by activity level: form-ink tints on the paper
LEVELS = [PAPER_DEEP, "#8DAE9C", "#5E8C75", "#3B6B55", FORM]

CELL, GAP = 11, 3
STEP = CELL + GAP
GX, GY = 56, 78            # grid origin
SHIP_Y = GY + 7 * STEP + 70
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
    W = 880
    H = SHIP_Y + 66
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

    # --- svg: the voyage log, on the same carbonless paper as the B/L --------
    total = cal["totalContributions"]
    sh = Sheet(W, H, f"Voyage log: {len(targets)} active days, {total} contributions; "
                     "a ship clears each day of the last 12 months, then the wave resets")
    sh.text(22, 36, "VOYAGE LOG", "title", 22, FORM, extra='letter-spacing="0.4"')
    sh.label(176, 35, "Last 12 months, one cargo box per active day", 11.5, FORM_SOFT)
    sh.label(W - 22, 22, "Cargo cleared", 10.5, FORM, "end")
    sh.text(W - 22, 42, f"{total:,} contributions", "typedb", 15, TYPED, "end")
    sh.hline(54, color=FORM, w=1.5)
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        sh.label(20, GY + row * STEP + 9, name, 9.5, FORM_SOFT)

    sh.raw('<g>')
    sh.raw('<animateTransform attributeName="transform" type="translate" '
           'values="0,0;0,2;0,0" dur="2.4s" repeatCount="indefinite"/>')
    for x, y in cells:
        sh.raw(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="1.5" fill="{PAPER_DEEP}"/>')
    for tg in targets:
        h = tg["hit"]
        sh.raw(
            f'<rect x="{tg["x"]}" y="{tg["y"]}" width="{CELL}" height="{CELL}" rx="1.5" '
            f'fill="{LEVELS[tg["lvl"]]}"><title>{tg["date"]}: {tg["count"]}</title>'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="{kt([0, h, h + 0.1, T])}" '
            f'dur="{T:.2f}s" repeatCount="indefinite"/></rect>')
        cx, cy = tg["x"] + CELL / 2.0, tg["y"] + CELL / 2.0
        k = kt([0, h, h + eps, h + 0.38, T])
        sh.raw(
            f'<circle cx="{cx}" cy="{cy}" r="2" fill="none" stroke="{STAMP}" stroke-width="1.5" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;0.9;0;0" keyTimes="{k}" dur="{T:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="2;2;2;10;10" keyTimes="{k}" dur="{T:.2f}s" repeatCount="indefinite"/>'
            '</circle>')
    sh.raw('</g>')

    # shot
    sh.raw(f'<rect x="-1.5" y="0" width="3" height="9" rx="1.5" fill="{STAMP}" opacity="0">'
           f'<animate attributeName="x" values="{";".join("%.1f" % (px - 1.5) for _, px in ship)}" '
           f'keyTimes="{ship_k}" dur="{T:.2f}s" repeatCount="indefinite"/>'
           f'<animate attributeName="y" values="{";".join("%.1f" % v for v in bullet_y)}" '
           f'keyTimes="{kt(bullet_yt)}" dur="{T:.2f}s" repeatCount="indefinite"/>'
           f'<animate attributeName="opacity" values="{";".join(map(str, bullet_o))}" '
           f'keyTimes="{kt(bullet_ot)}" dur="{T:.2f}s" repeatCount="indefinite"/></rect>')

    # the ship: a small container-ship hull seen from the side, drawn in form ink
    sh.raw(f'<g transform="translate({home:.1f},{SHIP_Y})">'
           f'<animateTransform attributeName="transform" type="translate" '
           f'values="{";".join("%.1f,%d" % (px, SHIP_Y) for _, px in ship)}" keyTimes="{ship_k}" '
           f'dur="{T:.2f}s" repeatCount="indefinite"/>'
           f'<path d="M-22 2 L22 2 L17 11 L-18 11 Z" fill="{FORM}"/>'
           f'<rect x="-17" y="-6" width="9" height="7" fill="{STAMP}"/>'
           f'<rect x="-7" y="-6" width="9" height="7" fill="{FORM_SOFT}"/>'
           f'<rect x="3" y="-6" width="9" height="7" fill="{TYPED}"/>'
           f'<rect x="-2" y="-13" width="6" height="7" fill="{FORM}"/>'
           f'<rect x="14" y="-9" width="6" height="10" fill="{FORM}"/></g>')
    # waterline
    sh.hline(SHIP_Y + 14, 22, W - 22, RULE)

    sh.hline(H - 34, color=FORM, w=1)
    sh.text(22, H - 13, f"{len(targets)} active days. Peak {peak} in a day. Darker box, busier day.",
            "typed", 12.5, TYPED_SOFT)
    sh.label(W - 22, H - 14, "Retyped daily from the GitHub API", 10.5, FORM_SOFT, "end")

    # all cargo cleared: the stamp comes down, holds, lifts
    ko = kt([0, end + 0.3, end + 0.5, T - 0.4, T])
    sh.raw(f'<g opacity="0" transform="translate({home:.0f} {GY + 3.5 * STEP}) rotate(-6)">'
           f'<animate attributeName="opacity" values="0;0;0.92;0.92;0" keyTimes="{ko}" dur="{T:.2f}s" repeatCount="indefinite"/>'
           f'<rect x="-150" y="-34" width="300" height="68" rx="5" fill="{PAPER}" stroke="{STAMP}" stroke-width="3"/>'
           f'<rect x="-143" y="-27" width="286" height="54" rx="3" fill="none" stroke="{STAMP}" stroke-width="1.2"/>')
    sh.text(0, -2, "ALL CARGO CLEARED", "title", 22, STAMP, "middle", 'letter-spacing="1"')
    sh.text(0, 19, "new manifest tomorrow", "typedb", 13, STAMP, "middle")
    sh.raw('</g>')
    svg = sh.render(top=True, bottom=True)
    return svg, dict(targets=len(targets), seconds=round(T, 1), total=total)


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
