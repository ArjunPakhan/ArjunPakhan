#!/usr/bin/env python3
"""
Unified generator:
  DATA_SOURCE=sample|github (+ GITHUB_TOKEN/GITHUB_USERNAME)
  -> adapters/github_contributions.py
  -> neural/culture-v2 (V2.2 frozen) → output/neural-culture-{dark,light}.svg
  -> generators/merged_prs.py → output/merged-prs-{dark,light}.svg

Usage:
  python generate.py
  DATA_SOURCE=github GITHUB_USERNAME=ArjunPakhan python generate.py --real
  python generate.py --gif  # also render GIF previews
"""
import os
import sys
import json
import argparse

# ensure neural/culture-v2 importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "neural", "culture-v2"))

import culture_model as CM
import culture_keyframes as CK

def generate_neural(data, out_path, theme="dark"):
    # theme affects background only; geometry identical, palette locked to fluorescence with contrast tweak
    # For light theme, we keep same semantic colors but adjust background/opacity contrast via build param
    # We'll call build with theme and post-process bg if needed
    import build_culture_svg as BC
    model = CM.build(data)
    svg = BC.build(model, theme=theme)
    # Light adaptation: swap bg vignette dark→light while keeping green/coral/violet hierarchy
    # BC already supports theme="light" via bg #f4f2f8 else dark #090A0F — we use it
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out_path} ({len(model['neurons'])} neurons, {len(model['axons'])} axons, {len(svg)//1024}KB)")
    return model, svg

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--real", action="store_true", help="force DATA_SOURCE=github")
    p.add_argument("--gif", action="store_true", help="also render GIF previews (slow)")
    p.add_argument("--out", default="output")
    p.add_argument("--username")
    args = p.parse_args()

    source = "github" if args.real or os.environ.get("DATA_SOURCE") == "github" else "sample"
    os.environ["DATA_SOURCE"] = source

    # 1. load contributions via adapter (decoupled)
    from adapters.github_contributions import load_contributions, validate
    data = load_contributions(source=source, username=args.username)
    validate(data)
    print(f"[{source}] {len(data['weeks'])} weeks, {sum(1 for w in data['weeks'] for d in w['days'] if d['count']>0)} active days")

    # 2. generate neural V2.2 dark/light (same geometry, same data)
    os.makedirs(args.out, exist_ok=True)
    # generate once model for dark, reuse geometry for light by rebuilding with same seed+data (deterministic)
    model_dark, _ = generate_neural(data, os.path.join(args.out, "neural-culture-dark.svg"), theme="dark")
    # light variant: same model but light bg — rebuild to keep identical geometry (deterministic seed)
    generate_neural(data, os.path.join(args.out, "neural-culture-light.svg"), theme="light")

    # 3. merged PR strip (verified only)
    from generators.merged_prs import generate as gen_prs
    gen_prs(out_dir=args.out, data_path="data/merged-prs.json")

    # 4. also emit latest contributions snapshot for site reuse
    with open(os.path.join(args.out, "contributions.json"), "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {args.out}/contributions.json")

    # optional GIF
    if args.gif:
        import render_culture_preview as RC
        # dark preview GIF from same model_dark
        RC.render_gif(model_dark, n_frames=60, scale=1, out=os.path.join(args.out, "neural-culture.gif"))
        print(f"wrote {args.out}/neural-culture.gif")

    print("done — no placeholders, verify README URLs point to output/ on output branch")

if __name__ == "__main__":
    main()
