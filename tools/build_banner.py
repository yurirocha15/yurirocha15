#!/usr/bin/env python3
"""Build assets/banner.svg: a terminal window with the name in ANSI Shadow, a typing line and a looped
robot animation (WebP frames captured from the palletizer scene on yurirocha.com).

Usage: build_banner.py <output.svg> <frames-dir> [terminal|ink|paper]

Everything is SMIL inside one SVG, which GitHub renders (animated) inside <img>.
"""
from __future__ import annotations

import base64
import sys
from html import escape
from pathlib import Path

W, H = 960, 250
NAME = "Yuri Rocha"
PREFIX = "I build "
PHRASES = [
    "real-time robot controllers in C++",
    "interfaces between AI agents and robots",
    "platforms to train and serve AI models",
    "optimized AI models for edge devices",
]
# figlet -f "ANSI Shadow" "Yuri Rocha" (font from github.com/xero/figlet-fonts)
NAME_ART = [
    "██╗   ██╗██╗   ██╗██████╗ ██╗    ██████╗  ██████╗  ██████╗██╗  ██╗ █████╗ ",
    "╚██╗ ██╔╝██║   ██║██╔══██╗██║    ██╔══██╗██╔═══██╗██╔════╝██║  ██║██╔══██╗",
    " ╚████╔╝ ██║   ██║██████╔╝██║    ██████╔╝██║   ██║██║     ███████║███████║",
    "  ╚██╔╝  ██║   ██║██╔══██╗██║    ██╔══██╗██║   ██║██║     ██╔══██║██╔══██║",
    "   ██║   ╚██████╔╝██║  ██║██║    ██║  ██║╚██████╔╝╚██████╗██║  ██║██║  ██║",
    "   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝    ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝",
]
INK, OLIVE_2, OLIVE, STEEL = "#151713", "#37402f", "#59624d", "#34464a"
PAPER, PAPER_2, YELLOW = "#fbfaf3", "#e3e2d8", "#d39b2a"
YELLOW_SOFT, RUST = "#efe4c1", "#a65e2e"
PREFIX_FILL, TYPED_FILL = PAPER_2, YELLOW
SANS = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
FONT = 19
CHAR_W = FONT * 0.6          # textLength pins every glyph to this advance
TYPE, HOLD, DELETE, GAP = 0.055, 1.8, 0.025, 0.35
ROBOT_LOOP = 22.76           # seconds, the palletizer loop: 6 boxes x 3.61 s, then 1.1 s to clear


def typing_timeline():
    """Return (cycle, [(t, width, phrase_index)]) for one loop over all phrases."""
    points, t = [], 0.0
    for i, phrase in enumerate(PHRASES):
        n = len(phrase)
        for c in range(n + 1):
            points.append((t + c * TYPE, c * CHAR_W, i))
        t += n * TYPE + HOLD
        for c in range(n, -1, -1):
            points.append((t + (n - c) * DELETE, c * CHAR_W, i))
        t += n * DELETE + GAP
    return t, points


def typing(x, y):
    cycle, pts = typing_timeline()
    key_times = ";".join(f"{p[0] / cycle:.5f}" for p in pts) + ";1"
    widths = ";".join(f"{p[1]:.1f}" for p in pts) + ";0"
    prefix_w = len(PREFIX) * CHAR_W
    x0 = x + prefix_w
    out = [f'<defs><clipPath id="typed"><rect x="{x0}" y="{y - FONT}" width="0" height="{FONT * 1.6}">'
           f'<animate attributeName="width" values="{widths}" keyTimes="{key_times}" dur="{cycle:.2f}s" '
           f'calcMode="discrete" repeatCount="indefinite"/></rect></clipPath></defs>',
           f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{FONT}" fill="{PREFIX_FILL}" '
           f'textLength="{len(PREFIX.rstrip()) * CHAR_W:.1f}" lengthAdjust="spacing">{escape(PREFIX.rstrip())}</text>',
           '<g clip-path="url(#typed)">']
    for i, phrase in enumerate(PHRASES):
        visible = ";".join("1" if p[2] == i else "0" for p in pts) + (";1" if i == 0 else ";0")
        out.append(f'<text x="{x0}" y="{y}" font-family="{MONO}" font-size="{FONT}" font-weight="700" '
                   f'fill="{TYPED_FILL}" textLength="{len(phrase) * CHAR_W:.1f}" lengthAdjust="spacing" '
                   f'opacity="{1 if i == 0 else 0}">{escape(phrase)}'
                   f'<animate attributeName="opacity" values="{visible}" keyTimes="{key_times}" '
                   f'dur="{cycle:.2f}s" calcMode="discrete" repeatCount="indefinite"/></text>')
    out.append("</g>")
    xs = ";".join(f"{x0 + p[1] + 2:.1f}" for p in pts) + f";{x0 + 2:.1f}"
    out.append(f'<rect x="{x0 + 2}" y="{y - FONT + 3}" width="{FONT * 0.55:.1f}" height="{FONT + 2}" fill="{TYPED_FILL}">'
               f'<animate attributeName="x" values="{xs}" keyTimes="{key_times}" dur="{cycle:.2f}s" '
               f'calcMode="discrete" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" '
               f'repeatCount="indefinite"/></rect>')
    return "".join(out)


def wave(y, amp, length, color, opacity, dur, reverse=False):
    """A wave twice the banner width, translated by one period in a loop."""
    seg = []
    x = -length
    d = [f"M {x} {y}"]
    while x < 2 * W + length:
        d.append(f"q {length / 4} {-amp} {length / 2} 0 t {length / 2} 0")
        x += length
    d.append(f"L {x} {H} L {-length} {H} Z")
    frm, to = (0, -length) if not reverse else (-length, 0)
    seg.append(f'<path d="{" ".join(d)}" fill="{color}" opacity="{opacity}">'
               f'<animateTransform attributeName="transform" type="translate" from="{frm} 0" to="{to} 0" '
               f'dur="{dur}s" repeatCount="indefinite"/></path>')
    return "".join(seg)


def robot(frames_dir: Path, x, y, w, h, panel="#ffffff", panel_opacity=0.35):
    frames = sorted(frames_dir.glob("frame-*.webp"))
    n = len(frames)
    key_times = ";".join(f"{j / n:.4f}" for j in range(n)) + ";1"
    out = [f'<defs><clipPath id="robot"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/></clipPath></defs>',
           f'<g clip-path="url(#robot)"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f6f5ee"/>']
    for i, f in enumerate(frames):
        data = base64.b64encode(f.read_bytes()).decode()
        visible = ";".join("1" if j == i else "0" for j in range(n)) + (";1" if i == 0 else ";0")
        out.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" '
                   f'opacity="{1 if i == 0 else 0}" href="data:image/webp;base64,{data}">'
                   f'<animate attributeName="opacity" values="{visible}" keyTimes="{key_times}" '
                   f'dur="{ROBOT_LOOP}s" calcMode="discrete" repeatCount="indefinite"/></image>')
    out.append("</g>")
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="none" stroke="{panel}" '
               f'stroke-opacity="{panel_opacity}" stroke-width="2"/>')
    return "".join(out)


def ascii_art(lines, x, y, cw, ch, fill=None, shadow=None):
    """Draw ANSI Shadow figlet text as shapes, so it does not depend on the viewer's fonts:
    '█' is a filled cell, the double-line box characters are two thin strokes."""
    fill = fill or YELLOW
    shadow = shadow or "#8a6a2c"
    a, b = 0.38, 0.62                       # positions of the two strokes inside a cell
    blocks, d = [], []
    for r, line in enumerate(lines):
        for c, ch_ in enumerate(line):
            x0, y0 = x + c * cw, y + r * ch
            X = lambda f: f"{x0 + f * cw:.2f}"
            Y = lambda f: f"{y0 + f * ch:.2f}"
            if ch_ == "█":
                blocks.append(f"M{X(0)} {Y(0)}h{cw:.2f}v{ch:.2f}h{-cw:.2f}z")
            elif ch_ == "═":
                d.append(f"M{X(0)} {Y(a)}H{X(1)}M{X(0)} {Y(b)}H{X(1)}")
            elif ch_ == "║":
                d.append(f"M{X(a)} {Y(0)}V{Y(1)}M{X(b)} {Y(0)}V{Y(1)}")
            elif ch_ == "╗":
                d.append(f"M{X(0)} {Y(a)}H{X(b)}V{Y(1)}M{X(0)} {Y(b)}H{X(a)}V{Y(1)}")
            elif ch_ == "╔":
                d.append(f"M{X(1)} {Y(a)}H{X(a)}V{Y(1)}M{X(1)} {Y(b)}H{X(b)}V{Y(1)}")
            elif ch_ == "╝":
                d.append(f"M{X(0)} {Y(b)}H{X(b)}V{Y(0)}M{X(0)} {Y(a)}H{X(a)}V{Y(0)}")
            elif ch_ == "╚":
                d.append(f"M{X(1)} {Y(b)}H{X(a)}V{Y(0)}M{X(1)} {Y(a)}H{X(b)}V{Y(0)}")
    return (f'<path d="{"".join(d)}" fill="none" stroke="{shadow}" stroke-width="{cw * 0.14:.2f}"/>'
            f'<path d="{"".join(blocks)}" fill="{fill}" shape-rendering="crispEdges"/>')


THEMES = {
    # Flat site ink with a faint grid and quiet waves.
    "ink": dict(bg=INK, grid=("#ffffff", 0.05), waves=[("#23261f", 1), ("#2c3027", 0.8)],
                name=PAPER, prefix=PAPER_2, typed=YELLOW, panel="#ffffff", panel_opacity=0.25, bar=False),
    # The site's paper page: light background, ink name, rust typing.
    "paper": dict(bg="#eeeee7", grid=(INK, 0.06), waves=[(PAPER_2, 1), (YELLOW_SOFT, 0.9)],
                  name=INK, prefix="#5d6259", typed=RUST, panel="#cdcdc1", panel_opacity=1, bar=False),
    # A terminal window: near-black, title bar, no waves.
    "terminal": dict(bg="#0c0d0b", grid=None, waves=[], name=PAPER, prefix=PAPER_2, typed=YELLOW,
                     panel="#ffffff", panel_opacity=0.2, bar=True),
}


def main():
    out_path, frames_dir = Path(sys.argv[1]), Path(sys.argv[2])
    th = THEMES[sys.argv[3] if len(sys.argv) > 3 else "terminal"]
    global PREFIX_FILL, TYPED_FILL
    PREFIX_FILL, TYPED_FILL = th["prefix"], th["typed"]
    defs = f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>'
    if th["grid"]:
        defs += ('<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
                 f'<path d="M 24 0 L 0 0 0 24" fill="none" stroke="{th["grid"][0]}" '
                 f'stroke-opacity="{th["grid"][1]}"/></pattern>')
    dy = 12 if th["bar"] else 0
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{NAME}. I build {escape(", ".join(PHRASES))}.">',
        f"<defs>{defs}</defs>",
        '<g clip-path="url(#frame)">',
        f'<rect width="{W}" height="{H}" fill="{th["bg"]}"/>',
        f'<rect width="{W}" height="{H}" fill="url(#grid)"/>' if th["grid"] else "",
    ]
    for (color, opacity), (y, amp, length, dur, rev) in zip(th["waves"], [(H - 34, 16, 480, 9, False),
                                                                          (H - 22, 12, 360, 6, True)]):
        svg.append(wave(y, amp, length, color, opacity, dur, reverse=rev))
    if th["bar"]:
        svg.append(f'<rect width="{W}" height="30" fill="#1c1e1a"/>')
        for i, c in enumerate(["#a65e2e", YELLOW, OLIVE]):
            svg.append(f'<circle cx="{22 + 18 * i}" cy="15" r="5.5" fill="{c}"/>')
        svg.append(f'<text x="{W / 2}" y="20" font-family="{MONO}" font-size="12" fill="#8a8d84" '
                   f'text-anchor="middle">~/yurirocha15</text>')
    if th["bar"]:
        svg.append(f'<text x="50" y="70" font-family="{MONO}" font-size="14" fill="#8a8d84">'
                   f'<tspan fill="{YELLOW}">$</tspan> whoami</text>')
        svg.append(ascii_art(NAME_ART, 50, 84, 5.0, 10.0))
        svg.append(typing(50, 186))
        svg.append(robot(frames_dir, 612, 46, 316, 180, th["panel"], th["panel_opacity"]))
    else:
        svg += [
            f'<text x="48" y="106" font-family="{SANS}" font-size="50" font-weight="800" '
            f'fill="{th["name"]}">{NAME}</text>',
            typing(50, 154),
            robot(frames_dir, 612, 26, 316, 184, th["panel"], th["panel_opacity"]),
        ]
    svg.append("</g></svg>")
    out_path.write_text("".join(svg), encoding="utf-8")
    print(f"{out_path.name}\t{out_path.stat().st_size // 1024} KiB\ttyping cycle {typing_timeline()[0]:.1f}s")


if __name__ == "__main__":
    main()
