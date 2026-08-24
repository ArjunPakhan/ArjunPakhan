# Neural Culture V2 — Architecture (FROZEN)

> **V2.2 accepted as final experimental version.** No further visual refinement, morphology, palette, growth, pulse, or rendering changes without explicit request. V1.4 (`neural-pulse-source`) kept untouched as reference graph branch.

## 1. V2 Purpose & Visual Concept

V1 = `53×7 GitHub grid → neural graph` (dots + Bézier edges).  
V2 = `GitHub activity → living cultured neuronal network` viewed through fluorescence microscopy.

Target perception: `cultured neurons growing in dark field → soma/dendrites/axon/terminal morphology → spontaneous electrical propagation → local cascade → violet memory`. Not a dot-graph with decoration, not a brain/3D/petri illustration.

 Canvas 880×420, palette obsidian + fluorescence, ~35 neurons + ~56 axons — morphology over density.

## 2. data.py — Contribution Contract

Mirrors GitHub GraphQL `contributionCalendar.weeks[].contributionDays[]`:

```json
{ "weeks": [{ "days": [{ "date":"2025-08-24", "weekday":0, "count":3, "level":2 }] }] }
```

`weekday 0=Sun..6=Sat`, `level 0-4` (0=0, 1=1-2, 2=3-5, 3=6-9, 4=10+). `generate(seed=42)` synthesizes 53×7 via random-walk `week_level` + bursts (14,15,33,47) + dead weeks (5,22,40). Swapping to real data = adapter emitting same `weeks[].days[]`; `culture_model` unchanged.

## 3. culture_model.py — Neuron Generation

`build(data, seed=7)` → `{ neurons, axons, clusters, last_neuron, width, height }`

- **Seed count per week:** `total`+`max_lvl`+`active` → 0-2 neurons/week (≥18 or L4+4→2; ≥8 or ≥3→1; ≥3→52%→1; ≥1→18%→1). Pad to ≥28, repulsion <34px.
- **Soma:** `r 4.2-7.4` (`4.4+activity*2.4+L`); `pre/peak/mid/floor` + `pre_op 0.24-0.40`, `peak 0.88-1.0`, halo `lvl≥3`. Organic `ox/oy ±0.7`.
- **Timing:** `delay_pct = PROP_START + (week_rank/jitter/stagger)` 6→87%, `rise 0.55+0.32*act`, `decay 3.0+2.8*act`, `growth_start 14+week/53*8±1.2`, `growth_end +12+8*act`.
- **Dendrites:** `2-4 primaries` (asymmetric sector, attraction to 3 nearest <108px, 62% bias), length `14-52`, `fork 42%+act`, optional `fork2 22%`, `width 0.48-1.15`. Attraction field = `nearby angles`.
- **Axons:** downstream `dw 1-5`, `dy<110`, `dx>8`, nearest 10 sorted, budget `L1→1, L2→2, L3→2 (+1 if act>0.75)`. Geometry `sx0 = soma+2.2*cos(ang)`, smooth `bend 0.12-0.26`, `term_r = target_r+4.0`, `Q cx,cy`, tier via `avg_lvl` (≥3→3, ≥2→2), `floor 0.12-0.33* tier`, `peak 0.44-0.88* tier`, `width 0.85-1.55`, `travel 1.15-2.45` (`dist*0.028+0.95`), `travel_end = b.delay+0.06`, `growth 18→56`.
- **Clusters:** weeks with ≥2 neurons.

Tunable: `MARGIN/CELL_X/Y`, burst/dead weeks, `n_primary` formula, `bend`, `budget`, `r` scales.

## 4. Representation

- **Soma:** organic circle (`r` + `ox/oy`), `filter soft-blur` halo `r*2.05/*1.48`, white highlight `r*0.38`.
- **Dendrite:** `M soma Q cx,cy x2,y2` + `fork`/`fork2` sharing same `dendrite_stops` opacity. Thin `0.48-1.15px`, green.
- **Axon:** `M sx0 Q cx,cy ex,ey` (dominant, smoother, thicker than dendrite), `tier1 green / tier3 violet`, growth `14-56`, terminal bouton `r 1.9+` drawn on `gf>0.72`.
- **Terminal:** small bouton circle + `discharge` ring `r 2.1→6.0` at `travel_end`.

## 5. Growth Timeline

Global culture development (opacity + partial-length via `growth_frac`):

- `0-8%` dormant culture (soma `0.32×`, processes `0`)
- `8-14%` soma fade-in
- `14-35%` dendrite outgrowth (`gs 14→ge ~32`)
- `18-56%` axon outgrowth (`gs 18→ge 38-56`), terminals appear `gf>0.72`
- `35-50%` contact (processes meet)
- `50-60%` network formation (all axons at `floor`)
- `60-85%` electrical activity (pulse `travel 60-87`)
- `85-95%` plasticity (violet residual)
- `95-100%` resting (`floor`)

PIL draws `n_pts = 26*gf` partial curves; SVG uses opacity ramp (dash via growth stops).

## 6. Color Semantics (LOCKED)

Background `#090A0F`.

| Role | Tokens | Use |
|------|--------|-----|
| **GREEN structure** | `#2e4d3e→#3E8F6A` / `#5FBF8A` / `#254636` | dormant soma, resting dendrites/axon tier1, healthy tissue |
| **CORAL firing** | `#c46a6e→#FF9A94` / `#B9575D/#E87972` | soma firing peak, halo `L3 0.28/L4 0.36` |
| **VIOLET plasticity** | `#5a4a7a→#8D72C0` / `#a99ad0` | residual soma, strengthened tier3 axons, cluster wash, afterglow |
| **WHITE electrical** | `#F7F3FF` core + `#EAF7F5` halo/trail | travelling pulse (brightest, `0.94` peak) |

Lifecycle: `green (rest) → coral (activate) → bright coral (fire) → white pulse → violet (afterglow) → green`. Never rainbow/random. Centralized in `culture_model.py` (`COLOR_*`, `PRE/PEAK/RESIDUAL_FILL`, `EDGE_*`).

## 7. Pulse Propagation

Shared `culture_keyframes._ease smoothstep`, `_qbez` Q-Bézier. Per axon `travel_start/end/dur` (~1.15-2.45% cycle). SVG: `offset-path:path('M…Q…')` + `offset-distance 0→100%` + `animateMotion` fallback; halo `r1.35` violet + core `r1.05` white + trail `fe-0.11`. PIL `pulse_xy/opacity` matches SVG stops. Sequence `source soma fire → pulse enters axon → travels → terminal discharge → dest dendrite → dest soma fire → local cascade`.

## 8. Neuroplasticity

- Resting `floor_op` tiered: `tier3 ×1.32` (+32%) violet-tinted → frequently used pathways subtly thicker (+18% width) and brighter at rest.
- After firing `mid/floor` violet residual lingers `decay 3-5.8`.
- Cluster wash `0.18` at `fire` hints memory.

Subtle `25-35%` difference, never neon. Repeated activity → green/violet shift.

## 9. SVG Renderer `build_culture_svg.py`

`build(model)` emits CSS `@keyframes` per element (soma/halo/axon/dendrite/cluster/discharge/scene + `pulse` offset-distance), layered `<g>` clusters→axons→dendrites→discharges→pulses→halos→somas, `radialGradient bg-vignette #17131f→#090A0F`, `soft-blur 2.2 / 7`. Outputs `dist/neural-culture-dark.svg` 880×420.

## 10. Preview Renderer `render_culture_preview.py`

`pil_frame(model,t,scale)` draws same stops via `eval_stops` + `growth_frac` partial paths to RGBA→RGB on `#090A0F`. `render_gif(120,scale2)` → `neural-culture-preview.gif` 24s, `render_snapshots([1,15,35,50,65,85,95],scale3)` + close-ups `620×480 @4×` crop `310×240` around top-3 active central neurons. Falls back to PIL if `cairosvg` missing.

## 11. Replacing Sample Data with Real GitHub Data

1. Query `contributionCalendar` (GraphQL or REST scrape) for 53 weeks ending Saturday.
2. Map each day → `{ date, weekday (0=Sun), count, level }` via `level_for_count`.
3. Write `sample-contributions.json` (or pass dict directly) `{ weeks:[{days:[7]}]*53 }`.
4. Call `culture_model.build(data)` — no renderer changes. Chronology preserved via `week` ordering; contribution intensity drives `soma_r`, `dendrite count`, `axon tier`, `firing prob`, `residual`.

## Final Output Paths

```
neural-culture-v2/dist/neural-culture-dark.svg        # 880×420 SVG (V2.2)
neural-culture-v2/dist/neural-culture-preview.gif     # 120f ×2 24s dev preview
neural-culture-v2/dist/neural-culture.gif             # 60f ×1 24s 64-96c
neural-culture-v2/dist/frame_*.png                    # 1,15,35,50,65,85,95 @3×
neural-culture-v2/dist/closeup_65.png / closeup_85.png # 620×480 focus
neural-pulse-source/dist/neural-pulse-dark.*          # V1.4 frozen reference (858×152, 192e)
```

## Tunable Parameters

`CYCLE_S 24`, `PROP 6-87`, `CELL_X 14.5`, `WIDTH/HEIGHT`, `soma_r 4.2-7.4`, `peak 1.32×`, `dendrite n_primary 2-4 spread 1.9`, `fork 0.42`, `axon budget L1:1 L2:2`, `bend 0.12-0.26`, `travel dist*0.028+0.95`, `growth_start 14/18`, `COLOR_*`, `halo *2.05/*1.48`, `cluster rx+14`.

---
*Branch frozen 2026-08-23 — V2.2 is the accepted fluorescence culture experiment. Compare against V1.4 before any V1.5 trunk or data wiring.*
