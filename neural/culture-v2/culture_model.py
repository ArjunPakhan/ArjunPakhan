import math
import random

CELL_X = 14.5
CELL_Y = 15.0
MARGIN_X = 48
MARGIN_Y = 42
N_WEEKS = 53
WIDTH = 880
HEIGHT = 420

PROP_START = 6.0
PROP_END = 87.0
INTRO_END = 5.0
RESOLUTION_AT = 90.5
HOLD_END = 96.0

COLOR_BACKGROUND = "#090A0F"
COLOR_STRUCTURE_GREEN_DIM = "#3E8F6A"
COLOR_STRUCTURE_GREEN_BRIGHT = "#5FBF8A"
COLOR_STRUCTURE_GREEN_DARK = "#254636"
COLOR_STRUCTURE_GREEN_SOFT = "#4a7a65"
COLOR_ACTIVE_CORAL_DIM = "#B9575D"
COLOR_ACTIVE_CORAL_BRIGHT = "#E87972"
COLOR_ACTIVE_CORAL_GLOW = "#f0a0a0"
COLOR_PLASTICITY_VIOLET = "#8D72C0"
COLOR_PLASTICITY_DIM = "#7059A6"
COLOR_PLASTICITY_SOFT = "#a99ad0"
COLOR_ELECTRICAL_WHITE = "#F7F3FF"
COLOR_ELECTRICAL_CYAN = "#EAF7F5"
COLOR_AXON_REST = "#3E8F6A"
COLOR_AXON_VIOLET = "#8D72C0"
COLOR_DENDRITE_REST = "#3E8F6A"

DORMANT_FILL = COLOR_STRUCTURE_GREEN_DARK
PRE_FIRE = {1: "#2e4d3e", 2: "#365c48", 3: "#3E6b52", 4: "#3E8F6A"}
PEAK_FILL = {1: "#c46a6e", 2: "#D86a62", 3: "#E87972", 4: "#FF9A94"}
RESIDUAL_FILL = {1: "#5a4a7a", 2: "#6b5a92", 3: "#7059A6", 4: "#8D72C0"}
EDGE_COLOR_HOT = COLOR_STRUCTURE_GREEN_BRIGHT
EDGE_DENDRITE = COLOR_DENDRITE_REST
EDGE_AXON_HOT = COLOR_AXON_REST


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def build(data, seed=7):
    rng = random.Random(seed)
    weeks = data["weeks"]
    neurons = []
    # --- create neurons from weekly activity ---
    nid = 0
    for w, wk in enumerate(weeks):
        total = sum(d["count"] for d in wk["days"])
        max_lvl = max(d["level"] for d in wk["days"])
        active = sum(1 for d in wk["days"] if d["count"] > 0)
        # decide how many neurons this week seeds
        n_here = 0
        if total >= 18 or (max_lvl == 4 and active >= 4):
            n_here = 2
        elif total >= 8 or active >= 3:
            n_here = 1
        elif total >= 3 and rng.random() < 0.52:
            n_here = 1
        elif total >= 1 and rng.random() < 0.18:
            n_here = 1
        for k in range(n_here):
            activity = clamp(total / 22.0, 0.08, 1.0)
            if max_lvl == 4:
                activity = max(activity, 0.85)
            elif max_lvl == 3:
                activity = max(activity, 0.55)
            base_x = MARGIN_X + w * CELL_X + rng.uniform(-4.5, 7.0)
            # organic vertical distribution: bias slightly by average weekday
            avg_wd = sum(d["weekday"] * (d["count"] + 0.2) for d in wk["days"]) / max(1, sum(d["count"] + 0.2 for d in wk["days"]))
            # map weekday 0-6 to y but with large jitter
            y_center = MARGIN_Y + (avg_wd / 6) * (HEIGHT - MARGIN_Y * 2) + rng.uniform(-38, 38)
            tries = 0
            y = clamp(y_center, MARGIN_Y + 14, HEIGHT - MARGIN_Y - 14)
            # simple repulsion against existing
            while tries < 12:
                too_close = False
                for nb in neurons:
                    if abs(nb["x"] - base_x) < 22 and abs(nb["y"] - y) < 28 and _dist((base_x, y), (nb["x"], nb["y"])) < 34:
                        too_close = True
                        break
                if not too_close:
                    break
                y = clamp(y + rng.uniform(-18, 18), MARGIN_Y + 14, HEIGHT - MARGIN_Y - 14)
                tries += 1
            lvl = max_lvl if n_here == 1 else (max_lvl if k == 0 else max(1, max_lvl - 1))
            # soma: organic offset + size via contribution activity, restrained
            soma_r = 4.4 + activity * 2.4 + (0.7 if lvl == 4 else 0.35 if lvl == 3 else 0)
            soma_r = clamp(soma_r, 4.2, 7.4)
            # organic jitter for non-circular soma
            ox = rng.uniform(-0.7, 0.7)
            oy = rng.uniform(-0.7, 0.7)
            neurons.append({
                "id": f"c{nid}",
                "week": w,
                "x": base_x + ox,
                "y": y + oy,
                "ox": ox, "oy": oy,
                "level": lvl,
                "total": total,
                "activity": activity,
                "soma_r": soma_r,
                "soma_floor_r": soma_r * 0.92,
                "soma_peak_r": soma_r * 1.32,
                "soma_mid_r": soma_r * 1.15,
                "pre_op": clamp(0.24 + activity * 0.16, 0.24, 0.40),
                "peak_op": 1.0 if lvl == 4 else 0.96 if lvl == 3 else 0.88,
                "mid_op": clamp(0.52 + activity * 0.16, 0.52, 0.74),
                "floor_op": clamp(0.34 + activity * 0.18, 0.34, 0.58),
                "decay": 3.0 + activity * 2.8,
                "rise": 0.55 + activity * 0.32,
                "dendrites": [],
                "axons": [],
            })
            nid += 1
    # ensure at least 28 neurons for visual richness
    if len(neurons) < 28:
        extra = 28 - len(neurons)
        for _ in range(extra):
            w = rng.randint(8, 50)
            x = MARGIN_X + w * CELL_X + rng.uniform(-5, 6)
            y = rng.uniform(MARGIN_Y + 18, HEIGHT - MARGIN_Y - 18)
            # avoid overlap
            if any(_dist((x, y), (n["x"], n["y"])) < 32 for n in neurons):
                continue
            lvl = rng.choice([1, 2, 2, 3])
            act = 0.35 + rng.random() * 0.3
            r = 4.3 + act * 1.9
            neurons.append({
                "id": f"c{nid}", "week": w, "x": x, "y": y, "level": lvl, "total": 4, "activity": act,
                "soma_r": r, "soma_floor_r": r*0.92, "soma_peak_r": r*1.28, "soma_mid_r": r*1.13,
                "pre_op": 0.26, "peak_op": 0.9, "mid_op": 0.58, "floor_op": 0.38,
                "decay": 3.2, "rise": 0.6, "dendrites": [], "axons": [],
                "ox": 0, "oy": 0,
                "growth_start": 14.0 + (w/53)*8.0, "growth_end": 28.0,
            })
            nid += 1
    neurons.sort(key=lambda n: n["week"])
    # firing timing - chronological with jitter
    active_ws = sorted(set(n["week"] for n in neurons))
    col_rank = {c: i for i, c in enumerate(active_ws)}
    n_ws = max(1, len(active_ws) - 1)
    for n in neurons:
        base = col_rank[n["week"]] / n_ws
        jitter = rng.uniform(-0.10, 0.10) / max(1, n_ws)
        # within same week, stagger by soma size (larger fires slightly earlier)
        same = [x for x in neurons if x["week"] == n["week"]]
        rank = same.index(n)
        stagger = (rank / max(1, len(same))) * (0.42 / max(1, n_ws))
        frac = clamp(base + stagger + jitter, 0, 1)
        n["delay_pct"] = PROP_START + frac * (PROP_END - PROP_START)
        n["halo"] = n["level"] >= 3

    # --- morphology: dendrites & axons ---
    for n in neurons:
        act = n["activity"]
        # find nearby neurons for attraction
        nearby = []
        for other in neurons:
            if other["id"] == n["id"]:
                continue
            d = _dist((n["x"], n["y"]), (other["x"], other["y"]))
            if 22 < d < 108:
                ang = math.atan2(other["y"] - n["y"], other["x"] - n["x"])
                nearby.append((d, ang, other))
        nearby.sort(key=lambda x: x[0])
        attract_angles = [a for _, a, _ in nearby[:3]]
        # dendrites: 2-4 primary branches, asymmetric
        n_primary = 2 + int(act * 1.8) + (1 if rng.random() < 0.28 else 0)
        n_primary = clamp(n_primary, 2, 4)
        # choose asymmetric sector: bias away from dominant axon direction (east)
        # occasional bias toward attractors
        if attract_angles and rng.random() < 0.62:
            base_ang = attract_angles[rng.randint(0, min(1, len(attract_angles)-1))] + rng.uniform(-0.55, 0.55)
        else:
            # broad spread but not full radial star
            sector_center = rng.uniform(-2.0, 2.2) if rng.random() < 0.5 else rng.uniform(1.0, 2.2)
            base_ang = sector_center
        spread = 1.9 + rng.uniform(-0.3, 0.45)
        for b in range(n_primary):
            # asymmetric spacing: not uniform
            t = (b + rng.uniform(-0.18, 0.18)) / max(1, n_primary - 1) if n_primary > 1 else 0.5
            ang = base_ang + (t - 0.5) * spread
            # micro jitter toward attraction if nearby
            if attract_angles and rng.random() < 0.38:
                ang = ang * 0.62 + attract_angles[0] * 0.38 + rng.uniform(-0.18, 0.18)
            # nudge away from pure east (axon reserved)
            if abs(math.cos(ang) - 1) < 0.22 and abs(math.sin(ang)) < 0.45:
                ang += rng.choice([-1, 1]) * (0.65 + rng.random()*0.35)
            length = 20 + act * 26 + rng.uniform(-5, 7) + b * 2.5
            # taper length variation per branch for asymmetry
            length *= (0.72 + rng.random()*0.48)
            length = clamp(length, 14, 52)
            has_fork = rng.random() < (0.42 + act * 0.22) if n_primary <= 3 else rng.random() < (0.28 + act*0.12)
            # primary can bifurcate into 1-2 secondary forks with different lengths
            c1_len = length * (0.38 + rng.uniform(-0.06, 0.07))
            c1_x = n["x"] + math.cos(ang) * c1_len + rng.uniform(-3.5, 3.5)
            c1_y = n["y"] + math.sin(ang) * c1_len + rng.uniform(-3.5, 3.5)
            end_x = n["x"] + math.cos(ang) * length + rng.uniform(-2.8, 2.8)
            end_y = n["y"] + math.sin(ang) * length + rng.uniform(-2.8, 2.8)
            end_x = clamp(end_x, MARGIN_X - 6, WIDTH - MARGIN_X + 6)
            end_y = clamp(end_y, MARGIN_Y - 6, HEIGHT - MARGIN_Y + 6)
            width = 0.62 + act * 0.28 + rng.uniform(-0.10, 0.10)
            width = clamp(width, 0.48, 1.15)
            dend = {"cx": c1_x, "cy": c1_y, "x2": end_x, "y2": end_y, "width": width, "fork": None, "fork2": None}
            if has_fork:
                fork_ang = ang + rng.choice([-1, 1]) * (0.68 + rng.random()*0.32)
                fork_len = length * (0.32 + rng.random()*0.18)
                f_cx = end_x + math.cos(fork_ang) * fork_len * 0.36
                f_cy = end_y + math.sin(fork_ang) * fork_len * 0.36
                f_x = end_x + math.cos(fork_ang) * fork_len
                f_y = end_y + math.sin(fork_ang) * fork_len
                dend["fork"] = {"cx": f_cx, "cy": f_cy, "x2": clamp(f_x, 6, WIDTH-6), "y2": clamp(f_y, 6, HEIGHT-6), "width": width*0.68}
                # rare second fork on same primary for richer asymmetry
                if rng.random() < 0.22 and act > 0.55:
                    f2_ang = ang + rng.choice([-1, 1]) * (0.52 + rng.random()*0.28)
                    f2_len = length * (0.26 + rng.random()*0.14)
                    f2_cx = end_x + math.cos(f2_ang) * f2_len * 0.30
                    f2_cy = end_y + math.sin(f2_ang) * f2_len * 0.30
                    f2_x = end_x + math.cos(f2_ang) * f2_len
                    f2_y = end_y + math.sin(f2_ang) * f2_len
                    dend["fork2"] = {"cx": f2_cx, "cy": f2_cy, "x2": clamp(f2_x, 6, WIDTH-6), "y2": clamp(f2_y, 6, HEIGHT-6), "width": width*0.58}
            n["dendrites"].append(dend)
        # growth window for this neuron's neurites
        n["growth_start"] = 14.0 + (n["week"] / 53) * 8.0 + rng.uniform(-1.2, 1.2)
        n["growth_end"] = n["growth_start"] + 12.0 + n["activity"] * 8.0

    # axons: connect downstream neurons
    axons = []
    seen = set()
    for i, a in enumerate(neurons):
        # candidates downstream within ~5 weeks and vertical ~110
        cand = []
        for b in neurons[i+1: min(len(neurons), i+10)]:
            dw = b["week"] - a["week"]
            if dw < 0 or dw > 5:
                continue
            dy = abs(b["y"] - a["y"])
            if dy > 110:
                continue
            dx = b["x"] - a["x"]
            if dx < 8:
                continue
            d = math.hypot(dx, dy)
            cand.append((d, b))
        cand.sort(key=lambda x: x[0])
        budget = 1 if a["level"] <= 1 else 2 if a["level"] == 2 else 2
        # high activity gets slightly more chance for second connection
        if a["activity"] > 0.75 and rng.random() < 0.45:
            budget = min(2, budget + 1)
        made = 0
        for d, b in cand:
            if made >= budget:
                break
            key = (a["id"], b["id"])
            if key in seen:
                continue
            seen.add(key)
            # dominant axon: smooth, longer, slightly thicker, directional eastward
            sx, sy = a["x"], a["y"]
            ex, ey = b["x"], b["y"]
            # start offset from soma edge along direction to target for clear origin
            ang_to = math.atan2(ey - sy, ex - sx)
            start_r = a["soma_r"] + 2.2
            sx0 = sx + math.cos(ang_to) * start_r
            sy0 = sy + math.sin(ang_to) * start_r
            mid_x = (sx0 + ex) / 2 + rng.uniform(-6, 12)
            mid_y = (sy0 + ey) / 2 + rng.uniform(-10, 10)
            dx, dy = ex - sx0, ey - sy0
            dist = math.hypot(dx, dy) or 1
            nx, ny = -dy/dist, dx/dist
            # smoother bend (reduced, more directional)
            bend = rng.uniform(0.12, 0.26) * dist * rng.choice([-1, 1]) * (0.55 + a["activity"]*0.18)
            term_r = b["soma_r"] + 4.0
            term_x = ex - math.cos(ang_to) * term_r
            term_y = ey - math.sin(ang_to) * term_r
            cx = mid_x + nx * bend * 0.48
            cy = mid_y + ny * bend * 0.48
            # bifurcation for high activity: small collateral
            # compute hierarchy tier
            avg_lvl = (a["level"] + b["level"]) / 2
            if avg_lvl >= 3.0:
                tier = 3
            elif avg_lvl >= 2.0:
                tier = 2
            else:
                tier = 1
            base_floor = clamp(0.12 + avg_lvl*0.05, 0.12, 0.33) * (1.12 if tier==2 else 1.26 if tier==3 else 1.0)
            base_peak = clamp(0.44 + avg_lvl*0.10, 0.44, 0.88) * (1.10 if tier==2 else 1.20 if tier==3 else 1.0)
            width = clamp(0.85 + avg_lvl*0.20, 0.85, 1.55) * (1.06 if tier==2 else 1.14 if tier==3 else 1.0)
            # timing
            desired = clamp(dist * 0.028 + 0.95, 1.15, 2.45)
            travel_end = b["delay_pct"] + 0.06
            travel_start = travel_end - desired
            min_start = a["delay_pct"] + 0.08
            if travel_start < min_start:
                travel_start = min_start
                travel_end = travel_start + desired
            travel_start = clamp(travel_start, PROP_START, PROP_END)
            travel_end = clamp(travel_end, travel_start + 0.9, 99.0)
            ax = {
                "id": f"ax_{a['id']}_{b['id']}",
                "a": a, "b": b,
                "sx": sx0, "sy": sy0, "ex": term_x, "ey": term_y,
                "orig_sx": sx, "orig_sy": sy,
                "cx": cx, "cy": cy,
                "tier": tier,
                "width": width,
                "peak_op": base_peak,
                "floor_op": base_floor,
                "fire_pct": max(a["delay_pct"], b["delay_pct"]) + 0.14,
                "travel_start": travel_start,
                "travel_end": travel_end,
                "travel_dur": travel_end - travel_start,
                "terminal_r": 1.9 + (0.6 if tier==3 else 0.3 if tier==2 else 0),
                "growth_start": max(a["growth_start"] + 3.0, 18.0),
                "growth_end": min(a["growth_end"] + 6.0, 56.0),
            }
            a["axons"].append(ax)
            axons.append(ax)
            made += 1

    # clusters for background wash: dense weeks
    by_week = {}
    for n in neurons:
        by_week.setdefault(n["week"], []).append(n)
    clusters = [g for g in by_week.values() if len(g) >= 2]

    return {
        "neurons": neurons,
        "axons": axons,
        "clusters": clusters,
        "last_neuron": neurons[-1] if neurons else None,
        "width": WIDTH,
        "height": HEIGHT,
    }
