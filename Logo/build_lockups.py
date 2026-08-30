#!/usr/bin/env python3
"""Compose self-contained Percolia lockups and a compact brand board."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def body(path: Path, group_id: str) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    styles = "\n".join(re.findall(r"<style>(.*?)</style>", text, flags=re.S))
    match = re.search(rf'(<g id="{re.escape(group_id)}".*?</g>)\s*</svg>', text, flags=re.S)
    if not match:
        raise ValueError(f"group {group_id!r} not found in {path}")
    return styles, match.group(1)


def svg_header(viewbox: str, title: str, desc: str, background: str | None = None) -> list[str]:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + viewbox + '" role="img" aria-labelledby="title desc">',
        f'  <title id="title">{title}</title>',
        f'  <desc id="desc">{desc}</desc>',
    ]
    if background:
        w = viewbox.split()[2]
        h = viewbox.split()[3]
        lines.append(f'  <rect width="{w}" height="{h}" fill="{background}"/>')
    return lines


def horizontal(variant: str) -> str:
    word_file = ROOT / "Police" / f"percolia-wordmark-{variant}.svg"
    bird_file = ROOT / "Oiseau" / f"percolia-bird-{variant}.svg"
    word_style, word = body(word_file, "percolia-wordmark")
    _, bird = body(bird_file, "percolia-bird")
    inverse = variant == "inverse"
    lines = svg_header("0 0 1400 290", f"Logo horizontal Percolia — {variant}", "Oiseau-réseau à gauche et mot-symbole Percolia à droite.", "#082C4C" if inverse else None)
    lines.append(f"  <style>{word_style}</style>")
    lines.append('  <g id="logo-horizontal">')
    lines.append(f'    <g transform="translate(14 -1) scale(.72)">{bird}</g>')
    lines.append(f'    <g transform="translate(472 57) scale(.74)">{word}</g>')
    lines.extend(['  </g>', '</svg>', ''])
    return "\n".join(lines)


def stacked() -> str:
    word_style, word = body(ROOT / "Police" / "percolia-wordmark-primary.svg", "percolia-wordmark")
    _, bird = body(ROOT / "Oiseau" / "percolia-bird-primary.svg", "percolia-bird")
    lines = svg_header("0 0 1300 650", "Logo vertical Percolia", "Oiseau-réseau centré au-dessus du mot-symbole Percolia.")
    lines.append(f"  <style>{word_style}</style>")
    lines.append('  <g id="logo-stacked">')
    lines.append(f'    <g transform="translate(362 -2) scale(.9)">{bird}</g>')
    lines.append(f'    <g transform="translate(54 406) scale(1)">{word}</g>')
    lines.extend(['  </g>', '</svg>', ''])
    return "\n".join(lines)


def brand_board() -> str:
    word_style, word = body(ROOT / "Police" / "percolia-wordmark-primary.svg", "percolia-wordmark")
    _, bird = body(ROOT / "Oiseau" / "percolia-bird-primary.svg", "percolia-bird")
    _, compact = body(ROOT / "Oiseau" / "percolia-bird-compact.svg", "percolia-bird")
    _, monogram = body(ROOT / "Police" / "percolia-p-monogram-primary.svg", "percolia-p-monogram")
    lines = svg_header("0 0 1600 1100", "Planche de marque Percolia", "Mot-symbole, oiseau-réseau, monogramme P et palette de couleurs.", "#F7FBFC")
    lines.extend([
        f"  <style>{word_style}\n.text{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;fill:#082C4C}} .label{{font-size:24px;font-weight:650;letter-spacing:2px}} .small{{font-size:19px;fill:#5D7385}}</style>",
        '  <text class="text" x="92" y="88" font-size="38" font-weight="750" letter-spacing="6">PERCOLIA — DIRECTION 01</text>',
        '  <text class="text small" x="92" y="128">La structure fiable qui émerge du bruit.</text>',
        '  <rect x="72" y="170" width="1456" height="330" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="112" y="222">SIGNATURE PRINCIPALE</text>',
        f'  <g transform="translate(112 237) scale(.62)">{bird}</g>',
        f'  <g transform="translate(535 296) scale(.69)">{word}</g>',
        '  <rect x="72" y="540" width="700" height="356" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="112" y="592">OISEAU-RÉSEAU COMPACT</text>',
        f'  <g transform="translate(151 605) scale(.93)">{compact}</g>',
        '  <rect x="808" y="540" width="330" height="356" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="848" y="592">MONOGRAMME P</text>',
        f'  <g transform="translate(866 630) scale(1.1)">{monogram}</g>',
        '  <rect x="1174" y="540" width="354" height="356" rx="32" fill="#FFFFFF" stroke="#DCEBED"/>',
        '  <text class="text label" x="1214" y="592">PALETTE</text>',
    ])
    colors = [("#082C4C", "Encre"), ("#1C83D4", "Signal"), ("#20C9C4", "Seuil"), ("#EAF5F7", "Brume")]
    for index, (hexcolor, name) in enumerate(colors):
        y = 630 + index * 60
        stroke = ' stroke="#D4E5E8"' if hexcolor == "#EAF5F7" else ""
        lines.append(f'  <rect x="1214" y="{y}" width="56" height="38" rx="9" fill="{hexcolor}"{stroke}/>')
        lines.append(f'  <text class="text" x="1290" y="{y + 26}" font-size="20">{name} · {hexcolor}</text>')
    lines.extend([
        '  <text class="text small" x="92" y="970">Typographie de marque vectorielle sur mesure · SVG sémantique et animable · contraste vérifié</text>',
        '  <text class="text small" x="92" y="1010">v0.1 — piste éditable, à valider par tests utilisateurs et recherche d’antériorités</text>',
        '</svg>', ''
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
