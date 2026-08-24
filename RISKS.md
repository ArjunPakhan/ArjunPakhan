# Known Open Risks

## Risk 1: GitHub README Sanitizer and SMIL `<animate>` Elements

**Status:** UNRESOLVED — requires empirical testing by pushing and viewing the rendered README.

GitHub's README sanitizer may strip or modify SMIL `<animate>` elements when embedded via `<picture>` or `<img>` tags referencing a raw committed SVG file. This has not been confirmed or denied.

**What could go wrong:**
- `<animate>` elements could be stripped, resulting in a static SVG with no animation
- `keyTimes` or `values` attributes could be sanitized, breaking the animation timing
- The `filter` elements (Gaussian blur) could be removed, losing the cluster wash and resolution overlays

**How to verify:**
1. Push the generated SVG to the `output` branch
2. Embed it in a profile README using `<img>` or `<picture>`
3. View the rendered README on github.com
4. Inspect the rendered SVG in browser DevTools to confirm `<animate>` elements are preserved

**Mitigation if it fails:**
- Convert to GIF fallback (requires adding a frame-by-frame renderer)
- Use a third-party SVG hosting service (e.g., GitHub Pages) and reference via `<img>` with an absolute URL
- Accept a static "resting state" frame as the fallback image

---

## Risk 2: Cluster-Activation Threshold Tuned Against Synthetic Data

**Status:** UNRESOLVED — needs re-checking once real contribution data is wired in.

The cluster wash overlay triggers when a week column has ≥4 active days AND combined intensity ≥10. This threshold was set against synthetic sample data and may not produce the correct visual density with real contribution calendars.

**What could go wrong:**
- Real contribution data may be sparser, causing almost no cluster washes to appear
- Real data may be denser, causing cluster washes to appear too frequently and overwhelm the visual
- The combined intensity threshold of 10 may need adjustment (e.g., 6–8 for sparse users, 12–15 for active users)

**How to verify:**
1. Wire in real GitHub username via `--username <user>`
2. Run the generator and inspect the output SVG
3. Count how many cluster washes appear and whether they feel visually balanced
4. Adjust the thresholds in `generate-svg.js` (`weekClusterIntensity` function) if needed

**Recommended approach:**
- Add a `--verbose` flag that logs which weeks qualify for cluster wash
- Test against 3–5 different contribution profiles (sparse, moderate, heavy)
- Consider making the threshold configurable via environment variables in the GitHub Action
