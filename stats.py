"""Render gold stats cards from the GitHub GraphQL API.

Usage: GITHUB_TOKEN=... python stats.py LOGIN OUTDIR
Writes stats.svg, langs.svg and activity.svg (replaces the paused github-readme-stats / activity-graph services).
"""
import json, os, sys, urllib.request
from datetime import date

LOGIN, OUT = sys.argv[1], sys.argv[2]
QUERY = """query($login: String!) { user(login: $login) {
  contributionsCollection { totalCommitContributions restrictedContributionsCount
    contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } }
  pullRequests { totalCount }
  repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) { totalCount
    nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } } }
} }"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
    headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"},
)
res = json.load(urllib.request.urlopen(req))
if "errors" in res:
    sys.exit(res["errors"])
u = res["data"]["user"]
cc = u["contributionsCollection"]
repos = u["repositories"]

FONT = "font-family=\"'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif\""
GOLD = ["#ffd36b", "#e8b949", "#d9771e", "#b8860b", "#f2efe8", "#8a5a14"]

def card(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {FONT}>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="6" fill="#0d1117"/>'
            f'<text x="25" y="35" font-size="18" font-weight="600" fill="#e8b949">{title}</text>{body}</svg>')

def save(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)

os.makedirs(OUT, exist_ok=True)

# stats card
rows = [
    ("Contributions (last year)", cc["contributionCalendar"]["totalContributions"]),
    ("Commits (last year)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
    ("Pull requests", u["pullRequests"]["totalCount"]),
    ("Stars earned", sum(r["stargazerCount"] for r in repos["nodes"])),
    ("Public repos", repos["totalCount"]),
]
body = "".join(
    f'<circle cx="31" cy="{66 + i * 26}" r="3" fill="#e8b949"/>'
    f'<text x="44" y="{71 + i * 26}" font-size="14" fill="#e6edf3">{label}</text>'
    f'<text x="470" y="{71 + i * 26}" font-size="14" font-weight="700" fill="#ffffff" text-anchor="end">{value}</text>'
    for i, (label, value) in enumerate(rows))
save("stats.svg", card(495, 195, "GitHub stats", body))

# languages card
sizes = {}
for r in repos["nodes"]:
    for e in r["languages"]["edges"]:
        sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
top = sorted(sizes.items(), key=lambda kv: -kv[1])[:6]
total = sum(s for _, s in top) or 1
bar, x = "", 25.0
for i, (_, s) in enumerate(top):
    wdt = 445 * s / total
    bar += f'<rect x="{x:.2f}" y="55" width="{wdt:.2f}" height="10" fill="{GOLD[i]}"/>'
    x += wdt
legend = "".join(
    f'<circle cx="{31 + (i % 2) * 225}" cy="{94 + (i // 2) * 28}" r="5" fill="{GOLD[i]}"/>'
    f'<text x="{44 + (i % 2) * 225}" y="{99 + (i // 2) * 28}" font-size="13" fill="#e6edf3">{name} '
    f'<tspan fill="#8b949e">{100 * s / total:.1f}%</tspan></text>'
    for i, (name, s) in enumerate(top))
save("langs.svg", card(495, 94 + (len(top) + 1) // 2 * 28, "Most used languages",
                       f'<clipPath id="r"><rect x="25" y="55" width="445" height="10" rx="5"/></clipPath>'
                       f'<g clip-path="url(#r)">{bar}</g>{legend}'))

# activity card: last 31 days
days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]][-31:]
W, H, L, R, T, B = 900, 300, 50, 25, 60, 50
top_v = max(max(d["contributionCount"] for d in days), 4)
px = lambda i: L + i * (W - L - R) / (len(days) - 1)
py = lambda v: H - B - v * (H - T - B) / top_v
pts = " ".join(f"{px(i):.1f},{py(d['contributionCount']):.1f}" for i, d in enumerate(days))
grid = "".join(
    f'<line x1="{L}" x2="{W - R}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="#21262d"/>'
    f'<text x="{L - 10}" y="{py(v) + 4:.1f}" font-size="11" fill="#8b949e" text-anchor="end">{v}</text>'
    for v in sorted({0, top_v // 2, top_v}))
labels = "".join(
    f'<text x="{px(i):.1f}" y="{H - B + 20}" font-size="11" fill="#8b949e" text-anchor="middle">{date.fromisoformat(d["date"]).day}</text>'
    for i, d in enumerate(days))
dots = "".join(f'<circle cx="{px(i):.1f}" cy="{py(d["contributionCount"]):.1f}" r="3" fill="#ffffff"/>' for i, d in enumerate(days))
save("activity.svg", card(W, H, "Contributions · last 31 days",
     '<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8b949" stop-opacity=".35"/>'
     '<stop offset="1" stop-color="#e8b949" stop-opacity="0"/></linearGradient></defs>'
     f'{grid}<polygon points="{px(0):.1f},{py(0):.1f} {pts} {px(len(days) - 1):.1f},{py(0):.1f}" fill="url(#a)"/>'
     f'<polyline points="{pts}" fill="none" stroke="#e8b949" stroke-width="2" stroke-linejoin="round"/>{dots}{labels}'))
print("wrote stats.svg langs.svg activity.svg")
