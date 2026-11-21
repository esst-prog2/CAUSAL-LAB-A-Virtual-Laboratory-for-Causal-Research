"""Figure 2 and Table 1 of the promo page (docs/index.html), drawn from the stored study.

Run from causal_lab/: python ../spike/page_figure2.py out.json
It summarizes causal_lab/data/demo_study/results.json with the app's own
simulation_engine.demo_study.summarize and writes the inline SVG (coverage and
pre-trend warning rate per threat and level, points red where the rule fails)
and the rows of Table 1 (bias share and coverage). No number is typed by hand.
"""
import sys, json
sys.path.insert(0, '.')
from simulation_engine.demo_study import load_study, summarize, LEVELS
meta, study = load_study()
names = {"differential_trend": "Diverging pre-trends", "confounding": "Confounding",
         "staggered_dynamic": "Staggered adoption, growing effects", "anticipation": "Anticipation"}
short = {"differential_trend": "Diverging pre-trends", "confounding": "Confounding",
         "staggered_dynamic": "Staggered, growing effects", "anticipation": "Anticipation"}
S = {th: {lv: summarize(lv, study[th][lv]) for lv in LEVELS} for th in names}

pw, ph = 168, 170
x0s = [52 + i * 212 for i in range(4)]
top = 46
W, H = x0s[-1] + pw + 26, top + ph + 34
def y(v): return top + ph * (1 - v)
out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f2t f2d" xmlns="http://www.w3.org/2000/svg">',
       '<title id="f2t">Coverage of the 95% interval and pre-trend warning rate, by threat and level</title>']
desc = []
for th in names:
    desc.append(names[th] + ": " + "; ".join(
        f"{lv} coverage {S[th][lv].coverage*100:.1f}%, warns {S[th][lv].detection*100:.1f}%" for lv in LEVELS))
out.append('<desc id="f2d">' + ". ".join(desc) + ".</desc>")
for i, th in enumerate(names):
    x0 = x0s[i]
    step = pw / (len(LEVELS) - 1)
    xs = [x0 + k * step for k in range(len(LEVELS))]
    out.append(f'<text class="ptitle" x="{x0}" y="{top-20}">{short[th]}</text>')
    for v in (0, .25, .5, .75, 1):
        out.append(f'<line class="grid" x1="{x0}" x2="{x0+pw}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
        if i == 0:
            out.append(f'<text class="tick" x="{x0-10}" y="{y(v)+4:.1f}" text-anchor="end">{int(v*100)}%</text>')
    out.append(f'<line class="rule" x1="{x0}" x2="{x0+pw}" y1="{y(.9):.1f}" y2="{y(.9):.1f}"/>')
    if i == 0:
        pass
    if i == 1:
        out.append(f'<text class="rulelab" x="{x0+2}" y="{y(.9)+17:.1f}">90% rule</text>')
    cov = [S[th][lv].coverage for lv in LEVELS]
    det = [S[th][lv].detection for lv in LEVELS]
    out.append('<polyline class="det" points="' + " ".join(f"{a:.1f},{y(b):.1f}" for a, b in zip(xs, det)) + '"/>')
    out.append('<polyline class="cov" points="' + " ".join(f"{a:.1f},{y(b):.1f}" for a, b in zip(xs, cov)) + '"/>')
    for a, lv in zip(xs, LEVELS):
        s = S[th][lv]
        cls = "ok" if s.acceptable else "fail"
        out.append(f'<circle class="pt {cls}" cx="{a:.1f}" cy="{y(s.coverage):.1f}" r="4.5"/>')
        out.append(f'<text class="tick" x="{a:.1f}" y="{top+ph+20}" text-anchor="middle">{lv.capitalize()}</text>')
out.append('</svg>')
svg = chr(10).join(out)
# Table: bias share and coverage per cell
rows = []
for th in names:
    cells = []
    for lv in LEVELS:
        s = S[th][lv]
        cls = "pass" if s.acceptable else "fail"
        bx = " bad" if s.bias_share > 0.10 else ""
        cx = " bad" if s.coverage < 0.90 else ""
        cells.append(f'<td class="{cls}"><span class="b{bx}">{s.bias_share*100:.0f}%</span><span class="c{cx}">{s.coverage*100:.1f}%</span></td>')
    rows.append(f'<tr><th scope="row">{names[th]}</th>' + "".join(cells) + "</tr>")
table = "\n".join(rows)
open(sys.argv[1], "w", encoding="utf-8").write(json.dumps({"svg": svg, "table": table, "computed_at": meta["computed_at"]}))
print(svg[:400]); print(table[:600])
