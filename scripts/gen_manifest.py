#!/usr/bin/env python3
"""Render the profile README as a bill of lading, in slices.

The sheet is cut into horizontal slices so each line of cargo can be its own
link in the README; stacked with align="top" they read as one document.

Usage:
    GITHUB_TOKEN=... python3 scripts/gen_manifest.py [login]

Outputs assets/bl-head.svg, assets/bl-goods-N.svg, assets/bl-stc.svg, assets/bl-foot.svg
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest_style import (  # noqa: E402
    ASSETS, ROOT, T, Sheet, iso6346_check, suffix, wrap, write,
)

W = 880
C1, C2 = 262, 672          # goods column rules
OWNER, SERIAL = "QAZU", "741074"


def api(path, token):
    req = urllib.request.Request("https://api.github.com/" + path, headers={
        "Authorization": "bearer " + token, "User-Agent": "profile-manifest"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def head():
    s = Sheet(W, 446, "Bill of lading: Komsan Nipharat, full-stack engineer, Nonthaburi, Thailand")
    # title block
    s.text(22, 52, "BILL OF LADING", "title", 36, T.FORM, extra='letter-spacing="0.4"')
    s.label(23, 76, "Combined transport  ·  shipper's copy  ·  not negotiable", 11.5, T.FORM_SOFT)
    s.vline(574, 0, 96, T.FORM, 1.5)
    s.label(592, 28, "B/L number")
    s.text(592, 66, f"{OWNER} {SERIAL}", "typedb", 25, T.TYPED)
    cx = 592 + 11 * 15 + 10
    s.raw(f'<rect x="{cx}" y="44" width="26" height="30" fill="none" stroke="{T.TYPED}" stroke-width="1.6"/>')
    s.text(cx + 13, 66, str(iso6346_check(OWNER + SERIAL)), "typedb", 25, T.TYPED, "middle")
    s.label(592, 88, "ISO 6346 check digit, boxed", 9.5, T.FORM_SOFT)
    s.hline(96, color=T.FORM, w=1.5)

    # shipper / consignee
    s.vline(440, 96, 214)
    s.label(20, 117, "Shipper")
    s.text(20, 145, "KOMSAN NIPHARAT", "typedb", 24)
    s.text(20, 170, "Full-stack engineer", "typed", 15)
    s.text(20, 192, "Pak Kret, Nonthaburi, Thailand", "typed", 15)
    s.label(458, 117, "Consignee")
    s.text(458, 145, "TO ORDER", "typedb", 19)
    s.text(458, 170, "of your engineering team", "typed", 15)
    s.hline(214)

    # route: three ports
    ports = [
        ("Place of receipt", "NECTEC", "Research assistant", "2017 – 2020"),
        ("Port of transhipment", "AddTech Hub", "Payments and MVAS", "2020 – 2023"),
        ("Vessel", "GRAM Software Solution", "Container yard operations", "2023 – present"),
    ]
    cw = W / 3.0
    for i, (lab, org, role, years) in enumerate(ports):
        x = 20 + i * cw
        if i:
            s.vline(i * cw, 214, 314)
        s.label(x, 235, lab)
        s.text(x, 261, org, "typedb", 15)
        s.text(x, 282, role, "typed", 14)
        s.text(x, 302, years, "typed", 14, T.TYPED_SOFT)
    s.hline(314)

    # notify party / packing
    s.vline(440, 314, 410)
    s.label(20, 335, "Notify party")
    s.text(20, 360, "my-portflio-navy.vercel.app", "typed", 14)
    s.text(20, 381, "linkedin.com/in/komsan-nipharat-187573211", "typed", 14)
    s.label(458, 335, "Packed with")
    s.text(458, 360, "Go, TypeScript, Node.js, NestJS,", "typed", 14)
    s.text(458, 381, "MongoDB, Redis, Angular, React,", "typed", 14)
    s.text(458, 400, "AWS, Docker", "typed", 14)
    s.hline(410, color=T.FORM, w=1.5)

    # goods table header
    s.raw(f'<rect x="0" y="411" width="{W}" height="35" fill="{T.PAPER_DEEP}"/>')
    s.label(20, 433, "Marks and numbers")
    s.label(C1 + 16, 433, "Description of goods")
    s.label(C2 + 16, 433, "Measurement")
    s.vline(C1, 411, 446)
    s.vline(C2, 411, 446)
    s.hline(445.5)
    return s.render(top=True)


def arrow(s, x, y, color=T.FORM):
    s.raw(f'<path d="M{x} {y}h11M{x + 7} {y - 4}l4 4-4 4" fill="none" stroke="{color}" '
          'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')


def goods_row(g, meta, h=84):
    s = Sheet(W, h, f"Cargo: {g['title']}. {g['desc']}")
    s.vline(C1, 0, h)
    s.vline(C2, 0, h)
    s.text(20, 31, g["repo"], "typedb", 14)
    lic = (meta.get("license") or {}).get("spdx_id") or ""
    sub = " · ".join(x for x in (meta.get("language"), lic if lic != "NOASSERTION" else "") if x)
    s.label(20, 53, sub, 11, T.FORM_SOFT)
    s.text(C1 + 16, 31, g["title"], "typedb", 15)
    for i, line in enumerate(wrap(g["desc"], 46)[:2]):
        s.text(C1 + 16, 53 + i * 18, line, "typed", 13.5, T.TYPED_SOFT)
    s.text(C2 + 16, 31, g["measure"], "typed", 14)
    s.label(C2 + 16, 56, "open repository", 11, T.FORM)
    arrow(s, C2 + 104, 52)
    s.hline(h - 0.5)
    return s.render()


def stc_row(g, h=84):
    s = Sheet(W, h, f"Said to contain: {g['title']}. {g['desc']} {g['measure']}.")
    s.raw(f'<rect x="0" y="0" width="{W}" height="{h}" fill="{T.PAPER_DEEP}" fill-opacity="0.55"/>')
    s.vline(C1, 0, h)
    s.vline(C2, 0, h)
    s.text(20, 31, "S.T.C.", "typedb", 14)
    s.label(20, 53, "said to contain, not inspected", 11, T.FORM_SOFT)
    s.text(C1 + 16, 31, g["title"], "typedb", 15)
    for i, line in enumerate(wrap(g["desc"], 46)[:2]):
        s.text(C1 + 16, 53 + i * 18, line, "typed", 13.5, T.TYPED_SOFT)
    s.text(C2 + 16, 31, g["measure"].split(",")[0], "typed", 14)
    s.text(C2 + 16, 53, g["measure"].split(",")[1].strip(), "typed", 14, T.TYPED_SOFT)
    s.hline(h - 0.75, color=T.FORM, w=1.5)
    return s.render()


def foot(now):
    s = Sheet(W, 236, "Remarks and stamp: shipped on board, issued at Nonthaburi")
    s.label(20, 26, "Remarks, measured on board")
    s.text(20, 52, "Tom's Storage fix, Java Flight Recorder, ~4 s of typing in a", "typed", 14)
    s.text(20, 72, "~365-mod pack: search samples 175 to 43, tooltip builds 167 to 10.", "typed", 14)
    s.text(20, 92, "Untested parts are declared untested, not rounded up.", "typed", 14, T.TYPED_SOFT)
    s.hline(110)
    s.vline(440, 110, 236)
    s.label(20, 131, "Place and date of issue")
    s.text(20, 157, f"Nonthaburi, {now.day} {now:%B %Y}", "typed", 15)
    s.label(20, 186, "Number of originals")
    s.text(20, 210, "One. This copy is retyped daily from GitHub.", "typed", 14, T.TYPED_SOFT)

    # the stamp: one red mark, set at an angle like it was pressed by hand
    date = f"{now:%d %b %Y}".upper()
    s.raw(f'<g transform="translate(655 172) rotate(-7)" opacity="0.88">')
    s.raw(f'<rect x="-118" y="-44" width="236" height="88" rx="6" fill="none" stroke="{T.STAMP}" stroke-width="3"/>')
    s.raw(f'<rect x="-111" y="-37" width="222" height="74" rx="3" fill="none" stroke="{T.STAMP}" stroke-width="1.2"/>')
    s.text(0, -8, "SHIPPED ON BOARD", "title", 21, T.STAMP, "middle", 'letter-spacing="1"')
    s.raw(f'<rect x="-92" y="2" width="184" height="1.2" fill="{T.STAMP}"/>')
    s.text(0, 26, date, "typedb", 19, T.STAMP, "middle")
    s.raw("</g>")
    return s.render(bottom=True)


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "qaz74107410"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set")
    data = json.load(open(os.path.join(ROOT, "projects.json"), encoding="utf-8"))
    now = datetime.now(timezone(timedelta(hours=7)))  # Bangkok: the place of issue
    metas = [api(f"repos/{login}/{g['repo']}", token) for g in data["goods"]]
    sizes = {}
    for theme in ("light", "dark"):
        T.use(theme)
        sfx = suffix()
        sizes[f"bl-head{sfx}.svg"] = write(f"bl-head{sfx}.svg", head())
        for i, (g, meta) in enumerate(zip(data["goods"], metas), 1):
            sizes[f"bl-goods-{i}{sfx}.svg"] = write(f"bl-goods-{i}{sfx}.svg", goods_row(g, meta))
        sizes[f"bl-stc{sfx}.svg"] = write(f"bl-stc{sfx}.svg", stc_row(data["said_to_contain"]))
        sizes[f"bl-foot{sfx}.svg"] = write(f"bl-foot{sfx}.svg", foot(now))
    print(json.dumps(sizes))


if __name__ == "__main__":
    main()
