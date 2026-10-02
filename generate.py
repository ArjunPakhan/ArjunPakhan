#!/usr/bin/env python3
"""
Unified generator (canonical):
  DATA_SOURCE=sample|github (+ GITHUB_TOKEN/GITHUB_USERNAME)
  -> adapters/github_contributions.py   (53x7 weeks[].days[], level 0-4)
  -> neural/node-grid (SMIL node-grid)  -> output/neural-grid-{dark,light}.svg
  -> generators/merged_prs.py           -> output/merged-prs-{dark,light}.svg

The node-grid (neural/node-grid) is the canonical animation. neural/v1 and
neural/culture-v2 are archived reference implementations — see ARCHITECTURE.md.

Usage:
  python generate.py
  DATA_SOURCE=github GITHUB_USERNAME=ArjunPakhan python generate.py --real
"""
import os
import sys
import json
import argparse

# make neural/node-grid importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "neural", "node-grid"))

import model as NG_MODEL
import build_svg as NG_BUILD


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--real", action="store_true", help="force DATA_SOURCE=github")
    p.add_argument("--out", default="output")
    p.add_argument("--username")
    args = p.parse_args()

    source = "github" if args.real or os.environ.get("DATA_SOURCE") == "github" else "sample"
    os.environ["DATA_SOURCE"] = source

    # 1. load contributions via the adapter (decoupled from rendering)
    from adapters.github_contributions import load_contributions, validate
    data = load_contributions(source=source, username=args.username)
    validate(data)
    active = sum(1 for w in data["weeks"] for d in w["days"] if d["count"] > 0)
    print(f"[{source}] {len(data['weeks'])} weeks, {active} active days")

    os.makedirs(args.out, exist_ok=True)

    # 2. node-grid SMIL animation, dark + light (canonical)
    for theme in ("dark", "light"):
        m = NG_MODEL.build_model(data, theme=theme)
        svg = NG_BUILD.render_svg(m)
        path = os.path.join(args.out, f"neural-grid-{theme}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(m['nodes'])} nodes, {len(m['clusters'])} clusters, {len(svg)//1024} KB)")

    # 3. merged-PR strip (reused, verified-merged only)
    from generators.merged_prs import generate as gen_prs
    gen_prs(out_dir=args.out, data_path="data/merged-prs.json")

    # 4. latest contributions snapshot for reuse elsewhere
    with open(os.path.join(args.out, "contributions.json"), "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {args.out}/contributions.json")

    print("done — output/neural-grid-*.svg + merged-prs-*.svg + contributions.json")


if __name__ == "__main__":
    main()
