"""
Emits the animated neural-pulse SVG from the model built in model.py, using
the shared stop generators in keyframes.py (also used by render_preview.py
so the CSS animation and the rendered PNG/GIF preview never drift apart).
"""
import model as M
import keyframes as K

CYCLE_S = 24.0  # full loop duration


def css_stops_to_rule(name, stops, props):
    lines = []
    for row in stops:
        pct = row[0]
        vals = row[1:]
        decls = "; ".join(f"{p}:{v}px" if p == "r" else f"{p}:{v}" for p, v in zip(props, vals))
        lines.append(f"  {pct}% {{ {decls}; }}")
    return f"@keyframes {name} {{\n" + "\n".join(lines) + "\n}"


def pulse_rule(name, stops):
    lines = []
    for pct, off, op in stops:
        lines.append(f"  {pct:.3f}% {{ offset-distance:{off:.2f}%; opacity:{op:.3f}; }}")
    return f"@keyframes {name} {{\n" + "\n".join(lines) + "\n}"


def build(model, theme="dark"):
    W, H = model["width"], model["height"]
    bg = "#0a0a0f" if theme == "dark" else "#f4f2f8"
    vignette = "#15111f" if theme == "dark" else "#e7e1f2"

    css_blocks = []
    node_els, halo_els, edge_els, cluster_els, pulse_els, discharge_els = [], [], [], [], [], []

    for e in model["edges"]:
        a, b = e["a"], e["b"]
        css_blocks.append(css_stops_to_rule(f"edge_{e['id']}", K.edge_stops(e), ["opacity"]))
        d = f"M {a['x']:.2f} {a['y']:.2f} Q {e['cx']:.2f} {e['cy']:.2f} {b['x']:.2f} {b['y']:.2f}"
        edge_els.append(
            f'<path d="{d}" class="edge" stroke-width="{e["width"]:.2f}" '
            f'style="animation-name: edge_{e["id"]}"/>'
        )
        css_blocks.append(pulse_rule(f"pulse_{e['id']}", K.pulse_stops(e)))
        css_blocks.append(pulse_rule(f"pulse_halo_{e['id']}", K.pulse_halo_stops(e)))
        css_blocks.append(css_stops_to_rule(f"discharge_{e['id']}", K.discharge_stops(e), ["opacity", "r"]))
        discharge_els.append(
            f'<circle cx="{b["x"]:.2f}" cy="{b["y"]:.2f}" r="1.9" class="discharge" style="animation-name: discharge_{e["id"]}"/>'
        )
        path_esc = d.replace('"', '&quot;')
        begin_s = e["travel_start"] / 100 * CYCLE_S
        dur_s = e["travel_dur"] / 100 * CYCLE_S
        amp = max(0.75, min(1.15, 0.65 + (e["a"]["level"] + e["b"]["level"]) * 0.07))
        pulse_els.append(
            f'<circle r="{1.35 * amp:.2f}" class="pulse-halo" style="offset-path:path(\'{d}\'); animation-name:pulse_halo_{e["id"]}">'
            f'<animateMotion path="{path_esc}" begin="{begin_s:.3f}s" dur="{dur_s:.3f}s" repeatCount="indefinite" rotate="auto" calcMode="spline" keySplines="0.4 0 0.2 1;0.4 0 0.2 1" keyTimes="0;1"/>'
            f'</circle>'
        )
        pulse_els.append(
            f'<circle r="{1.05 * amp:.2f}" class="pulse-core" style="offset-path:path(\'{d}\'); animation-name:pulse_{e["id"]}">'
            f'<animateMotion path="{path_esc}" begin="{begin_s:.3f}s" dur="{dur_s:.3f}s" repeatCount="indefinite" rotate="auto" calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/>'
            f'</circle>'
        )

    for idx, group in enumerate(model["clusters"]):
        xs = [n["x"] for n in group]
        ys = [n["y"] for n in group]
        cx, cy = sum(xs) / len(xs), (min(ys) + max(ys)) / 2
        rx = (max(xs) - min(xs)) / 2 + 9
        ry = (max(ys) - min(ys)) / 2 + 9
        fire_pct = min(n["delay_pct"] for n in group) + 0.3
        css_blocks.append(css_stops_to_rule(f"cluster_{idx}", K.cluster_stops(fire_pct), ["opacity"]))
        cluster_els.append(
            f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
            f'class="cluster-flash" style="animation-name: cluster_{idx}"/>'
        )

    for n in model["nodes"]:
        if not n["active"]:
            node_els.append(
                f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{n["pre_r"]:.2f}" class="dormant"/>'
            )
            continue
        css_blocks.append(css_stops_to_rule(f"fire_{n['id']}", K.node_stops(n), ["opacity", "r", "fill"]))
        if n["halo"]:
            css_blocks.append(css_stops_to_rule(f"halo_{n['id']}", K.halo_stops(n), ["opacity", "r"]))
            halo_els.append(
                f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{n["floor_r"]:.2f}" '
                f'class="halo" style="animation-name: halo_{n["id"]}"/>'
            )
        node_els.append(
            f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{n["pre_r"]:.2f}" '
            f'class="node" style="animation-name: fire_{n["id"]}"/>'
        )

    resolution_el = ""
    if model["last_active"]:
        la = model["last_active"]
        css_blocks.append(css_stops_to_rule("resolution", K.resolution_stops(), ["opacity", "r"]))
        resolution_el = (
            f'<circle cx="{la["x"]:.2f}" cy="{la["y"]:.2f}" r="6" '
            f'class="resolution" style="animation-name: resolution"/>'
        )

    css_blocks.append(css_stops_to_rule("scene_fade", K.scene_stops(), ["opacity"]))

    style = f"""
    .scene {{ animation: scene_fade {CYCLE_S}s linear infinite; }}
    .dormant {{ fill:{M.DORMANT_FILL}; opacity:0.28; }}
    .node, .halo, .edge, .cluster-flash, .resolution, .discharge {{
      animation-duration:{CYCLE_S}s; animation-timing-function:linear;
      animation-iteration-count:infinite;
    }}
    .halo {{ filter:url(#soft-blur); }}
    .edge {{ fill:none; stroke:{M.EDGE_COLOR_HOT}; stroke-linecap:round; }}
    .cluster-flash {{ fill:{M.EDGE_COLOR_HOT}; filter:url(#soft-blur-lg); }}
    .resolution {{ fill:none; stroke:{M.PEAK_FILL[4]}; stroke-width:1.15; filter:url(#soft-blur); }}
    .discharge {{ fill:none; stroke:#d8c8ff; stroke-width:0.9; filter:url(#soft-blur); }}
    .pulse-core {{ fill:#f8f3ff; stroke:#e6deff; stroke-width:0.25; }}
    .pulse-halo {{ fill:#c9b6ef; filter:url(#soft-blur); }}
    .pulse-core, .pulse-halo {{
      offset-rotate: auto; offset-anchor: center;
      animation-duration:{CYCLE_S}s; animation-timing-function:linear;
      animation-iteration-count:infinite;
    }}
    {''.join(css_blocks)}
    """

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}"
     viewBox="0 0 {W:.0f} {H:.0f}" role="img"
     aria-label="Neural network visualization driven by GitHub contribution activity">
  <title>Neural contribution graph</title>
  <defs>
    <radialGradient id="bg-vignette" cx="30%" cy="35%" r="85%">
      <stop offset="0%" stop-color="{vignette}"/>
      <stop offset="100%" stop-color="{bg}"/>
    </radialGradient>
    <filter id="soft-blur" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="2.1"/>
    </filter>
    <filter id="soft-blur-lg" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="6"/>
    </filter>
  </defs>
  <style>{style}</style>
  <rect width="{W:.0f}" height="{H:.0f}" fill="url(#bg-vignette)"/>
  <g class="scene">
    <g class="clusters">{''.join(cluster_els)}</g>
    <g class="edges">{''.join(edge_els)}</g>
    <g class="discharges">{''.join(discharge_els)}</g>
    <g class="pulses">{''.join(pulse_els)}</g>
    <g class="halos">{''.join(halo_els)}</g>
    <g class="nodes">{''.join(node_els)}</g>
    {resolution_el}
  </g>
</svg>'''
    return svg


if __name__ == "__main__":
    import data as D
    ds = D.generate()
    m = M.build(ds)
    svg = build(m, theme="dark")
    with open("dist/neural-pulse-dark.svg", "w") as f:
        f.write(svg)
    print(f"wrote dist/neural-pulse-dark.svg  ({len(svg)/1024:.1f} KB), "
          f"{len(m['active_nodes'])} active nodes, {len(m['edges'])} edges, "
          f"{len(m['clusters'])} cluster weeks")
