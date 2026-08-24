"""
Merged PR Strip — reads data/merged-prs.json (hand-curated, merged only)
→ renders output/merged-prs-{dark,light}.svg (static synapse strip)
README never contains hand-typed PR entries; it embeds the generated SVG.
"""
import json
import os
from datetime import datetime

DARK = {
    "bg": "#090A0F",
    "card": "#13141c",
    "border": "#2a2f42",
    "text": "#e6e8f2",
    "muted": "#9aa2b8",
    "accent": "#5FBF8A",
    "violet": "#8D72C0",
    "coral": "#E87972",
}
LIGHT = {
    "bg": "#f6f7fb",
    "card": "#ffffff",
    "border": "#d9deeb",
    "text": "#1a1d2e",
    "muted": "#6b7288",
    "accent": "#2e7d55",
    "violet": "#7059A6",
    "coral": "#B9575D",
}

def load_prs(path="data/merged-prs.json"):
    with open(path, "r") as f:
        prs = json.load(f)
    # validate: only merged PRs, required fields
    for pr in prs:
        for k in ("repo","pr_number","title","url","merged_date"):
            assert k in pr, f"missing {k} in {pr}"
        assert pr["url"].startswith("https://github.com/"), f"invalid url {pr['url']}"
        # ensure merged_date parses
        datetime.fromisoformat(pr["merged_date"])
    # sort by merged_date ascending (chronological)
    prs.sort(key=lambda x: x["merged_date"])
    return prs

def render_svg(prs, palette, label="dark"):
    # horizontal synapse strip: each PR = node + label
    pad = 16
    gap = 18
    card_h = 44
    # estimate width: title truncated
    def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
    n = len(prs)
    if n == 0:
        w = 400
        h = 62
        inner = f'<text x="{w/2}" y="{h/2}" text-anchor="middle" fill="{palette["muted"]}" font-family="Inter,ui-sans-serif,system-ui" font-size="12">No merged PRs yet — curation required</text>'
    else:
        # width per card ~ 320, plus gaps + pads
        card_w = 340
        w = pad*2 + n*card_w + (n-1)*gap
        w = max(w, 520)
        h = 86
        inner = ""
        # connection line behind
        if n > 1:
            y_mid = h/2 + 2
            inner += f'<line x1="{pad+card_w/2:.0f}" y1="{y_mid}" x2="{w-pad-card_w/2:.0f}" y2="{y_mid}" stroke="{palette["border"]}" stroke-width="2" stroke-dasharray="6 6" opacity="0.7"/>'
        for i, pr in enumerate(prs):
            x = pad + i*(card_w+gap)
            y = 14
            repo = esc(f"{pr.get('owner','')}/{pr['repo']}#{pr['pr_number']}") if pr.get('owner') else esc(f"{pr['repo']}#{pr['pr_number']}")
            title = esc(pr["title"][:48] + ("…" if len(pr["title"])>48 else ""))
            date = esc(pr["merged_date"])
            # card
            inner += f'<a href="{esc(pr["url"])}" target="_blank">'
            inner += f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="10" fill="{palette["card"]}" stroke="{palette["border"]}" stroke-width="1.2"/>'
            # synapse dot
            inner += f'<circle cx="{x+16}" cy="{y+card_h/2:.0f}" r="6.5" fill="{palette["accent"]}" stroke="{palette["violet"]}" stroke-width="1.5" opacity="0.95"/>'
            inner += f'<circle cx="{x+16}" cy="{y+card_h/2:.0f}" r="2.2" fill="white" opacity="0.95"/>'
            inner += f'<text x="{x+32}" y="{y+17}" fill="{palette["text"]}" font-family="JetBrains Mono,ui-monospace,monospace" font-size="11.5" font-weight="600">{repo}</text>'
            inner += f'<text x="{x+32}" y="{y+30}" fill="{palette["muted"]}" font-family="Inter,ui-sans-serif,system-ui" font-size="10.5">{title}</text>'
            inner += f'<text x="{x+card_w-10}" y="{y+30}" text-anchor="end" fill="{palette["violet"]}" font-family="JetBrains Mono,monospace" font-size="9">{date}</text>'
            inner += f'</a>'
        # label
        inner += f'<text x="{w/2:.0f}" y="{h-10}" text-anchor="middle" fill="{palette["muted"]}" font-family="Inter,ui-sans-serif" font-size="9.5" letter-spacing="0.8">MERGED — verified synapses that fired</text>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<title>Merged PRs — verified synapses ({label})</title>
<rect width="{w}" height="{h}" rx="12" fill="{palette["bg"]}"/>
{inner}
</svg>'''
    return svg

def generate(out_dir="output", data_path="data/merged-prs.json"):
    os.makedirs(out_dir, exist_ok=True)
    prs = load_prs(data_path)
    for palette, label in [(DARK, "dark"), (LIGHT, "light")]:
        svg = render_svg(prs, palette, label)
        path = os.path.join(out_dir, f"merged-prs-{label}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(prs)} PRs)")
    return prs

if __name__ == "__main__":
    generate()
