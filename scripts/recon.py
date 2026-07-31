"""Generate the recon-report card SVG from live GitHub data.

Runs daily in CI (.github/workflows/recon.yml) and can be run locally.
Pure stdlib. On API failure it keeps the previously generated SVGs so the
profile never shows a broken card.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from theme import CELL, ROW, PAD, FS, FONT, PALETTES, esc

USER = "Crepco"
COLS = 82
BAR_CELLS = 34
LANG_COLORS = ["b", "g", "y", "v", "c"]
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def api(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": f"{USER}-recon",
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
           if os.environ.get("GITHUB_TOKEN") else {}),
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def fetch():
    user = api(f"https://api.github.com/users/{USER}")
    repos = [r for r in api(f"https://api.github.com/users/{USER}/repos?per_page=100")
             if not r["fork"]]
    langs = {}
    for r in repos:
        for lang, n in api(r["languages_url"]).items():
            langs[lang] = langs.get(lang, 0) + n
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    now = datetime.now(timezone.utc)
    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    last_push = max((r["pushed_at"] for r in repos if r["pushed_at"]), default=None)
    return {
        "age_days": (now - created).days,
        "last_push": (last_push or "n/a")[:10],
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "langs": [(l.lower()[:12], n / total * 100) for l, n in top],
        "stamp": now.strftime("%Y-%m-%d %H:%M UTC"),
    }


def frame_row(kind, inner=""):
    """kind: top | mid | bottom; inner text is embedded in the rule."""
    if kind == "mid":
        return None
    lead = "┌─" if kind == "top" else "└─"
    tail = "┐" if kind == "top" else "┘"
    label = f"[ {inner} ]" if inner else ""
    return lead + label + "─" * (COLS - len(lead) - len(label) - 1) + tail


def build(theme, d):
    pal = PALETTES[theme]
    rows = []  # each row: list of (col, text, cls) spans

    def R(*spans):
        rows.append(list(spans))

    def pipes(*spans):
        R((0, "│", "m"), *spans, (COLS - 1, "│", "m"))

    R((0, frame_row("top", f"RECON // github.com/{USER}"), "m"))
    pipes()
    pipes((3, "host", "m"), (15, f"github.com/{USER} — up {d['age_days']:,} days", "f"))
    pipes((3, "last push", "m"), (15, d["last_push"], "f"),
          (41, "public repos", "m"), (56, str(d["repos"]), "f"))
    pipes((3, "followers", "m"), (15, str(d["followers"]), "f"),
          (41, "stars looted", "m"), (56, str(d["stars"]), "f"))
    pipes()
    pipes((3, "LANG SCAN ", "b"), (13, "─" * 56, "m"))
    for i, (lang, pct) in enumerate(d["langs"]):
        filled = max(1, round(pct / 100 * BAR_CELLS))
        cls = LANG_COLORS[i % len(LANG_COLORS)]
        pipes((3, lang, "f"),
              (17, "█" * filled, cls), (17 + filled, "░" * (BAR_CELLS - filled), "m"),
              (53, f"{pct:5.1f}%", cls))
    pipes()
    pipes((3, "status", "m"), (15, "ACTIVE — probing new attack surfaces", "g"))
    pipes()
    R((0, frame_row("bottom", f"regenerated {d['stamp']} · scripts/recon.py"), "m"))

    W = round(PAD * 2 + COLS * CELL)
    H = round(PAD * 2 + len(rows) * ROW)
    status_row = len(rows) - 3

    body = []
    for r, spans in enumerate(rows):
        y = PAD + r * ROW + FS
        tspans = "".join(
            f'<tspan x="{PAD + c * CELL:g}" class="c{cls}">{esc(t)}</tspan>'
            for c, t, cls in spans)
        if tspans:
            body.append(f'<text y="{y:g}">{tspans}</text>')
    # blinking cursor after the status line — SMIL so it runs inside <img>
    cx = PAD + (15 + len("ACTIVE — probing new attack surfaces") + 1) * CELL
    cy = PAD + status_row * ROW + FS
    body.append(f'<rect x="{cx:g}" y="{cy - FS + 1:g}" width="{CELL:g}" height="{FS + 3}" '
                f'fill="{pal["g"]}"><animate attributeName="opacity" '
                f'values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.06s" '
                f'repeatCount="indefinite"/></rect>')

    color_css = "".join(f".c{k}{{fill:{pal[k]}}}" for k in "fmbgryvc")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Recon report on github.com/{USER}: {d['repos']} public repos, {d['stars']} stars, last push {d['last_push']}. Top languages: {', '.join(f"{l} {p:.0f}%" for l, p in d['langs'])}. Status: active.">
<style>
text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}
{color_css}
</style>
<rect width="{W}" height="{H}" rx="9" fill="{pal["bg"]}" stroke="{pal["border"]}"/>
{"".join(body)}
</svg>'''


def main():
    try:
        d = fetch()
    except Exception as e:
        if (ASSETS / "recon-dark.svg").exists():
            print(f"api fetch failed ({e}); keeping previous recon SVGs")
            return
        sys.exit(f"api fetch failed and no cached SVG exists: {e}")
    ASSETS.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        path = ASSETS / f"recon-{theme}.svg"
        path.write_text(build(theme, d), encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
