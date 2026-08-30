#!/usr/bin/env python3
"""Generate the Percolia wordmark: full-size P, small-cap ERCOLIA."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source'/'geometry.json'
NS='http://www.w3.org/2000/svg'

def load_geometry()->dict[str,Any]: return json.loads(SOURCE.read_text(encoding='utf-8'))
def esc(text:str)->str: return text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
def svg_header(width:float,height:float,title:str,desc:str,viewbox:str|None=None)->str:
    vb=viewbox or f'0 0 {width:g} {height:g}'
    return f'<svg xmlns="{NS}" viewBox="{vb}" role="img" aria-labelledby="title desc">\n  <title id="title">{esc(title)}</title>\n  <desc id="desc">{esc(desc)}</desc>\n'
def style_block()->str:
    return '''  <style>
    .glyph-path{fill:none;stroke:#082C4C;stroke-width:14;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
    .glyph-node{vector-effect:non-scaling-stroke}.tone-ink{fill:#082C4C}.tone-blue{fill:#1C83D4}.tone-cyan{fill:#20C9C4}
  </style>\n'''
def render_glyph(letter:str,spec:dict[str,Any],x:float=0,y:float=0,*,mono=False,scale=1.0,gid:str|None=None)->str:
    group_id=gid or f'glyph-{letter}'
    transform=f'translate({x:g} {y:g})'+(f' scale({scale:g})' if scale!=1 else '')
    out=[f'  <g id="{group_id}" data-glyph="{letter}" transform="{transform}">']
    for i,path in enumerate(spec.get('paths',[]),1): out.append(f'    <path id="{group_id}-stroke-{i}" class="glyph-path" d="{path}"/>')
    for i,node in enumerate(spec.get('nodes',[]),1):
        tone='ink' if mono else node.get('tone','ink')
        out.append(f'    <circle id="{group_id}-node-{i}" class="glyph-node tone-{tone}" data-role="{node.get("role","node")}" cx="{node["cx"]}" cy="{node["cy"]}" r="{node["r"]}"/>')
    out.append('  </g>'); return '\n'.join(out)
def placements(data):
    tracking=data['units']['tracking']; scale=data['units']['small_caps_scale']; baseline=data['units']['baseline']
    shift=baseline*(1-scale); x=20.0; out=[]
    for i,letter in enumerate(data['wordmark']):
        glyph_scale=1.0 if i==0 else scale
        y=0 if i==0 else shift
        out.append((letter,x,y,glyph_scale))
        x += data['glyphs'][letter]['advance']*glyph_scale
        if i<len(data['wordmark'])-1: x += tracking
    return int(x+20),data['units']['canvas_height'],out
def write_wordmark(data,mono=False):
    width,height,items=placements(data); suffix='mono' if mono else 'primary'; out=ROOT/f'percolia-wordmark-{suffix}.svg'
    parts=[svg_header(width,height,f'Percolia wordmark — {suffix}','Full-size distinctive P followed by geometric small capitals.'),style_block(),f'  <g id="percolia-wordmark" data-version="{data["version"]}" data-style="small-caps">']
    for idx,(letter,x,y,scale) in enumerate(items,1): parts.append(render_glyph(letter,data['glyphs'][letter],x=x,y=y,scale=scale,gid=f'letter-{idx}-{letter}',mono=mono))
    parts += ['  </g>','</svg>','']; out.write_text('\n'.join(parts),encoding='utf-8'); return out
def write_monogram(data,mono=False):
    suffix='mono' if mono else 'primary'; out=ROOT/f'percolia-p-monogram-{suffix}.svg'; sb=style_block().replace('stroke-width:14','stroke-width:18')
    parts=[svg_header(256,256,f'Percolia P monogram — {suffix}','Standalone custom P with two threshold nodes.','0 0 256 256'),sb,'  <g id="percolia-p-monogram" transform="translate(38 0) scale(1.35)">',render_glyph('P',data['glyphs']['P'],mono=mono,gid='percolia-p'),'  </g>','</svg>','']
    out.write_text('\n'.join(parts),encoding='utf-8'); return out
def write_inverse(source:Path,target:Path):
    target.write_text(source.read_text(encoding='utf-8').replace('primary','inverse').replace('#082C4C','#FFFFFF'),encoding='utf-8'); return target
def write_glyph_sheet(data):
    out=ROOT/'percolia-glyph-sheet.svg'; letters=list(data['wordmark']); cell_w,cell_h,cols=280,300,4; rows=(len(letters)+cols-1)//cols; width,height=cols*cell_w,rows*cell_h+90
    parts=[svg_header(width,height,'Percolia Display glyph sheet','Construction sheet for the custom letters used in Percolia.'),style_block(),'''  <style>.sheet-bg{fill:#fff}.cell{fill:none;stroke:#DDE9EE}.guide{stroke:#D4E4EA;stroke-dasharray:4 5}.sheet-label{fill:#5D7385;font:600 18px system-ui,sans-serif}.sheet-title{fill:#082C4C;font:700 28px system-ui,sans-serif}</style>''',f'  <rect class="sheet-bg" width="{width}" height="{height}"/>','  <text class="sheet-title" x="40" y="48">PERCOLIA DISPLAY — SMALL-CAPS WORDMARK v0.2</text>']
    for i,letter in enumerate(letters):
        col,row=i%cols,i//cols; x0,y0=col*cell_w,90+row*cell_h
        parts += [f'  <g id="cell-{i+1}-{letter}" transform="translate({x0} {y0})">','    <rect class="cell" x="12" y="12" width="256" height="276" rx="16"/>','    <line class="guide" x1="22" y1="70" x2="250" y2="70"/>','    <line class="guide" x1="22" y1="204" x2="250" y2="204"/>',render_glyph(letter,data['glyphs'][letter],x=65,y=32,gid=f'sheet-{i+1}-{letter}'),f'    <text class="sheet-label" x="28" y="268">{letter} · advance {data["glyphs"][letter]["advance"]}</text>','  </g>']
    parts += ['</svg>','']; out.write_text('\n'.join(parts),encoding='utf-8'); return out
def main():
    data=load_geometry(); pw=write_wordmark(data); pp=write_monogram(data)
    paths=[pw,write_wordmark(data,True),pp,write_monogram(data,True),write_inverse(pw,ROOT/'percolia-wordmark-inverse.svg'),write_inverse(pp,ROOT/'percolia-p-monogram-inverse.svg'),write_glyph_sheet(data)]
    for path in paths: print(path.name)
if __name__=='__main__': main()
