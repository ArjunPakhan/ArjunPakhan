# NeuroGit Architecture — V2.2 Frozen

## Overview
`REAL GITHUB DATA → adapters/github_contributions.py → normalized weeks[].days[] → neural/culture-v2 (frozen V2.2) → output/*.svg → README / portfolio`

V1 (`neural/v1`, 858×152, 192e) kept as reference graph branch. V2 (`neural/culture-v2`, 880×420, ~35 neurons 56 axons, fluorescence) is the preferred artistic direction.

## Repository Tree
```
/
├── README.md
├── adapters/github_contributions.py
├── data/merged-prs.json
├── design/tokens.md
├── generate.py                     # unified pipeline (sample/github → dark/light)
├── generators/merged_prs.py
├── neural/
│   ├── v1/ (frozen python + generate-svg.js legacy)
│   └── culture-v2/ (data.py, culture_model.py, culture_keyframes.py, build_culture_svg.py, render_culture_preview.py, ARCHITECTURE.md, sample-contributions.json)
├── output/
│   ├── neural-culture-dark.svg
│   ├── neural-culture-light.svg
│   ├── merged-prs-dark.svg
│   ├── merged-prs-light.svg
│   └── contributions.json
└── .github/workflows/update-neural.yml + update-profile-assets.yml
```

## Data Pipeline
1. `DATA_SOURCE=sample` → loads `neural/culture-v2/sample-contributions.json`
   `DATA_SOURCE=github` → `GITHUB_TOKEN` + `GITHUB_USERNAME` → GraphQL `contributionCalendar` → `level_map NONE/QUARTILE → 0-4` → normalized 53×7
2. `adapters.validate` ensures 53×7, weekday 0-6, level 0-4
3. `culture_model.build` generates soma/dendrites/axons + firing delays + tiers + growth windows
4. `build_culture_svg` emits CSS `@keyframes` (soma/halo/axon/dendrite/cluster/discharge/pulse) dark/light variants (same geometry)
5. `generators/merged_prs` templats hand-curated `data/merged-prs.json` → synapse strip SVGs
6. Commit to `output` branch, README `<picture>` switches `neural-culture-dark/light.svg` via `#gh-dark-mode-only`

## Files Created/Modified
Created: `neural/`, `adapters/github_contributions.py`, `data/merged-prs.json`, `generators/merged_prs.py`, `generate.py`, `output/`, `.github/workflows/update-neural.yml`, `.github/workflows/update-profile-assets.yml`, `design/tokens.md`, `ARCHITECTURE.md`. Preserved: `neural/culture-v2` (frozen), `neural/v1` (frozen), `generate-svg.js` legacy.

## Workflows
- `update-neural.yml`: `cron 4AM UTC` + `workflow_dispatch` + `push` on `neural/culture-v2/**, adapters/**`. Setup Python 3.12, `pip install Pillow`, `DATA_SOURCE=github GITHUB_TOKEN secrets.GITHUB_TOKEN python generate.py --real`, deploy to `output` branch only if changed (`git diff --cached --quiet || commit`). Least privilege `contents: write`.
- `update-profile-assets.yml`: on `data/merged-prs.json` push → regenerates strip.

## Local Commands
```bash
# sample render
python generate.py
# real GitHub
DATA_SOURCE=github GITHUB_USERNAME=ArjunPakhan GITHUB_TOKEN=ghp_xxx python generate.py --real
python generate.py --gif   # also 60f GIF
python adapters/github_contributions.py --source sample --out /tmp/test.json
python -m generators.merged_prs
# validate
python -c "import json, xml.etree.ElementTree as ET; json.load(open('output/contributions.json')); ET.parse('output/neural-culture-dark.svg')"
```

## Env Vars
- `DATA_SOURCE` sample|github (default sample)
- `GITHUB_TOKEN` / `GH_TOKEN` (required for github)
- `GITHUB_USERNAME` / `GITHUB_REPOSITORY_OWNER` / `GITHUB_REPOSITORY`

No secrets hard-coded, no private repo leaks, never log token.

## Placeholders (unresolved)
- `README.md` now points to `ArjunPakhan/ArjunPakhan` — verify repository is renamed to `ArjunPakhan/ArjunPakhan` for profile README.
- LinkedIn URL — not guessed; `https://linkedin.com/in/<your>` remains to be configured before live push.

## Live Verification (status: local only)
- Local: `python generate.py` → dark/light SVGs validate, 35n 56ax, merged-prs 2 entries, JSON ok.
- Live GitHub: **pending** — needs push to `output` branch and profile repo rename; dark/light `<picture>` and PR strip URLs not yet live-verified.

## Portfolio Reuse
Future site imports `output/contributions.json` + `output/neural-culture-*.svg` + `design/tokens.md` as shared data layer — no direct GitHub API coupling. `SHARED DATA LAYER → GitHub README (editorial) + Portfolio (interactive + Obsidian Brain)`; neural assets reusable statically, culture growth/pulse logic portable without re-fetching.
