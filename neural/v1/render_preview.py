import io
from PIL import Image, ImageDraw
import math

import model as M
import keyframes as K
import data as D

try:
    import cairosvg
    HAS_CAIROSVG = True
except Exception:
    HAS_CAIROSVG = False
    cairosvg = None


def _hex_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def frame_svg(model, t_pct, theme="dark"):
    W, H = model["width"], model["height"]
    bg = "#0a0a0f" if theme == "dark" else "#f4f2f8"
    vignette = "#15111f" if theme == "dark" else "#e7e1f2"
    scene_op = K.eval_stops(K.scene_stops(), t_pct)[0]
    parts = []
    for group in model["clusters"]:
        xs = [n["x"] for n in group]; ys = [n["y"] for n in group]
        cx, cy = sum(xs) / len(xs), (min(ys) + max(ys)) / 2
        rx = (max(xs) - min(xs)) / 2 + 9
        ry = (max(ys) - min(ys)) / 2 + 9
        fire_pct = min(n["delay_pct"] for n in group) + 0.3
        op = K.eval_stops(K.cluster_stops(fire_pct), t_pct)[0] * scene_op
        if op > 0.003:
            parts.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                          f'fill="{M.EDGE_COLOR_HOT}" opacity="{op:.3f}" filter="url(#b2)"/>')
    for e in model["edges"]:
        op = K.eval_stops(K.edge_stops(e), t_pct)[0] * scene_op
        a, b = e["a"], e["b"]
        d = f"M {a['x']:.2f} {a['y']:.2f} Q {e['cx']:.2f} {e['cy']:.2f} {b['x']:.2f} {b['y']:.2f}"
        parts.append(f'<path d="{d}" fill="none" stroke="{M.EDGE_COLOR_HOT}" '
                      f'stroke-width="{e["width"]:.2f}" stroke-linecap="round" opacity="{op:.3f}"/>')
    for e in model["edges"]:
        pos = K.pulse_xy(e, t_pct)
        if pos is None:
            continue
        x, y, fe = pos
        op = K.pulse_opacity(e, t_pct) * scene_op
        if op < 0.01:
            continue
        amp = max(0.85, min(1.15, 0.65 + (e["a"]["level"] + e["b"]["level"]) * 0.07))
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{3.0 * amp:.2f}" fill="#c9b6ef" opacity="{op * 0.26:.3f}" filter="url(#b1)"/>')
        trail_t = max(0.0, fe - 0.11)
        tx = K._qbez(e["a"]["x"], e["cx"], e["b"]["x"], trail_t)
        ty = K._qbez(e["a"]["y"], e["cy"], e["b"]["y"], trail_t)
        parts.append(f'<circle cx="{tx:.2f}" cy="{ty:.2f}" r="{1.6 * amp:.2f}" fill="#d8ccf5" opacity="{op * 0.18:.3f}" filter="url(#b1)"/>')
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{1.25 * amp:.2f}" fill="#f8f3ff" stroke="#e6deff" stroke-width="0.22" opacity="{op:.3f}"/>')
    for n in model["nodes"]:
        if n["active"] and n["halo"]:
            op, r = K.eval_stops(K.halo_stops(n), t_pct)
            op *= scene_op
            if op > 0.003:
                parts.append(f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{r:.2f}" '
                              f'fill="{M.PEAK_FILL[n["level"]]}" opacity="{op:.3f}" filter="url(#b1)"/>')
    for n in model["nodes"]:
        if not n["active"]:
            parts.append(f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{n["pre_r"]:.2f}" '
                          f'fill="{M.DORMANT_FILL}" opacity="{0.28*scene_op:.3f}"/>')
            continue
        op, r, fill = K.eval_stops(K.node_stops(n), t_pct, has_color=True)
        parts.append(f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{r:.2f}" '
                      f'fill="{fill}" opacity="{op*scene_op:.3f}"/>')
    if model["last_active"]:
        la = model["last_active"]
        op, r = K.eval_stops(K.resolution_stops(), t_pct)
        op *= scene_op
        if op > 0.003:
            parts.append(f'<circle cx="{la["x"]:.2f}" cy="{la["y"]:.2f}" r="{r:.2f}" '
                          f'fill="none" stroke="{M.PEAK_FILL[4]}" stroke-width="1.1" '
                          f'opacity="{op:.3f}" filter="url(#b1)"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">
  <defs>
    <radialGradient id="bgv" cx="30%" cy="35%" r="85%">
      <stop offset="0%" stop-color="{vignette}"/><stop offset="100%" stop-color="{bg}"/>
    </radialGradient>
    <filter id="b1" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.1"/></filter>
    <filter id="b2" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="6"/></filter>
  </defs>
  <rect width="{W:.0f}" height="{H:.0f}" fill="url(#bgv)"/>
  {''.join(parts)}
</svg>'''


def pil_frame(model, t_pct, scale=2, theme="dark"):
    W, H = model["width"], model["height"]
    sw, sh = int(W * scale), int(H * scale)
    bg_rgb = _hex_rgb("#0a0a0f" if theme == "dark" else "#f4f2f8")
    vignette_rgb = _hex_rgb("#15111f" if theme == "dark" else "#e7e1f2")
    img = Image.new("RGBA", (sw, sh), bg_rgb + (255,))
    draw = ImageDraw.Draw(img, "RGBA")
    scene_op = K.eval_stops(K.scene_stops(), t_pct)[0]

    def sc(v):
        return v * scale

    def alpha(op):
        return int(max(0, min(255, round(op * 255 * scene_op))))

    # clusters (ellipses)
    for group in model["clusters"]:
        xs = [n["x"] for n in group]; ys = [n["y"] for n in group]
        cx, cy = sum(xs) / len(xs), (min(ys) + max(ys)) / 2
        rx = (max(xs) - min(xs)) / 2 + 9
        ry = (max(ys) - min(ys)) / 2 + 9
        fire_pct = min(n["delay_pct"] for n in group) + 0.3
        op = K.eval_stops(K.cluster_stops(fire_pct), t_pct)[0]
        if op < 0.003:
            continue
        a = alpha(op * 0.9)
        if a < 2:
            continue
        rgb = _hex_rgb(M.EDGE_COLOR_HOT)
        draw.ellipse([sc(cx - rx), sc(cy - ry), sc(cx + rx), sc(cy + ry)], fill=rgb + (int(a * 0.35),))

    # edges (quadratic bezier tessellated)
    for e in model["edges"]:
        op = K.eval_stops(K.edge_stops(e), t_pct)[0]
        if op < 0.004:
            continue
        a = alpha(op)
        if a < 2:
            continue
        rgb = _hex_rgb(M.EDGE_COLOR_HOT)
        pts = []
        for i in range(25):
            t = i / 24
            x = K._qbez(e["a"]["x"], e["cx"], e["b"]["x"], t)
            y = K._qbez(e["a"]["y"], e["cy"], e["b"]["y"], t)
            pts.append((sc(x), sc(y)))
        draw.line(pts, fill=rgb + (a,), width=max(1, int(round(e["width"] * scale * 0.9))), joint="round")

    # discharges at destination on pulse arrival
    for e in model["edges"]:
        op, r = K.eval_stops(K.discharge_stops(e), t_pct)
        if op < 0.005:
            continue
        a = alpha(op)
        if a < 2:
            continue
        rr = r * scale
        bx, by = e["b"]["x"], e["b"]["y"]
        draw.ellipse([sc(bx) - rr, sc(by) - rr, sc(bx) + rr, sc(by) + rr], outline=_hex_rgb("#d8c8ff") + (a,), width=max(1, int(round(0.9 * scale))))

    # travelling pulses
    for e in model["edges"]:
        pos = K.pulse_xy(e, t_pct)
        if pos is None:
            continue
        x, y, fe = pos
        op = K.pulse_opacity(e, t_pct)
        if op < 0.01:
            continue
        a_core = alpha(op)
        if a_core < 3:
            continue
        amp = max(0.85, min(1.15, 0.65 + (e["a"]["level"] + e["b"]["level"]) * 0.07))
        # halo
        hr = 3.4 * amp * scale
        halo_a = alpha(op * 0.26)
        if halo_a > 2:
            draw.ellipse([sc(x) - hr, sc(y) - hr, sc(x) + hr, sc(y) + hr], fill=_hex_rgb("#c9b6ef") + (halo_a,))
        # trail
        trail_t = max(0.0, fe - 0.11)
        tx = K._qbez(e["a"]["x"], e["cx"], e["b"]["x"], trail_t)
        ty = K._qbez(e["a"]["y"], e["cy"], e["b"]["y"], trail_t)
        tr = 1.6 * amp * scale
        trail_a = alpha(op * 0.18)
        if trail_a > 2:
            draw.ellipse([sc(tx) - tr, sc(ty) - tr, sc(tx) + tr, sc(ty) + tr], fill=_hex_rgb("#d8ccf5") + (trail_a,))
        # core
        cr = 1.45 * amp * scale
        draw.ellipse([sc(x) - cr, sc(y) - cr, sc(x) + cr, sc(y) + cr], fill=_hex_rgb("#f8f3ff") + (a_core,), outline=_hex_rgb("#e6deff") + (min(255, a_core),))

    # halos under nodes
    for n in model["nodes"]:
        if n["active"] and n["halo"]:
            op, r = K.eval_stops(K.halo_stops(n), t_pct)
            if op < 0.003:
                continue
            a = alpha(op)
            if a < 2:
                continue
            rgb = _hex_rgb(M.PEAK_FILL[n["level"]])
            rr = r * scale
            # simulate blur with two concentric circles
            draw.ellipse([sc(n["x"]) - rr * 1.15, sc(n["y"]) - rr * 1.15, sc(n["x"]) + rr * 1.15, sc(n["y"]) + rr * 1.15], fill=rgb + (int(a * 0.22),))
            draw.ellipse([sc(n["x"]) - rr, sc(n["y"]) - rr, sc(n["x"]) + rr, sc(n["y"]) + rr], fill=rgb + (int(a * 0.45),))

    # nodes
    for n in model["nodes"]:
        if not n["active"]:
            a = alpha(0.28)
            rgb = _hex_rgb(M.DORMANT_FILL)
            rr = n["pre_r"] * scale
            draw.ellipse([sc(n["x"]) - rr, sc(n["y"]) - rr, sc(n["x"]) + rr, sc(n["y"]) + rr], fill=rgb + (a,))
            continue
        op, r, fill = K.eval_stops(K.node_stops(n), t_pct, has_color=True)
        a = alpha(op)
        if a < 2:
            continue
        rgb = _hex_rgb(fill)
        rr = r * scale
        draw.ellipse([sc(n["x"]) - rr, sc(n["y"]) - rr, sc(n["x"]) + rr, sc(n["y"]) + rr], fill=rgb + (a,))

    # resolution
    if model["last_active"]:
        la = model["last_active"]
        op, r = K.eval_stops(K.resolution_stops(), t_pct)
        if op > 0.003:
            a = alpha(op)
            rgb = _hex_rgb(M.PEAK_FILL[4])
            rr = r * scale
            draw.ellipse([sc(la["x"]) - rr, sc(la["y"]) - rr, sc(la["x"]) + rr, sc(la["y"]) + rr], outline=rgb + (a,), width=max(1, int(scale)))

    rgb_img = Image.new("RGB", (sw, sh), bg_rgb)
    rgb_img.paste(Image.new("RGB", (sw, sh), vignette_rgb), mask=img.split()[3] if False else None)
    # composite RGBA over solid bg
    bg = Image.new("RGB", (sw, sh), bg_rgb)
    bg.paste(img, mask=img.split()[3])
    return bg


def render_gif(model, n_frames=90, cycle_s=24.0, scale=2, out_path="dist/neural-pulse-dark.gif"):
    frames = []
    for i in range(n_frames):
        t = (i / n_frames) * 100.0
        if HAS_CAIROSVG:
            try:
                svg = frame_svg(model, t)
                png_bytes = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=int(model["width"] * scale), output_height=int(model["height"] * scale))
                img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            except Exception:
                img = pil_frame(model, t, scale=scale)
        else:
            img = pil_frame(model, t, scale=scale)
        frames.append(img)
    delay_ms = int(cycle_s * 1000 / n_frames)
    frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=delay_ms, loop=0, optimize=True)
    return out_path


def render_snapshots(model, pcts, scale=3, prefix="dist/frame"):
    paths = []
    for pct in pcts:
        if HAS_CAIROSVG:
            try:
                svg = frame_svg(model, pct)
                p = f"{prefix}_{pct:05.1f}.png"
                cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=p, output_width=int(model["width"] * scale), output_height=int(model["height"] * scale))
                paths.append(p)
                continue
            except Exception:
                pass
        img = pil_frame(model, pct, scale=scale)
        p = f"{prefix}_{pct:05.1f}.png"
        img.save(p)
        paths.append(p)
    return paths


if __name__ == "__main__":
    ds = D.generate()
    m = M.build(ds)
    render_snapshots(m, [1, 12, 34, 45, 52, 88, 91], scale=3, prefix="dist/frame")
    render_gif(m, n_frames=120, scale=2, out_path="dist/neural-pulse-dark-preview.gif")
    frames = []
    n_frames = 60
    for i in range(n_frames):
        t = (i / n_frames) * 100.0
        img = pil_frame(m, t, scale=1)
        img = img.quantize(colors=64, method=Image.MEDIANCUT)
        frames.append(img)
    delay_ms = int(24.0 * 1000 / n_frames)
    frames[0].save("dist/neural-pulse-dark.gif", save_all=True, append_images=frames[1:], duration=delay_ms, loop=0, optimize=True)
    import os
    print("preview gif:", os.path.getsize("dist/neural-pulse-dark-preview.gif") / 1024, "KB")
    print("readme gif:", os.path.getsize("dist/neural-pulse-dark.gif") / 1024, "KB")
