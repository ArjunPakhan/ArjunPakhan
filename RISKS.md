# Known Open Risks

## Risk 1: GitHub README Sanitizer and SMIL `<animate>` Elements

**Status:** RESOLVED — verified empirically 2026-10-02 against the live `output` branch.

Result: GitHub serves the profile SVG directly from `raw.githubusercontent.com` (GitHub-hosted images
are not camo-proxied or sanitized). The served bytes contain all `<animate>` elements (486 for dark,
486 for light), `Content-Type: image/svg+xml`, and
`Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox` — that CSP blocks
scripts and external resources but NOT declarative SMIL animation. SMIL runs inside `<img>`, so the
animation renders on the profile README. Final visual confirmation (pixels moving) is a human check
on github.com/ArjunPakhan, but the technical gate is cleared.

GitHub's README sanitizer may strip or modify SMIL `<animate>` elements when embedded via `<picture>`
or `<img>` tags referencing a raw committed SVG file.

**What could go wrong:**
- `<animate>` elements could be stripped, resulting in a static SVG with no animation
- `keyTimes` or `values` attributes could be sanitized, breaking the animation timing
- The `filter` elements (Gaussian blur) could be removed, losing the cluster wash and resolution overlays

**How to verify:**
1. Push the generated SVG to the `output` branch
2. Fetch the raw URL (`raw.githubusercontent.com/.../output/neural-grid-dark.svg`) — confirm `<animate>` survives serving
3. Fetch the rendered profile HTML — locate the camo-proxied `<img>` URL and confirm the proxied bytes still contain `<animate>`
4. Final confirmation: view the rendered README on github.com

**Mitigation if it fails:**
- Convert to GIF fallback (frame-by-frame renderer)
- Host via GitHub Pages and reference by absolute URL
- Fall back to a static "resting state" frame

---

## Risk 2: Cluster-Activation Threshold Tuned Against Synthetic Data

**Status:** UNRESOLVED — needs re-checking once real contribution data flows through the Action.

The cluster wash triggers when a week column has ≥4 active days AND combined intensity ≥10
(see `neural/node-grid/model.py`, `build_model`). This threshold was set against the sample fixture
and may not match a real contribution calendar's density.

**What could go wrong:**
- Sparse real data → almost no cluster washes appear
- Dense real data → washes overwhelm the visual
- Combined-intensity threshold of 10 may need tuning (e.g. 6–8 sparse, 12–15 heavy)

**How to verify:**
1. Let the daily Action run with real data (`GITHUB_USERNAME`)
2. Inspect `output/neural-grid-*.svg` — count cluster washes and check visual balance
3. Adjust the `active >= 4 and combined >= 10` test in `neural/node-grid/model.py` if needed

**Recommended approach:**
- Test against 3–5 contribution profiles (sparse, moderate, heavy)
- Consider making the threshold configurable via environment variable in the Action
