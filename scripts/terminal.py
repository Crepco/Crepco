"""Generate the animated terminal-session hero SVG for the profile README.

Pure stdlib. Emits assets/terminal-dark.svg and assets/terminal-light.svg.
The animation is a scripted shell session on a fixed character grid:
typed commands reveal per-character, output lines print per-line, and the
whole thing ends on an infinitely blinking cursor.

Design note: the canvas is kept short and the reveal fast so the terminal
fills within a few seconds — a tall canvas that reveals slowly spends too
long looking half-empty. `prefers-reduced-motion` gets the final frame.
"""
from datetime import datetime, timezone
from pathlib import Path

from theme import (CELL, ROW, PAD, BAR_H, FS, FONT, PALETTES,
                   esc, col_x, row_y)

COLS = 80
CHAR_SPEED = 0.038      # s per typed character
LINE_STAGGER = 0.085    # s between printed output lines
CMD_PAUSE = 0.18        # pause after a command before its output
THINK_PAUSE = 0.38      # pause before each new prompt

# fixed-width columns for the nmap-style port table
PORT_W, STATE_W, SVC_W = 10, 7, 12


def P(cmd):  # a typed prompt line
    return [("❯ ", "g", "i"), (cmd, "f", "t")]


def O(*spans):  # an instant output line; spans as (text, cls)
    return [(t, c, "i") for t, c in spans]


def port(num, svc, desc):
    return O((num.ljust(PORT_W), "f"), ("open".ljust(STATE_W), "g"),
             (svc.ljust(SVC_W), "b"), (desc, "m"))


SESSION = [
    ("pause", 0.40),
    ("line", P("whoami")),
    ("line", O(("hamza", "c"),
               (" — security research · python tooling · web dev · India", "m"))),
    ("pause", THINK_PAUSE),
    ("line", P("nmap -sV localhost")),
    ("line", O(("PORT".ljust(PORT_W) + "STATE".ljust(STATE_W)
                + "SERVICE".ljust(SVC_W) + "VERSION", "m"))),
    ("line", port("22/tcp", "python", "django · automation · scrapers")),
    ("line", port("80/tcp", "web", "react · node · vercel")),
    ("line", port("443/tcp", "security", "burp · nmap · wireshark · metasploit")),
    ("line", port("1337/tcp", "ctf", "always grinding")),
    ("line", O(("4 services up — host is very much alive.", "m"))),
    ("blank", None),
    ("pause", THINK_PAUSE),
    ("line", P("sudo ./exploit --target comfort_zone")),
    ("line", [("[sudo] password for hamza: ", "m", "i"), ("········", "f", "t")]),
    ("pause", 0.28),
    ("line", [("[+]", "g", "i"), (" payload delivered [", "f", "i"),
              ("████████████████████", "g", "t"), ("] ", "f", "i"), ("100%", "g", "i")]),
    ("pause", 0.18),
    ("line", O(("[+] ", "g"),
               ("persistence established — learning daemon is now running.", "f"))),
    ("blank", None),
    ("pause", 0.35),
    ("cursor", None),
]

TYPE_SPEEDS = {"········": 0.075, "████████████████████": 0.05}


def build(theme: str) -> str:
    pal = PALETTES[theme]
    rows = sum({"line": 1, "blank": 1, "cursor": 1}.get(k, 0) for k, _ in SESSION)
    W = round(PAD * 2 + COLS * CELL)
    H = round(BAR_H + PAD * 2 + rows * ROW)

    body = []
    t = 0.0
    row = 0

    for kind, payload in SESSION:
        if kind == "pause":
            t += payload
            continue
        if kind == "blank":
            row += 1
            continue
        if kind == "cursor":
            y = row_y(row)
            body.append(f'<text x="{col_x(0):g}" y="{y:g}" class="t cg" '
                        f'style="animation-delay:{t:.2f}s">❯</text>')
            body.append(f'<rect x="{col_x(2):g}" y="{y - FS + 1:g}" width="{CELL:g}" '
                        f'height="{FS + 3}" class="curwrap" '
                        f'style="animation-delay:{t:.2f}s"/>')
            row += 1
            continue

        # kind == "line": walk spans, advancing a column cursor
        y = row_y(row)
        col = 0
        group, group_t = [], None
        is_prompt = payload and payload[0][0] == "❯ "
        has_typed = any(m == "t" for _, _, m in payload)

        def flush():
            nonlocal group, group_t
            if group:
                body.append(f'<text y="{y:g}" class="t" '
                            f'style="animation-delay:{group_t:.2f}s">'
                            + "".join(group) + "</text>")
                group, group_t = [], None

        for text, cls, mode in payload:
            if mode == "i":
                if group_t is None:
                    group_t = t
                group.append(f'<tspan x="{col_x(col):g}" class="c{cls}">{esc(text)}</tspan>')
                col += len(text)
            else:  # typed, per character
                flush()
                speed = TYPE_SPEEDS.get(text, CHAR_SPEED)
                for ch in text:
                    if ch != " ":
                        body.append(f'<text x="{col_x(col):g}" y="{y:g}" class="t c{cls}" '
                                    f'style="animation-delay:{t:.2f}s">{esc(ch)}</text>')
                    t += speed
                    col += 1
        flush()

        t += CMD_PAUSE if is_prompt else (0 if has_typed else LINE_STAGGER)
        row += 1

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    scan = ""
    if pal["scanlines"]:
        scan = (f'<rect x="1" y="{BAR_H}" width="{W - 2}" height="{H - BAR_H - 1}" '
                f'fill="url(#scan)" opacity="0.25"/>')
    color_css = "".join(f".c{k}{{fill:{pal[k]}}}" for k in "fmbgryvc")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated terminal session. whoami returns: hamza, security research and python tooling. An nmap scan of localhost lists open ports as skills: 22 python, 80 web, 443 security, 1337 ctf. Then sudo ./exploit --target comfort_zone delivers a payload and reports: persistence established, learning daemon is now running.">
<style>
text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}
.t{{opacity:0;animation:on .01s steps(1) forwards}}
.cg{{fill:{pal["g"]}}}
.curwrap{{fill:{pal["b"]};opacity:0;animation:on .01s steps(1) forwards,blink 1.06s step-end infinite}}
{color_css}
.bartxt{{fill:{pal["m"]};font-size:12px}}
.barhost{{fill:{pal["b"]};font-size:12px}}
@keyframes on{{to{{opacity:1}}}}
@keyframes blink{{50%{{opacity:0}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}.t{{opacity:1!important}}.curwrap{{opacity:1!important}}}}
</style>
<defs>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".55"/></pattern>
<clipPath id="win"><rect width="{W}" height="{H}" rx="9"/></clipPath>
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


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        path = out / f"terminal-{theme}.svg"
        path.write_text(build(theme), encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
