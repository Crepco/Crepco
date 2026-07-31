"""Shared grid + palette for the README SVG generators.

Everything renders on a fixed character grid so alignment survives any
monospace font substitution (the SVGs can't embed fonts on GitHub).
"""

# character grid
CELL = 8.5        # px per column
ROW = 20          # px per row
PAD = 16          # inner padding
BAR_H = 30        # tmux status bar height
FS = 14           # font size
FONT = "ui-monospace,'Cascadia Code','JetBrains Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace"

PALETTES = {
    "dark": {
        "bg": "#1a1b26", "bar": "#16161e", "border": "#292e42",
        "f": "#c0caf5",   # default fg
        "m": "#565f89",   # muted
        "b": "#7aa2f7",   # blue
        "g": "#9ece6a",   # green
        "r": "#f7768e",   # red
        "y": "#e0af68",   # yellow
        "v": "#bb9af7",   # violet
        "c": "#7dcfff",   # cyan
        "scanlines": True,
    },
    "light": {
        "bg": "#e1e2e7", "bar": "#d5d6db", "border": "#b4b9d4",
        "f": "#3760bf",
        "m": "#8990b3",
        "b": "#2e7de9",
        "g": "#587539",
        "r": "#f52a65",
        "y": "#8c6c3e",
        "v": "#9854f1",
        "c": "#007197",
        "scanlines": False,
    },
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def col_x(col: int) -> float:
    return PAD + col * CELL


def row_y(row: int) -> float:
    # baseline for a text row inside the body (below the status bar)
    return BAR_H + PAD + row * ROW + FS


def lerp_hex(a: str, b: str, t: float) -> str:
    av = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    bv = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(av[i] + (bv[i] - av[i]) * t):02x}" for i in range(3))
