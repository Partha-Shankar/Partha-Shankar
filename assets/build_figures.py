"""Regenerates the README figures (fig1-*.svg, fig2-*.svg) in this folder.

Text is converted to outlines because an SVG shown through <img> cannot load
web fonts. To add a project or tool to Fig. 2, edit COLUMNS and ROWS below.

    pip install fonttools uharfbuzz
    python build_figures.py <dir with Computer Modern Unicode .ttf files>

Fonts: npm package computer-modern (cmu-serif-*, cmu-typewriter-text-*).
"""
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
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
    "light": {"ink": "#1f2328", "muted": "#59636e", "rule": "#1f2328", "faint": "#d1d9e0", "heat": "#d9480f"},
    "dark": {"ink": "#f0f6fc", "muted": "#9198a1", "rule": "#9198a1", "faint": "#3d444d", "heat": "#ff7a45"},
}


class Face:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, text, size):
        _, pos = self.shape(text)
        return sum(p.x_advance for p in pos) * size / self.upem

    def path(self, text, x, y, size):
        """SVG path data for `text` with its baseline starting at (x, y)."""
        infos, pos = self.shape(text)
        scale = size / self.upem
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        cursor = x
        for info, p in zip(infos, pos):
            name = self.order[info.codepoint]
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor + p.x_offset * scale, y)))
            cursor += p.x_advance * scale
        return pen.getCommands()


FACES = {key: Face(FONT_DIR / name) for key, name in FONT_FILES.items()}


def text(s, x, y, size, fill, face="serif", anchor="start", extra=""):
    f = FACES[face]
    w = f.width(s, size)
    x0 = x - w / 2 if anchor == "middle" else x - w if anchor == "end" else x
    return f'<path d="{f.path(s, x0, y, size)}" fill="{fill}"{extra}/>'


def rule(x1, x2, y, color, width=1.0):
    return f'<path d="M{x1} {y}H{x2}" stroke="{color}" stroke-width="{width}"/>'


def svg(w, h, title, desc, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
        f'<title id="t">{title}</title><desc id="d">{desc}</desc>{"".join(body)}</svg>\n'
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


# Fig. 2: tools against projects, in place of a wall of badges.
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


def fig2(c):
    W, left, cw = 1000, 34, 86
    tool_x, col0 = left, 268
    row_h, head_h, group_gap = 24, 30, 15
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
    label = "Fig. 2."
    note = "  The stack, by where it was used. A mark means the tool is in that project."
    lw = FACES["bold"].width(label, 16)
    body.append(text(label, left, y, 16, c["ink"], "bold"))
    body.append(text(note, left + lw, y, 16, c["muted"]))
    y += 16

    summary = "; ".join(f"{t}: {u.replace(' ', ', ')}" for _, tools in ROWS for t, u in tools)
    return svg(W, int(y), "The stack, by where it was used", summary.replace("&", "and"), body)


for theme, colors in THEMES.items():
    (OUT / f"fig1-{theme}.svg").write_text(fig1(colors), encoding="utf-8")
    (OUT / f"fig2-{theme}.svg").write_text(fig2(colors), encoding="utf-8")
print("wrote", sorted(p.name for p in OUT.glob("fig*.svg")))
