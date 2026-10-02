# Design Tokens — Shared (GitHub Profile + Future Portfolio)

Centralized palette from the canonical node-grid spec. Used by `neural/node-grid`, `output/*.svg`,
and the future portfolio (Obsidian Brain).

## Backgrounds
- `--bg-obsidian`: `#0b0c12` (obsidian — not pure black)
- `--bg-light`: `#f4f3f8` (light variant; colors re-adjusted for contrast, not the dark values reused)
- `--card-dark`: `#13141c` with `border #2a2f42`
- `--card-light`: `#ffffff` with `border #d9deeb`

## Neural Semantics (LOCKED — canonical spec)
| Token | Dark | Light | Role |
|-------|------|-------|------|
| `COLOR_DORMANT` | `#3a3f4d` | `#a7adc3` | graphite/slate — dormant day |
| `COLOR_FIRE` | `#d8f7ff` | `#0c9cc4` | warm cyan-white firing/peak flash |
| `COLOR_RESTING` | `#8f5de0` | `#7c50c8` | plum — resting/strengthened state |
| `COLOR_CLUSTER` | `#4b3a7a` | `#6a5ba0` | cluster-activation wash (low opacity, blurred) |
| `COLOR_BREATH` | `#cbb8ff` | `#b6a3e6` | whole-grid resolution / breathing overlay (low opacity) |

Resting fill is an interpolation of graphite → plum weighted by contribution intensity + recency.

Lifecycle: `dormant (graphite) → firing (cyan-white flash) → resting (plum, brighter than dormant)`.
Inactive days never fire; they stay dormant. This residual-trace "neuroplasticity" is the signature beat.

## Typography (direction)
- Mono: `JetBrains Mono, ui-monospace` for PR strip / repo# / dates
- Sans: `Inter, ui-sans-serif` for labels / editorial copy
- Profile copy stays editorial, no badge wall.

## Spacing / Glow
- Node grid: cell pitch `12`, gap `3`, margin `24`, base node radius `4.6`.
- `filter blur-cluster 4` (cluster wash), `blur-overlay 8` (resolution/breathing).
- Strip: `stroke-linecap round`, `rx 10-12`, `letter-spacing 0.8` for label.

## Usage
- GitHub `output/` SVGs embed tokens as inline SMIL/`fill` values; no external CSS.
- Future portfolio imports the same tokens via `design/tokens.json` (generate from this doc) to reuse
  the shared palette without calling the GitHub API.

Do not invent new semantic colors; map any new state to graphite / cyan-white / plum.
