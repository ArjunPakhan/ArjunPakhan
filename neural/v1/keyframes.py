import model as M


def _clean(stops):
    cleaned = []
    last = -1.0
    for row in stops:
        pct = row[0]
        pct = max(pct, last + 0.01) if cleaned else pct
        pct = min(pct, 100.0)
        cleaned.append((round(pct, 3), *row[1:]))
        last = pct
    return cleaned


def node_stops(n):
    d, rise, decay = n["delay_pct"], n["rise_pct"], n["decay_pct"]
    start = max(0.0, d - rise)
    mid = min(99.9, d + decay * 0.4)
    end = min(99.9, d + decay)
    pre_fill, peak_fill, resid_fill = (
        M.PRE_FIRE[n["level"]], M.PEAK_FILL[n["level"]], M.RESIDUAL_FILL[n["level"]]
    )
    return _clean([
        (0.0, n["pre_op"], n["pre_r"], pre_fill),
        (start, n["pre_op"], n["pre_r"], pre_fill),
        (d, n["peak_op"], n["peak_r"], peak_fill),
        (mid, n["mid_op"], n["mid_r"], peak_fill if n["level"] >= 3 else resid_fill),
        (end, n["floor_op"], n["floor_r"], resid_fill),
        (100.0, n["floor_op"], n["floor_r"], resid_fill),
    ])


def halo_stops(n):
    d, rise = n["delay_pct"], n["rise_pct"]
    decay = n["decay_pct"] * 1.3
    start = max(0.0, d - rise)
    end = min(99.9, d + decay)
    peak_r, floor_r = n["peak_r"] * 1.95, n["floor_r"] * 1.42
    peak_op = {3: 0.28, 4: 0.36}[n["level"]]
    floor_op = {3: 0.07, 4: 0.10}[n["level"]]
    return _clean([
        (0.0, 0.0, floor_r), (start, 0.0, floor_r),
        (d, peak_op, peak_r),
        (min(99.9, d + decay * 0.5), peak_op * 0.38, peak_r * 0.84),
        (end, floor_op, floor_r), (100.0, floor_op, floor_r),
    ])


def edge_stops(e):
    fire = min(99.5, e["fire_pct"])
    start = max(0.0, fire - 0.5)
    end = min(99.9, fire + 3.4)
    return _clean([
        (0.0, e["floor_op"] * 0.4), (start, e["floor_op"] * 0.4),
        (fire, e["peak_op"]), (min(99.9, fire + 1.1), e["peak_op"] * 0.5),
        (end, e["floor_op"]), (100.0, e["floor_op"]),
    ])


def cluster_stops(fire_pct):
    start = max(0.0, fire_pct - 1.2)
    end = min(99.9, fire_pct + 4.6)
    return _clean([
        (0.0, 0.0), (start, 0.0), (fire_pct, 0.22),
        (min(99.9, fire_pct + 1.5), 0.11), (min(99.9, fire_pct + 3.0), 0.04), (end, 0.0), (100.0, 0.0),
    ])


def resolution_stops():
    return _clean([
        (0.0, 0.0, 6.0), (M.RESOLUTION_AT - 1, 0.0, 6.0),
        (M.RESOLUTION_AT + 2, 0.16, 52.0), (M.HOLD_END, 0.0, 78.0),
        (100.0, 0.0, 78.0),
    ])


def scene_stops():
    return _clean([
        (0.0, 0.0), (2.0, 0.2), (M.INTRO_END, 1.0),
        (M.HOLD_END, 1.0), (100.0, 0.0),
    ])


def _ease(t):
    return t * t * (3 - 2 * t)


def _qbez(a, c, b, t):
    u = 1 - t
    return u * u * a + 2 * u * t * c + t * t * b


def pulse_xy(e, t_pct):
    ts, te = e["travel_start"], e["travel_end"]
    if t_pct < ts or t_pct > te:
        return None
    dur = te - ts or 1e-6
    f = (t_pct - ts) / dur
    fe = _ease(max(0.0, min(1.0, f)))
    x = _qbez(e["a"]["x"], e["cx"], e["b"]["x"], fe)
    y = _qbez(e["a"]["y"], e["cy"], e["b"]["y"], fe)
    return x, y, fe


def pulse_opacity(e, t_pct):
    ts, te = e["travel_start"], e["travel_end"]
    if t_pct < ts - 0.08 or t_pct > te + 0.08:
        return 0.0
    if t_pct < ts:
        return 0.0
    if t_pct < ts + 0.10:
        return ((t_pct - ts) / 0.10) * 0.92
    if t_pct < te - 0.10:
        return 0.92
    if t_pct <= te:
        return 0.92 * (1 - (t_pct - (te - 0.10)) / 0.10 * 0.35)
    if t_pct <= te + 0.08:
        return 0.60 * (1 - (t_pct - te) / 0.08)
    return 0.0


def pulse_stops(e):
    ts, te = e["travel_start"], e["travel_end"]
    dur = te - ts
    n = 7
    stops = []
    stops.append((0.0, 0.0, 0.0))
    stops.append((max(0.0, ts - 0.06), 0.0, 0.0))
    stops.append((ts, 0.02, 0.0))
    for i in range(1, n):
        f = i / n
        fe = _ease(f)
        pct = ts + f * dur
        op = 0.92 if 0.12 < f < 0.88 else (0.92 * (0.5 + f * 0.5) if f <= 0.12 else 0.92 * (1 - (f - 0.88) / 0.12 * 0.4))
        stops.append((pct, fe * 100.0, op))
    stops.append((te, 100.0, 0.0))
    stops.append((min(99.9, te + 0.08), 100.0, 0.0))
    stops.append((100.0, 100.0, 0.0))
    return _clean(stops)


def pulse_halo_stops(e):
    ts, te = e["travel_start"], e["travel_end"]
    dur = te - ts
    n = 5
    stops = []
    stops.append((0.0, 0.0, 0.0))
    stops.append((max(0.0, ts - 0.06), 0.0, 0.0))
    stops.append((ts, 0.02, 0.0))
    for i in range(1, n):
        f = i / n
        fe = _ease(f)
        pct = ts + f * dur
        op = 0.28 if 0.15 < f < 0.80 else 0.18
        stops.append((pct, fe * 100.0, op))
    stops.append((te, 100.0, 0.0))
    stops.append((100.0, 100.0, 0.0))
    return _clean(stops)


def discharge_stops(e):
    te = e["travel_end"]
    start = te
    peak = min(99.9, te + 0.08)
    mid = min(99.9, te + 0.42)
    end = min(99.9, te + 0.90)
    r0, r_peak, r_mid, r_end = 1.9, 3.6, 5.0, 5.8
    o0, o_peak, o_mid, o_end = 0.0, 0.30, 0.10, 0.0
    lvl = max(e["a"]["level"], e["b"]["level"])
    if lvl >= 3:
        o_peak = 0.34
        r_peak = 4.0
        r_mid = 5.4
    return _clean([
        (0.0, 0.0, r0),
        (max(0.0, start - 0.06), 0.0, r0),
        (start, o0, r0),
        (peak, o_peak, r_peak),
        (mid, o_mid, r_mid),
        (end, o_end, r_end),
        (100.0, 0.0, r_end),
    ])


# ---- interpolation for the frame-by-frame preview renderer -----------

def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_hex(c1, c2, t):
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = round(_lerp(r1, r2, t)); g = round(_lerp(g1, g2, t)); b = round(_lerp(b1, b2, t))
    return f"#{r:02x}{g:02x}{b:02x}"


def eval_stops(stops, t_pct, has_color=False):
    """Linear-interpolate a CSS-keyframe-like stop list at a given percent,
    matching how a browser interpolates between keyframe stops."""
    if t_pct <= stops[0][0]:
        return stops[0][1:]
    if t_pct >= stops[-1][0]:
        return stops[-1][1:]
    for i in range(len(stops) - 1):
        p0, p1 = stops[i][0], stops[i + 1][0]
        if p0 <= t_pct <= p1:
            span = (p1 - p0) or 1e-6
            f = (t_pct - p0) / span
            s0, s1 = stops[i][1:], stops[i + 1][1:]
            out = [_lerp(s0[0], s1[0], f)]
            if len(s0) > 1:
                out.append(_lerp(s0[1], s1[1], f))
            if has_color:
                out.append(_lerp_hex(s0[-1], s1[-1], f))
            return tuple(out)
    return stops[-1][1:]
