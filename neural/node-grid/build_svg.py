"""Emit the SMIL-animated node-grid SVG from the model built in model.py.

Uses SMIL <animate> elements only (no CSS @keyframes, no JS, no WebGL) so the
animation is driven entirely by the static SVG file, which is the only thing a
GitHub profile README can render.
"""
from __future__ import annotations

import model as M


def _animate(attr: str, values: list, keytimes: list, dur: float = M.CYCLE) -> str:
    vs = ";".join(values)
    ks = ";".join(f"{k:.4f}" for k in keytimes)
    return (
        f'<animate attributeName="{attr}" values="{vs}" keyTimes="{ks}" '
        f'dur="{dur}s" repeatCount="indefinite"/>'
    )


def _opacity_values(peak: float, rest: float) -> list:
    return [f"{v:.3f}" for v in (0.0, M.DORMANT_OPACITY, M.DORMANT_OPACITY, peak, rest, rest, 0.0)]


def _node_el(node: dict, pal: dict) -> str:
    """One circle + its SMIL animations."""
    cx, cy = node["cx"], node["cy"]
    T = node["activation"]

    if node["level"] == 0:
        # Inactive node: fade in to dormant, hold, fade out. No firing.
        kt = [0.0, M.INTRO_END / M.CYCLE, M.FADE_START / M.CYCLE, 1.0]
        vals = [f"{v:.3f}" for v in (0.0, M.DORMANT_OPACITY, M.DORMANT_OPACITY, 0.0)]
        anims = _animate("opacity", vals, kt)
        fill = pal["dormant"]
        r = f"{M.BASE_R:.2f}"
    else:
        kt_op = [
            0.0,
            M.INTRO_END / M.CYCLE,
            T / M.CYCLE,
            (T + 0.3) / M.CYCLE,
            (T + 0.8) / M.CYCLE,
            M.FADE_START / M.CYCLE,
            1.0,
        ]
        vals_op = _opacity_values(node["peak_op"], node["rest_op"])
        anim_op = _animate("opacity", vals_op, kt_op)

        kt_fill = [0.0, T / M.CYCLE, (T + 0.3) / M.CYCLE, (T + 0.8) / M.CYCLE, 1.0]
        vals_fill = [pal["dormant"], pal["dormant"], pal["fire"], node["rest_color"], node["rest_color"]]
        anim_fill = _animate("fill", vals_fill, kt_fill)

        kt_r = kt_fill
        base = f"{M.BASE_R:.2f}"
        fire = f"{node['fire_r']:.2f}"
        vals_r = [base, base, fire, base, base]
        anim_r = _animate("r", vals_r, kt_r)

        anims = anim_op + anim_fill + anim_r
        fill = pal["dormant"]
        r = f"{M.BASE_R:.2f}"

    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}">{anims}</circle>'


def _cluster_el(cluster: dict, model: dict) -> str:
    """Blurred wash behind a dense week column."""
    pal = model["pal"]
    col = cluster["col"]
    T = cluster["activation"]
    x0 = M.PAD + col * (M.CELL + M.GAP) - 3.0
    w = M.CELL + 6.0
    y0 = M.PAD - 3.0
    h = model["grid_h"] + 6.0

    kt = [0.0, T / M.CYCLE, (T + 0.4) / M.CYCLE, (T + 1.6) / M.CYCLE, 1.0]
    vals = [f"{v:.3f}" for v in (0.0, 0.0, 0.25, 0.0, 0.0)]
    anim = _animate("opacity", vals, kt)

    return (
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'fill="{pal["cluster"]}" filter="url(#blur-cluster)">{anim}</rect>'
    )


def _overlay_el(model: dict) -> str:
    """Whole-grid resolution + breathing overlay (low opacity, blurred)."""
    pal = model["pal"]
    w, h = model["width"], model["height"]
    b1, b2 = M.BREATH1, M.BREATH2
    b1p, b1e = b1 + 0.25, b1 + 0.55
    b2p, b2e = b2 + 0.25, b2 + 0.55

    kt = [
        0.0,
        M.RES_START / M.CYCLE,
        M.RES_PEAK / M.CYCLE,
        M.RES_END / M.CYCLE,
        b1 / M.CYCLE, b1p / M.CYCLE, b1e / M.CYCLE,
        b2 / M.CYCLE, b2p / M.CYCLE, b2e / M.CYCLE,
        M.FADE_START / M.CYCLE,
        1.0,
    ]
    vals = [f"{v:.3f}" for v in (0.0, 0.0, 0.22, 0.0, 0.0, 0.08, 0.0, 0.0, 0.08, 0.0, 0.0, 0.0)]
    anim = _animate("opacity", vals, kt)

    return (
        f'<rect x="0" y="0" width="{w:.0f}" height="{h:.0f}" '
        f'fill="{pal["breath"]}" filter="url(#blur-overlay)">{anim}</rect>'
    )


def render_svg(model: dict) -> str:
    pal = model["pal"]
    W, H = model["width"], model["height"]

    node_els = "\n    ".join(_node_el(n, pal) for n in model["nodes"])
    cluster_els = "\n    ".join(_cluster_el(c, model) for c in model["clusters"])
    overlay = _overlay_el(model)

    label = (
        "GitHub contribution activity rendered as a neural-inspired network "
        "(a neural metaphor applied to contribution data, not cognition)"
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="{label}">
  <title>Contribution activity — neural metaphor</title>
  <defs>
    <filter id="blur-cluster" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
    <filter id="blur-overlay" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
  </defs>
  <rect width="{W:.0f}" height="{H:.0f}" fill="{pal['bg']}"/>
  <g>
    {cluster_els}
    {node_els}
    {overlay}
  </g>
</svg>'''


if __name__ == "__main__":
    import json
    import sys
    # quick self-test: render from a sample fixture if given, else from model default
    data = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {"weeks": []}
    if not data["weeks"]:
        # minimal 1-week fixture
        data = {"weeks": [{"days": [{"date": f"2026-01-0{i}", "weekday": i, "count": i, "level": min(i, 4)} for i in range(7)]}]}
    for theme in ("dark", "light"):
        m = M.build_model(data, theme=theme)
        svg = render_svg(m)
        print(f"{theme}: {len(m['nodes'])} nodes, {len(m['clusters'])} clusters, {len(svg)/1024:.1f} KB")
