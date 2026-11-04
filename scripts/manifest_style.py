"""Shared look for the profile: a shipper's copy of a bill of lading.

Pale green carbonless paper, form furniture printed in deep green ink,
values typed in ribbon black, one red rubber stamp. Fonts are subset to the
characters each SVG uses and embedded, because GitHub serves README images
through <img>, which cannot load web fonts.
"""
import base64
import io
import os
import re

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
ASSETS = os.path.join(ROOT, "assets")

PAPER = "#E3ECE3"      # carbonless shipper's copy
PAPER_DEEP = "#D3DFD4"  # pressed areas, empty cells
FORM = "#1F5641"       # printed form ink
FORM_SOFT = "#5E7F70"  # secondary printed text
RULE = "#8FAA9B"       # hairline rules
TYPED = "#1B1E26"      # typewriter ribbon
TYPED_SOFT = "#4A4F5C"
STAMP = "#B3302A"      # rubber stamp

FACES = {
    "label": ("Archivo-SemiCondensed-Medium.ttf", "BL Label"),
    "title": ("Archivo-SemiCondensed-ExtraBold.ttf", "BL Title"),
    "typed": ("CourierPrime-Regular.ttf", "BL Typed"),
    "typedb": ("CourierPrime-Bold.ttf", "BL Typed Bold"),
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _font_face(kind, chars):
    fname, family = FACES[kind]
    font = TTFont(os.path.join(FONTS, fname))
    opts = subset.Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(set(chars))) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff;base64,{data}) format('woff');}}"


class Sheet:
    """Collects SVG text runs per face so the embedded fonts carry only used glyphs."""

    def __init__(self, w, h, label):
        self.w, self.h, self.aria = w, h, label
        self.body = []
        self.used = {k: set() for k in FACES}

    def raw(self, s):
        self.body.append(s)

    def text(self, x, y, s, kind="typed", size=14, fill=TYPED, anchor="start", extra=""):
        self.used[kind].update(str(s))
        fam = FACES[kind][1]
        a = "" if anchor == "start" else f' text-anchor="{anchor}"'
        self.body.append(
            f'<text x="{x}" y="{y}" font-family="\'{fam}\'" font-size="{size}" fill="{fill}"{a} {extra}>'
            f'{esc(s)}</text>')

    def label(self, x, y, s, size=10.5, fill=FORM, anchor="start"):
        self.text(x, y, s, "label", size, fill, anchor, 'letter-spacing="0.5"')

    def hline(self, y, x0=0, x1=None, color=RULE, w=1):
        x1 = self.w if x1 is None else x1
        self.body.append(f'<rect x="{x0}" y="{y - w / 2:.1f}" width="{x1 - x0}" height="{w}" fill="{color}"/>')

    def vline(self, x, y0, y1, color=RULE, w=1):
        self.body.append(f'<rect x="{x - w / 2:.1f}" y="{y0}" width="{w}" height="{y1 - y0}" fill="{color}"/>')

    def render(self, top=False, bottom=False):
        css = "".join(_font_face(k, v) for k, v in self.used.items() if v)
        w, h = self.w, self.h
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(self.aria)}">',
            f"<style>{css}</style>",
            f'<rect width="{w}" height="{h}" fill="{PAPER}"/>',
        ]
        out += self.body
        # the sheet's outer frame: sides on every slice, top/bottom only at the ends
        out.append(f'<rect x="0" y="0" width="2" height="{h}" fill="{FORM}"/>')
        out.append(f'<rect x="{w - 2}" y="0" width="2" height="{h}" fill="{FORM}"/>')
        if top:
            out.append(f'<rect x="0" y="0" width="{w}" height="2" fill="{FORM}"/>')
        if bottom:
            out.append(f'<rect x="0" y="{h - 2}" width="{w}" height="2" fill="{FORM}"/>')
        out.append("</svg>\n")
        return "\n".join(out)


def iso6346_check(code):
    """Check digit for an ISO 6346 container number such as 'QAZU741074'."""
    vals, v = {}, 10
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if v % 11 == 0:
            v += 1
        vals[ch] = v
        v += 1
    total = 0
    for i, ch in enumerate(code):
        n = vals[ch] if ch.isalpha() else int(ch)
        total += n * (2 ** i)
    return total % 11 % 10


def write(name, svg):
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
        f.write(svg)
    return len(svg)


def wrap(s, n):
    words, lines, cur = re.split(r"\s+", s.strip()), [], ""
    for wd in words:
        if len(cur) + len(wd) + (1 if cur else 0) > n:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}" if cur else wd
    if cur:
        lines.append(cur)
    return lines
