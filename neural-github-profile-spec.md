# Neural GitHub Profile — Concept & Build Spec
### For: arjun-github-profile-readme (github.com/<username>/<username>)
### Status: Ready to hand to a coding agent (Claude Code / Cursor / OpenCode)

---

## 1. What this is

A GitHub profile README (`github.com/<username>/<username>`) re-themed around a
**neural / neuroplasticity metaphor**, distinct from and simpler than the full
3D "World Between Worlds" brain portfolio planned for the AIN site. This is the
**fast, low-lift version** of the same visual language, built entirely from
static assets a GitHub Action regenerates on a schedule.

Two things live here:
1. A **neural-pulse contribution animation** — a reskinned fork of the
   "snake eats contribution graph" pattern, where instead of a snake eating
   cells, a **traveling impulse lights up contribution cells like a firing
   neuron**, leaving a faint afterglow trail (myelinated-path feel).
2. A **merged-PR / proof-of-work strip** — a static SVG panel listing only
   *merged* PRs (Presidio #2084, LiteLLM #34087, etc.), styled as "synapses
   that fired" — i.e. contributions that actually connected, not just opened.

---

## 2. Why this, and why now (reasoning)

- **README ≠ website.** A GitHub profile README is markdown rendered by
  GitHub. It cannot execute JavaScript or WebGL — no Three.js, no camera
  travel, no React. It *can* show static images, GIFs, and animated SVGs
  that a scheduled GitHub Action regenerates and commits. So the neural
  metaphor has to be expressed through **pre-rendered animation**, not
  interaction. That's a real constraint, not a limitation of ambition — it's
  the medium.
- **This is the correct scope-split.** The big 3D brain (Three.js, pathway
  travel, camera choreography) belongs on the AIN portfolio site, which is a
  multi-week build. This README piece is a weekend-scale fork-and-reskin job.
  Doing this first lets the neural visual language get tested and refined
  cheaply before it's committed to in the much bigger build.
- **It's native to the audience.** People who land on a GitHub profile —
  OSS maintainers who just merged your PR, recruiters doing a background
  check — are already primed to trust the contribution graph and PR history
  as ground truth. This surface is where the "only merged PRs count" rule
  does its work with zero persuasion needed.
- **It's low-risk.** If the reskin looks bad, it's a CSS/SVG palette change
  in an Action, not a rebuild of a 3D scene graph.

---

## 3. Technical foundation

Base project to fork: **Platane/snk** — generates a snake game from a GitHub
user's contribution graph and outputs an animated SVG/GIF via a scheduled
GitHub Action, designed specifically to be embedded in profile READMEs.

We are **not** using its snake mechanic conceptually (no eating). We're
reusing its **pipeline**: pull contribution data → walk a path across the
grid → render each frame as SVG → animate. The path-walking logic gets
replaced with a neural-pulse traversal; the render/animate/commit pipeline
stays.

For the merged-PR strip, the reference pattern is generic **SVG widget
generation** (see: github-widgets-style repos) — GitHub API pull → template
into SVG → cache/serve or commit as a static file.

---

## 4. Component specs

### 4a. Neural Pulse Contribution Animation

**Behavior:**
- Instead of a snake consuming cells in sequence, render a **single glowing
  point (the impulse)** that travels along a path visiting contributed cells
  in chronological order (oldest → newest, left to right as GitHub already
  lays out the grid).
- Each cell the impulse passes **lights up and fades to a dim residual glow**
  (not fully dark, not fully bright) — this is the "myelinated pathway"
  look: recently active regions stay slightly brighter than untouched cells.
- Empty (no-contribution) cells stay as low-opacity dark nodes the whole time
  — they're part of the "brain" but never fire.
- Palette: dark background (near-black or deep indigo, not pure black),
  cell-off color a muted slate, pulse color a warm bright cyan-to-violet
  gradient (avoid generic "AI blue" — go slightly warmer/purpler to match
  Obsidian's plum-and-graphite palette rather than sci-fi teal).
- Frame rate / duration: same cadence as the original snk output (loops,
  regenerates daily via cron).

**Deliverables:**
- `.github/workflows/neural-pulse.yml` — scheduled Action (daily, plus
  `workflow_dispatch` for manual trigger)
- Forked/modified renderer package (or a small Node script using the same
  contribution-graph data source snk uses) that outputs
  `dist/neural-pulse-dark.svg` and a light-mode variant if desired
- Output committed to an `output` branch, referenced in `README.md` via
  `<picture>` markdown for light/dark mode switching

### 4b. Merged-PR / Proof-of-Work Strip

**Behavior:**
- Static SVG panel, regenerated on a schedule (or on-push via Action),
  listing merged PRs only — pulled via GitHub API (`state: closed`,
  `merged: true`).
- Each entry: repo name, PR number/title (short), merge date. Rendered as a
  short horizontal list or small card row — styled as a synapse strip
  (each entry a small connected node), not a big block.
- Data source for now can be **hand-maintained JSON** (`prs.json`) rather
  than a live API call, since the volume is small and curation matters more
  than automation here — matches the existing rule that only a verified
  merged badge qualifies. Automate later if volume grows.

**Deliverables:**
- `data/merged-prs.json` — hand-curated list (repo, PR#, title, url, date)
- Small Node/Python script that templates this into `dist/merged-prs.svg`
- Action step (can be the same workflow as 4a) that regenerates on push to
  `main` when `prs.json` changes

### 4c. README layout

- Header: name/tagline, minimal
- Neural pulse animation (4a) embedded via `<picture>` for dark/light
- Merged-PR strip (4b)
- Plain, fast list underneath: current focus (Aegis / O&G), links (AIN
  portfolio, LinkedIn) — no cleverness here, this is the scan-fast layer
- No live 3D, no JS-dependent embeds — everything must degrade gracefully
  to a static image if animation fails to load

---

## 5. Explicit non-goals (for this component)

- No Three.js / WebGL / React here — that's the AIN site's job.
- No literal Star Wars references, no realistic anatomical brain render —
  abstract node-and-path visual only.
- No "every commit = fireworks" — the pulse should read as calm and
  deliberate, not gamified.

---

## 6. Ready-to-paste prompt for a coding agent

```
You are implementing a GitHub profile README animation for user <github_username>.

GOAL
Fork the rendering pipeline from Platane/snk (github.com/Platane/snk) but
replace its snake-eats-cells path logic with a "neural pulse" traversal:
a single glowing point moves through the user's contribution graph in
chronological order, lighting each contributed cell as it passes and
leaving a dim residual glow behind (not full fade-to-black). Uncontributed
cells stay as low-opacity static nodes throughout.

CONSTRAINTS
- Output must be a GitHub-embeddable animated SVG (and GIF fallback),
  generated by a scheduled GitHub Action (daily cron + workflow_dispatch),
  committed to an `output` branch — same deployment pattern as the
  Platane/snk project.
- No client-side JS execution assumed at render time in the README (GitHub
  READMEs don't execute scripts) — all animation must be baked into the SVG/GIF.
- Provide both a dark-mode and light-mode variant, switched via a <picture>
  tag in README.md.
- Color palette: dark near-black/deep-indigo background, muted slate for
  inactive cells, warm cyan-to-violet gradient for the pulse and its trail.
  Avoid generic flat "tech blue."
- Keep the animation calm/deliberate — no per-commit fireworks, no
  screen-filling bursts.

DELIVERABLES
1. `.github/workflows/neural-pulse.yml` — the scheduled Action
2. Modified renderer (fork of snk's core or an equivalent small Node
   package) producing `dist/neural-pulse-dark.svg` and
   `dist/neural-pulse-light.svg`
3. A second, independent component: a "merged PR strip" SVG generator that
   reads a hand-maintained `data/merged-prs.json` (fields: repo, pr_number,
   title, url, merged_date) and renders it as a small horizontal strip of
   connected nodes (synapse styling, not full cards). Regenerate on push to
   main when prs.json changes, via the same or a second workflow.
4. A `README.md` draft embedding both pieces plus a plain scannable text
   section (current focus, portfolio link, LinkedIn) below them — this
   section must render correctly even if the SVGs fail to load.
5. A short SETUP.md explaining: how to trigger the Action manually, where
   output lands, and how to update prs.json.

ACCEPTANCE CRITERIA
- Animation loops cleanly, dark and light variants both readable
- Uncontributed grid cells are visibly present but clearly dimmer than any
  cell the pulse has touched
- Merged-PR strip only ever shows entries from prs.json — no live-fetch
  fallback that could surface unmerged/open PRs
- Everything degrades to a static (non-animated) image if SVG animation is
  unsupported by the viewer, per GitHub's README rendering behavior
- No dependency on WebGL, Three.js, or any client-side script execution
```

---

## 7. Suggested next step

Take Section 6 to Claude Code (or your preferred coding agent) as-is. Once
the neural-pulse animation exists and you've seen it render for real, that's
the moment to decide whether the same palette/motion language should carry
over unchanged into the AIN site's 3D brain, or whether it needs adjustment
once seen at scale.
