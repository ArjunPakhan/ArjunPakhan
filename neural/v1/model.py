"""
Turns the contribution dataset into the geometry + timing model the SVG
builder needs: node positions, per-node fire timing (with cluster bursts),
per-node color/size states across the dormant -> activation -> firing ->
afterglow -> resting lifecycle, and sparse local synaptic edges.
"""
import math
import random

# ---- layout ----------------------------------------------------------
CELL = 15.0          # column/row pitch
MARGIN_X = 34.0
MARGIN_Y = 26.0
N_WEEKS = 53
N_DAYS = 7

WIDTH = MARGIN_X * 2 + (N_WEEKS - 1) * CELL + 10
HEIGHT = MARGIN_Y * 2 + (N_DAYS - 1) * CELL + 10

# ---- animation timeline (percent of one full cycle) -------------------
INTRO_END = 5.0
PROP_START = 6.0
PROP_END = 87.0
RESOLUTION_AT = 90.5
HOLD_END = 96.0
# 96-100%: fade back to dormant for the loop seam

# ---- palette: obsidian graphite / plum / violet / warm cyan-white ----
DORMANT_FILL = "#2a2a35"          # never-contributed node, barely there
PRE_FIRE = {  # latent color before the sweep reaches an active node this cycle
    1: "#3c3350",
    2: "#4a3a63",
    3: "#59417a",
    4: "#654a8f",
}
PEAK_FILL = {  # the firing instant
    1: "#a98bd6",
    2: "#c3a3ef",
    3: "#ddc4ff",
    4: "#f3ecff",   # near white-violet core for the hottest days
}
RESIDUAL_FILL = {  # strengthened resting glow after firing (neuroplasticity)
    1: "#4c3f68",
    2: "#5f4d85",
    3: "#7859ab",
    4: "#9271c9",
}

EDGE_COLOR_DIM = "#4a3d63"
EDGE_COLOR_HOT = "#c9b6ef"


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def build(data: dict, seed: int = 7):
    rng = random.Random(seed)
    weeks = data["weeks"]

    nodes = []
    by_col_row = {}
    for col, week in enumerate(weeks):
        for day in week["days"]:
            row = day["weekday"]
            level = day["level"]
            x = MARGIN_X + col * CELL
            y = MARGIN_Y + row * CELL
            n = {
                "id": f"n{col}_{row}",
                "col": col, "row": row,
                "x": x, "y": y,
                "level": level,
                "count": day["count"],
                "date": day["date"],
                "active": level > 0,
            }
            nodes.append(n)
            by_col_row[(col, row)] = n

    active_nodes = [n for n in nodes if n["active"]]
    # chronological order = column-major, top-to-bottom within a column,
    # which is exactly chronological day order in a GitHub grid.
    active_nodes.sort(key=lambda n: (n["col"], n["row"]))

    active_cols = sorted(set(n["col"] for n in active_nodes))
    col_rank = {c: i for i, c in enumerate(active_cols)}
    n_active_cols = max(1, len(active_cols) - 1)

    # group active nodes by column to detect dense/cluster weeks
    by_col = {}
    for n in active_nodes:
        by_col.setdefault(n["col"], []).append(n)

    for n in active_nodes:
        col_group = by_col[n["col"]]
        rank_in_col = col_group.index(n)
        cluster_size = len(col_group)
        n["cluster_size"] = cluster_size

        base_frac = col_rank[n["col"]] / n_active_cols
        # small stagger within a week so a dense week reads as a near-
        # simultaneous burst rather than one node at a time, while still
        # keeping a faint sense of order.
        stagger = (rank_in_col / max(1, cluster_size)) * (0.55 / n_active_cols)
        jitter = rng.uniform(-0.12, 0.12) / n_active_cols
        frac = clamp(base_frac + stagger + jitter, 0.0, 1.0)

        delay = PROP_START + frac * (PROP_END - PROP_START)
        n["delay_pct"] = delay

        lvl = n["level"]
        rise_w = {1: 0.45, 2: 0.55, 3: 0.7, 4: 0.85}[lvl]
        decay_w = {1: 2.4, 2: 3.2, 3: 4.3, 4: 5.6}[lvl]
        n["rise_pct"] = rise_w
        n["decay_pct"] = decay_w

        n["pre_r"] = {1: 1.52, 2: 1.68, 3: 1.84, 4: 2.00}[lvl]
        n["peak_r"] = {1: 2.62, 2: 3.12, 3: 3.62, 4: 4.12}[lvl]
        n["mid_r"] = {1: 2.10, 2: 2.48, 3: 2.84, 4: 3.18}[lvl]
        n["floor_r"] = {1: 1.74, 2: 1.96, 3: 2.18, 4: 2.42}[lvl]

        n["pre_op"] = {1: 0.20, 2: 0.26, 3: 0.32, 4: 0.38}[lvl]
        n["peak_op"] = {1: 0.88, 2: 0.94, 3: 0.99, 4: 1.0}[lvl]
        n["mid_op"] = {1: 0.54, 2: 0.62, 3: 0.70, 4: 0.78}[lvl]
        n["floor_op"] = {1: 0.34, 2: 0.42, 3: 0.51, 4: 0.60}[lvl]

        n["halo"] = lvl >= 3

    for n in nodes:
        if not n["active"]:
            n["pre_r"] = n["peak_r"] = n["mid_r"] = n["floor_r"] = 1.30
            n["pre_op"] = n["peak_op"] = n["mid_op"] = n["floor_op"] = 0.28
            n["delay_pct"] = 0
            n["rise_pct"] = n["decay_pct"] = 0
            n["halo"] = False
            n["cluster_size"] = 0

    # ---- sparse local synaptic edges --------------------------------
    # connect each active node forward to 1-2 nearby-in-time, nearby-in-
    # space active nodes only. Keeps it sparse, local, and organic instead
    # of a dense mesh, and keeps the underlying grid legible.
    edges = []
    seen_pairs = set()
    WINDOW = 7          # look ahead this many active nodes in time
    MAX_DCOL = 4         # spatial locality caps
    MAX_DROW = 5
    MAX_EDGES_PER_NODE = 3

    for i, a in enumerate(active_nodes):
        candidates = []
        for b in active_nodes[i + 1: i + 1 + WINDOW]:
            dcol = b["col"] - a["col"]
            drow = abs(b["row"] - a["row"])
            if dcol > MAX_DCOL or drow > MAX_DROW:
                continue
            dist = math.hypot(dcol, drow)
            candidates.append((dist, b))
        candidates.sort(key=lambda t: t[0])

        if a["level"] == 1:
            budget = 1
        elif a["level"] == 2:
            budget = 2
        else:
            budget = MAX_EDGES_PER_NODE
        made = 0
        for dist, b in candidates:
            if made >= budget:
                break
            key = (a["id"], b["id"])
            if key in seen_pairs:
                continue
            # skip near-duplicate very-short same-column links sometimes,
            # to avoid every dense week turning into a solid ladder
            if a["col"] == b["col"] and rng.random() < 0.35:
                continue
            seen_pairs.add(key)
            edges.append(make_edge(a, b, rng))
            made += 1

    return {
        "nodes": nodes,
        "active_nodes": active_nodes,
        "edges": edges,
        "clusters": [g for g in by_col.values() if len(g) >= 3],
        "last_active": active_nodes[-1] if active_nodes else None,
        "width": WIDTH,
        "height": HEIGHT,
    }


def make_edge(a, b, rng):
    mx, my = (a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2
    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
    dist = math.hypot(dx, dy) or 1
    nx, ny = -dy / dist, dx / dist
    bend = rng.uniform(0.22, 0.5) * dist * rng.choice([-1, 1])
    cx, cy = mx + nx * bend, my + ny * bend

    fire_at = max(a["delay_pct"], b["delay_pct"]) + 0.15
    avg_level = (a["level"] + b["level"]) / 2
    desired = clamp(dist * 0.032 + 0.95, 1.15, 2.40)
    travel_end = b["delay_pct"] + 0.06
    travel_start = travel_end - desired
    min_start = a["delay_pct"] + 0.08
    if travel_start < min_start:
        travel_start = min_start
        travel_end = travel_start + desired
        if travel_end > b["delay_pct"] + 0.55:
            travel_end = b["delay_pct"] + 0.22
            travel_start = travel_end - desired
    travel_start = clamp(travel_start, PROP_START, PROP_END)
    travel_end = clamp(travel_end, travel_start + 0.90, 99.0)
    base_peak = clamp(0.42 + avg_level * 0.11, 0.42, 0.86)
    base_floor = clamp(0.11 + avg_level * 0.05, 0.11, 0.31)
    base_width = clamp(0.62 + avg_level * 0.17, 0.62, 1.28)
    if avg_level >= 3.0 or (a["level"] >= 3 and b["level"] >= 3) or (max(a["cluster_size"], b["cluster_size"]) >= 4 and avg_level >= 2.5):
        tier = 3
        peak = clamp(base_peak * 1.28, 0.42, 0.92)
        floor = clamp(base_floor * 1.32, 0.11, 0.38)
        width = clamp(base_width * 1.18, 0.62, 1.42)
    elif avg_level >= 2.0:
        tier = 2
        peak = clamp(base_peak * 1.18, 0.42, 0.88)
        floor = clamp(base_floor * 1.20, 0.11, 0.34)
        width = clamp(base_width * 1.10, 0.62, 1.34)
    else:
        tier = 1
        peak, floor, width = base_peak, base_floor, base_width
    return {
        "id": f"e_{a['id']}_{b['id']}",
        "a": a, "b": b,
        "cx": cx, "cy": cy,
        "fire_pct": fire_at,
        "peak_op": peak,
        "floor_op": floor,
        "width": width,
        "tier": tier,
        "travel_start": travel_start,
        "travel_end": travel_end,
        "travel_dur": travel_end - travel_start,
    }
