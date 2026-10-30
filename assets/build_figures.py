"""Regenerates the README figures in this folder.

Text is converted to outlines because an SVG shown through <img> cannot load
web fonts. To update the page, edit the data tables below: THESIS (Fig. 1),
PRS (Fig. 2 and the PR cards), COLUMNS and ROWS (Fig. 3).

    pip install fonttools uharfbuzz
    python build_figures.py <dir with Computer Modern Unicode .ttf files>

Fonts: npm package computer-modern (cmu-serif-*, cmu-typewriter-text-*).
"""
import base64
import sys
from datetime import date
from html import escape
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

OUT = Path(__file__).parent
FONT_DIR = Path(sys.argv[1])
FONT_FILES = {
    "serif": "cmu-serif-500-roman.ttf",
    "bold": "cmu-serif-700-roman.ttf",
    "italic": "cmu-serif-500-italic.ttf",
    "mono": "cmu-typewriter-text-500-roman.ttf",
}
THEMES = {
    "light": {
        "ink": "#1f2328", "muted": "#59636e", "rule": "#1f2328", "faint": "#d1d9e0", "heat": "#d9480f",
        "merged": "#8250df", "add": "#1a7f37", "del": "#d1242f", "off": "#d1d9e0",
    },
    "dark": {
        "ink": "#f0f6fc", "muted": "#9198a1", "rule": "#9198a1", "faint": "#3d444d", "heat": "#ff7a45",
        "merged": "#a371f7", "add": "#3fb950", "del": "#f85149", "off": "#3d444d",
    },
}
MERGE_ICON = (  # octicon git-merge-16 (MIT)
    "M5.45 5.154A4.25 4.25 0 0 0 9.25 7.5h1.378a2.251 2.251 0 1 1 0 1.5H9.25A5.734 5.734 0 0 1 5 7.123v3.505"
    "a2.25 2.25 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.95-.218ZM4.25 13.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
    "m8.5-4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5ZM5 3.25a.75.75 0 1 0 0 .005V3.25Z"
)


class Face:
    def __init__(self, key, path):
        self.key = key
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def shape(self, s):
        buf = hb.Buffer()
        buf.add_str(s)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": self.key != "mono"})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, s, size):
        _, pos = self.shape(s)
        return sum(p.x_advance for p in pos) * size / self.upem

    def uses(self, s, x, y, size):
        """<use> elements for `s`, baseline at (x, y). Each glyph is defined once per file."""
        infos, pos = self.shape(s)
        scale = size / self.upem
        out, cursor = [], x
        for info, p in zip(infos, pos):
            gid = f"{self.key[0]}{info.codepoint}"
            if gid not in GLYPHS:
                pen = SVGPathPen(self.glyphs, ntos=lambda v: str(round(v)))
                self.glyphs[self.order[info.codepoint]].draw(pen)
                GLYPHS[gid] = pen.getCommands()
            if GLYPHS[gid]:
                out.append(
                    f'<use href="#{gid}" transform="translate({cursor + p.x_offset * scale:.2f} {y})'
                    f'scale({scale:.5f} -{scale:.5f})"/>'
                )
            cursor += p.x_advance * scale
        return "".join(out)


GLYPHS = {}  # glyph outlines used by the SVG being built
FACES = {key: Face(key, FONT_DIR / name) for key, name in FONT_FILES.items()}


def text(s, x, y, size, fill, face="serif", anchor="start", extra=""):
    f = FACES[face]
    w = f.width(s, size)
    x0 = x - w / 2 if anchor == "middle" else x - w if anchor == "end" else x
    return f'<g fill="{fill}"{extra}>{f.uses(s, x0, y, size)}</g>'


def rule(x1, x2, y, color, width=1.0):
    return f'<path d="M{x1} {y}H{x2}" stroke="{color}" stroke-width="{width}"/>'


def logo(org, cx, cy, r, c, clip_id):
    raw = (OUT / "logos" / f"{org}.png").read_bytes()
    mime = "image/png" if raw[:4] == b"\x89PNG" else "image/jpeg"
    data = base64.b64encode(raw).decode()
    return (
        f'<clipPath id="{clip_id}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
        f'<image href="data:{mime};base64,{data}" x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" '
        f'clip-path="url(#{clip_id})"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["faint"]}"/>'
    )


def svg(w, h, title, desc, body):
    defs = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in GLYPHS.items() if d)
    GLYPHS.clear()
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
        f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f'<defs>{defs}</defs>{"".join(body)}</svg>\n'
    )


# Fig. 1: the title page, with the thesis rendered as a token attribution map.
THESIS = [
    [("Machine", 0.04), ("Learning", 0.06), ("Systems", 0.11)],
    [("That", 0.01), ("Can", 0.02), ("Show", 0.38), ("Their", 0.09), ("Work", 0.29)],
]


def fig1(c):
    W, H, size, gap, pad = 1000, 390, 54, 18, 7
    body = []
    stamp = "github.com/Partha-Shankar   [cs.LG]   Oct 2026"
    body.append(text(stamp, 0, 0, 14, c["muted"], extra=' transform="translate(26 344) rotate(-90)"'))

    for line, baseline in zip(THESIS, (84, 186)):
        widths = [FACES["serif"].width(word, size) for word, _ in line]
        x = (W - sum(widths) - gap * (len(line) - 1)) / 2
        for (word, weight), w in zip(line, widths):
            # Fill opacity tracks the weight, so the map reads like a real one.
            alpha = 0.05 + weight * 1.9
            body.append(
                f'<rect x="{x - pad:.1f}" y="{baseline - 46}" width="{w + 2 * pad:.1f}" height="62" rx="2" '
                f'fill="{c["heat"]}" fill-opacity="{alpha:.2f}"/>'
            )
            body.append(text(word, x, baseline, size, c["ink"]))
            body.append(text(f"+{weight:.2f}", x + w / 2, baseline + 36, 14, c["muted"], "mono", "middle"))
            x += w + gap

    body.append(text("Partha Shankar", W / 2, 278, 31, c["ink"], anchor="middle"))
    body.append(
        text(
            "AI/ML Engineer Intern, Tapplent  ·  Nagarjuna College of Engineering & Technology, Bengaluru",
            W / 2, 309, 18, c["muted"], "italic", "middle",
        )
    )
    body.append(rule(330, 670, 340, c["faint"]))
    label = "Fig. 1."
    note = "  Token attribution for this page’s thesis. Values set by hand; the author is not an unbiased estimator."
    lw, nw = FACES["bold"].width(label, 16), FACES["serif"].width(note, 16)
    x0 = (W - lw - nw) / 2
    body.append(text(label, x0, 372, 16, c["ink"], "bold"))
    body.append(text(note, x0 + lw, 372, 16, c["muted"]))
    return svg(
        W, H, "Machine Learning Systems That Can Show Their Work, by Partha Shankar",
        "Styled like a paper's title page. Each word of the title is shaded by an attribution weight; "
        "the words Show and Work carry the most.",
        body,
    )


# Fig. 2 and the PR cards.
PRS = [
    {
        "id": 95358, "org": "vercel", "repo": "vercel/next.js", "lang": "JavaScript", "stars": "143k",
        "opened": date(2026, 7, 1), "merged": date(2026, 7, 2), "add": 42, "del": 1,
        "why": "The cacheHandlers name check wasn’t anchored, so handler! passed as valid. Added regression tests.",
    },
    {
        "id": 47158, "org": "huggingface", "repo": "huggingface/transformers", "lang": "Python", "stars": "168k",
        "opened": date(2026, 7, 8), "merged": date(2026, 7, 14), "add": 1, "del": 1,
        "why": "A warning told people debugging multi-GPU inference the opposite of what the code does.",
    },
    {
        "id": 14394, "org": "cloudflare", "repo": "cloudflare/workers-sdk", "lang": "TypeScript", "stars": "4.6k",
        "opened": date(2026, 6, 23), "merged": date(2026, 6, 23), "add": 146, "del": 8,
        "why": "SQLite read a hyphenated migrations table name as subtraction, and an apostrophe in a filename "
               "ended the string.",
    },
    {
        "id": 14530, "org": "cloudflare", "repo": "cloudflare/workers-sdk", "lang": "TypeScript", "stars": "4.6k",
        "opened": date(2026, 7, 3), "merged": date(2026, 7, 6), "add": 143, "del": 0,
        "why": "Type checks for four optional D1 binding fields that were being silently accepted, "
               "with one regression test each.",
    },
    {
        "id": 8950, "org": "Apicurio", "repo": "Apicurio/apicurio-registry", "lang": "Java", "stars": "900+",
        "opened": date(2026, 7, 28), "merged": date(2026, 7, 29), "add": 1, "del": 1,
        "why": "In react-router v7 a route with no path never matches, so unknown URLs rendered a blank page.",
    },
]
STATS = [("5", "merged pull requests"), ("4", "upstream projects"), ("+333 −11", "lines changed"),
         ("300k+", "combined GitHub stars")]
START, END = date(2026, 6, 15), date(2026, 8, 1)
TICKS = [(date(2026, 6, 15), "15 Jun"), (date(2026, 7, 1), "1 Jul"), (date(2026, 7, 15), "15 Jul"),
         (date(2026, 8, 1), "1 Aug")]


def fig2(c):
    W, left, right, axis0, axis1 = 1000, 34, 966, 310, 942
    lane_h = 84

    def xpos(d):
        return axis0 + (d - START).days / (END - START).days * (axis1 - axis0)

    body = [rule(left, right, 22, c["rule"], 1.6)]
    col = (right - left) / len(STATS)
    for i, (value, label) in enumerate(STATS):
        cx = left + col * (i + 0.5)
        body.append(text(value, cx, 72, 38, c["ink"], anchor="middle"))
        body.append(text(label, cx, 98, 16, c["muted"], "italic", "middle"))
    body.append(rule(left, right, 118, c["rule"], 0.8))

    # Lanes run in order of first merge, so the figure reads as a staircase over time.
    lanes = []
    for pr in sorted(PRS, key=lambda p: p["merged"]):
        if pr["repo"] not in [lane["repo"] for lane in lanes]:
            lanes.append({**pr, "prs": [p for p in PRS if p["repo"] == pr["repo"]]})

    top, bottom = 138, 138 + lane_h * len(lanes)
    for d, label in TICKS:
        x = xpos(d)
        body.append(f'<path d="M{x:.1f} {top}V{bottom}" stroke="{c["faint"]}" stroke-width="0.7" stroke-dasharray="2 4"/>')
        body.append(text(label, x, bottom + 18, 14, c["muted"], "mono", "middle"))

    for i, lane in enumerate(lanes):
        y = top + lane_h * i + 38
        body.append(logo(lane["org"], left + 20, y, 20, c, f"l{i}"))
        body.append(text(lane["repo"], left + 50, y - 2, 17, c["ink"]))
        body.append(text(f"{lane['stars']} stars  ·  {lane['lang']}", left + 50, y + 17, 14.5, c["muted"], "italic"))
        body.append(rule(axis0, axis1, y, c["rule"], 1.2))
        for pr in lane["prs"]:
            x1 = xpos(pr["merged"])
            x0 = min(xpos(pr["opened"]), x1 - 26)  # keep same-day merges visible as an arc
            rise = 22
            body.append(
                f'<path d="M{x0:.1f} {y}C{x0 + 8:.1f} {y - rise} {x1 - 12:.1f} {y - rise} {x1:.1f} {y}" '
                f'fill="none" stroke="{c["merged"]}" stroke-width="2"/>'
            )
            body.append(f'<circle cx="{x0:.1f}" cy="{y}" r="3.2" fill="{c["merged"]}"/>')
            body.append(f'<circle cx="{x1:.1f}" cy="{y}" r="7" fill="{c["merged"]}"/>')
            stat = f"+{pr['add']} −{pr['del']}"
            body.append(text(f"#{pr['id']}", x1, y + 24, 14.5, c["ink"], "mono", "middle"))
            body.append(text(stat, x1, y + 40, 13, c["muted"], "mono", "middle"))

    y = bottom + 34
    body.append(rule(left, right, y, c["rule"], 1.6))
    y += 30
    label, note = "Fig. 2.", "  Merged upstream, 2026. Each arc runs from the day a pull request was opened to the day it merged."
    lw = FACES["bold"].width(label, 16)
    body.append(text(label, left, y, 16, c["ink"], "bold"))
    body.append(text(note, left + lw, y, 16, c["muted"]))
    summary = "; ".join(f"{p['repo']} #{p['id']}, merged {p['merged'].isoformat()}, +{p['add']} -{p['del']}" for p in PRS)
    return svg(W, y + 14, "Five merged pull requests in four upstream projects", summary, body)


def card(pr, c):
    W, pad, h = 1000, 20, 98
    body = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="7" fill="none" stroke="{c["faint"]}"/>']
    body.append(logo(pr["org"], pad + 16, 34, 16, c, "l"))
    x = pad + 42
    body.append(text(pr["repo"], x, 40, 20, c["ink"], "bold"))
    x += FACES["bold"].width(pr["repo"], 20) + 10
    body.append(text(f"#{pr['id']}", x, 40, 18, c["muted"], "mono"))

    # Right edge: diffstat blocks, then the counts, then the Merged pill.
    total = pr["add"] + pr["del"]
    dels = pr["del"] if total < 5 else max(1, round(5 * pr["del"] / total)) if pr["del"] else 0
    adds = pr["add"] if total < 5 else 5 - dels
    blocks = [c["add"]] * adds + [c["del"]] * dels
    blocks += [c["off"]] * (5 - len(blocks))
    bx = W - pad - 5 * 12
    for i, color in enumerate(blocks):
        body.append(f'<rect x="{bx + i * 12}" y="27" width="10" height="10" rx="1.5" fill="{color}"/>')
    sx = bx - 10
    body.append(text(f"−{pr['del']}", sx, 37, 15, c["del"], "mono", "end"))
    sx -= FACES["mono"].width(f"−{pr['del']}", 15) + 7
    body.append(text(f"+{pr['add']}", sx, 37, 15, c["add"], "mono", "end"))
    sx -= FACES["mono"].width(f"+{pr['add']}", 15) + 16
    pill_w = 90
    px = sx - pill_w
    body.append(f'<rect x="{px:.1f}" y="19" width="{pill_w}" height="27" rx="13.5" fill="{c["merged"]}"/>')
    body.append(f'<path d="{MERGE_ICON}" transform="translate({px + 10:.1f} 25)scale(.92)" fill="#fff"/>')
    body.append(text("Merged", px + 30, 37.5, 16, "#ffffff"))

    assert FACES["serif"].width(pr["why"], 17.5) < W - 2 * pad, pr["id"]
    body.append(text(pr["why"], pad, 78, 17.5, c["muted"]))
    return svg(W, h, f"{pr['repo']} pull request {pr['id']}, merged", pr["why"], body)


# Fig. 3: tools against projects, in place of a wall of badges.
COLUMNS = [
    ("DeepBreath", "check"), ("CardioXAI", "check"), ("MedLens", "check"), ("MFD-AI", "check"),
    ("IKYA", "field"), ("GramSetu", "field"), ("HostelDesk", "field"), ("RoadSoS", "field"),
]
ROWS = [
    ("Languages", [
        ("Python", "DeepBreath CardioXAI MedLens MFD-AI RoadSoS"),
        ("TypeScript", "MedLens MFD-AI IKYA GramSetu HostelDesk RoadSoS"),
    ]),
    ("Models", [
        ("PyTorch", "DeepBreath MedLens MFD-AI"),
        ("Hugging Face Transformers", "DeepBreath MedLens MFD-AI"),
        ("OpenCV", "DeepBreath MedLens MFD-AI"),
        ("scikit-learn", "CardioXAI MFD-AI"),
        ("XGBoost, LightGBM, TabPFN", "CardioXAI"),
        ("Gemini, Llama (Ollama)", "MedLens GramSetu"),
        ("ONNX Runtime Web", "GramSetu"),
    ]),
    ("Explanation", [
        ("SHAP, Grad-CAM++", "DeepBreath CardioXAI"),
    ]),
    ("Serving", [
        ("FastAPI", "MedLens MFD-AI RoadSoS"),
        ("Flask", "DeepBreath"),
        ("Cloudflare Workers, D1, R2", "IKYA HostelDesk"),
        ("SQLite", "MFD-AI IKYA HostelDesk"),
    ]),
    ("Interface", [
        ("React", "DeepBreath MedLens MFD-AI IKYA RoadSoS"),
        ("Next.js", "GramSetu"),
        ("SvelteKit", "HostelDesk"),
        ("Streamlit", "CardioXAI"),
        ("Three.js, WebGL", "DeepBreath IKYA"),
    ]),
]


def fig3(c):
    W, left, cw = 1000, 34, 86
    tool_x, col0 = left, 268
    row_h, group_gap = 24, 15
    names = [n for n, _ in COLUMNS]
    # A little air between the two families of projects.
    cx = {n: col0 + cw * i + (24 if i >= 4 else 0) + cw / 2 for i, n in enumerate(names)}
    right = int(cx[names[-1]] + cw / 2)
    body = []

    y = 28
    body.append(rule(left, right, y, c["rule"], 1.6))
    y += 26
    a0, a1 = cx["DeepBreath"] - cw / 2 + 4, cx["MFD-AI"] + cw / 2 - 4
    b0, b1 = cx["IKYA"] - cw / 2 + 4, cx["RoadSoS"] + cw / 2 - 4
    body.append(text("can you check it?", (a0 + a1) / 2, y, 16, c["muted"], "italic", "middle"))
    body.append(text("does it hold up?", (b0 + b1) / 2, y, 16, c["muted"], "italic", "middle"))
    y += 9
    body.append(rule(a0, a1, y, c["faint"]))
    body.append(rule(b0, b1, y, c["faint"]))
    y += 22
    for n in names:
        body.append(text(n, cx[n], y, 15, c["ink"], anchor="middle"))
    y += 12
    body.append(rule(left, right, y, c["rule"], 0.8))

    y += 8
    for gi, (group, tools) in enumerate(ROWS):
        if gi:
            y += group_gap
            body.append(rule(left, right, y - group_gap / 2 + 4, c["faint"], 0.7))
        y += 22
        body.append(text(group, tool_x, y, 16, c["muted"], "italic"))
        y += 2
        for tool, used in tools:
            y += row_h
            used = used.split()
            accent = group == "Explanation"
            body.append(text(tool, tool_x + 14, y - 7, 17, c["ink"]))
            for n in names:
                if n in used:
                    body.append(
                        f'<rect x="{cx[n] - 6:.1f}" y="{y - 18}" width="12" height="12" rx="1.5" '
                        f'fill="{c["heat"] if accent else c["ink"]}"/>'
                    )
    y += 12
    body.append(rule(left, right, y, c["rule"], 1.6))
    y += 32
    label = "Fig. 3."
    note = "  The stack, by where it was used. A mark means the tool is in that project."
    lw = FACES["bold"].width(label, 16)
    body.append(text(label, left, y, 16, c["ink"], "bold"))
    body.append(text(note, left + lw, y, 16, c["muted"]))
    y += 16

    summary = "; ".join(f"{t}: {u.replace(' ', ', ')}" for _, tools in ROWS for t, u in tools)
    return svg(W, int(y), "The stack, by where it was used", summary, body)


for theme, colors in THEMES.items():
    (OUT / f"fig1-{theme}.svg").write_text(fig1(colors), encoding="utf-8")
    (OUT / f"fig2-{theme}.svg").write_text(fig2(colors), encoding="utf-8")
    (OUT / f"fig3-{theme}.svg").write_text(fig3(colors), encoding="utf-8")
    for pr in PRS:
        (OUT / f"pr-{pr['id']}-{theme}.svg").write_text(card(pr, colors), encoding="utf-8")
print("wrote", len(list(OUT.glob("*.svg"))), "figures")
