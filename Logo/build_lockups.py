#!/usr/bin/env python3
"""Compose static Percolia signatures from the generated SVG sources."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
SVG_NS='http://www.w3.org/2000/svg'
ET.register_namespace('',SVG_NS)

def extract(path:Path, element_id:str)->tuple[str,str]:
    text=path.read_text(encoding='utf-8')
    styles='\n'.join(re.findall(r'<style>(.*?)</style>',text,flags=re.S))
    root=ET.fromstring(text)
    found=None
    for element in root.iter():
        if element.attrib.get('id')==element_id:
            found=element; break
    if found is None: raise ValueError(f'{element_id!r} not found in {path}')
    return styles,ET.tostring(deepcopy(found),encoding='unicode')

def header(viewbox:str,title:str,desc:str,background:str|None=None)->list[str]:
    x,y,w,h=viewbox.split()
    out=[f'<svg xmlns="{SVG_NS}" viewBox="{viewbox}" role="img" aria-labelledby="title desc">',f'  <title id="title">{title}</title>',f'  <desc id="desc">{desc}</desc>']
    if background: out.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{background}"/>')
    return out

def horizontal(variant:str)->str:
    word_style,word=extract(ROOT/'Police'/f'percolia-wordmark-{variant}.svg','percolia-wordmark')
    _,bird=extract(ROOT/'Oiseau'/'percolia-bird-compact.svg','percolia-bird')
    inverse=variant=='inverse'
    lines=header('0 0 1120 300',f'Logo horizontal Percolia — {variant}','Mot-symbole en petites capitales, avec un petit oiseau-réseau perché sur le P.','#082C4C' if inverse else None)
    lines.append(f'  <style>{word_style}</style>')
    lines.append('  <g id="logo-horizontal">')
    lines.append(f'    <g transform="translate(60 70) scale(.96)">{word}</g>')
    # The compact bird is already in its folded/perched pose. Keep it small:
    # it is an accent on the P, not a competing illustration.
    lines.append(f'    <g transform="translate(149 93) scale(.46)">{bird}</g>')
    lines.extend(['  </g>','</svg>',''])
    return '\n'.join(lines)

def stacked()->str:
    word_style,word=extract(ROOT/'Police'/'percolia-wordmark-primary.svg','percolia-wordmark')
    _,bird=extract(ROOT/'Oiseau'/'percolia-bird-compact.svg','percolia-bird')
    lines=header('0 0 1120 410','Logo vertical Percolia','Signature centrée avec le petit oiseau-réseau perché sur le P.')
    lines.append(f'  <style>{word_style}</style>')
    lines.append('  <g id="logo-stacked">')
    lines.append(f'    <g transform="translate(56 145) scale(.98)">{word}</g>')
    lines.append(f'    <g transform="translate(149 167) scale(.47)">{bird}</g>')
    lines.extend(['  </g>','</svg>',''])
    return '\n'.join(lines)

def brand_board()->str:
    word_style,word=extract(ROOT/'Police'/'percolia-wordmark-primary.svg','percolia-wordmark')
    _,bird_glide=extract(ROOT/'Oiseau'/'percolia-bird-primary.svg','percolia-bird')
    _,bird_perched=extract(ROOT/'Oiseau'/'percolia-bird-compact.svg','percolia-bird')
    _,monogram=extract(ROOT/'Police'/'percolia-p-monogram-primary.svg','percolia-p-monogram')
    lines=header('0 0 1600 1120','Planche de marque Percolia','Mot-symbole en petites capitales, P distinctif et oiseau-réseau articulé.','#F7FBFC')
    lines.extend([
      f'''  <style>{word_style}
      .text{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;fill:#082C4C}}
      .label{{font-size:24px;font-weight:680;letter-spacing:2px}}
      .small{{font-size:19px;fill:#5D7385}}
      </style>''',
      '  <text class="text" x="92" y="84" font-size="38" font-weight="760" letter-spacing="5">PERCOLIA — DIRECTION 02</text>',
      '  <text class="text small" x="92" y="124">Un P mémorable, des petites capitales calmes, un oiseau-réseau réellement articulé.</text>',
      '  <rect x="72" y="160" width="1456" height="300" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
      '  <text class="text label" x="112" y="212">SIGNATURE PRINCIPALE</text>',
      f'  <g transform="translate(120 250) scale(.78)">{word}</g>',
      f'  <g transform="translate(193 267) scale(.38)">{bird_perched}</g>',
      '  <rect x="72" y="500" width="700" height="390" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
      '  <text class="text label" x="112" y="552">OISEAU ARTICULÉ — POSE DE VOL</text>',
      f'  <g transform="translate(390 720) scale(1.55)">{bird_glide}</g>',
      '  <rect x="808" y="500" width="330" height="390" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
      '  <text class="text label" x="848" y="552">MONOGRAMME P</text>',
      f'  <g transform="translate(850 620) scale(1.12)">{monogram}</g>',
      '  <rect x="1174" y="500" width="354" height="390" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
      '  <text class="text label" x="1214" y="552">PALETTE</text>'
    ])
    colors=[('#082C4C','Encre'),('#1C83D4','Signal'),('#20C9C4','Seuil'),('#EAF5F7','Brume')]
    for i,(hexcolor,name) in enumerate(colors):
        y=595+i*62; stroke=' stroke="#D4E5E8"' if hexcolor=='#EAF5F7' else ''
        lines.append(f'  <rect x="1214" y="{y}" width="56" height="40" rx="9" fill="{hexcolor}"{stroke}/>')
        lines.append(f'  <text class="text" x="1290" y="{y+27}" font-size="20">{name} · {hexcolor}</text>')
    lines.extend([
      '  <text class="text small" x="92" y="975">Le bird rig sépare épaule, coude, poignet, queue, tête et pattes. Le vol n’est plus un simple balancement.</text>',
      '  <text class="text small" x="92" y="1015">v0.2 — actifs vectoriels éditables, animation autonome et génération reproductible.</text>',
      '</svg>',''
    ])
    return '\n'.join(lines)

def main()->None:
    outputs={
      'percolia-lockup-horizontal.svg':horizontal('primary'),
      'percolia-lockup-horizontal-mono.svg':horizontal('mono'),
      'percolia-lockup-horizontal-inverse.svg':horizontal('inverse'),
      'percolia-lockup-stacked.svg':stacked(),
      'brand-board.svg':brand_board(),
    }
    for name,content in outputs.items(): (ROOT/name).write_text(content,encoding='utf-8'); print(f'wrote {name}')
if __name__=='__main__': main()
