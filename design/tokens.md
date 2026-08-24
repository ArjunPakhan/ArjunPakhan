# Design Tokens — Shared (GitHub Profile + Future Portfolio)

Centralized palette from frozen V2.2 fluorescence culture. Used by `neural/culture-v2`, `output/*.svg`, and future portfolio (Obsidian Brain).

## Backgrounds
- `--bg-obsidian`: `#090A0F` (dark field, vignette `#17131f` → `#090A0F` radial 32% 38% r88%)
- `--bg-light`: `#f4f2f8` / `#f6f7fb` (for light variant, keep same semantic colors with +15% opacity)
- `--card-dark`: `#13141c` / `#090A0F` with `border #2a2f42`
- `--card-light`: `#ffffff` `border #d9deeb`

## Neural Semantics (LOCKED)
| Token | Value | Role |
|-------|-------|------|
| `COLOR_STRUCTURE_GREEN_DIM` | `#3E8F6A` | dendrite/axon rest, healthy tissue, dormant dendrites |
| `COLOR_STRUCTURE_GREEN_BRIGHT` | `#5FBF8A` | accent on green, healthy resting neurons |
| `COLOR_STRUCTURE_GREEN_DARK` | `#254636` | dormant soma `DORMANT_FILL` |
| `COLOR_ACTIVE_CORAL_DIM` | `#B9575D` | active neuron base |
| `COLOR_ACTIVE_CORAL_BRIGHT` | `#E87972` | firing peak |
| `COLOR_ACTIVE_CORAL_GLOW` | `#f0a0a0` / `#FF9A94` L4 | bright coral + pale center |
| `COLOR_PLASTICITY_DIM` | `#7059A6` | residual afterglow base |
| `COLOR_PLASTICITY` | `#8D72C0` | strengthened pathway |
| `COLOR_PLASTICITY_SOFT` | `#a99ad0` / `#d8c8ff` | discharge ring, pulse halo |
| `COLOR_ELECTRICAL_WHITE` | `#F7F3FF` | pulse core (brightest) |
| `COLOR_ELECTRICAL_CYAN` | `#EAF7F5` | pulse halo/trail stroke |

Lifecycle: `green (0.24-0.40 resting) → coral (0.88-1.0 firing) → white pulse (0.94) → violet (0.32-0.58 residual) → green`

## Neurite
- Axon: `0.85-1.55px` (tier3 `+14%`), tier1 green, tier3 violet, `floor 0.12-0.33`, `peak 0.44-0.88`
- Dendrite: `0.48-1.15px`, green `0.9`, fork `0.68×`, grows `14-32%`
- Soma: `4.2-7.4px`, halo `r*2.05`, growth `14-28`

## Typography (direction)
- Mono: `JetBrains Mono, ui-monospace` for PR strip / repo# / dates
- Sans: `Inter, ui-sans-serif` for labels / editorial copy
- Profile copy stays editorial, no badge wall.

## Spacing / Glow
- `MARGIN_X 48, MARGIN_Y 42, CELL_X 14.5`, `filter soft-blur 2.2 / soft-blur-lg 7`, `stroke-linecap round`, `rx 10-12`, `letter-spacing 0.8` for strip label.

## Usage
- GitHub `output/` SVGs embed tokens via inline CSS; no external CSS.
- Future portfolio imports same tokens via `design/tokens.json` (generate from this doc) to reuse neural assets without calling GitHub API.

Do not invent new semantic colors; map any new state to green/coral/violet/white.
