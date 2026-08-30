#!/usr/bin/env python3
"""Generate the articulated Percolia network bird from ``bird_model.json``.

The SVG exposes stable ``data-bone`` attributes for shoulder, elbow, wrist,
head, tail and legs. Those groups form a true 2-D rig rather than a single
flat polygon being wobbled around by CSS, which humanity had somehow decided
was animation.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source' / 'bird_model.json'

def fmt(v: float) -> str: return f'{v:g}'
def load_model() -> dict: return json.loads(SOURCE.read_text(encoding='utf-8'))

def svg_header(view_box: Iterable[float], title: str, desc: str, background: str | None = None) -> list[str]:
    x,y,w,h=view_box
    out=['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x)} {fmt(y)} {fmt(w)} {fmt(h)}" role="img" aria-labelledby="title desc" class="percolia-bird">',
         f'  <title id="title">{escape(title)}</title>', f'  <desc id="desc">{escape(desc)}</desc>']
    if background: out.append(f'  <rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="{background}"/>')
    return out

def tone(name: str, palette: dict, variant: str) -> str:
    if variant=='mono': return palette['ink']
    if variant=='inverse' and name=='ink': return palette['white']
    return palette[name]

def render_mesh(mesh: dict, prefix: str, palette: dict, variant: str, phase: int, opacity_scale: float=1.0) -> str:
    nodes=mesh['nodes']; inverse=variant=='inverse'; mono=variant=='mono'
    base=palette['white'] if inverse else palette['ink']
    edge_styles={'mesh':(1.05,base,.80),'outline':(1.55,base,.94),'critical':(1.85,palette['blue'] if not mono else palette['ink'],1.0)}
    out=[f'      <g id="{prefix}-faces" data-layer="faces">']
    for fid, ids, fill, opacity in mesh.get('faces',[]):
        pts=' '.join(f'{fmt(nodes[n][0])},{fmt(nodes[n][1])}' for n in ids)
        out.append(f'        <polygon id="{prefix}-{escape(fid)}" points="{pts}" fill="{tone(fill,palette,variant)}" fill-opacity="{fmt(opacity*opacity_scale)}" data-phase="{phase}" data-anim="face"/>')
    out.append('      </g>')
    out.append(f'      <g id="{prefix}-edges" data-layer="edges" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for i,(a,b,kind) in enumerate(mesh.get('edges',[]),1):
        x1,y1=nodes[a][:2]; x2,y2=nodes[b][:2]; width,stroke,opacity=edge_styles[kind]
        out.append(f'        <line id="{prefix}-edge-{i:02d}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{stroke}" stroke-width="{fmt(width)}" stroke-opacity="{fmt(opacity*opacity_scale)}" data-phase="{phase}" data-anim="edge" data-kind="{kind}" vector-effect="non-scaling-stroke"/>')
    out.append('      </g>')
    out.append(f'      <g id="{prefix}-nodes" data-layer="nodes">')
    for nid,(x,y,r,fill,kind) in nodes.items():
        node_stroke=palette['ink'] if inverse else palette['white']
        if mono: node_stroke=palette['white']
        out.append(f'        <circle id="{prefix}-node-{escape(nid)}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{tone(fill,palette,variant)}" fill-opacity="{fmt(opacity_scale)}" stroke="{node_stroke}" stroke-opacity="{fmt(opacity_scale)}" stroke-width="0.65" data-phase="{phase}" data-anim="node" data-kind="{kind}" vector-effect="non-scaling-stroke"/>')
    out.append('      </g>')
    return '\n'.join(out)

def render_wing(model: dict, side: str, variant: str, pose: tuple[float,float,float], opacity: float) -> str:
    palette=model['palette']; rig=model['rig']; shoulder=rig[f'shoulder_{side}']; elbow=rig['elbow']; wrist=rig['wrist']
    ua,fa,ha=pose; mirror=' scale(1 -0.82)' if side=='far' else ''
    phase=0 if side=='far' else 3
    return '\n'.join([
        f'    <g id="wing-{side}" class="bird-wing bird-wing-{side}" data-side="{side}" transform="translate({fmt(shoulder[0])} {fmt(shoulder[1])}){mirror}" opacity="{fmt(opacity)}">',
        f'      <g id="wing-{side}-upper" data-bone="wing-{side}-upper" transform="rotate({fmt(ua)})">',
        render_mesh(model['wing']['upper'],f'wing-{side}-upper',palette,variant,phase,1),
        f'        <g id="wing-{side}-forearm" data-bone="wing-{side}-forearm" transform="translate({fmt(elbow[0])} {fmt(elbow[1])}) rotate({fmt(fa)})">',
        render_mesh(model['wing']['forearm'],f'wing-{side}-forearm',palette,variant,phase+1,1),
        f'          <g id="wing-{side}-hand" data-bone="wing-{side}-hand" transform="translate({fmt(wrist[0])} {fmt(wrist[1])}) rotate({fmt(ha)})">',
        render_mesh(model['wing']['hand'],f'wing-{side}-hand',palette,variant,phase+2,1),
        '          </g>','        </g>','      </g>','    </g>'
    ])

def render_legs(model: dict, variant: str, folded: bool) -> str:
    p=model['palette']; stroke=p['white'] if variant=='inverse' else p['ink']
    if variant=='mono': stroke=p['ink']
    out=['    <g id="bird-legs" data-layer="legs" fill="none" stroke-linecap="round" stroke-linejoin="round">']
    for side,leg in model['legs'].items():
        hip,knee,ankle=leg['hip'],leg['knee'],leg['ankle']; rot=-42 if folded else 0; opacity=.46 if side=='far' else .88
        out.append(f'      <g id="leg-{side}" data-bone="leg-{side}" transform="rotate({rot} {fmt(hip[0])} {fmt(hip[1])})" opacity="{opacity}">')
        out.append(f'        <polyline points="{fmt(hip[0])},{fmt(hip[1])} {fmt(knee[0])},{fmt(knee[1])} {fmt(ankle[0])},{fmt(ankle[1])}" stroke="{stroke}" stroke-width="1.45" vector-effect="non-scaling-stroke"/>')
        out.append(f'        <circle cx="{fmt(knee[0])}" cy="{fmt(knee[1])}" r="1.35" fill="{p["blue"] if variant!="mono" else stroke}" stroke="none"/>')
        for tx,ty in leg['toes']:
            out.append(f'        <line x1="{fmt(ankle[0])}" y1="{fmt(ankle[1])}" x2="{fmt(tx)}" y2="{fmt(ty)}" stroke="{stroke}" stroke-width="1.05" vector-effect="non-scaling-stroke"/>')
        out.append('      </g>')
    out.append('    </g>')
    return '\n'.join(out)

def render_scatter(model: dict, variant: str) -> str:
    p=model['palette']; dots=[(-151,-76,1.0,'ink'),(-139,-51,1.25,'blue'),(-122,-103,.8,'cyan'),(-103,-118,1.0,'ink'),(-86,-89,.75,'blue'),(-145,48,1.0,'cyan'),(-121,62,.75,'ink'),(-96,53,1.15,'blue')]
    out=['    <g id="bird-scatter" data-layer="scatter" opacity="0.46">']
    for i,(x,y,r,c) in enumerate(dots,1): out.append(f'      <circle id="scatter-{i:02d}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{tone(c,p,variant)}" data-anim="scatter"/>')
    out.append('    </g>'); return '\n'.join(out)

def render_bird(model: dict, variant: str, pose_name: str, compact: bool=False) -> str:
    p=model['palette']; pose=model['poses'][pose_name]; background=p['ink'] if variant=='inverse' else None
    view_box=[-112,-54,222,104] if compact else model['viewBox']
    out=svg_header(view_box,'Oiseau-réseau articulé Percolia','Un martinet géométrique articulé, composé de facettes et animé par un squelette 2-D.',background)
    out.append(
        f'  <g id="percolia-bird" data-percolia-bird="true" data-model-version="{escape(model["version"])}" '
        f'data-elbow="{fmt(model["rig"]["elbow"][0])},{fmt(model["rig"]["elbow"][1])}" '
        f'data-wrist="{fmt(model["rig"]["wrist"][0])},{fmt(model["rig"]["wrist"][1])}" '
        f'data-hip-near="{fmt(model["rig"]["hip_near"][0])},{fmt(model["rig"]["hip_near"][1])}" '
        f'data-hip-far="{fmt(model["rig"]["hip_far"][0])},{fmt(model["rig"]["hip_far"][1])}">'
    )
    if not compact: out.append(render_scatter(model,variant))
    out.append(render_wing(model,'far',variant,tuple(pose['far']),0.0 if compact else .38))
    out.append(f'    <g id="bird-tail" data-bone="tail" transform="rotate({fmt(pose["tail"])} -44 6)">')
    out.append(render_mesh(model['tail'],'tail',p,variant,1,.94)); out.append('    </g>')
    out.append(f'    <g id="bird-body" data-bone="body" transform="rotate({fmt(pose["body"])} -5 2)">')
    out.append(render_mesh(model['body'],'body',p,variant,2,1)); out.append('    </g>')
    full_wing_opacity = 0.0 if compact else 0.92
    folded_opacity = 0.96 if compact else 0.0
    out.append(f'    <g id="folded-wing" data-bone="folded-wing" opacity="{fmt(folded_opacity)}">')
    out.append(render_mesh(model['folded_wing'],'folded-wing',p,variant,3,1)); out.append('    </g>')
    out.append(render_wing(model,'near',variant,tuple(pose['near']),full_wing_opacity))
    out.append('    <g id="bird-head" data-bone="head">')
    out.append(render_mesh(model['head'],'head',p,variant,6,1))
    sx,sy=model['rig']['scan_origin']; out.append(f'      <circle id="scan-origin" data-scan-origin="true" cx="{fmt(sx)}" cy="{fmt(sy)}" r="0.1" fill="none"/>')
    out.append('    </g>')
    out.append(f'    <g id="lidar-scan" data-layer="lidar" transform="translate({fmt(sx)} {fmt(sy)})" opacity="0" pointer-events="none">')
    out.append('      <g id="lidar-sweep" data-bone="lidar-sweep">')
    out.append(f'        <path d="M 0 0 L 68 -12 A 69 69 0 0 1 68 12 Z" fill="{p["cyan"]}" fill-opacity="0.13"/>')
    out.append(f'        <line x1="0" y1="0" x2="72" y2="0" stroke="{p["blue"]}" stroke-width="1.35" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
    out.append('      </g>')
    out.append(f'      <circle id="lidar-return" cx="75" cy="0" r="2.7" fill="{p["cyan"]}" opacity="0"/>')
    out.append(f'      <circle id="lidar-ring" cx="75" cy="0" r="3" fill="none" stroke="{p["cyan"]}" stroke-width="1.1" opacity="0" vector-effect="non-scaling-stroke"/>')
    out.append('    </g>')
    out.append(render_legs(model,variant,pose_name!='perched'))
    out.append('  </g>'); out.extend(['</svg>',''])
    return '\n'.join(out)

def main() -> None:
    m=load_model(); outputs={
        'percolia-bird-primary.svg':render_bird(m,'primary','glide'),
        'percolia-bird-mono.svg':render_bird(m,'mono','glide'),
        'percolia-bird-inverse.svg':render_bird(m,'inverse','glide'),
        'percolia-bird-compact.svg':render_bird(m,'primary','perched',True),
    }
    for name,content in outputs.items():
        (ROOT/name).write_text(content,encoding='utf-8'); print(f'wrote {name}')

if __name__=='__main__': main()
