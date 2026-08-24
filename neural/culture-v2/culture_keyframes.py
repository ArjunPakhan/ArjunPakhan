import culture_model as CM

def _clean(stops):
    c = []
    last = -1
    for row in stops:
        pct = row[0]
        pct = max(pct, last + 0.01) if c else pct
        pct = min(pct, 100)
        c.append((round(pct, 3), *row[1:]))
        last = pct
    return c

def soma_stops(n):
    d, rise, decay = n["delay_pct"], n["rise"], n["decay"]
    start = max(0, d - rise)
    mid = min(99.9, d + decay * 0.42)
    end = min(99.9, d + decay)
    pre, peak, resid = CM.PRE_FIRE[n["level"]], CM.PEAK_FILL[n["level"]], CM.RESIDUAL_FILL[n["level"]]
    # dormant culture: faint until 8%, then fade in by 14%
    return _clean([(0, n["pre_op"]*0.32, n["soma_r"]*0.78, pre), (8, n["pre_op"]*0.45, n["soma_r"]*0.85, pre), (14, n["pre_op"], n["soma_r"], pre), (start, n["pre_op"], n["soma_r"], pre), (d, n["peak_op"], n["soma_peak_r"], peak), (mid, n["mid_op"], n["soma_mid_r"], peak if n["level"]>=3 else resid), (end, n["floor_op"], n["soma_floor_r"], resid), (100, n["floor_op"], n["soma_floor_r"], resid)])

def halo_stops(n):
    d, rise = n["delay_pct"], n["rise"]
    decay = n["decay"] * 1.28
    start = max(0, d - rise)
    end = min(99.9, d + decay)
    peak_r, floor_r = n["soma_peak_r"] * 2.05, n["soma_floor_r"] * 1.48
    peak_op = {3: 0.28, 4: 0.36}.get(n["level"], 0.16)
    floor_op = {3: 0.06, 4: 0.09}.get(n["level"], 0.03)
    return _clean([(0, 0, floor_r), (start, 0, floor_r), (d, peak_op, peak_r), (min(99.9, d+decay*0.5), peak_op*0.36, peak_r*0.82), (end, floor_op, floor_r), (100, floor_op, floor_r)])

def axon_stops(a):
    fire = min(99.5, a["fire_pct"])
    fstart = max(0, fire - 0.6)
    fend = min(99.9, fire + 3.2)
    gs, ge = a.get("growth_start", 16), a.get("growth_end", 38)
    # growth ramp: 0 until gs, then rise to floor by ge
    base_floor = a["floor_op"]
    return _clean([(0, 0), (max(0, gs-1), 0), (gs, base_floor*0.22), (ge, base_floor*0.92), (ge+4, base_floor), (fstart, base_floor*0.92), (fire, a["peak_op"]), (min(99.9, fire+1.0), a["peak_op"]*0.52), (fend, a["floor_op"]), (100, a["floor_op"])])

def dendrite_stops(n):
    d = n["delay_pct"]
    fstart = max(0, d - 0.32)
    fend = min(99.9, d + 2.6)
    base = 0.16 + n["activity"]*0.14
    peak = 0.42 + n["activity"]*0.22
    floor = 0.09 + n["activity"]*0.06
    gs, ge = n.get("growth_start", 14), n.get("growth_end", 32)
    return _clean([(0, 0), (max(0, gs-1), 0), (gs, floor*0.28), (ge, floor*0.88), (ge+4, floor), (fstart, floor), (d, peak), (min(99.9, d+1.0), peak*0.48), (fend, floor), (100, floor)])

def cluster_stops(fire):
    s = max(0, fire - 1.2)
    e = min(99.9, fire + 4.8)
    return _clean([(0,0),(s,0),(fire,0.18),(min(99.9,fire+1.6),0.09),(e,0),(100,0)])

def resolution_stops():
    return _clean([(0,0,6),(CM.RESOLUTION_AT-1,0,6),(CM.RESOLUTION_AT+2,0.15,58),(CM.HOLD_END,0,82),(100,0,82)])

def scene_stops():
    return _clean([(0,0),(2,0.22),(CM.INTRO_END,1),(CM.HOLD_END,1),(100,0)])

def _ease(t):
    return t*t*(3-2*t)

def _qbez(a,c,b,t):
    u=1-t
    return u*u*a+2*u*t*c+t*t*b

def pulse_xy(ax, t):
    ts, te = ax["travel_start"], ax["travel_end"]
    if t < ts or t > te:
        return None
    f = (t-ts)/(te-ts or 1e-6)
    fe = _ease(max(0,min(1,f)))
    x = _qbez(ax["sx"], ax["cx"], ax["ex"], fe)
    y = _qbez(ax["sy"], ax["cx"] if False else ax["cy"], ax["ex"] if False else ax["ey"], fe)
    # correct: x uses cx, y uses cy
    x = _qbez(ax["sx"], ax["cx"], ax["ex"], fe)
    y = _qbez(ax["sy"], ax["cy"], ax["ey"], fe)
    return x,y,fe

def pulse_opacity(ax,t):
    ts,te=ax["travel_start"],ax["travel_end"]
    if t < ts-0.08 or t>te+0.08:
        return 0
    if t < ts:
        return 0
    if t < ts+0.10:
        return ((t-ts)/0.10)*0.94
    if t < te-0.10:
        return 0.94
    if t <= te:
        return 0.94*(1-(t-(te-0.10))/0.10*0.35)
    if t <= te+0.08:
        return 0.62*(1-(t-te)/0.08)
    return 0

def pulse_stops(ax):
    ts,te=ax["travel_start"],ax["travel_end"]
    dur=te-ts
    stops=[(0,0,0),(max(0,ts-0.06),0,0),(ts,0.02,0)]
    for i in range(1,7):
        f=i/7
        fe=_ease(f)
        pct=ts+f*dur
        op=0.94 if 0.12<f<0.88 else (0.94*(0.5+f*0.5) if f<=0.12 else 0.94*(1-(f-0.88)/0.12*0.4))
        stops.append((pct, fe*100, op))
    stops.append((te,100,0))
    stops.append((min(99.9,te+0.08),100,0))
    stops.append((100,100,0))
    return _clean(stops)

def pulse_halo_stops(ax):
    ts,te=ax["travel_start"],ax["travel_end"]
    dur=te-ts
    stops=[(0,0,0),(max(0,ts-0.06),0,0),(ts,0.02,0)]
    for i in range(1,5):
        f=i/5
        fe=_ease(f)
        pct=ts+f*dur
        op=0.30 if 0.15<f<0.80 else 0.18
        stops.append((pct,fe*100,op))
    stops.append((te,100,0))
    stops.append((100,100,0))
    return _clean(stops)

def discharge_stops(ax):
    te=ax["travel_end"]
    gs=ax.get("growth_end", 38)
    # invisible until axon has grown and pulse arrives
    return _clean([(0,0,2.1),(max(0,gs-1),0,2.1),(max(0,te-0.06),0,2.1),(te,0,2.1),(min(99.9,te+0.09),0.32,3.8),(min(99.9,te+0.45),0.11,5.4),(min(99.9,te+0.95),0,6.0),(100,0,6.0)])

def axon_growth_frac(ax, t):
    gs, ge = ax.get("growth_start", 16), ax.get("growth_end", 38)
    if t < gs:
        return 0.0
    if t >= ge:
        return 1.0
    return (t - gs) / (ge - gs or 1e-6)

def dendrite_growth_frac(n, t):
    gs, ge = n.get("growth_start", 14), n.get("growth_end", 32)
    if t < gs:
        return 0.0
    if t >= ge:
        return 1.0
    return (t - gs) / (ge - gs or 1e-6)

def _lerp(a,b,t):
    return a+(b-a)*t

def _lerp_hex(c1,c2,t):
    c1=c1.lstrip("#");c2=c2.lstrip("#")
    r1,g1,b1=int(c1[0:2],16),int(c1[2:4],16),int(c1[4:6],16)
    r2,g2,b2=int(c2[0:2],16),int(c2[2:4],16),int(c2[4:6],16)
    return f"#{round(_lerp(r1,r2,t)):02x}{round(_lerp(g1,g2,t)):02x}{round(_lerp(b1,b2,t)):02x}"

def eval_stops(stops,t,has_color=False):
    if t <= stops[0][0]:
        return stops[0][1:]
    if t >= stops[-1][0]:
        return stops[-1][1:]
    for i in range(len(stops)-1):
        p0,p1=stops[i][0],stops[i+1][0]
        if p0 <= t <= p1:
            f=(t-p0)/(p1-p0 or 1e-6)
            s0,s1=stops[i][1:],stops[i+1][1:]
            out=[_lerp(s0[0],s1[0],f)]
            if len(s0)>1:
                out.append(_lerp(s0[1],s1[1],f))
            if has_color:
                out.append(_lerp_hex(s0[-1],s1[-1],f))
            return tuple(out)
    return stops[-1][1:]
