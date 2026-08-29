#!/usr/bin/env python3
"""
Render data/contributions.json (produced by fetch_contributions.py) as an
animated contribution heatmap: squares pop in one-by-one, with active days
flashing bright before settling. No terminal-window chrome -- just the grid,
month/weekday labels, and a stats footer (total, current/longest streak,
best day, date range).

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.

Usage:
    python scripts/generate_streak_svg.py [output.svg]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "streak.svg")

# ---- layout ----------------------------------------------------------
CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
GRAY = "#7d8590"
GREEN = "#39d353"
ACCENT = "#22d3ee"
GOLD = "#f2cc60"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
          "Sep", "Oct", "Nov", "Dec"]

# same 6-level bucketing render_heatmap_svg.py used, since contributions.json
# stores raw counts, not a pre-computed level like the jogruber API does.
def level_for(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    return 4  # this palette only has 5 entries (0-4), one fewer than the
              # 6-color PALETTE in render_heatmap_svg.py


import datetime

def main():
    data = json.load(open(IN_PATH))
    days = data["days"]

    sd = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (sd.weekday() + 1) % 7  # align to Sunday-start columns

    n = len(days) + lead_pad
    NW = (n + 6) // 7
    W = LEFT + NW * (CELL + GAP) + 6
    FOOTER_H = 54  # room for two lines of stats text below the grid
    H = TOP + 7 * (CELL + GAP) + 22 + FOOTER_H

    REVEAL, DUR = 3.6, 0.55
    maxorder = (NW - 1) + 6 * 0.55

    rects, labels = [], []
    last_m = None
    for wk in range(NW):
        d = sd + datetime.timedelta(days=wk * 7 - lead_pad)
        if d.month != last_m:
            last_m = d.month
            labels.append(f'<text class="lbl" x="{LEFT+wk*(CELL+GAP)}" y="{TOP-8}">{MONTHS[d.month-1]}</text>')
    for name, r in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
        labels.append(f'<text class="lbl" x="2" y="{TOP+r*(CELL+GAP)+CELL-2}">{name}</text>')

    for i, day in enumerate(days):
        idx = i + lead_pad
        wk, row = idx // 7, idx % 7
        lvl = level_for(day["count"])
        x = LEFT + wk * (CELL + GAP)
        y = TOP + row * (CELL + GAP)
        delay = round((wk + row * 0.55) / maxorder * REVEAL, 3)
        cls = "c g" if lvl >= 1 else "c e"
        rects.append(
            f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
            f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s">'
            f'<title>{day["date"]}: {day["count"]} contribution{"s" if day["count"] != 1 else ""}</title>'
            f'</rect>'
        )

    # ---- stats footer (from fetch_contributions.py's precomputed stats) ----
    total = data["total_contributions"]
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    best = data["best_day"]
    rng = data["range"]

    footer_top = TOP + 7 * (CELL + GAP) + 20
    footer = [
        f'<text class="total" x="{LEFT}" y="{footer_top}">'
        f'<tspan fill="{GREEN}" font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{GRAY}"> contributions in the last year</tspan></text>',
        f'<text class="lbl" x="{W - 6}" y="{footer_top}" text-anchor="end">'
        f'{rng["start"]} &#8594; {rng["end"]}</text>',
        f'<text class="total" x="{LEFT}" y="{footer_top + 22}" font-size="13">'
        f'<tspan fill="{GRAY}">current streak </tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan>'
        f'<tspan fill="{GRAY}">   &#183;   longest </tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>',
        f'<text class="lbl" x="{W - 6}" y="{footer_top + 22}" text-anchor="end">'
        f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>',
    ]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:{GRAY}; font-size:13px; font-weight:600; }}
  text.total {{ fill:#e6edf3; font-size:15px; font-weight:700; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.15}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" fill="none"/>
{''.join(labels)}
{''.join(rects)}
{''.join(footer)}
</svg>'''

    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}: {len(days)} days, {total:,} contributions, current streak {cs}, longest {ls}")


if __name__ == "__main__":
    main()