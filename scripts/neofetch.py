"""Generate the neofetch-style stack card SVG for the profile README.

Pure stdlib, static output (no animation needed — neofetch is a snapshot),
so it stays light and renders identically everywhere. Emits
assets/neofetch-dark.svg and assets/neofetch-light.svg.

Colour is the whole point here: the distro logo, per-category field labels,
and the trailing palette swatches turn a flat text block into the card a
terminal person expects to see.
"""
from pathlib import Path

from theme import CELL, ROW, PAD, FS, FONT, PALETTES, esc, lerp_hex

# Arch logo, drawn blue→cyan top to bottom
LOGO = [
    r"      /\      ",
    r"     /  \     ",
    r"    /    \    ",
    r"   /  __  \   ",
    r"  /  (  )  \  ",
    r" / __|  |__ \ ",
    r"/.`        `.\ ",
]
LOGO_COL = 2
INFO_COL = 18          # where labels start
VAL_COL = 29           # where values start

# (label, label_color, value) — value spans are (text, color) tuples
SYS = [
    ("distro", "b", [("Arch Linux ", "f"), ("(btw)", "m")]),
    ("wm/edit", "b", [("Hyprland", "f"), (" · ", "m"), ("Neovim", "f")]),
    ("lab", "b", [("Kali Linux", "f")]),
    ("uptime", "b", [("CSE student · ", "f"), ("always learning", "m")]),
]
SKILLS = [
    ("lang", "c", "python · javascript · bash · c++ · sql"),
    ("backend", "g", "django · node · react"),
    ("security", "r", "burp · nmap · wireshark · metasploit · sqlmap"),
    ("hardware", "y", "esp32 · arduino · yolov8 · bioamp · i2c/spi"),
]
SWATCH_ORDER = "brgyvcfm"   # palette keys, left to right


def build(theme: str) -> str:
    pal = PALETTES[theme]

    # assemble content rows as (col, text, color) spans
    rows = []

    def R(*spans):
        rows.append(list(spans))

    R((INFO_COL, "crepco", "g"), (INFO_COL + 6, "@", "m"), (INFO_COL + 7, "arch", "b"))
    R((INFO_COL, "─" * 30, "m"))
    for label, lc, val in SYS:
        R((INFO_COL, label, lc), (VAL_COL, "", "f"), *_val_spans(VAL_COL, val))
    R()  # blank
    for label, lc, val in SKILLS:
        R((INFO_COL, label, lc), (VAL_COL, val, "f"))
    R()  # blank (swatches drawn separately on this row)
    swatch_row = len(rows) - 1

    n_rows = max(len(rows), LOGO_COL and len(LOGO) + 1)
    max_col = 0
    for spans in rows:
        for c, t, _ in spans:
            max_col = max(max_col, c + len(t))
    max_col = max(max_col, INFO_COL + 30)
    # match the recon/terminal card width (82 cols) so text size is consistent
    # across every card in the README; extra space becomes right margin.
    W = max(round(PAD * 2 + (max_col + 2) * CELL), round(PAD * 2 + 82 * CELL))
    H = round(PAD * 2 + (len(rows) + 0.4) * ROW)

    def x(col):
        return PAD + col * CELL

    def y(r):
        return PAD + r * ROW + FS

    body = []

    # logo, vertically centred against the info block
    logo_top = max(0, (len(rows) - len(LOGO)) // 2)
    for i, line in enumerate(LOGO):
        color = lerp_hex(pal["b"], pal["c"], i / (len(LOGO) - 1))
        body.append(f'<text x="{x(LOGO_COL):g}" y="{y(logo_top + i):g}" '
                    f'fill="{color}">{esc(line)}</text>')

    # info rows
    for r, spans in enumerate(rows):
        for c, t, cls in spans:
            if not t:
                continue
            body.append(f'<text x="{x(c):g}" y="{y(r):g}" class="c{cls}">{esc(t)}</text>')

    # palette swatches on the swatch row
    sw_w, sw_gap = 3, 1
    sy = PAD + swatch_row * ROW + FS - FS + 2
    for i, k in enumerate(SWATCH_ORDER):
        sx = x(INFO_COL + i * (sw_w + sw_gap))
        body.append(f'<rect x="{sx:g}" y="{sy:g}" width="{sw_w * CELL:g}" '
                    f'height="{FS + 1}" rx="2" fill="{pal[k]}"/>')

    color_css = "".join(f".c{k}{{fill:{pal[k]}}}" for k in "fmbgryvc")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="neofetch-style stack card. crepco@arch on Arch Linux, Hyprland, Neovim, Kali Linux in the lab. Languages: python, javascript, bash, c++, sql. Backend: django, node, react. Security: burp, nmap, wireshark, metasploit, sqlmap. Hardware: esp32, arduino, yolov8, bioamp, i2c/spi.">
<style>text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}{color_css}</style>
<rect width="{W}" height="{H}" rx="9" fill="{pal["bg"]}" stroke="{pal["border"]}"/>
{"".join(body)}
</svg>'''


def _val_spans(start_col, spans):
    out, col = [], start_col
    for text, cls in spans:
        out.append((col, text, cls))
        col += len(text)
    return out


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        path = out / f"neofetch-{theme}.svg"
        path.write_text(build(theme), encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
