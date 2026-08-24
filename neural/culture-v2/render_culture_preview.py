from PIL import Image, ImageDraw
import culture_model as CM
import culture_keyframes as K
import data as D
def _hex(h):
    h=h.lstrip("#")
    return int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
def pil_frame(model,t,scale=2):
    W,H=model["width"],model["height"]
    sw,sh=int(W*scale),int(H*scale)
    bg=_hex("#090a0f")
    img=Image.new("RGBA",(sw,sh),bg+(255,))
    draw=ImageDraw.Draw(img,"RGBA")
    scene=K.eval_stops(K.scene_stops(),t)[0]
    def sc(v): return v*scale
    def alpha(o): return int(max(0,min(255,round(o*255*scene))))
    # clusters
    for grp in model["clusters"]:
        xs=[n["x"] for n in grp]; ys=[n["y"] for n in grp]
        cx=sum(xs)/len(xs); cy=(min(ys)+max(ys))/2
        rx=(max(xs)-min(xs))/2+14; ry=(max(ys)-min(ys))/2+14
        fire=min(n["delay_pct"] for n in grp)+0.3
        op=K.eval_stops(K.cluster_stops(fire),t)[0]
        if op<0.003: continue
        a=alpha(op*0.9)
        if a<2: continue
        draw.ellipse([sc(cx-rx),sc(cy-ry),sc(cx+rx),sc(cy+ry)], fill=_hex(CM.COLOR_PLASTICITY_VIOLET)+(int(a*0.28),))
    # axons - tiered + growth partial
    for ax in model["axons"]:
        op=K.eval_stops(K.axon_stops(ax),t)[0]
        if op<0.004: continue
        a=alpha(op)
        if a<2: continue
        gf=K.axon_growth_frac(ax, t)
        if gf < 0.01: continue
        n_pts = max(6, int(26 * gf))
        pts=[]
        for i in range(n_pts):
            tt=(i/(n_pts-1) if n_pts>1 else 0) * gf
            x=K._qbez(ax["sx"],ax["cx"],ax["ex"],tt)
            y=K._qbez(ax["sy"],ax["cy"],ax["ey"],tt)
            pts.append((sc(x),sc(y)))
        # terminal bouton growing with axon
        ax_col = CM.COLOR_PLASTICITY_VIOLET if ax["tier"]==3 else CM.COLOR_AXON_REST
        draw.line(pts, fill=_hex(ax_col)+(a,), width=max(1,int(round(ax["width"]*scale*0.88))), joint="round")
        if gf > 0.72:
            term_a = alpha(op * max(0, (gf-0.72)/0.28))
            if term_a > 3:
                tr = ax.get("terminal_r", 1.9) * scale * (0.55 + gf*0.45)
                draw.ellipse([sc(ax["ex"])-tr, sc(ax["ey"])-tr, sc(ax["ex"])+tr, sc(ax["ey"])+tr], fill=_hex(ax_col)+(int(term_a*0.42),), outline=_hex(CM.COLOR_PLASTICITY_SOFT)+(int(term_a*0.62),))
    # dendrites - growth partial + asymmetric forks
    for n in model["neurons"]:
        op=K.eval_stops(K.dendrite_stops(n),t)[0]
        if op<0.004: continue
        a=alpha(op)
        if a<2: continue
        gf=K.dendrite_growth_frac(n, t)
        if gf < 0.01: continue
        for den in n["dendrites"]:
            n_seg = max(6, int(18 * gf))
            pts=[]
            for i in range(n_seg):
                tt=(i/(n_seg-1) if n_seg>1 else 0) * gf
                x=K._qbez(n["x"],den["cx"],den["x2"],tt)
                y=K._qbez(n["y"],den["cy"],den["y2"],tt)
                pts.append((sc(x),sc(y)))
            draw.line(pts, fill=_hex(CM.COLOR_DENDRITE_REST)+(a,), width=max(1,int(round(den["width"]*scale*0.75))), joint="round")
            if den["fork"] and gf > 0.62:
                fk=den["fork"]
                fa=alpha(op * max(0, (gf-0.62)/0.38))
                if fa>2:
                    pts2=[]
                    for i in range(14):
                        tt=i/13
                        x=K._qbez(den["x2"],fk["cx"],fk["x2"],tt)
                        y=K._qbez(den["y2"],fk["cy"],fk["y2"],tt)
                        pts2.append((sc(x),sc(y)))
                    draw.line(pts2, fill=_hex(CM.COLOR_DENDRITE_REST)+(int(fa*0.82),), width=max(1,int(round(fk["width"]*scale*0.70))), joint="round")
                if den.get("fork2") and gf > 0.78:
                    fk2=den["fork2"]
                    fa2=alpha(op * max(0, (gf-0.78)/0.22))
                    if fa2>2:
                        pts3=[]
                        for i in range(12):
                            tt=i/11
                            x=K._qbez(den["x2"],fk2["cx"],fk2["x2"],tt)
                            y=K._qbez(den["y2"],fk2["cy"],fk2["y2"],tt)
                            pts3.append((sc(x),sc(y)))
                        draw.line(pts3, fill=_hex(CM.COLOR_DENDRITE_REST)+(int(fa2*0.74),), width=max(1,int(round(fk2["width"]*scale*0.62))), joint="round")
    # discharges
    for ax in model["axons"]:
        op,r=K.eval_stops(K.discharge_stops(ax),t)
        if op<0.005: continue
        a=alpha(op)
        if a<2: continue
        rr=r*scale
        draw.ellipse([sc(ax["ex"])-rr,sc(ax["ey"])-rr,sc(ax["ex"])+rr,sc(ax["ey"])+rr], outline=_hex(CM.COLOR_PLASTICITY_SOFT)+(a,), width=max(1,int(scale*0.9)))
    # pulses
    for ax in model["axons"]:
        pos=K.pulse_xy(ax,t)
        if not pos: continue
        x,y,fe=pos
        op=K.pulse_opacity(ax,t)
        if op<0.01: continue
        ac=alpha(op)
        if ac<3: continue
        amp=max(0.85,min(1.15,0.65+(ax["a"]["level"]+ax["b"]["level"])*0.07))
        hr=3.4*amp*scale
        ha=alpha(op*0.26)
        if ha>2:
            draw.ellipse([sc(x)-hr,sc(y)-hr,sc(x)+hr,sc(y)+hr], fill=_hex(CM.COLOR_PLASTICITY_SOFT)+(ha,))
        tr=1.6*amp*scale
        trail=max(0,fe-0.11)
        tx=K._qbez(ax["sx"],ax["cx"],ax["ex"],trail)
        ty=K._qbez(ax["sy"],ax["cy"],ax["ey"],trail)
        ta=alpha(op*0.18)
        if ta>2:
            draw.ellipse([sc(tx)-tr,sc(ty)-tr,sc(tx)+tr,sc(ty)+tr], fill=_hex(CM.COLOR_ELECTRICAL_CYAN)+(ta,))
        cr=1.45*amp*scale
        draw.ellipse([sc(x)-cr,sc(y)-cr,sc(x)+cr,sc(y)+cr], fill=_hex(CM.COLOR_ELECTRICAL_WHITE)+(ac,), outline=_hex(CM.COLOR_ELECTRICAL_CYAN)+(min(255,ac),))
    # halos
    for n in model["neurons"]:
        if not n["halo"]: continue
        op,r=K.eval_stops(K.halo_stops(n),t)
        if op<0.003: continue
        a=alpha(op)
        if a<2: continue
        rgb=_hex(CM.PEAK_FILL[n["level"]])
        rr=r*scale
        draw.ellipse([sc(n["x"])-rr*1.15,sc(n["y"])-rr*1.15,sc(n["x"])+rr*1.15,sc(n["y"])+rr*1.15], fill=rgb+(int(a*0.20),))
        draw.ellipse([sc(n["x"])-rr,sc(n["y"])-rr,sc(n["x"])+rr,sc(n["y"])+rr], fill=rgb+(int(a*0.42),))
    # somas
    for n in model["neurons"]:
        op,r,fill=K.eval_stops(K.soma_stops(n),t,has_color=True)
        a=alpha(op)
        if a<2: continue
        rgb=_hex(fill)
        rr=r*scale
        draw.ellipse([sc(n["x"])-rr,sc(n["y"])-rr,sc(n["x"])+rr,sc(n["y"])+rr], fill=rgb+(a,))
        # soma highlight
        hr=rr*0.38
        draw.ellipse([sc(n["x"])-hr+rr*0.18,sc(n["y"])-hr-rr*0.18,sc(n["x"])+hr+rr*0.18,sc(n["y"])+hr-rr*0.18], fill=(255,255,255,int(a*0.10)))
    if model["last_neuron"]:
        la=model["last_neuron"]
        op,r=K.eval_stops(K.resolution_stops(),t)
        if op>0.003:
            a=alpha(op)
            draw.ellipse([sc(la["x"])-r*scale,sc(la["y"])-r*scale,sc(la["x"])+r*scale,sc(la["y"])+r*scale], outline=_hex(CM.PEAK_FILL[4])+(a,), width=max(1,int(scale)))
    bg_img=Image.new("RGB",(sw,sh),bg)
    bg_img.paste(img, mask=img.split()[3])
    return bg_img

def render_gif(model, n_frames=120, scale=2, out="dist/neural-culture-preview.gif"):
    frames=[]
    for i in range(n_frames):
        t=i/n_frames*100
        frames.append(pil_frame(model,t,scale))
    delay=int(24.0*1000/n_frames)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=delay, loop=0, optimize=True)
    return out

def render_snapshots(model, pcts, scale=3, prefix="dist/frame"):
    paths=[]
    for pct in pcts:
        img=pil_frame(model,pct,scale)
        p=f"{prefix}_{pct:05.1f}.png"
        img.save(p)
        paths.append(p)
    return paths

if __name__=="__main__":
    ds=D.generate()
    m=CM.build(ds)
    render_snapshots(m, [1,15,35,50,65,85,95], scale=3, prefix="dist/frame")
    # close-up around central cluster (2-4 neurons)
    # pick neurons near center (week 32-38, y 150-280)
    cand=[n for n in m["neurons"] if 30 <= n["week"] <= 38]
    cand.sort(key=lambda n: n["activity"], reverse=True)
    focus=cand[:3] if len(cand)>=3 else m["neurons"][12:15]
    xs=[n["x"] for n in focus]; ys=[n["y"] for n in focus]
    cx=sum(xs)/len(xs); cy=sum(ys)/len(ys)
    # render high-res close-up by cropping
    for pct in [65, 85]:
        img=pil_frame(m, pct, scale=4)
        sw,sh=img.size
        # crop 420x320 around cx,cy
        W,H=m["width"],m["height"]
        scale=4
        cx_px=int(cx*scale); cy_px=int(cy*scale)
        left=max(0, cx_px-310); top=max(0, cy_px-240)
        right=min(sw, left+620); bottom=min(sh, top+480)
        crop=img.crop((left, top, right, bottom))
        crop.save(f"dist/closeup_{pct:.0f}.png")
        print(f"closeup {pct}% at {cx:.0f},{cy:.0f}")
    render_gif(m, n_frames=120, scale=2, out="dist/neural-culture-preview.gif")
    frames=[]
    n_frames=60
    for i in range(n_frames):
        t=i/n_frames*100
        img=pil_frame(m,t,scale=1)
        img=img.quantize(colors=96, method=Image.MEDIANCUT)
        frames.append(img)
    delay=int(24*1000/n_frames)
    frames[0].save("dist/neural-culture.gif", save_all=True, append_images=frames[1:], duration=delay, loop=0, optimize=True)
    import os
    print("preview",os.path.getsize("dist/neural-culture-preview.gif")/1024,"KB")
    print("gif",os.path.getsize("dist/neural-culture.gif")/1024,"KB")
