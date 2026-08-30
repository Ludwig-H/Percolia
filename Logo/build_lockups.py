#!/usr/bin/env python3
"""Compose static Percolia signatures from canonical vector sources."""
from __future__ import annotations

import importlib.util
import re
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def load_bird_builder():
    path = ROOT / "Oiseau" / "build_bird.py"
    spec = importlib.util.spec_from_file_location("build_bird", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import bird builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_from_text(text: str, element_id: str) -> tuple[str, str]:
    styles = "\n".join(re.findall(r"<style>(.*?)</style>", text, flags=re.S))
    root = ET.fromstring(text)
    found = next((element for element in root.iter() if element.attrib.get("id") == element_id), None)
    if found is None:
        raise ValueError(f"{element_id!r} not found")
    return styles, ET.tostring(deepcopy(found), encoding="unicode")


def extract_file(path: Path, element_id: str) -> tuple[str, str]:
    return extract_from_text(path.read_text(encoding="utf-8"), element_id)


def header(view_box: str, title: str, desc: str, background: str | None = None) -> list[str]:
    x, y, width, height = view_box.split()
    lines = [
        f'<svg xmlns="{SVG_NS}" viewBox="{view_box}" role="img" aria-labelledby="title desc">',
        f'  <title id="title">{title}</title>',
        f'  <desc id="desc">{desc}</desc>',
    ]
    if background:
        lines.append(f'  <rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{background}"/>')
    return lines


def compact_bird(variant: str) -> str:
    builder = load_bird_builder()
    model = builder.load_model()
    svg = builder.render_bird(model, variant, True)
    _, group = extract_from_text(svg, "percolia-bird")
    return group


def horizontal(variant: str) -> str:
    word_style, wordmark = extract_file(ROOT / "Police" / f"percolia-wordmark-{variant}.svg", "percolia-wordmark")
    bird = compact_bird(variant)
    inverse = variant == "inverse"
    lines = header(
        "0 0 1120 300",
        f"Logo horizontal Percolia — {variant}",
        "Mot-symbole en petites capitales avec le modèle d’oiseau-réseau initial, perché sur le P.",
        "#082C4C" if inverse else None,
    )
    lines.append(f"  <style>{word_style}</style>")
    lines.append('  <g id="logo-horizontal">')
    lines.append(f'    <g transform="translate(60 70) scale(.96)">{wordmark}</g>')
    # Local foot point (306,285) is mapped to the top of the P.
    lines.append(f'    <g transform="translate(148 106) scale(.22) translate(-306 -285)">{bird}</g>')
    lines.extend(['  </g>', '</svg>', ''])
    return "\n".join(lines)


def stacked() -> str:
    word_style, wordmark = extract_file(ROOT / "Police" / "percolia-wordmark-primary.svg", "percolia-wordmark")
    bird = compact_bird("primary")
    lines = header("0 0 1120 410", "Logo vertical Percolia", "Signature centrée avec le petit oiseau-réseau perché sur le P.")
    lines.append(f"  <style>{word_style}</style>")
    lines.append('  <g id="logo-stacked">')
    lines.append(f'    <g transform="translate(56 160) scale(.98)">{wordmark}</g>')
    lines.append(f'    <g transform="translate(146 198) scale(.23) translate(-306 -285)">{bird}</g>')
    lines.extend(['  </g>', '</svg>', ''])
    return "\n".join(lines)


def brand_board() -> str:
    word_style, wordmark = extract_file(ROOT / "Police" / "percolia-wordmark-primary.svg", "percolia-wordmark")
    _, flight_bird = extract_file(ROOT / "Oiseau" / "percolia-bird-primary.svg", "percolia-bird")
    perched_bird = compact_bird("primary")
    _, monogram = extract_file(ROOT / "Police" / "percolia-p-monogram-primary.svg", "percolia-p-monogram")
    lines = header("0 0 1600 1120", "Planche de marque Percolia", "P distinctif, petites capitales et retour au premier oiseau-réseau.", "#F7FBFC")
    lines.extend([
        f'''  <style>{word_style}
        .text{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;fill:#082C4C}}
        .label{{font-size:24px;font-weight:680;letter-spacing:2px}}
        .small{{font-size:19px;fill:#5D7385}}
        </style>''',
        '  <text class="text" x="92" y="84" font-size="38" font-weight="760" letter-spacing="5">PERCOLIA — DIRECTION 03</text>',
        '  <text class="text small" x="92" y="124">Retour au modèle d’oiseau en réseau initial, avec ailes déformables et vol directionnel.</text>',
        '  <rect x="72" y="160" width="1456" height="300" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="112" y="212">SIGNATURE PRINCIPALE</text>',
        f'  <g transform="translate(120 250) scale(.78)">{wordmark}</g>',
        f'  <g transform="translate(190 274) scale(.18) translate(-306 -285)">{perched_bird}</g>',
        '  <rect x="72" y="500" width="700" height="390" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="112" y="552">OISEAU-RÉSEAU — POSE DE VOL</text>',
        f'  <g transform="translate(100 575) scale(.95)">{flight_bird}</g>',
        '  <rect x="808" y="500" width="330" height="390" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="848" y="552">MONOGRAMME P</text>',
        f'  <g transform="translate(850 620) scale(1.12)">{monogram}</g>',
        '  <rect x="1174" y="500" width="354" height="390" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="1214" y="552">PALETTE</text>',
    ])
    colors = [("#082C4C", "Encre"), ("#1C83D4", "Signal"), ("#20C9C4", "Seuil"), ("#EAF5F7", "Brume")]
    for index, (hex_color, name) in enumerate(colors):
        y = 595 + index * 62
        stroke = ' stroke="#D4E5E8"' if hex_color == "#EAF5F7" else ""
        lines.append(f'  <rect x="1214" y="{y}" width="56" height="40" rx="9" fill="{hex_color}"{stroke}/>')
        lines.append(f'  <text class="text" x="1290" y="{y + 27}" font-size="20">{name} · {hex_color}</text>')
    lines.extend([
        '  <text class="text small" x="92" y="975">Le corps conserve la topologie initiale. Les ailes seules sont recalculées à partir d’une chaîne épaule–coude–poignet.</text>',
        '  <text class="text small" x="92" y="1015">Deux oiseaux distincts assurent le départ et le retour : aucun demi-tour artificiel hors champ.</text>',
        '</svg>',
        '',
    ])
    return "\n".join(lines)


def main() -> None:
    outputs = {
        "percolia-lockup-horizontal.svg": horizontal("primary"),
        "percolia-lockup-horizontal-mono.svg": horizontal("mono"),
        "percolia-lockup-horizontal-inverse.svg": horizontal("inverse"),
        "percolia-lockup-stacked.svg": stacked(),
        "brand-board.svg": brand_board(),
    }
    for filename, content in outputs.items():
        (ROOT / filename).write_text(content, encoding="utf-8")
        print(f"wrote {filename}")


if __name__ == "__main__":
    main()
