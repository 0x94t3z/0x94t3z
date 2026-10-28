#!/usr/bin/env python3
"""Generate the animated SVGs used by the profile README.

Run from anywhere: python3 scripts/build_assets.py
Writes assets/header.svg, assets/header-light.svg and assets/footer.svg.

assets/avatar.gif is embedded into the header as a data URI: GitHub serves
README images as standalone SVGs, which cannot load external files.

The header has no background of its own, so it ships in two palettes and the
README's <picture> picks one from the viewer's GitHub theme. The footer only
uses mid-tones and works on every theme as a single file.
"""
import base64
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
FONT = 'ui-monospace, "JetBrains Mono", SFMono-Regular, Menlo, Consolas, monospace'
WIDTH = 840

# Parabolic flight approximated with paired cubic curves: rising decelerates,
# falling accelerates, so the hop apex reads as weight rather than a bounce.
RISE = "cubic-bezier(.33,.67,.67,1)"
FALL = "cubic-bezier(.33,0,.67,.33)"
SETTLE = "cubic-bezier(.2,.7,.3,1)"
IN_OUT = "cubic-bezier(.65,0,.35,1)"


def pct(t, total):
    return f"{t / total * 100:.3f}".rstrip("0").rstrip(".") + "%"


def keyframes(name, stops, total):
    """stops: (time, declarations, easing to the next stop or None)."""
    body = []
    for t, decl, ease in sorted(stops, key=lambda s: s[0]):
        timing = f" animation-timing-function: {ease};" if ease else ""
        body.append(f"      {pct(t, total)} {{ {decl};{timing} }}")
    return f"    @keyframes {name} {{\n" + "\n".join(body) + "\n    }"


# ---------------------------------------------------------------- header ---

PALETTES = {
    "dark": dict(fg="#e6edf3", muted="#9198a1", line="#3d444d", accent="#3fb950",
                 rim="#3d444d", star="#e6edf3"),
    "light": dict(fg="#1f2328", muted="#59636e", line="#d1d9e0", accent="#1a7f37",
                  rim="#c8d1da", star="#6e7781"),
}

CHAIN = [
    ("2018", "IT Intern"),
    ("2019", "Informatics"),
    ("2022", "Backend"),
    ("2024", "Web3"),
    ("2026", "CodeCore"),
]

# One clock drives the narrative layer. The wave runs genesis to head in under
# three seconds, then the header rests so the loop never feels busy.
CYCLE = 8.0
WAVE_START = 0.6
WAVE_STEP = 0.55
BLOCK_X0, BLOCK_W, BLOCK_GAP, BLOCK_Y, BLOCK_H = 18, 140, 26, 146, 52
LINK_LEN = BLOCK_GAP
AVATAR = dict(cx=60, cy=70, r=42)
# Stars only sit in empty sky: around the avatar and right of the text.
# (x, y, radius, phase offset in quarter-beats of the twinkle)
STARS = [(112, 16, 1.8, 0), (8, 104, 1.4, 5), (118, 122, 1.5, 2), (470, 20, 1.4, 6),
         (702, 36, 2.0, 3), (786, 92, 1.5, 7), (690, 124, 1.4, 1), (814, 16, 1.7, 4)]


def header(p):
    head = len(CHAIN) - 1
    lit_at = [WAVE_START + i * WAVE_STEP for i in range(len(CHAIN))]
    css, blocks, links = [], [], []

    for i, (year, label) in enumerate(CHAIN):
        x = BLOCK_X0 + i * (BLOCK_W + BLOCK_GAP)
        tag = f"#{i} · {year}"
        if i == head:
            css.append(keyframes("arrive", [
                (0, "fill-opacity: 0", None),
                (lit_at[i], "fill-opacity: 0", "linear"),
                (lit_at[i] + 0.08, "fill-opacity: .16", SETTLE),
                (lit_at[i] + 1.6, "fill-opacity: 0", None),
                (CYCLE, "fill-opacity: 0", None),
            ], CYCLE))
            blocks.append(
                f'    <rect class="head" x="{x}" y="{BLOCK_Y}" width="{BLOCK_W}" height="{BLOCK_H}" rx="8"/>\n'
                f'    <text class="tag now" x="{x + 14}" y="{BLOCK_Y + 20}">{tag}</text>\n'
                f'    <text class="label" x="{x + 14}" y="{BLOCK_Y + 40}">{label}</text>'
            )
            continue

        css.append(keyframes(f"b{i}", [
            (0, f"stroke: {p['line']}", None),
            (lit_at[i], f"stroke: {p['line']}", "linear"),
            (lit_at[i] + 0.08, f"stroke: {p['accent']}", SETTLE),
            (lit_at[i] + 1.4, f"stroke: {p['line']}", None),
            (CYCLE, f"stroke: {p['line']}", None),
        ], CYCLE))
        blocks.append(
            f'    <rect class="blk" style="animation-name: b{i}" x="{x}" y="{BLOCK_Y}" width="{BLOCK_W}" height="{BLOCK_H}" rx="8"/>\n'
            f'    <text class="tag" x="{x + 14}" y="{BLOCK_Y + 20}">{tag}</text>\n'
            f'    <text class="label" x="{x + 14}" y="{BLOCK_Y + 40}">{label}</text>'
        )

        # The link draws in as block i confirms and finishes exactly when the
        # next block lights, then wipes forward so the signal reads as travel.
        lx = x + BLOCK_W
        ly = BLOCK_Y + BLOCK_H / 2
        css.append(keyframes(f"l{i}", [
            (0, f"stroke-dashoffset: {LINK_LEN}", None),
            (lit_at[i] + 0.1, f"stroke-dashoffset: {LINK_LEN}", IN_OUT),
            (lit_at[i + 1], "stroke-dashoffset: 0", IN_OUT),
            (lit_at[i + 1] + 0.35, f"stroke-dashoffset: {-LINK_LEN}", None),
            (CYCLE, f"stroke-dashoffset: {-LINK_LEN}", None),
        ], CYCLE))
        links.append(
            f'    <line class="link" x1="{lx}" y1="{ly}" x2="{lx + LINK_LEN}" y2="{ly}"/>\n'
            f'    <line class="pulse" style="animation-name: l{i}" x1="{lx}" y1="{ly}" x2="{lx + LINK_LEN}" y2="{ly}"/>'
        )

    m = AVATAR
    gif = base64.b64encode((ASSETS / "avatar.gif").read_bytes()).decode()
    stars = "\n".join(
        f'  <circle class="star" style="animation-delay: -{k * CYCLE / 16:g}s" cx="{x}" cy="{y}" r="{r}"/>'
        for x, y, r, k in STARS)
    alt = ", ".join(f"{y} {label}" for y, label in CHAIN)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="214" viewBox="0 0 {WIDTH} 214" role="img" aria-labelledby="title desc">
  <title id="title">Muhamad Taopik, Backend &amp; Software Developer</title>
  <desc id="desc">An animated avatar of a crescent Earth among twinkling stars. Below it, a chain of milestones ({alt}) lights up from the first block to the current one.</desc>
  <style>
    text {{ font-family: {FONT}; }}
    .name {{ font-size: 34px; font-weight: 700; fill: {p['fg']}; letter-spacing: -0.5px; }}
    .sub {{ font-size: 15px; fill: {p['muted']}; }}
    .tag {{ font-size: 11px; fill: {p['muted']}; }}
    .now {{ fill: {p['accent']}; }}
    .label {{ font-size: 14px; fill: {p['fg']}; }}

    /* Fills stay transparent so blocks sit on dark, dark dimmed and light alike. */
    .blk {{ fill: none; stroke: {p['line']}; stroke-width: 1.25; animation-duration: {CYCLE}s; animation-iteration-count: infinite; }}
    .link {{ stroke: {p['line']}; stroke-width: 1.5; }}
    .pulse {{ stroke: {p['accent']}; stroke-width: 2; stroke-dasharray: {LINK_LEN} {LINK_LEN}; stroke-dashoffset: {LINK_LEN};
             animation-duration: {CYCLE}s; animation-iteration-count: infinite; }}

    /* The head block is still being mined: a slow dash march on a beat that
       divides the main cycle evenly. */
    .head {{ fill: {p['accent']}; fill-opacity: 0; stroke: {p['accent']}; stroke-width: 1.25; stroke-dasharray: 6 4;
            animation: march 1s linear infinite, arrive {CYCLE}s infinite; }}
    @keyframes march {{ to {{ stroke-dashoffset: -10; }} }}

    /* Twinkle on half the main cycle; negative delays spread the stars across
       the beat so they never pulse in unison. */
    .star {{ fill: {p['star']}; opacity: .55; animation: twinkle {CYCLE / 2:g}s ease-in-out infinite; }}
    @keyframes twinkle {{ 0%, 100% {{ opacity: .2; }} 50% {{ opacity: .95; }} }}

{chr(10).join(css)}

    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; }}
    }}
  </style>

{stars}

  <defs>
    <clipPath id="disc"><circle cx="{m['cx']}" cy="{m['cy']}" r="{m['r']}"/></clipPath>
  </defs>
  <image clip-path="url(#disc)" x="{m['cx'] - m['r']}" y="{m['cy'] - m['r']}" width="{2 * m['r']}" height="{2 * m['r']}"
         href="data:image/gif;base64,{gif}"/>
  <circle cx="{m['cx']}" cy="{m['cy']}" r="{m['r']}" fill="none" stroke="{p['rim']}"/>

  <text class="name" x="130" y="66">Muhamad Taopik</text>
  <text class="sub" x="130" y="98">Backend &amp; Software Developer based in Bandung, Indonesia</text>

  <g>
{chr(10).join(links)}
{chr(10).join(blocks)}
  </g>
</svg>
'''


# ---------------------------------------------------------------- footer ---

FROG = [
    ".GGG....GGG.",
    "GWWWG..GWWWG",
    "GWKWGGGGWKWG",
    "GGGGGGGGGGGG",
    "GPGGGGGGGGPG",
    "GGKKKKKKKKGG",
    ".GGLLLLLLGG.",
    "GG.G....G.GG",
]
FROG_COLORS = {"G": "#3fb950", "W": "#ffffff", "K": "#0d1117", "P": "#f778ba", "L": "#aff5b4"}
# Closed eyes: green lid over the white with a dark lash line on the pupil row.
LIDS = [(1, 1, 3, "G"), (2, 1, 3, "K"), (1, 8, 3, "G"), (2, 8, 3, "K")]
PX = 4
FROG_W, FROG_H = len(FROG[0]) * PX, len(FROG) * PX
HOPS = 12
STEP = 56
FROG_X0 = (WIDTH - (HOPS * STEP + FROG_W)) // 2
GROUND = 58
HOP_TIME = 0.62


class Timeline:
    """Absolute-time stops for each animated layer of the frog."""

    def __init__(self):
        self.t = 0.0
        self.x, self.body, self.lid = [], [], []
        self.lands = {k: [] for k in range(HOPS + 1)}

    def hop(self, start, end):
        t, xa, xb = self.t, (start * STEP), (end * STEP)
        # Ground time (crouch, landing squash) holds x still; the frog only
        # travels while airborne so its feet never slide.
        self.x += [(t, xa, "linear"), (t + 0.12, xa, "linear"), (t + 0.46, xb, "linear")]
        self.body += [
            (t, (0, 1, 1), "ease-in-out"),
            (t + 0.12, (0, 1.12, 0.8), "ease-out"),
            (t + 0.205, (-16.5, 0.92, 1.1), RISE),
            (t + 0.29, (-22, 1, 1), FALL),
            (t + 0.375, (-16.5, 0.95, 1.06), FALL),
            (t + 0.46, (0, 1.12, 0.84), SETTLE),
            (t + HOP_TIME, (0, 1, 1), None),
        ]
        self.lands[end].append(t + 0.46)
        self.t += HOP_TIME

    def turn(self, pad):
        # Rest, blink, then a small hop in place before heading back.
        t = self.t
        self.body.append((t, (0, 1, 1), None))
        self.lid += [(t + 0.25, 0, "linear"), (t + 0.26, 1, None), (t + 0.38, 1, "linear"), (t + 0.39, 0, None)]
        h = t + 0.7
        self.body += [
            (h, (0, 1, 1), "ease-in-out"),
            (h + 0.08, (0, 1.08, 0.88), "ease-out"),
            (h + 0.2, (-8, 0.96, 1.06), FALL),
            (h + 0.32, (0, 1.08, 0.9), SETTLE),
            (h + 0.45, (0, 1, 1), None),
        ]
        self.lands[pad].append(h + 0.32)
        self.t = h + 0.75


def footer():
    tl = Timeline()
    for k in range(HOPS):
        tl.hop(k, k + 1)
    tl.turn(HOPS)
    for k in range(HOPS, 0, -1):
        tl.hop(k, k - 1)
    tl.turn(0)
    total = tl.t

    def bookend(stops, first):
        return [(0, first, None)] + stops + [(total, first, None)]

    css = [
        keyframes("travel", [(t, f"transform: translateX({x:g}px)", e)
                             for t, x, e in bookend(tl.x, 0)], total),
        keyframes("body", [(t, f"transform: translateY({y:g}px) scale({sx:g}, {sy:g})", e)
                           for t, (y, sx, sy), e in bookend(tl.body, (0, 1, 1))], total),
        keyframes("blink", [(t, f"opacity: {o}", e) for t, o, e in bookend(tl.lid, 0)], total),
    ]

    pads = []
    for k, lands in tl.lands.items():
        x = FROG_X0 + FROG_W / 2 - 20 + k * STEP
        rest = "fill: #8b949e; fill-opacity: .3; transform: translateY(0)"
        stops = [(0, rest, None), (total, rest, None)]
        for land in lands:
            # Pads dip on impact and glow, then settle back.
            stops += [
                (land - 0.005, rest, "linear"),
                (land, "fill: #3fb950; fill-opacity: 1; transform: translateY(2px)", SETTLE),
                (land + 0.14, "fill: #3fb950; fill-opacity: .9; transform: translateY(0)", SETTLE),
                (land + 0.8, rest, None),
            ]
        css.append(keyframes(f"p{k}", stops, total))
        pads.append(f'  <rect class="pad" style="animation-name: p{k}" x="{x:g}" y="{GROUND}" width="40" height="10" rx="3"/>')

    def pixels(rows):
        out = []
        for y, row in enumerate(rows):
            x = 0
            while x < len(row):
                if row[x] == ".":
                    x += 1
                    continue
                end = x
                while end < len(row) and row[end] == row[x]:
                    end += 1
                out.append(f'<rect x="{x * PX}" y="{y * PX}" width="{(end - x) * PX}" height="{PX}" fill="{FROG_COLORS[row[x]]}"/>')
                x = end
        return out

    lids = [f'<rect x="{c * PX}" y="{r * PX}" width="{n * PX}" height="{PX}" fill="{FROG_COLORS[col]}"/>'
            for r, c, n, col in LIDS]
    indent = "\n          "
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="80" viewBox="0 0 {WIDTH} 80" role="img" aria-labelledby="title">
  <title id="title">A pixel frog hopping back and forth along a row of blocks</title>
  <style>
    .pad {{ fill: #8b949e; fill-opacity: .3; transform-box: fill-box; animation-duration: {total:g}s; animation-iteration-count: infinite; }}
    .travel {{ animation: travel {total:g}s linear infinite; }}
    .body {{ transform-box: fill-box; transform-origin: 50% 100%; animation: body {total:g}s infinite; }}
    .lid {{ opacity: 0; animation: blink {total:g}s infinite; }}

{chr(10).join(css)}

    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; }}
    }}
  </style>
{chr(10).join(pads)}
  <g transform="translate({FROG_X0} {GROUND - FROG_H})">
    <g class="travel">
      <g class="body">
          {indent.join(pixels(FROG))}
        <g class="lid">
          {indent.join(lids)}
        </g>
      </g>
    </g>
  </g>
</svg>
'''


def main():
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "header.svg").write_text(header(PALETTES["dark"]))
    (ASSETS / "header-light.svg").write_text(header(PALETTES["light"]))
    (ASSETS / "footer.svg").write_text(footer())


if __name__ == "__main__":
    main()
