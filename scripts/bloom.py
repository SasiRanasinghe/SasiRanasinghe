"""Draws an animated lavender contribution graph (last 31 days) as light and dark SVGs."""
import json, os, sys, urllib.request, datetime as dt

USER = os.environ.get("GH_USER", "SasiRanasinghe")
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"

def fetch():
    if os.environ.get("BLOOM_SAMPLE"):
        import random; random.seed(4)
        today = dt.date.today()
        return [((today - dt.timedelta(days=30 - i)).isoformat(), random.choice([0,0,1,2,3,5,8,4])) for i in range(31)]
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"u": USER}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data or not data.get("data", {}).get("user"):
        sys.exit("GitHub API error: " + json.dumps(data)[:500])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [(d["date"], d["contributionCount"]) for w in weeks for d in w["contributionDays"]]
    return days[-31:]

THEMES = {
    "light": dict(bg1="#F7F2FD", bg2="#ECE3F8", ink="#2B1D3A", muted="#6E5F80", line="#9670D6",
                  area="#B79BE6", gold="#A8823F", grid="#DCD0EC", card="#FFFFFF"),
    "dark":  dict(bg1="#1E1630", bg2="#161020", ink="#F1EAFB", muted="#B4A6C8", line="#C3A6F5",
                  area="#9C7FD6", gold="#DCBC7E", grid="#3A2E50", card="#221A33"),
}

def svg(days, t):
    W, H = 1200, 360
    L, R, T, B = 70, 40, 96, 60
    pw, ph = W - L - R, H - T - B
    vals = [c for _, c in days]
    top = max(4, max(vals))
    step = 1 if top <= 5 else 2 if top <= 10 else 5 if top <= 25 else 10
    top = ((top + step - 1) // step) * step
    xs = [L + i * pw / (len(days) - 1) for i in range(len(days))]
    ys = [T + ph - v / top * ph for v in vals]
    pts = list(zip(xs, ys))
    def smooth(p):
        d = f"M{p[0][0]:.1f},{p[0][1]:.1f}"
        for i in range(1, len(p)):
            x0, y0 = p[i-1]; x1, y1 = p[i]; cx = (x0 + x1) / 2
            d += f" C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
        return d
    line = smooth(pts)
    area = line + f" L{xs[-1]:.1f},{T+ph} L{xs[0]:.1f},{T+ph} Z"
    total = sum(vals); best = max(vals)
    grid = ""
    for v in range(0, top + 1, step):
        y = T + ph - v / top * ph
        grid += f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="{t["grid"]}" stroke-dasharray="3 6"/>'
        grid += f'<text x="{L-14}" y="{y+4:.1f}" text-anchor="end" class="ax">{v}</text>'
    labels = ""
    for i in range(0, len(days), 5):
        d = dt.date.fromisoformat(days[i][0])
        labels += f'<text x="{xs[i]:.1f}" y="{H-B+26}" text-anchor="middle" class="ax">{d.strftime("%d %b")}</text>'
    dots = ""
    for i, (x, y) in enumerate(pts):
        delay = 1.6 + i * 0.04
        r = 5.5 if vals[i] == best and best > 0 else 3.6
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{t["card"]}" stroke="{t["gold"]}" stroke-width="2" class="dot" style="animation-delay:{delay:.2f}s"><title>{days[i][0]}: {vals[i]}</title></circle>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.ax{{font:12px Consolas,'Liberation Mono',monospace;fill:{t["muted"]}}}
.ln{{stroke-dasharray:4000;stroke-dashoffset:4000;animation:draw 2.4s cubic-bezier(.6,0,.2,1) .2s forwards}}
.ar{{opacity:0;animation:fade 1.4s ease 1.2s forwards}}
.dot{{opacity:0;animation:pop .5s ease forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes pop{{0%{{opacity:0}}60%{{opacity:1}}100%{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.ln,.ar,.dot{{animation:none;opacity:1;stroke-dashoffset:0}}}}
</style>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["bg1"]}"/><stop offset="1" stop-color="{t["bg2"]}"/></linearGradient>
<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["area"]}" stop-opacity=".55"/><stop offset="1" stop-color="{t["area"]}" stop-opacity="0"/></linearGradient>
</defs>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="24" fill="url(#bg)" stroke="{t["gold"]}" stroke-opacity=".4"/>
<text x="{L}" y="52" font-family="Georgia,serif" font-style="italic" font-size="28" fill="{t["ink"]}">Contribution bloom</text>
<text x="{L}" y="74" class="ax" letter-spacing="2" style="fill:{t["gold"]}">LAST 31 DAYS</text>
<text x="{W-R}" y="52" text-anchor="end" font-family="Georgia,serif" font-size="28" fill="{t["line"]}">{total}</text>
<text x="{W-R}" y="74" text-anchor="end" class="ax" letter-spacing="2">CONTRIBUTIONS</text>
{grid}{labels}
<path d="{area}" fill="url(#ar)" class="ar"/>
<path d="{line}" fill="none" stroke="{t["line"]}" stroke-width="3" stroke-linecap="round" class="ln"/>
{dots}
</svg>'''

days = fetch()
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "bloom.svg"), "w").write(svg(days, THEMES["light"]))
open(os.path.join(OUT, "bloom-dark.svg"), "w").write(svg(days, THEMES["dark"]))
print("wrote bloom graphs,", sum(c for _, c in days), "contributions")
