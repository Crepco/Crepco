"""Generate one themed project card SVG per project for the README.

Pure stdlib, static. Emits assets/proj-<slug>-<theme>.svg for each project.
Each card is embedded in the README as an <img> wrapped in a link, which is
the one way to get a fully custom-styled, tokyonight-themed panel that is
still clickable through to the repo — a markdown table can't be styled and a
plain <img> can't hold a link, but a linked <picture> gets both.
"""
import textwrap
from pathlib import Path

from theme import CELL, ROW, PAD, FS, FONT, PALETTES, esc

# (slug, name, accent-key, stack, link-label, description)
PROJECTS = [
    ("ariadne", "ariadne/", "b", "Python · LLM agents · AD", "github.com/Crepco/Ariadne",
     "Can an LLM agent trace an Active Directory attack path to Domain Admin on its "
     "own — and how does it compare to BloodHound? A scored, reproducible benchmark."),
    ("dart", "dart/", "r", "Python · CV · Arduino", "github.com/Crepco/DART",
     "Autonomous pan-tilt turret: YOLOv8 person tracking + face authorization, arming "
     "only on a confirmed unauthorized target — laptop vision, Arduino servos."),
    ("flowstate", "flowstate/", "v", "Python · EEG · Arduino R4", "github.com/Crepco/flowstate",
     "Real-time focus tracking from a forehead EEG sensor — a live 0–100 score that "
     "buzzes the moment you zone out. Physiological, not a webcam guessing at your gaze."),
    ("argus", "argus/", "c", "Python · OSINT", "github.com/Crepco/Argus",
     "Defensive OSINT self-audit — shows what an attacker could find about an identity "
     "you can prove you own, then hands you a prioritized remediation plan."),
    ("clerkview", "clerkview/", "g", "Web · shipped", "clerkview.com",
     "Clinical case log for medical students — document and track cases during "
     "training. Shipped, with real users."),
]

W = round(PAD * 2 + 82 * CELL)   # 729, matching the other cards
WRAP = 80                        # description wrap width in characters
NAME_COL = 2
DESC_COL = 2


def build(theme, slug, name, accent, stack, label, desc):
    pal = PALETTES[theme]
    lines = textwrap.wrap(desc, WRAP)[:2]
    n = len(lines)
    H = round(PAD * 2 + (1 + n + 1) * ROW)

    def x(col):
        return PAD + col * CELL

    def y(row):
        return PAD + row * ROW + FS

    body = []
    # accent rail down the left edge
    body.append(f'<rect x="0" y="0" width="4" height="{H}" fill="{pal[accent]}" opacity="0.9"/>')
    # name (accent, bold) + a leading dot
    body.append(f'<text x="{x(NAME_COL):g}" y="{y(0):g}" fill="{pal[accent]}" '
                f'font-weight="700">▸ {esc(name)}</text>')
    # stack, right-aligned, muted, smaller
    body.append(f'<text x="{W - PAD:g}" y="{y(0):g}" fill="{pal["m"]}" '
                f'font-size="12" text-anchor="end">{esc(stack)}</text>')
    # description lines
    for i, line in enumerate(lines):
        body.append(f'<text x="{x(DESC_COL):g}" y="{y(1 + i):g}" fill="{pal["f"]}">'
                    f'{esc(line)}</text>')
    # footer: open-repo hint, right-aligned accent
    body.append(f'<text x="{W - PAD:g}" y="{y(1 + n):g}" fill="{pal[accent]}" '
                f'font-size="12" text-anchor="end">→ {esc(label)}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(name)} — {esc(stack)}. {esc(desc)} Link: {esc(label)}.">
<style>text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}</style>
<rect width="{W}" height="{H}" rx="9" fill="{pal["bg"]}" stroke="{pal["border"]}"/>
{"".join(body)}
</svg>'''


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for slug, name, accent, stack, label, desc in PROJECTS:
        for theme in ("dark", "light"):
            path = out / f"proj-{slug}-{theme}.svg"
            path.write_text(build(theme, slug, name, accent, stack, label, desc),
                            encoding="utf-8")
    print(f"wrote {len(PROJECTS) * 2} project cards to {out}")


if __name__ == "__main__":
    main()
