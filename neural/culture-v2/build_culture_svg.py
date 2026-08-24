import culture_model as CM
import culture_keyframes as K
CYCLE_S=24.0
def css_rule(name,stops,props):
    lines=[]
    for row in stops:
        pct=row[0]
        vals=row[1:]
        decls="; ".join(f"{p}:{v}px" if p=="r" else f"{p}:{v}" for p,v in zip(props,vals))
        lines.append(f"  {pct}% {{ {decls}; }}")
    return f"@keyframes {name} {{\n"+"\n".join(lines)+"\n}"
def pulse_rule(name,stops):
    lines=[]
    for pct,off,op in stops:
        lines.append(f"  {pct:.3f}% {{ offset-distance:{off:.2f}%; opacity:{op:.3f}; }}")
    return f"@keyframes {name} {{\n"+"\n".join(lines)+"\n}"
def build(model, theme="dark"):
    W,H=model["width"],model["height"]
    bg="#090a0f" if theme=="dark" else "#f4f2f8"
    vignette="#17131f" if theme=="dark" else "#e7e1f2"
    css=[]
    dend_els=[]; axon_els=[]; pulse_els=[]; discharge_els=[]; halo_els=[]; soma_els=[]; cluster_els=[]
    for ax in model["axons"]:
        css.append(css_rule(f"axon_{ax['id']}", K.axon_stops(ax), ["opacity"]))
        d=f"M {ax['sx']:.2f} {ax['sy']:.2f} Q {ax['cx']:.2f} {ax['cy']:.2f} {ax['ex']:.2f} {ax['ey']:.2f}"
        axon_els.append(f'<path d="{d}" class="axon tier{ax["tier"]}" stroke-width="{ax["width"]:.2f}" style="animation-name: axon_{ax["id"]}"/>')
        css.append(pulse_rule(f"pulse_{ax['id']}", K.pulse_stops(ax)))
        css.append(pulse_rule(f"pulse_h_{ax['id']}", K.pulse_halo_stops(ax)))
        css.append(css_rule(f"dis_{ax['id']}", K.discharge_stops(ax), ["opacity","r"]))
        discharge_els.append(f'<circle cx="{ax["ex"]:.2f}" cy="{ax["ey"]:.2f}" r="2.1" class="discharge" style="animation-name: dis_{ax["id"]}"/>')
        path_esc=d.replace('"','&quot;')
        begin=ax["travel_start"]/100*CYCLE_S
        dur=ax["travel_dur"]/100*CYCLE_S
        amp=max(0.85,min(1.15,0.65+(ax["a"]["level"]+ax["b"]["level"])*0.07))
        pulse_els.append(f'<circle r="{1.35*amp:.2f}" class="pulse-halo" style="offset-path:path(\'{d}\'); animation-name:pulse_h_{ax["id"]}">'
                         f'<animateMotion path="{path_esc}" begin="{begin:.3f}s" dur="{dur:.3f}s" repeatCount="indefinite" rotate="auto" calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/></circle>')
        pulse_els.append(f'<circle r="{1.05*amp:.2f}" class="pulse-core" style="offset-path:path(\'{d}\'); animation-name:pulse_{ax["id"]}">'
                         f'<animateMotion path="{path_esc}" begin="{begin:.3f}s" dur="{dur:.3f}s" repeatCount="indefinite" rotate="auto" calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/></circle>')
    for n in model["neurons"]:
        for di, den in enumerate(n["dendrites"]):
            css.append(css_rule(f"den_{n['id']}_{di}", K.dendrite_stops(n), ["opacity"]))
            d=f"M {n['x']:.2f} {n['y']:.2f} Q {den['cx']:.2f} {den['cy']:.2f} {den['x2']:.2f} {den['y2']:.2f}"
            dend_els.append(f'<path d="{d}" class="dendrite" stroke-width="{den["width"]:.2f}" style="animation-name: den_{n["id"]}_{di}"/>')
            if den["fork"]:
                fk=den["fork"]
                d2=f"M {den['x2']:.2f} {den['y2']:.2f} Q {fk['cx']:.2f} {fk['cy']:.2f} {fk['x2']:.2f} {fk['y2']:.2f}"
                dend_els.append(f'<path d="{d2}" class="dendrite fork" stroke-width="{fk["width"]:.2f}" style="animation-name: den_{n["id"]}_{di}"/>')
            if den.get("fork2"):
                fk2=den["fork2"]
                d3=f"M {den['x2']:.2f} {den['y2']:.2f} Q {fk2['cx']:.2f} {fk2['cy']:.2f} {fk2['x2']:.2f} {fk2['y2']:.2f}"
                dend_els.append(f'<path d="{d3}" class="dendrite fork fork2" stroke-width="{fk2["width"]:.2f}" style="animation-name: den_{n["id"]}_{di}"/>')
    for idx, grp in enumerate(model["clusters"]):
        xs=[n["x"] for n in grp]; ys=[n["y"] for n in grp]
        cx=sum(xs)/len(xs); cy=(min(ys)+max(ys))/2
        rx=(max(xs)-min(xs))/2+14; ry=(max(ys)-min(ys))/2+14
        fire=min(n["delay_pct"] for n in grp)+0.3
        css.append(css_rule(f"cluster_{idx}", K.cluster_stops(fire), ["opacity"]))
        cluster_els.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" class="cluster" style="animation-name: cluster_{idx}"/>')
    for n in model["neurons"]:
        css.append(css_rule(f"soma_{n['id']}", K.soma_stops(n), ["opacity","r","fill"]))
        if n["halo"]:
            css.append(css_rule(f"halo_{n['id']}", K.halo_stops(n), ["opacity","r"]))
            halo_els.append(f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{n["soma_floor_r"]:.2f}" class="halo" style="animation-name: halo_{n["id"]}"/>')
        soma_els.append(f'<circle cx="{n["x"]:.2f}" cy="{n["y"]:.2f}" r="{n["soma_r"]:.2f}" class="soma" style="animation-name: soma_{n["id"]}"/>')
    if model["last_neuron"]:
        css.append(css_rule("resolution", K.resolution_stops(), ["opacity","r"]))
        la=model["last_neuron"]
        res_el=f'<circle cx="{la["x"]:.2f}" cy="{la["y"]:.2f}" r="6" class="resolution" style="animation-name: resolution"/>'
    else:
        res_el=""
    css.append(css_rule("scene_fade", K.scene_stops(), ["opacity"]))
    style=f""".scene {{ animation: scene_fade {CYCLE_S}s linear infinite; }}
.dormant {{ fill:{CM.DORMANT_FILL}; }}
.soma, .halo, .axon, .dendrite, .cluster, .resolution, .discharge {{ animation-duration:{CYCLE_S}s; animation-timing-function:linear; animation-iteration-count:infinite; }}
.halo {{ filter:url(#soft-blur); }}
.axon {{ fill:none; stroke:{CM.COLOR_AXON_REST}; stroke-linecap:round; }}
.axon.tier3 {{ stroke:{CM.COLOR_PLASTICITY_VIOLET}; }}
.dendrite {{ fill:none; stroke:{CM.COLOR_DENDRITE_REST}; stroke-linecap:round; opacity:0.92; }}
.fork {{ opacity:0.86; }}
.cluster {{ fill:{CM.COLOR_PLASTICITY_VIOLET}; filter:url(#soft-blur-lg); }}
.resolution {{ fill:none; stroke:{CM.COLOR_ACTIVE_CORAL_BRIGHT}; stroke-width:1.15; filter:url(#soft-blur); }}
.discharge {{ fill:none; stroke:{CM.COLOR_PLASTICITY_SOFT}; stroke-width:0.9; filter:url(#soft-blur); }}
.pulse-core {{ fill:{CM.COLOR_ELECTRICAL_WHITE}; stroke:{CM.COLOR_ELECTRICAL_CYAN}; stroke-width:0.30; }}
.pulse-halo {{ fill:{CM.COLOR_PLASTICITY_SOFT}; filter:url(#soft-blur); }}
.pulse-core, .pulse-halo {{ offset-rotate:auto; offset-anchor:center; animation-duration:{CYCLE_S}s; animation-timing-function:linear; animation-iteration-count:infinite; }}
.axon.tier1 {{ opacity:0.95; }}
.axon.tier2 {{ opacity:1; }}
.axon.tier3 {{ opacity:1; }}
{''.join(css)}"""
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cultured neuronal network from contribution activity">
<title>Neural culture</title>
<defs>
<radialGradient id="bg-vignette" cx="32%" cy="38%" r="88%"><stop offset="0%" stop-color="{vignette}"/><stop offset="100%" stop-color="{bg}"/></radialGradient>
<filter id="soft-blur" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.2"/></filter>
<filter id="soft-blur-lg" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="7"/></filter>
</defs>
<style>{style}</style>
<rect width="{W}" height="{H}" fill="url(#bg-vignette)"/>
<g class="scene">
<g class="clusters">{''.join(cluster_els)}</g>
<g class="axons">{''.join(axon_els)}</g>
<g class="dendrites">{''.join(dend_els)}</g>
<g class="discharges">{''.join(discharge_els)}</g>
<g class="pulses">{''.join(pulse_els)}</g>
<g class="halos">{''.join(halo_els)}</g>
<g class="somas">{''.join(soma_els)}</g>
{res_el}
</g>
</svg>'''
    return svg
if __name__=="__main__":
    import data as D
    ds=D.generate()
    m=CM.build(ds)
    svg=build(m)
    open("dist/neural-culture-dark.svg","w").write(svg)
    print(f"wrote dist/neural-culture-dark.svg {len(svg)/1024:.1f}KB {len(m['neurons'])} neurons {len(m['axons'])} axons")
