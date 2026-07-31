"""Generate the animated terminal-session hero SVG for the profile README.

Pure stdlib. Emits assets/terminal-dark.svg and assets/terminal-light.svg.
The animation is a scripted shell session on a fixed character grid:
typed commands reveal per-character, output lines print per-line, and the
whole thing ends on an infinitely blinking cursor. `prefers-reduced-motion`
gets the final frame statically.
"""
from datetime import datetime, timezone
from pathlib import Path

from theme import (CELL, ROW, PAD, BAR_H, FS, FONT, PALETTES,
                   esc, col_x, row_y, lerp_hex)

COLS = 82
CHAR_SPEED = 0.045      # s per typed character
LINE_STAGGER = 0.09     # s between printed output lines
CMD_PAUSE = 0.22        # pause between a command finishing and its output
THINK_PAUSE = 0.50      # pause before each new prompt

BANNER = [
    "██╗  ██╗ █████╗ ███╗   ███╗███████╗ █████╗",
    "██║  ██║██╔══██╗████╗ ████║╚══███╔╝██╔══██╗",
    "███████║███████║██╔████╔██║  ███╔╝ ███████║",
    "██╔══██║██╔══██║██║╚██╔╝██║ ███╔╝  ██╔══██║",
    "██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║",
    "╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝",
]

# span = (text, color_class, mode) — mode "i" instant, "t" typed
def P(cmd):  # a typed prompt line
    return [("❯ ", "g", "i"), (cmd, "f", "t")]


def O(*spans):  # an instant output line; spans as (text, cls)
    return [(t, c, "i") for t, c in spans]


SESSION = [
    ("pause", 0.55),
    ("line", P("whoami")),
    ("line", O(("hamza", "f"), (" — security research · python tooling · web dev — India", "m"))),
    ("pause", THINK_PAUSE),
    ("line", P("cat /etc/motd")),
    ("banner", None),
    ("line", O(("i break things to understand them — then build better ones.", "v"))),
    ("blank", None),
    ("pause", THINK_PAUSE),
    ("line", P("nmap -sV crepco.local")),
    ("line", O(("PORT      STATE   SERVICE     VERSION", "m"))),
    ("line", O(("22/tcp    ", "f"), ("open", "g"), ("    python      ", "f"), ("tooling · automation · scrapers", "m"))),
    ("line", O(("80/tcp    ", "f"), ("open", "g"), ("    web         ", "f"), ("django · react · node", "m"))),
    ("line", O(("443/tcp   ", "f"), ("open", "g"), ("    security    ", "f"), ("burp · wireshark · nmap · metasploit", "m"))),
    ("line", O(("1337/tcp  ", "f"), ("open", "g"), ("    ctf         ", "f"), ("always grinding", "m"))),
    ("line", O(("Service detection performed — host is very much alive.", "m"))),
    ("blank", None),
    ("pause", THINK_PAUSE),
    ("line", P("sudo ./exploit --target comfort_zone")),
    ("line", [("[sudo] password for hamza: ", "m", "i"), ("········", "f", "t")]),
    ("pause", 0.30),
    ("line", [("[*]", "y", "i"), (" probing attack surface ", "f", "i"),
              ("············", "m", "t"), (" done", "g", "i")]),
    ("pause", 0.25),
    ("line", [("[+]", "g", "i"), (" delivering payload [", "f", "i"),
              ("████████████████████", "g", "t"), ("] ", "f", "i"), ("100%", "g", "i")]),
    ("pause", 0.20),
    ("line", O(("[+] ", "g"), ("persistence established — learning daemon is now running.", "f"))),
    ("blank", None),
    ("pause", 0.40),
    ("cursor", None),
]

TYPE_SPEEDS = {"········": 0.08, "············": 0.09, "████████████████████": 0.055}


def build(theme: str) -> str:
    pal = PALETTES[theme]
    rows = 0
    for kind, _ in SESSION:
        rows += {"line": 1, "blank": 1, "cursor": 1, "banner": 6}.get(kind, 0)
    W = round(PAD * 2 + COLS * CELL)
    H = round(BAR_H + PAD * 2 + rows * ROW)

    body = []
    t = 0.0
    row = 0

    def text_node(x, y, cls, content, delay, extra_anim="", style_extra=""):
        d = f"{delay:.2f}s"
        delays = f"{d},{d}" if extra_anim else d
        return (f'<text x="{x:g}" y="{y:g}" class="t {cls}{extra_anim}" '
                f'style="animation-delay:{delays}{style_extra}">{esc(content)}</text>')

    for kind, payload in SESSION:
        if kind == "pause":
            t += payload
            continue
        if kind == "blank":
            row += 1
            continue
        if kind == "cursor":
            y = row_y(row)
            body.append(text_node(col_x(0), y, "cg", "❯", t))
            body.append(f'<rect x="{col_x(2):g}" y="{y - FS + 1:g}" width="{CELL:g}" height="{FS + 3}" '
                        f'class="curwrap" style="animation-delay:{t:.2f}s">'
                        f'<title>cursor</title></rect>')
            row += 1
            continue
        if kind == "banner":
            for i, brow in enumerate(BANNER):
                y = row_y(row)
                color = lerp_hex(pal["b"], pal["v"], i / (len(BANNER) - 1))
                d = f"{t:.2f}s"
                # chromatic ghost flashes
                body.append(f'<text x="{col_x(0) - 1.5:g}" y="{y:g}" class="gh" fill="{pal["r"]}" '
                            f'style="animation-delay:{d}">{esc(brow)}</text>')
                body.append(f'<text x="{col_x(0) + 1.5:g}" y="{y:g}" class="gh" fill="{pal["c"]}" '
                            f'style="animation-delay:{d}">{esc(brow)}</text>')
                body.append(f'<text x="{col_x(0):g}" y="{y:g}" class="t jit" fill="{color}" '
                            f'style="animation-delay:{d},{d}">{esc(brow)}</text>')
                t += 0.10
                row += 1
            continue

        # kind == "line": walk spans sequentially, advancing a column cursor
        y = row_y(row)
        col = 0
        line_parts = []          # instant tspans grouped into one <text>
        line_t = None            # reveal time of the instant group
        has_typed = any(m == "t" for _, _, m in payload)
        is_prompt = payload and payload[0][0] == "❯ "

        def flush_group():
            nonlocal line_parts, line_t
            if line_parts:
                d = f"{line_t:.2f}s"
                body.append(f'<text y="{y:g}" class="t" style="animation-delay:{d}">'
                            + "".join(line_parts) + "</text>")
                line_parts, line_t = [], None

        for text, cls, mode in payload:
            if mode == "i":
                if line_t is None:
                    line_t = t
                line_parts.append(f'<tspan x="{col_x(col):g}" class="c{cls}">{esc(text)}</tspan>')
                col += len(text)
            else:  # typed
                flush_group()
                speed = TYPE_SPEEDS.get(text, CHAR_SPEED)
                for ch in text:
                    if ch != " ":
                        body.append(text_node(col_x(col), y, f"c{cls}", ch, t))
                    t += speed
                    col += 1
        flush_group()

        if is_prompt:
            t += CMD_PAUSE
        elif not has_typed:
            t += LINE_STAGGER
        row += 1

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    scan = ""
    if pal["scanlines"]:
        scan = (f'<rect x="1" y="{BAR_H}" width="{W - 2}" height="{H - BAR_H - 1}" '
                f'fill="url(#scan)" opacity="0.3"/>')

    color_css = "".join(f".c{k}{{fill:{pal[k]}}}" for k in "fmbgryvc")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated terminal session: whoami — Hamza, security research and python tooling. An nmap scan finds open ports: python, web, security, ctf. Then ./exploit --target comfort_zone establishes persistence: the learning daemon is running.">
<style>
text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}
.t{{opacity:0;animation:on .01s steps(1) forwards}}
.gh{{opacity:0;font-family:{FONT};animation:gf .18s linear forwards}}
.jit{{animation:on .01s steps(1) forwards,jit .22s steps(3) forwards}}
.curwrap{{fill:{pal["b"]};opacity:0;animation:on .01s steps(1) forwards,blink 1.06s step-end infinite}}
.cg{{fill:{pal["g"]}}}
{color_css}
.bartxt{{fill:{pal["m"]};font-size:12px}}
.barhost{{fill:{pal["b"]};font-size:12px}}
@keyframes on{{to{{opacity:1}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes gf{{0%{{opacity:.5}}60%{{opacity:.22}}100%{{opacity:0}}}}
@keyframes jit{{0%{{transform:translateX(-2px)}}40%{{transform:translateX(1.5px)}}75%{{transform:translateX(-.7px)}}100%{{transform:none}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}.t{{opacity:1!important}}.curwrap{{opacity:1!important}}.gh{{opacity:0!important}}}}
</style>
<defs>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
<rect width="4" height="1" fill="#000" opacity=".55"/>
</pattern>
<clipPath id="win"><rect x="0" y="0" width="{W}" height="{H}" rx="9"/></clipPath>
</defs>
<g clip-path="url(#win)">
<rect width="{W}" height="{H}" fill="{pal["bg"]}"/>
<rect width="{W}" height="{BAR_H}" fill="{pal["bar"]}"/>
<circle cx="{PAD + 4}" cy="{BAR_H / 2:g}" r="4" fill="{pal["g"]}"/>
<text x="{PAD + 16}" y="{BAR_H / 2 + 4:g}" class="barhost">[0] crepco@arch:~</text>
<text x="{W - PAD}" y="{BAR_H / 2 + 4:g}" class="bartxt" text-anchor="end">tokyonight · {stamp}</text>
{"".join(body)}
{scan}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8.5" fill="none" stroke="{pal["border"]}"/>
</svg>'''
    return svg


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        path = out / f"terminal-{theme}.svg"
        path.write_text(build(theme), encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
