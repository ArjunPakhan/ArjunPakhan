"""Node-grid model for the Neural GitHub profile.

53x7 circle grid matching the real contribution calendar. Each active day
becomes a node with a dormant -> activation -> firing -> afterglow -> resting
lifecycle. A neural metaphor applied to contribution data (not a literal brain).

Palette and timing are locked to the canonical spec (neural-github-profile-spec).
"""
from __future__ import annotations

# --- Palette (exact from spec) -------------------------------------------------
DARK = {
    "bg": "#0b0c12",        # obsidian (not pure black)
    "dormant": "#3a3f4d",   # graphite / slate
    "fire": "#d8f7ff",      # warm cyan-white flash
    "plum": "#8f5de0",      # resting / strengthened state
    "cluster": "#4b3a7a",   # cluster-activation wash
    "breath": "#cbb8ff",    # whole-grid resolution / breathing overlay
}

# Light variant: genuinely re-adjusted for contrast on a light background.
LIGHT = {
    "bg": "#f4f3f8",
    "dormant": "#a7adc3",   # light slate, visible on light bg
    "fire": "#0c9cc4",      # deeper cyan, visible on light bg
    "plum": "#7c50c8",      # mid plum, visible on light bg
    "cluster": "#6a5ba0",
    "breath": "#b6a3e6",
}

# --- Cycle timing (seconds) — locked -------------------------------------------------
CYCLE = 14.0
INTRO_END = 1.0
PROP_START = 1.0
PROP_END = 8.5
RES_START = 8.5
RES_PEAK = 9.0
RES_END = 9.5
BREATH1 = 10.6
BREATH2 = 12.1
FADE_START = 13.2
FADE_END = 14.0

DORMANT_OPACITY = 0.22

# --- Geometry ----------------------------------------------------------------------
CELL = 12.0   # cell pitch (px)
GAP = 3.0     # gap between cells
PAD = 24.0    # outer margin
BASE_R = 4.6  # dormant node radius


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def _lerp_hex(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    t = _clamp(t)
    rgb = [round(a[i] + (b[i] - a[i]) * t) for i in range(3)]
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def intensity_norm(level: int) -> float:
    return _clamp(level / 4.0)


def peak_opacity(level: int) -> float:
    """Peak firing opacity: min(1.0, 0.82 + 0.18*intensity_norm)."""
    if level == 0:
        return DORMANT_OPACITY  # inactive node never fires
    return min(1.0, 0.82 + 0.18 * intensity_norm(level))


def resting_opacity(level: int, recency: float) -> float:
    """Resting floor: min(0.78, 0.20 + 0.34*intensity + 0.20*recency).

    This is the neuroplasticity effect — a residual trace brighter than the
    dormant baseline. Inactive (level 0) nodes stay dormant.
    """
    if level == 0:
        return DORMANT_OPACITY
    return min(0.78, 0.20 + 0.34 * intensity_norm(level) + 0.20 * recency)


def resting_color(pal: dict, level: int, recency: float) -> str:
    """Graphite -> plum, weighted by intensity + recency."""
    if level == 0:
        return pal["dormant"]
    w = _clamp(0.34 * intensity_norm(level) + 0.20 * recency)
    return _lerp_hex(pal["dormant"], pal["plum"], w)


def fire_radius(level: int) -> float:
    if level == 0:
        return BASE_R
    return BASE_R * (1.0 + 0.28 * intensity_norm(level))


def build_model(data: dict, theme: str = "dark") -> dict:
    """Turn normalized weeks[].days[] into a node-grid model."""
    pal = DARK if theme == "dark" else LIGHT

    days = [d for w in data["weeks"] for d in w["days"]]
    total = len(days)                # 53 * 7 = 371
    ncols = len(data["weeks"])       # 53
    nrows = 7

    grid_w = ncols * (CELL + GAP) - GAP
    grid_h = nrows * (CELL + GAP) - GAP
    width = grid_w + 2 * PAD
    height = grid_h + 2 * PAD

    nodes = []
    for i, d in enumerate(days):
        level = int(d.get("level", 0))
        recency = i / (total - 1) if total > 1 else 0.0
        col = i // nrows
        row = i % nrows
        cx = PAD + col * (CELL + GAP) + CELL / 2.0
        cy = PAD + row * (CELL + GAP) + CELL / 2.0
        activation = PROP_START + (PROP_END - PROP_START) * recency
        nodes.append({
            "id": i,
            "col": col,
            "row": row,
            "cx": round(cx, 2),
            "cy": round(cy, 2),
            "level": level,
            "recency": round(recency, 4),
            "activation": round(activation, 4),
            "peak_op": round(peak_opacity(level), 4),
            "rest_op": round(resting_opacity(level, recency), 4),
            "rest_color": resting_color(pal, level, recency),
            "fire_r": round(fire_radius(level), 2),
        })

    # Cluster wash: a week column with >=4 active days and combined intensity >=10.
    clusters = []
    for w in range(ncols):
        week_days = [days[w * nrows + r] for r in range(nrows)]
        active = sum(1 for d in week_days if d.get("count", 0) > 0)
        combined = sum(int(d.get("level", 0)) for d in week_days)
        if active >= 4 and combined >= 10:
            clusters.append({
                "col": w,
                "activation": nodes[w * nrows]["activation"],
                "combined": combined,
            })

    return {
        "theme": theme,
        "pal": pal,
        "width": round(width, 1),
        "height": round(height, 1),
        "grid_w": round(grid_w, 1),
        "grid_h": round(grid_h, 1),
        "ncols": ncols,
        "nrows": nrows,
        "nodes": nodes,
        "clusters": clusters,
    }
