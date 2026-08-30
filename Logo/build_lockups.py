#!/usr/bin/env python3
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
SVG_NS='http://www.w3.org/2000/svg'
ET.register_namespace('',SVG_NS)

def extract(path:Path,element_id:str)->tuple[str,str]:
    text=path.read_text(encoding='utf-8')
    styles='\n'.join(re.findall(r'<style>(.*?)</style>',text,flags=re.S))
    root=ET.fromstring(text)
    found=next((e for e in root.iter() if e.attrib.get('id')==element_id),None)
    if found is None: raise ValueError(f'{element_id} not found in {path}')
    return styles,ET.tostring(deepcopy(found),encoding='unicode')

def header(viewbox,title,desc,background=None):
    x,y,w,h=viewbox.split();out=[f'<svg xmlns="{SVG_NS}" viewBox="{viewbox}" role="img" aria-labelledby="title desc">',f'<title id="title">{title}</title>',f'<desc id="desc">{desc}</desc>']
    if background: out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{background}"/>')
    return out

def horizontal(variant):
    word_style,word=extract(ROOT/'Police'/f'percolia-wordmark-{variant}.svg','percolia-wordmark')
    _,bird=extract(ROOT/'Oiseau'/'percolia-bird-compact.svg','percolia-bird')
    lines=header('0 0 1120 300',f'Logo horizontal Percolia — {variant}','P distinctif, petites capitales et petit oiseau-réseau perché.','#082C4C' if variant=='inverse' else None)
    lines.append(f'<style>{word_style}</style><g id="logo-horizontal">')
    lines.append(f'<g transform="translate(60 70) scale(.96)">{word}</g>')
    lines.append(f'<g transform="translate(151 91) scale(.35)">{bird}</g>')
    lines.extend(['</g>','</svg>',''])
    return '\n'.join(lines)

def stacked():
    word_style,word=extract(ROOT/'Police'/'percolia-wordmark-primary.svg','percolia-wordmark')
    _,bird=extract(ROOT/'Oiseau'/'percolia-bird-compact.svg','percolia-bird')
    lines=header('0 0 1120 410','Logo vertical Percolia','Petit oiseau-réseau perché sur le P.')
    lines.append(f'<style>{word_style}</style><g id="logo-stacked">')
    lines.append(f'<g transform="translate(56 145) scale(.98)">{word}</g>')
    lines.append(f'<g transform="translate(151 166) scale(.36)">{bird}</g>')
    lines.extend(['</g>','</svg>',''])
    return '\n'.join(lines)

def brand_board():
    word_style,word=extract(ROOT/'Police'/'percolia-wordmark-primary.svg','percolia-wordmark')
    _,bird_glide=extract(ROOT/'Oiseau'/'percolia-bird-primary.svg','percolia-bird')
    _,bird_perched=extract(ROOT/'Oiseau'/'percolia-bird-compact.svg','percolia-bird')
    lines=header('0 0 1600 1080','Planche de marque Percolia','Mot-symbole, oiseau perché et modèle paramétrique.','#F7FBFC')
    lines.append(f'''<style>{word_style}.text{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;fill:#082C4C}}.label{{font-size:24px;font-weight:680;letter-spacing:2px}}.small{{font-size:19px;fill:#5D7385}}</style>''')
    lines.extend([
      '<text class="text" x="92" y="84" font-size="38" font-weight="760" letter-spacing="5">PERCOLIA — DIRECTION 03</text>',
      '<text class="text small" x="92" y="124">P distinctif, petites capitales et aile paramétrique à battement lent.</text>',
      '<rect x="72" y="160" width="1456" height="300" rx="32" fill="#fff" stroke="#DCEBED"/>',
      '<text class="text label" x="112" y="212">SIGNATURE PRINCIPALE</text>',
      f'<g transform="translate(120 250) scale(.78)">{word}</g>',
      f'<g transform="translate(194 267) scale(.29)">{bird_perched}</g>',
      '<rect x="72" y="500" width="910" height="390" rx="32" fill="#fff" stroke="#DCEBED"/>',
      '<text class="text label" x="112" y="552">OISEAU PARAMÉTRIQUE — POSE DE VOL</text>',
      f'<g transform="translate(515 700) scale(1.65)">{bird_glide}</g>',
      '<rect x="1018" y="500" width="510" height="390" rx="32" fill="#fff" stroke="#DCEBED"/>',
      '<text class="text label" x="1058" y="552">MODÈLE</text>',
      '<text class="text small" x="1058" y="610">3 segments osseux</text>',
      '<text class="text small" x="1058" y="652">7 stations par aile</text>',
      '<text class="text small" x="1058" y="694">Spline de Catmull–Rom</text>',
      '<text class="text small" x="1058" y="736">Projection 3D oblique</text>',
      '<text class="text small" x="1058" y="778">Période lente : 5,2 s</text>',
      '<text class="text small" x="92" y="972">Sources éditables, génération reproductible, test numérique de continuité et démonstration autonome.</text>',
      '</svg>',''
    ])
    return '\n'.join(lines)

def main():
    outputs={'percolia-lockup-horizontal.svg':horizontal('primary'),'percolia-lockup-horizontal-mono.svg':horizontal('mono'),'percolia-lockup-horizontal-inverse.svg':horizontal('inverse'),'percolia-lockup-stacked.svg':stacked(),'brand-board.svg':brand_board()}
    for name,content in outputs.items(): (ROOT/name).write_text(content,encoding='utf-8');print('wrote',name)
if __name__=='__main__': main()
