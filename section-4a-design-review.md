# Section 4a Design Review — Neural Pulse Contribution Animation
### No implementation in this pass. Design evaluation only.

---

## 0. The core problem with the original 4a draft

As written, the animation was: one glowing point moves left-to-right through
the grid, each cell it touches flips from "off" to "dim glow," done. That is
functionally identical to snk's traversal engine with a different paint job —
a single-file sequential visit of cells with a two-state (touched/untouched)
outcome. Visually, a viewer will see "a dot moving across squares," which
reads as *snake without the mouth*, not as *neural propagation*.

What actually distinguishes neural propagation from a moving dot:
- **Variable response** (not every node reacts the same way)
- **Non-uniform timing** (nodes can fire near-simultaneously in clusters,
  not strictly one-at-a-time)
- **State that persists and decays** rather than binary on/off
- **A sense of a signal traveling through a structure**, not a cursor
  sweeping a grid

The elements below are evaluated against how much they buy you on those
four points versus what they cost.

---

## 1. Per-behavior evaluation

### 1.1 Contribution cells as neural nodes
- **Data available:** Yes — this is just a relabeling of the existing grid;
  no new data needed.
- **SVG/GIF-embeddable:** Yes, trivially — it's the base grid.
- **Complexity:** Low. This is the substrate everything else sits on.
- **Metaphor value:** Foundational, not optional. Every other behavior below
  depends on this framing being explicit (node styling — circle/dot rather
  than square cell — rather than a re-skinned calendar square).
- **Verdict: V1, non-negotiable.**

### 1.2 Sparse synaptic connections between nodes
- **Data available:** No direct "relationship" data exists between
  contribution-days in GitHub's API — any edge is authored, not derived.
  The only data-grounded way to define an edge is temporal adjacency
  (connect a cell to its nearest *active* neighbor in time) or
  same-weekday adjacency (connect vertically within a column).
- **SVG/GIF-embeddable:** Yes — static or animated `<path>`/`<line>`
  elements, straightforward in SVG.
- **Complexity:** Medium. Needs a rule for which pairs get an edge (else
  a dense contributor's graph turns into a solid mesh and a sparse
  contributor's graph looks empty and disconnected either way).
  Constraining edges to *immediate* temporal neighbors only keeps this
  tractable; connecting distant/non-adjacent nodes is a different,
  harder problem (see 2.1).
- **Metaphor value:** High for "network" read, but risks visual noise if
  edge density isn't tightly bounded, and risks obscuring the underlying
  grid shape (which must stay recognizable per your constraint) if edges
  run diagonally or across large distances.
- **Verdict: defer. Local-neighbor-only edges → V1.5. Non-adjacent
  "correlated activity" edges → V2, and only if V1.5 doesn't already feel
  cluttered.**

### 1.3 Firing lifecycle (dormant → activation → firing → afterglow → resting)
- **Data available:** Yes — this is a state machine over existing
  per-cell date + intensity data; no new data required.
- **SVG/GIF-embeddable:** Yes — SMIL `<animate>` keyTimes or a small
  keyframe sequence per node, keyed to that node's position in the
  chronological sweep.
- **Complexity:** Low-to-medium. This is really the same complexity as
  the "binary touch" version in the original draft, just with more
  defined keyframes instead of two states.
- **Metaphor value:** This is the single highest-leverage change from the
  original draft. A binary touched/untouched cell reads as "swept over."
  A cell that ramps up, peaks, and decays to a non-zero resting glow reads
  as "something happened here and left a trace." This is what makes it
  stop looking like snake.
- **Verdict: V1, core mechanic — this replaces the original binary model
  entirely rather than sitting on top of it.**

### 1.4 Variable contribution intensity
- **Data available:** Yes, directly — GitHub's contribution graph already
  encodes 5 intensity levels (0–4) per day. This is arguably the most
  under-used piece of data in the original draft, which treated all
  contributed cells identically.
- **SVG/GIF-embeddable:** Yes — trivial, map intensity to peak brightness/
  saturation/glow-radius during the firing state and to resting-floor
  opacity afterward.
- **Complexity:** Low. No new data pipeline — you already have this value
  for the standard green-square graph.
- **Metaphor value:** High, and cheap. A commit-heavy day should visibly
  fire brighter/wider than a single-commit day. This is the second
  highest-leverage, lowest-cost change available.
- **Verdict: V1, non-negotiable, and low-cost enough that skipping it
  would be a mistake.**

### 1.5 Local branching / propagation
- **Data available:** Derivable — a "dense week" (multiple active days in
  the same column) can be detected from existing data and used to trigger
  parallel firing instead of strict single-file sequence.
- **SVG/GIF-embeddable:** Yes, but requires multiple simultaneously
  animated elements with independent timing rather than one traveling
  point — more moving parts to keep in sync.
- **Complexity:** Medium-high if implemented as genuine multi-path
  forking (front splits, travels, reconverges). Medium if simplified to
  "simultaneous parallel firing within a dense column" without true
  path-forking logic (see 1.7, which is a cheaper version of this idea).
- **Metaphor value:** This is the strongest available differentiator from
  "single dot traversal" — a front that can split is unambiguously *not*
  a snake. But full path-forking is real animation-authoring complexity
  and has real risk of reducing clarity (competing simultaneous motion
  can be harder to read than a single sweep, especially at small
  GitHub-embed size).
- **Verdict: true forking → V1.5. Ship the cheaper cluster-burst version
  (1.7) in V1 as a stand-in; upgrade to full branching only if V1's
  single-front sweep still reads as "just a moving dot" once seen live.**

### 1.6 Pulse acceleration / deceleration
- **Data available:** Partially — gap length between active days could
  drive variable travel speed (skip fast through dormant stretches, slow
  through dense stretches), but that requires per-segment speed
  authoring rather than a flat animation duration.
- **SVG/GIF-embeddable:** Yes — SMIL supports `keyTimes`/`keySplines` for
  easing, including per-segment easing if you're willing to hand-author
  or generate the keyframe table.
- **Complexity:** Low for simple global ease-in/ease-out on the traveling
  front. Medium-high for genuinely data-driven variable speed across the
  whole year's timeline.
- **Metaphor value:** Medium. A flat, constant-speed sweep does read as
  slightly mechanical/cursor-like, and a *simple* ease curve fixes most of
  that cheaply. Full data-driven variable speed is a nicer touch but is a
  refinement, not a metaphor-defining feature.
- **Verdict: simple global easing → V1 (cheap, worth it). Full data-driven
  variable speed → V1.5.**

### 1.7 Subtle cluster activation
- **Data available:** Yes — detecting a "busy week" (several active days
  in one column) is a direct read of existing data.
- **SVG/GIF-embeddable:** Yes — a synchronized brief opacity pulse across
  a column's nodes, layered under/alongside the normal sequential firing.
- **Complexity:** Low-medium — meaningfully cheaper than true branching
  (1.5) because it doesn't require path logic, just "these nodes glow
  together briefly when the sweep enters this column."
- **Metaphor value:** Medium-high — it's a reasonable stand-in for
  branching that gets you most of the "this wasn't a single-file sweep"
  read at a fraction of the authoring cost.
- **Verdict: V1**, specifically as the practical substitute for 1.5 until
  there's evidence the extra complexity of true branching is warranted.

### 1.8 Pathway strengthening (neuroplasticity mechanic)
- **Data available:** Yes — a recency-weighted decay function over
  existing intensity data (e.g., a cell's resting-floor brightness is a
  function of its own intensity plus a small contribution from nearby
  recent activity) requires no new data, just a formula on what's already
  there.
- **SVG/GIF-embeddable:** Yes — this only affects the resting-state
  opacity floor set at the end of each node's lifecycle (1.3); no new
  rendering primitive needed.
- **Complexity:** Low. This is a formula, not a new animation system.
- **Metaphor value:** Very high relative to cost — this is the literal
  neuroplasticity metaphor ("pathways that get used stay stronger") and
  it's nearly free to add once 1.3 and 1.4 exist, since it's just
  choosing a non-zero, activity-weighted floor instead of letting every
  cell decay to the same dim baseline.
- **Verdict: V1.** Excluding this would mean skipping the cheapest
  highest-narrative-value element in the whole spec.
- **Note:** a *persistent-across-regenerations* version (floor state that
  accumulates across multiple daily Action runs rather than being
  recomputed fresh each time) requires storing state between runs — that
  infra step is real added complexity for a subtle visual difference.
  That escalated version → **V2**.

### 1.9 Distinct visual states for dormant / active / firing nodes
- **Data available:** Yes — directly derived from contribution presence
  and sweep position.
- **SVG/GIF-embeddable:** Yes — this is the state machine backbone (same
  underlying mechanism as 1.3, described from the node's perspective
  rather than the timeline's).
- **Complexity:** Low — this isn't an additional feature, it's the
  architecture that 1.3/1.4/1.8 all sit on top of.
- **Metaphor value:** Foundational — without clearly distinct states, none
  of the above reads correctly regardless of how well each is designed
  individually.
- **Verdict: V1, structural requirement, not a discrete feature to
  evaluate separately from 1.3.**

### 1.10 Defined animation cycle (start → propagation → resolution → loop)
- **Data available:** N/A — structural, not data-dependent.
- **SVG/GIF-embeddable:** Yes — `repeatCount` plus phase-based `keyTimes`
  support this directly.
- **Complexity:** Low-medium to design well, mainly in choosing what
  "resolution" looks like (see below).
- **Metaphor value:** High. An animation with no defined beginning or end
  (like a looping snake) reads as decorative wallpaper. A structured cycle
  — dormant grid fades in, chronological signal propagates, then a brief
  whole-grid synchronized pulse marking "present state reached" before a
  pause and loop — gives the piece a legible narrative arc instead of
  looking like an idle background loop.
- **Verdict: V1, required.** Proposed phase structure:
  1. **Intro** — grid fades in, all nodes dormant/static
  2. **Propagation** — chronological sweep with full lifecycle (1.3),
     intensity mapping (1.4), cluster bursts (1.7), simple easing (1.6)
  3. **Resolution** — brief synchronized soft pulse across the *entire*
     grid once the sweep reaches the present day (a visual "here's where
     things stand now" beat, distinct from the traveling-front phase)
  4. **Hold** — short pause at rest state (pathway-strengthened floor
     visible, 1.8)
  5. **Loop** back to Intro

---

## 2. What must NOT slip into V1 (explicitly excluded)

- Any literal brain outline, anatomical shape, or skull/neuron-cell
  illustration — grid geometry must stay a recognizable transformation of
  the actual GitHub contribution graph, not a redrawn brain with data
  mapped onto it.
- Any Star Wars-derived visual motifs.
- Dense/long-range synaptic edges connecting distant, non-adjacent cells
  (2.1 below) — high noise risk, low data grounding.
- Particle systems, screen-filling bursts, or per-commit "fireworks."
- True multi-path branching with path-finding logic (1.5 full version) —
  worth revisiting only after the cheaper cluster-burst (1.7) has been
  seen live and judged insufficient.

### 2.1 On non-adjacent "correlated activity" edges specifically
Connecting cells that aren't temporally adjacent (e.g., "you always commit
on Tuesdays" style edges) is the most genuinely *network-like* visual
available, but it is the hardest to keep both accurate and uncluttered,
and it's the one most likely to make the grid stop reading as a
transformation of the real contribution graph and start reading as an
unrelated generative network laid over it. This stays firmly out of scope
until V1 and V1.5 have both been validated live.

---

## 3. V1 / V1.5 / V2 split

### V1 — weekend-scale, reliable, ships first
- Grid geometry identical to the real contribution graph (positions,
  weekday rows, week columns) — non-negotiable anchor to recognizability
- Node-based styling (dot/circle, not literal calendar squares)
- Full state machine: dormant → activation → firing → afterglow → resting
  floor (replaces the original binary touched/untouched model entirely)
- Intensity-driven brightness/saturation (reuses existing 0–4 contribution
  levels — no new data needed)
- Cluster-burst activation on dense weeks (cheap stand-in for true
  branching)
- Pathway-strengthening resting floor (recency-weighted, cheap formula,
  highest narrative value per unit of effort in the whole spec)
- Simple global ease-in/ease-out on the traveling front
- Full defined cycle: intro → propagation → resolution → hold → loop
- Dark and light mode variants

### V1.5 — second pass, once V1 has been seen live
- True local branching: front forks into parallel mini-pulses during dense
  weeks, reconverges after
- Data-driven variable pulse speed (fast through gaps, slow through dense
  stretches) replacing the flat easing curve
- Sparse, *adjacent-only* synaptic edges (nearest active temporal
  neighbor), rendered subtly, to add network texture without breaking
  grid recognizability
- Palette refinement based on real rendering feedback (SVG color behavior
  in GitHub's actual dark/light theme differs from a design mockup)

### V2 — exploratory, only if V1/V1.5 land well and there's real appetite
- Non-adjacent "correlated activity" edges (2.1) — highest complexity,
  highest noise risk, needs careful curation
- Persistent-across-regenerations plasticity (state stored between daily
  Action runs rather than recomputed fresh each time) — real infra
  addition for a subtle effect
- Deeper resolution-phase choreography, potentially designed to visually
  rhyme with the AIN site's eventual 3D brain, once that exists to rhyme
  with

---

## 4. Net recommendation

Ship V1 as specified above — it already fully solves the "this just looks
like a recolored snake" problem via the state-lifecycle + intensity
mapping + pathway-strengthening combination, all three of which are cheap
relative to their payoff. True branching and long-range synaptic edges are
the two elements worth the most visually but are also the two most likely
to either blow the weekend-scale budget or introduce clutter — good
candidates to evaluate only after seeing V1 rendered for real, not to
design blind.
