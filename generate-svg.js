#!/usr/bin/env node
/**
 * Neural Contributions V1 — SVG Generator
 *
 * Generates an animated SVG that visualizes contribution data through a
 * neural-propagation metaphor. Outputs neural-contributions-dark.svg and
 * neural-contributions-light.svg.
 *
 * Usage: node generate-svg.js [--username <user>]
 *   With --username, fetches real GitHub contribution data via the API.
 *   Without --username, uses synthetic sample data.
 */

const https = require("https");
const fs = require("fs");
const path = require("path");

// ─── Layout constants ───────────────────────────────────────────────────────
const COLS = 52;
const ROWS = 7;
const SPACING = 14;
const RADIUS = 4.6;
const MARGIN = 31; // First node center at (31, 31), matching original validated prototype
const NODE_RADIUS = 4.6;
// Match original SVG: first node at (MARGIN, MARGIN), last at (MARGIN + 51*14, MARGIN + 6*14)
// viewBox pads by ~NODE_RADIUS on each side beyond the node centers
// Match the original validated prototype dimensions exactly
const CANVAS_W = 776;
const CANVAS_H = 146;
const DURATION = 14.0; // total loop seconds

// ─── Phase boundaries (seconds) ────────────────────────────────────────────
const PHASE = {
  introEnd: 1.0,
  propStart: 1.0,
  propEnd: 8.5,
  resPeak: 9.0,
  resEnd: 9.5,
  breathe1Peak: 10.6,
  breathe1End: 11.2,
  breathe2Peak: 12.1,
  breathe2End: 12.7,
  fadeEnd: 13.2,
};

// ─── Color palette (dark mode) ──────────────────────────────────────────────
const DARK = {
  bg: "#0b0c12",
  dormant: "#3a3f4d",
  fire: "#d8f7ff",
  restTarget: [0x8f, 0x5d, 0xe0], // #8f5de0 plum/violet
  cluster: "#4b3a7a",
  resOverlay: "#cbb8ff",
};

// ─── Color palette (light mode) ─────────────────────────────────────────────
const LIGHT = {
  bg: "#f0f0f5",
  dormant: "#c0c4cc",
  fire: "#006080",
  restTarget: [0x50, 0x30, 0xa0],
  cluster: "#8a6fcf",
  resOverlay: "#5030a0",
};

// ─── Opacity constants ──────────────────────────────────────────────────────
const DORMANT_OPACITY = 0.22;
const RAMP_DURATION = 0.15; // seconds before peak
const AFTERGLOW_DURATION = 0.45; // seconds after peak

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Convert seconds to keyTimes fraction (0–1) */
function t(s) {
  return (s / DURATION).toFixed(6);
}

/** Clamp a value between min and max */
function clamp(v, min, max) {
  return Math.min(max, Math.max(min, v));
}

/** Linear interpolation between two RGB colors */
function lerpColor(hex1, hex2, factor) {
  const parse = (h) => [
    parseInt(h.slice(1, 3), 16),
    parseInt(h.slice(3, 5), 16),
    parseInt(h.slice(5, 7), 16),
  ];
  const a = parse(hex1);
  const b = typeof hex2 === "string" ? parse(hex2) : hex2;
  const r = Math.round(a[0] + (b[0] - a[0]) * factor);
  const g = Math.round(a[1] + (b[1] - a[1]) * factor);
  const bl = Math.round(a[2] + (b[2] - a[2]) * factor);
  return `#${r.toString(16).padStart(2, "0")}${g
    .toString(16)
    .padStart(2, "0")}${bl.toString(16).padStart(2, "0")}`;
}

/** Generate synthetic contribution data: 52 weeks x 7 days, levels 0–4 */
function generateSyntheticData() {
  const data = [];
  // Seed a pseudo-random for reproducibility
  let seed = 42;
  const rand = () => {
    seed = (seed * 16807 + 0) % 2147483647;
    return seed / 2147483647;
  };

  for (let week = 0; week < COLS; week++) {
    const weekData = [];
    for (let day = 0; day < ROWS; day++) {
      // Create realistic-ish patterns: some busy weeks, some quiet
      const weekDensity = 0.3 + 0.4 * rand(); // 0.3–0.7 chance of activity
      const isContributing = rand() < weekDensity;
      if (!isContributing) {
        weekData.push(0);
      } else {
        // Bias toward lower levels with occasional spikes
        const r = rand();
        const level = r < 0.3 ? 1 : r < 0.6 ? 2 : r < 0.85 ? 3 : 4;
        weekData.push(level);
      }
    }
    data.push(weekData);
  }
  return data;
}

/** Fetch real GitHub contribution data */
async function fetchGitHubContributions(username) {
  return new Promise((resolve, reject) => {
    const year = new Date().getFullYear();
    const url = `https://api.github.com/users/${username}/contributions?year=${year}`;

    https
      .get(url, { headers: { "User-Agent": "neural-contributions-v1" } }, (res) => {
        let body = "";
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          try {
            const contribs = JSON.parse(body);
            // GitHub returns { total, contributions: [{ date, count }] }
            const data = [];
            const contribsArr = contribs.contributions || [];
            // Build 52x7 grid from flat list
            for (let w = 0; w < COLS; w++) {
              const weekData = [];
              for (let d = 0; d < ROWS; d++) {
                const idx = w * 7 + d;
                const entry = contribsArr[idx];
                const count = entry ? entry.count : 0;
                // Map count to level 0-4
                const level = count === 0 ? 0 : count <= 2 ? 1 : count <= 5 ? 2 : count <= 8 ? 3 : 4;
                weekData.push(level);
              }
              data.push(weekData);
            }
            resolve(data);
          } catch (e) {
            reject(new Error(`Failed to parse GitHub response: ${e.message}`));
          }
        });
      })
      .on("error", reject);
  });
}

/**
 * Build all active nodes with their chronological index and parameters.
 * Returns: [{ week, day, level, seqIndex, totalActive, intensityNorm, recencyNorm }]
 */
function buildNodeList(data) {
  const nodes = [];
  for (let w = 0; w < COLS; w++) {
    for (let d = 0; d < ROWS; d++) {
      if (data[w][d] > 0) {
        nodes.push({ week: w, day: d, level: data[w][d] });
      }
    }
  }
  // Sort chronologically (oldest first = lowest week, lowest day)
  nodes.sort((a, b) => a.week - b.week || a.day - b.day);

  const totalActive = nodes.length;
  return nodes.map((n, i) => ({
    ...n,
    seqIndex: i,
    totalActive,
    intensityNorm: n.level / 4,
    recencyNorm: totalActive > 1 ? i / (totalActive - 1) : 0.5,
  }));
}

/** Check if a week column qualifies for cluster wash */
function weekClusterIntensity(data, week) {
  let activeDays = 0;
  let totalIntensity = 0;
  for (let d = 0; d < ROWS; d++) {
    if (data[week][d] > 0) {
      activeDays++;
      totalIntensity += data[week][d];
    }
  }
  return { activeDays, totalIntensity };
}

// ─── SVG generation ─────────────────────────────────────────────────────────

function generateSVG(data, palette, label) {
  const nodes = buildNodeList(data);
  const activeNodes = nodes;

  // Calculate fire times for each active node
  // Ensure earliest fire is at least RAMP_DURATION after introEnd so ramp_start > intro_end
  const propDuration = PHASE.propEnd - PHASE.propStart; // 7.5s
  const earliestFire = PHASE.introEnd + RAMP_DURATION + 0.05; // ~1.2s
  const fireTimes = activeNodes.map(
    (n) => earliestFire + (n.seqIndex / Math.max(1, n.totalActive - 1)) * (PHASE.propEnd - earliestFire)
  );

  let svg = "";

  // ── Header & defs ──────────────────────────────────────────────────────
  svg += `<svg viewBox="0 0 ${CANVAS_W} ${CANVAS_H}" xmlns="http://www.w3.org/2000/svg" width="${CANVAS_W}" height="${CANVAS_H}">\n`;
  svg += `<title>Neural metaphor for contribution activity — V1 (${label})</title>\n`;
  svg += `<defs>\n`;
  svg += `<filter id="clusterBlur" x="-50%" y="-50%" width="200%" height="200%">\n`;
  svg += `<feGaussianBlur stdDeviation="6"/>\n`;
  svg += `</filter>\n`;
  svg += `<filter id="resBlur" x="-50%" y="-50%" width="200%" height="200%">\n`;
  svg += `<feGaussianBlur stdDeviation="18"/>\n`;
  svg += `</filter>\n`;
  svg += `</defs>\n`;

  // ── Background ─────────────────────────────────────────────────────────
  svg += `<rect x="0" y="0" width="${CANVAS_W}" height="${CANVAS_H}" fill="${palette.bg}"/>\n`;

  // ── Cluster wash overlays ──────────────────────────────────────────────
  for (let w = 0; w < COLS; w++) {
    const { activeDays, totalIntensity } = weekClusterIntensity(data, w);
    if (activeDays < 4 || totalIntensity < 10) continue;

    // Find the range of active nodes in this week
    const weekNodes = activeNodes.filter((n) => n.week === w);
    if (weekNodes.length === 0) continue;

    const firstFire = fireTimes[activeNodes.indexOf(weekNodes[0])];
    const lastFire = fireTimes[activeNodes.indexOf(weekNodes[weekNodes.length - 1])];
    const clusterStart = firstFire - 0.2;
    const clusterPeak = (firstFire + lastFire) / 2;
    const clusterEnd = lastFire + 0.3;

    const cx = MARGIN + w * SPACING;
    const x = cx - 8.68;
    const y = 18;
    const w2 = 17.36;
    const h = 110;

    const keyTimes = `0;${t(clusterStart)};${t(clusterPeak)};${t(clusterEnd)};${t(PHASE.fadeEnd)};1`;
    const values = `0;0;0.16;0;0;0`;

    svg += `<rect x="${x}" y="${y}" width="${w2}" height="${h}" rx="10" fill="${palette.cluster}" opacity="0" filter="url(#clusterBlur)"><animate attributeName="opacity" dur="${DURATION}s" repeatCount="indefinite" keyTimes="${keyTimes}" values="${values}"/></rect>\n`;
  }

  // ── Resolution / breathing ellipse overlay ─────────────────────────────
  const ellipseCX = CANVAS_W / 2;
  const ellipseCY = CANVAS_H / 2;
  const ellipseRX = CANVAS_W * 0.55;
  const ellipseRY = CANVAS_H * 0.9;
  const resKeyTimes = `0;${t(PHASE.propEnd)};${t(PHASE.resPeak)};${t(PHASE.resEnd)};${t(PHASE.breathe1Peak)};${t(PHASE.breathe1End)};${t(PHASE.breathe2Peak)};${t(PHASE.breathe2End)};${t(PHASE.fadeEnd)};1`;
  const resValues = `0;0;0.16;0;0.05;0;0.045;0;0;0`;
  svg += `<ellipse cx="${ellipseCX}" cy="${ellipseCY}" rx="${ellipseRX}" ry="${ellipseRY}" fill="${palette.resOverlay}" opacity="0" filter="url(#resBlur)"><animate attributeName="opacity" dur="${DURATION}s" repeatCount="indefinite" keyTimes="${resKeyTimes}" values="${resValues}"/></ellipse>\n`;

  // ── Node circles ───────────────────────────────────────────────────────
  for (let w = 0; w < COLS; w++) {
    for (let d = 0; d < ROWS; d++) {
      const cx = MARGIN + w * SPACING;
      const cy = MARGIN + d * SPACING;
      const level = data[w][d];

      if (level === 0) {
        // Dormant node: flat fade in, hold, fade out
        const keyTimes = `0;${t(PHASE.introEnd)};${t(PHASE.fadeEnd)};1`;
        const values = `0;${DORMANT_OPACITY};${DORMANT_OPACITY};0`;
        svg += `<circle cx="${cx}" cy="${cy}" r="${RADIUS}" fill="${palette.dormant}" opacity="0"><animate attributeName="opacity" dur="${DURATION}s" repeatCount="indefinite" keyTimes="${keyTimes}" values="${values}"/></circle>\n`;
      } else {
        // Active node with full lifecycle
        const idx = activeNodes.findIndex(
          (n) => n.week === w && n.day === d
        );
        const node = activeNodes[idx];
        const fireTime = fireTimes[idx];
        const rampStart = Math.max(PHASE.introEnd, fireTime - RAMP_DURATION);
        const afterglowEnd = fireTime + AFTERGLOW_DURATION;

        const intensityNorm = node.intensityNorm;
        const recencyNorm = node.recencyNorm;
        const peakOpacity = +Math.min(1.0, 0.82 + 0.18 * intensityNorm).toFixed(2);
        const restingR = +Math.min(
          0.78,
          0.2 + 0.34 * intensityNorm + 0.2 * recencyNorm
        ).toFixed(2);
        const restColor = lerpColor(palette.dormant, palette.restTarget,
          clamp(0.35 * intensityNorm + 0.65 * recencyNorm, 0.15, 1.0)
        );

        // 7-keyframe structure: [0, intro_end, ramp_start, fire_time, afterglow_end, pause_end, loop_end]
        const opKeyTimes = `0;${t(PHASE.introEnd)};${t(rampStart)};${t(fireTime)};${t(afterglowEnd)};${t(PHASE.fadeEnd)};1`;
        const opValues = `0;${DORMANT_OPACITY};${DORMANT_OPACITY};${peakOpacity};${restingR};${restingR};0`;

        svg += `<circle cx="${cx}" cy="${cy}" r="${RADIUS}" fill="${palette.dormant}" opacity="0">`;
        svg += `<animate attributeName="opacity" dur="${DURATION}s" repeatCount="indefinite" keyTimes="${opKeyTimes}" values="${opValues}"/>`;
        svg += `<animate attributeName="fill" dur="${DURATION}s" repeatCount="indefinite" keyTimes="${opKeyTimes}" values="${palette.dormant};${palette.dormant};${palette.dormant};${palette.fire};${restColor};${restColor};${palette.dormant}"/>`;
        svg += `</circle>\n`;
      }
    }
  }

  svg += `</svg>`;
  return svg;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const usernameIdx = args.indexOf("--username");
  let data;

  if (usernameIdx !== -1 && args[usernameIdx + 1]) {
    const username = args[usernameIdx + 1];
    console.log(`Fetching contribution data for ${username}...`);
    data = await fetchGitHubContributions(username);
  } else {
    console.log("Using synthetic sample data (pass --username <user> for real data)...");
    data = generateSyntheticData();
  }

  const outDir = path.join(__dirname, "dist");
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  // Generate dark mode
  const darkSVG = generateSVG(data, DARK, "dark");
  const darkPath = path.join(outDir, "neural-contributions-dark.svg");
  fs.writeFileSync(darkPath, darkSVG);
  console.log(`Written: ${darkPath}`);

  // Generate light mode
  const lightSVG = generateSVG(data, LIGHT, "light");
  const lightPath = path.join(outDir, "neural-contributions-light.svg");
  fs.writeFileSync(lightPath, lightSVG);
  console.log(`Written: ${lightPath}`);

  // Also copy dark to project root for quick preview
  fs.writeFileSync(path.join(__dirname, "neural-contributions-v1.svg"), darkSVG);
  console.log(`Written: neural-contributions-v1.svg (dark, for preview)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
