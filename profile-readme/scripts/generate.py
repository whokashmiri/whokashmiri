"""Generates every graphic in the profile README except ascii.svg.
  headings:  hd-*.svg                       (static, drawn in the page's own typeface)
  stats:     stats.svg streak.svg langs.svg year.svg   (from the GitHub GraphQL API)
Env: GH_USER, GH_TOKEN.   Run with --headings-only to skip the API."""
import json, os, sys, urllib.request, datetime as dt
from html import escape
from svgfont import font_face

RAMP = ":+#@"  # quiet -> loud, used by year.svg
THEME = """:root{--bg:#f6f8fa;--fg:#1f2328;--mut:#656d76;--acc:#2da44e;--line:#d0d7de}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--acc:#3fb950;--line:#30363d}}"""

def svg(w, h, text, body, bg=True):
    css = font_face(text, 400) + font_face(text, 700) + THEME + \
        "text{font-family:'JBM',ui-monospace,Menlo,Consolas,monospace;fill:var(--fg)}" \
        ".m{fill:var(--mut)}.a{fill:var(--acc)}.b{font-weight:700}"
    rect = f'<rect width="{w}" height="{h}" rx="10" fill="var(--bg)" stroke="var(--line)"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<style>{css}</style>{rect}{body}</svg>')

def write(name, s): open(name, "w", encoding="utf-8").write(s); print("wrote", name, f"{len(s)/1024:.1f} KB")

# ---------- headings ----------
def heading(name, label):
    t = f"## {label}"
    body = (f'<text x="2" y="26" font-size="20" class="b"><tspan class="a">##</tspan> {escape(label)}'
            f'<tspan class="a">_<animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/></tspan></text>'
            f'<line x1="0" y1="36" x2="0" y2="36" stroke="var(--line)" stroke-width="1"><animate attributeName="x2" from="0" to="820" dur="0.8s" fill="freeze"/></line>')
    write(f"hd-{name}.svg", svg(820, 42, t + "_", body, bg=False))

def headings():
    for n, l in [("about", "about"), ("stack", "stack"), ("projects", "projects"), ("stats", "stats"),
                 ("about-this-page", "about this page")]:
        heading(n, l)

# ---------- API ----------
Q = """query($u:String!){user(login:$u){
 contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
 repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount
  languages(first:8,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""

def fetch(user, token):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": Q, "variables": {"u": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req))
    if "errors" in d: sys.exit(d["errors"])
    return d["data"]["user"]

def streaks(days):
    best = cur = run = 0
    today = dt.date.today().isoformat()
    for i, (d, c) in enumerate(days):
        run = run + 1 if c > 0 else 0
        best = max(best, run)
    # current: walk back from today (today may still be empty)
    cur = 0
    for d, c in reversed(days):
        if c > 0: cur += 1
        elif d == today: continue
        else: break
    return cur, best

# ---------- stats graphics ----------
def stat_cards(u):
    cc = u["contributionsCollection"]
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    items = [("contributions", cc["contributionCalendar"]["totalContributions"]), ("commits", cc["totalCommitContributions"]),
             ("pull requests", cc["totalPullRequestContributions"]), ("issues", cc["totalIssueContributions"]),
             ("stars", stars), ("public repos", u["repositories"]["totalCount"])]
    txt = "contributions in the last year0123456789" + "".join(k for k, _ in items)
    body = '<text x="20" y="30" font-size="12" class="m">contributions in the last year</text>'
    for i, (k, v) in enumerate(items):
        x = 20 + (i % 3) * 180; y = 70 + (i // 3) * 52
        body += (f'<text x="{x}" y="{y}" font-size="26" class="b a" opacity="0">{v:,}'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{i*.12:.2f}s" dur=".5s" fill="freeze"/></text>'
                 f'<text x="{x}" y="{y+16}" font-size="11" class="m">{k}</text>')
    write("stats.svg", svg(580, 150, txt, body))

def streak_card(days):
    cur, best = streaks(days)
    txt = "current streak longest streak days0123456789"
    body = (f'<text x="20" y="30" font-size="12" class="m">streak</text>'
            f'<text x="20" y="75" font-size="34" class="b a">{cur}<animate attributeName="opacity" values="0;1" dur=".6s" fill="freeze"/></text>'
            f'<text x="20" y="95" font-size="11" class="m">current · days</text>'
            f'<text x="190" y="75" font-size="34" class="b">{best}</text>'
            f'<text x="190" y="95" font-size="11" class="m">longest · days</text>')
    write("streak.svg", svg(360, 116, txt, body))

def langs_card(u):
    by_bytes, by_repo = {}, {}
    for r in u["repositories"]["nodes"]:
        seen = set()
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]; by_bytes[n] = by_bytes.get(n, 0) + e["size"]
            if n not in seen: by_repo[n] = by_repo.get(n, 0) + 1; seen.add(n)
    top = sorted(by_bytes.items(), key=lambda kv: -kv[1])[:6]
    tot = sum(v for _, v in top) or 1
    txt = "top languages by bytes0123456789%" + "".join(n for n, _ in top)
    body = '<text x="20" y="30" font-size="12" class="m">top languages · by bytes</text>'
    for i, (n, v) in enumerate(top):
        y = 56 + i * 22; pct = v / tot * 100; bw = 150 * v / top[0][1]
        body += (f'<text x="20" y="{y}" font-size="12">{escape(n)}</text>'
                 f'<rect x="130" y="{y-9}" width="0" height="9" rx="2" fill="var(--acc)">'
                 f'<animate attributeName="width" from="0" to="{bw:.0f}" begin="{i*.1:.1f}s" dur=".7s" fill="freeze"/></rect>'
                 f'<text x="290" y="{y}" font-size="11" class="m">{pct:.0f}%</text>')
    write("langs.svg", svg(360, 56 + len(top) * 22 + 8, txt, body))

def year_card(days):
    days = days[-364:]
    vals = [c for _, c in days]; mx = max(vals) or 1
    def ch(c):
        if c == 0: return "·"
        return RAMP[min(3, int(c / mx * 4 - 1e-9))] if c / mx > 0 else "·"
    txt = "the last year, one character per day·" + RAMP
    body = '<text x="20" y="28" font-size="12" class="m">the last year · one character per day · : + # @</text>'
    cw = 10
    for w in range(0, len(days), 7):
        col = days[w:w + 7]
        for r, (d, c) in enumerate(col):
            g = ch(c)
            fill = "m" if g == "·" else "a"
            body += (f'<text x="{20 + (w // 7) * cw}" y="{56 + r * 14}" font-size="12" class="{fill}" opacity="{1 if g!="·" else .5}">{g}</text>')
    write("year.svg", svg(20 * 2 + 52 * cw, 56 + 7 * 14 + 4, txt, body))

if __name__ == "__main__":
    headings()
    if "--headings-only" in sys.argv: sys.exit()
    u = fetch(os.environ["GH_USER"], os.environ["GH_TOKEN"])
    days = [(d["date"], d["contributionCount"]) for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    stat_cards(u); streak_card(days); langs_card(u); year_card(days)
