# Neural Pulse Contribution Animation — V1 Prototype

## What's here
- `data.py` — sample 53×7 dataset generator, shaped exactly like GitHub's
  GraphQL `contributionsCollection.contributionCalendar.weeks[].contributionDays[]`
  (date, weekday 0-6, count, level 0-4). Swap this module for a real API
  adapter later; `model.py` never needs to change as long as it gets that
  same `weeks[].days[]` shape.
- `model.py` — turns the dataset into node geometry, per-node fire timing
  (chronological, with cluster bursts and organic jitter), color/size states
  across the dormant → activation → firing → afterglow → resting lifecycle,
  and sparse local synaptic edges (temporally + spatially local only).
- `keyframes.py` — shared CSS-keyframe stop generator, used by both the SVG
  builder (emits real `@keyframes`) and the preview renderer (interpolates
  the same stops at arbitrary t) — so the exported SVG and the GIF preview
  can't drift out of sync.
- `build_svg.py` → `dist/neural-pulse-dark.svg` — the real deliverable.
- `render_preview.py` → `dist/neural-pulse-dark.gif` (README-weight, ~270KB)
  and `dist/neural-pulse-dark-preview.gif` (larger, for closer inspection).

## Design decisions worth flagging for review
- **24s loop**, phases: intro fade (0–5%) → chronological propagation with
  cluster bursts (6–87%) → soft resolution wash at the most recent
  contribution (90.5%) → hold (87–96%) → fade back to dormant for the seam.
- **Edges are local-only**: each active node links to at most 1–2 nearby
  (within ~4 weeks / 5 rows) upcoming active nodes, picked from a short
  lookahead window — this is what keeps it from turning into a dense mesh
  or a straight-line "UI" look. Quiet (level-1) nodes usually get only one
  link or none.
- **Neuroplasticity** is a resting-opacity/radius floor that's meaningfully
  higher after a node has fired than before (latent vs. strengthened), and
  scales with that node's contribution intensity — repeated/high activity
  literally leaves a brighter trace.
- **Cluster bursts**: dense weeks (3+ active days) get near-simultaneous
  fire timing (small stagger, not simultaneous-simultaneous) plus a soft
  shared wash behind them, instead of true multi-path branching — this is
  the cheap V1 stand-in the design review flagged; true branching is a V1.5
  candidate once this has been seen live.
- Used **CSS `@keyframes`**, not SMIL, since it's far easier to generate
  programmatically at this density (~110 active nodes + ~130 edges each
  need their own timing). Both animate correctly in an `<img>`-embedded SVG
  in current Chrome/Firefox, which is how GitHub renders README images —
  but this is exactly the kind of thing that needs a real README test
  before final sign-off, which is why the GIF fallback exists.

## Explicitly NOT in this pass (per your spec)
- No real GitHub API wiring — sample data only.
- No light-mode variant yet — dark only, to get the palette/motion right
  first.
- No true multi-path branching, no long-range "correlated activity" edges.

## Known open questions for your review
1. Is the propagation speed right? Right now gaps compress and dense weeks
   stretch slightly, but it's tuned by eye, not against real commit-gap
   statistics.
2. Pre-fire "latent" opacity vs. post-fire "residual" opacity — is the
   contrast between them strong enough at README thumbnail size, or should
   dormant-but-contributed nodes stay closer to invisible until touched?
3. Edge density — currently caps at 1 edge for level 1-2 nodes, 2 for
   level 3-4. Want it sparser or a bit more connected?
