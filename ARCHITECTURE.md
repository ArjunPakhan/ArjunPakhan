# NeuroGit Architecture — Node-Grid (canonical)

## Overview
`REAL GITHUB DATA → adapters/github_contributions.py → normalized weeks[].days[] → neural/node-grid (SMIL) → output/*.svg → README`

The **node-grid** generator (`neural/node-grid/`) is the single canonical output. It renders the
contribution calendar as a 53×7 circle grid with a per-node lifecycle
(dormant → activation → firing → afterglow → resting), using static SMIL
`<animate>` elements (no JS/WebGL/CSS — the only thing a GitHub README can animate).

**Archived (reference only, not deleted, not wired to anything):**
- `neural/v1/` — node-grid with edges, CSS `@keyframes`, 24s cycle.
- `neural/culture-v2/` — fluorescence "cultured neurons" (dendrites/axons/soma), CSS `@keyframes`.

Both predate the canonical spec and diverged from it (palette + structure + rendering tech).
Do not regenerate, wire, or extend them; the canonical path is `neural/node-grid/`.

## Repository Tree
```
/
├── README.md                          # points at output/neural-grid-{dark,light}.svg
├── adapters/github_contributions.py   # data pull (reused; not visual-direction-dependent)
├── data/merged-prs.json               # hand-curated, verified-merged PRs only
├── design/tokens.md
├── generate.py                        # unified pipeline (sample/github → dark/light)
├── generators/merged_prs.py           # merged-PR strip (reused)
├── neural/
│   ├── node-grid/                     # ★ CANONICAL — SMIL node grid
│   │   ├── model.py                   #   palette, timing, geometry, lifecycle params
│   │   ├── build_svg.py               #   SMIL <animate> emission (dark + light)
│   │   └── sample-contributions.json
│   ├── v1/                            # ARCHIVED reference
│   └── culture-v2/                    # ARCHIVED reference
├── output/                            # committed to `output` branch
│   ├── neural-grid-dark.svg
│   ├── neural-grid-light.svg
│   ├── merged-prs-dark.svg
│   ├── merged-prs-light.svg
│   └── contributions.json
└── .github/workflows/update-neural.yml
```

## Data Pipeline
1. `DATA_SOURCE=sample` → `neural/node-grid/sample-contributions.json`;
   `DATA_SOURCE=github` → `GITHUB_TOKEN` + `GITHUB_USERNAME` → GraphQL `contributionCalendar` → level 0–4 → normalized 53×7.
2. `adapters.validate` ensures 53 weeks × 7 days, weekday 0–6, level 0–4.
3. `model.build_model` computes per-node grid position, intensity (0–4), recency, activation time,
   peak/resting opacity, resting color (graphite→plum), fire radius, and dense-week clusters.
4. `build_svg.render_svg` emits SMIL `<animate>` (opacity lifecycle, fill flash, radius, cluster wash,
   resolution+breathing overlay) for dark and light variants (same geometry, re-adjusted palette).
5. `generators.merged_prs` renders `data/merged-prs.json` → PR strip SVGs (verified-merged only).
6. Workflow commits everything to the `output` branch; README `<picture>` switches dark/light.

## Cycle (locked to spec)
`DORMANT → INTRO → NEURAL PROPAGATION → CLUSTER ACTIVATION → PRESENT DAY → WHOLE-NETWORK RESOLUTION → RESTING STATE (2 breathing pulses) → PAUSE → fade to black → LOOP` — 14s total.
The resting-state glow (brighter than dormant, weighted by intensity + recency) is the signature
neuroplasticity beat; inactive days stay dormant and never fire.

## Workflows
- `update-neural.yml` (only workflow): `cron 4AM UTC` + `workflow_dispatch` + `push` on
  `neural/node-grid/**, adapters/**, generators/**, generate.py, data/**`.
  Python 3.12, no pip deps (stdlib only), `DATA_SOURCE=github GITHUB_TOKEN=secrets.GITHUB_TOKEN
  python generate.py --real`, deploy to `output` branch. Least privilege `contents: write`.
- Removed: `neural-pulse.yml` (stale Node.js `generate-svg.js` that no longer exists) and
  `update-profile-assets.yml` (redundant — the canonical workflow already regenerates merged-prs
  on `data/**` changes, and it committed to the wrong branch).

## Local Commands
```bash
python generate.py                                              # sample render
DATA_SOURCE=github GITHUB_USERNAME=ArjunPakhan python generate.py --real
python -m generators.merged_prs
# validate
python -c "import json, xml.etree.ElementTree as ET; json.load(open('output/contributions.json')); [ET.parse(f'output/neural-grid-{t}.svg') for t in ('dark','light')]"
```

## Env Vars
- `DATA_SOURCE` sample|github (default sample)
- `GITHUB_TOKEN` / `GH_TOKEN` (required for github)
- `GITHUB_USERNAME` / `GITHUB_REPOSITORY_OWNER` / `GITHUB_REPOSITORY`

No secrets hard-coded, no private repo leaks, never log token.

## Placeholders (unresolved)
- LinkedIn URL — **not guessed**; `https://linkedin.com/in/<your>` remains to be configured.
  Flagged back to Arjun in this session (see commit message).
- Portfolio URL — `https://arjunpakhan.example.com` placeholder, wired to future Obsidian Brain site.

## Live Verification
- Local: `python generate.py` → dark/light SVGs validate (371 nodes, 6 clusters, valid XML), merged-prs 2 entries, JSON ok.
- Live GitHub (2026-10-02): `output` branch pushed. `raw.githubusercontent.com/.../output/neural-grid-*.svg`
  serves the full SMIL (486 `<animate>` per theme, `image/svg+xml`, CSP permits SMIL). See RISKS.md risk-1 —
  resolved. Final pixel-level animation check remains a visual confirmation on github.com/ArjunPakhan.

## Portfolio Reuse
Future site imports `output/contributions.json` + `output/neural-grid-*.svg` + `design/tokens.md` as a
shared data layer — no direct GitHub API coupling. `SHARED DATA LAYER → GitHub README (editorial) + Portfolio (interactive + Obsidian Brain)`.
