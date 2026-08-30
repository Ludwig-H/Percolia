#!/usr/bin/env python3
"""Generate the editable Percolia network-bird SVG variants from topology.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "topology.json"


def fmt(value: float) -> str:
    return f"{value:g}"


def point_string(ids: Iterable[str], nodes: dict[str, list]) -> str:
    return " ".join(f"{fmt(nodes[node][0])},{fmt(nodes[node][1])}" for node in ids)


def render_full(data: dict, variant: str) -> str:
    nodes = data["nodes"]
    palette = data["palette"]
    inverse = variant == "inverse"
    mono = variant == "mono"
    base = palette["white"] if inverse else palette["ink"]
    background = palette["ink"] if inverse else "none"

    def color(name: str) -> str:
        if mono:
            return palette["ink"]
        if inverse and name == "ink":
            return palette["white"]
        return palette[name]

    edge_styles = {
        "mesh": (1.75, base),
        "outline": (2.35, base),
        "critical": (2.8, palette["blue"] if not mono else palette["ink"]),
    }

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" role="img" aria-labelledby="title desc" class="percolia-bird">',
        '  <title id="title">Oiseau-réseau Percolia</title>',
        '  <desc id="desc">Des points dispersés deviennent un oiseau structuré par un réseau géométrique.</desc>',
        f'  <rect width="640" height="360" fill="{background}"/>',
        '  <g id="percolia-bird" data-percolia-bird="true">',
        '    <g id="faces" data-layer="faces">',
    ]

    for face_id, ids, fill_name, opacity, phase in data["faces"]:
        lines.append(
            f'      <polygon id="{escape(face_id)}" points="{point_string(ids, nodes)}" '
            f'fill="{color(fill_name)}" fill-opacity="{fmt(opacity)}" '
            f'data-phase="{phase}" data-anim="face"/>'
        )
    lines.extend(['    </g>', '    <g id="edges" data-layer="edges" fill="none" stroke-linecap="round" stroke-linejoin="round">'])

    for index, (a, b, kind, phase) in enumerate(data["edges"], start=1):
        x1, y1 = nodes[a][0:2]
        x2, y2 = nodes[b][0:2]
        width, stroke = edge_styles[kind]
        lines.append(
            f'      <line id="edge-{index:02d}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" '
            f'stroke="{stroke}" stroke-width="{fmt(width)}" data-phase="{phase}" data-anim="edge" data-kind="{kind}"/>'
        )
    lines.extend(['    </g>', '    <g id="nodes" data-layer="nodes">'])

    for node_id, (x, y, radius, fill_name, kind) in nodes.items():
        if kind == "scatter":
            continue
        stroke = palette["ink"] if inverse else palette["white"]
        if mono:
            stroke = palette["white"]
        lines.append(
            f'      <circle id="node-{escape(node_id)}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" '
            f'fill="{color(fill_name)}" stroke="{stroke}" stroke-width="0.9" '
            f'data-anim="node" data-kind="{kind}"/>'
        )
    lines.extend(['    </g>', '    <g id="scatter" data-layer="scatter" opacity="0.58">'])

    for node_id, (x, y, radius, fill_name, _kind) in nodes.items():
        if _kind != "scatter":
            continue
        lines.append(
            f'      <circle id="node-{escape(node_id)}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" '
            f'fill="{color(fill_name)}" data-anim="scatter"/>'
        )
    lines.extend(['    </g>', '  </g>', '</svg>', ''])
    return "\n".join(lines)


def render_compact(data: dict) -> str:
    nodes = data["nodes"]
    palette = data["palette"]
    pairs = [
        ("t0", "t1"), ("t1", "t2"), ("t2", "b1"), ("b1", "w1"), ("w1", "w2"),
        ("w2", "w3"), ("w3", "w4"), ("w4", "w5"), ("w5", "n0"), ("n0", "n1"),
        ("n1", "h0"), ("h0", "h1"), ("h1", "h2"), ("h2", "q1"), ("q1", "q2"),
        ("q2", "h3"), ("h3", "h4"), ("h4", "c0"), ("b5", "c0"), ("b5", "b6"),
        ("b6", "b7"), ("t5", "b7"), ("t4", "t5"), ("t0", "t4"), ("t0", "t6"),
        ("t6", "b8"), ("b3", "b8"), ("b3", "n0"), ("n0", "h5"), ("h2", "h5"),
        ("w3", "w6"), ("w6", "b3"), ("b1", "b8"), ("b6", "b8"), ("b3", "b5"),
        ("h0", "h5"), ("h3", "h5"), ("n0", "h4")
    ]
    critical_pairs = {frozenset(x) for x in [("t0", "t6"), ("t6", "b8"), ("b3", "b8"), ("b3", "n0"), ("n0", "h5"), ("h2", "h5"), ("h2", "q1")]}
    compact_faces = [
        ("cf01", ["t0", "t6", "t4"], "cyan", 0.10, 0),
        ("cf02", ["t2", "b1", "b8"], "blue", 0.10, 1),
        ("cf03", ["b1", "b3", "b8"], "cyan", 0.12, 1),
        ("cf04", ["b8", "b5", "b6"], "blue", 0.10, 1),
        ("cf05", ["b1", "w2", "w3"], "cyan", 0.09, 2),
        ("cf06", ["w3", "w5", "b3"], "blue", 0.10, 2),
        ("cf07", ["b3", "n0", "h4"], "cyan", 0.10, 3),
        ("cf08", ["n1", "h0", "h5"], "blue", 0.10, 4),
        ("cf09", ["h5", "h2", "h3"], "cyan", 0.12, 4),
        ("cf10", ["h2", "q1", "q2"], "blue", 0.10, 5),
    ]
    visible_nodes = sorted({node for pair in pairs for node in pair} | {"eye"})

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="45 35 510 265" role="img" aria-labelledby="title desc" class="percolia-bird percolia-bird--compact">',
        '  <title id="title">Oiseau-réseau compact Percolia</title>',
        '  <desc id="desc">Version simplifiée de l’oiseau-réseau pour les petites tailles.</desc>',
        '  <g id="percolia-bird" data-percolia-bird="true">',
        '    <g id="faces" data-layer="faces">',
    ]
    for face_id, ids, color, opacity, phase in compact_faces:
        lines.append(f'      <polygon id="{face_id}" points="{point_string(ids, nodes)}" fill="{palette[color]}" fill-opacity="{fmt(opacity)}" data-phase="{phase}" data-anim="face"/>')
    lines.extend(['    </g>', '    <g id="edges" data-layer="edges" fill="none" stroke-linecap="round" stroke-linejoin="round">'])
    for index, (a, b) in enumerate(pairs, start=1):
        x1, y1 = nodes[a][0:2]
        x2, y2 = nodes[b][0:2]
        critical = frozenset((a, b)) in critical_pairs
        stroke = palette["blue"] if critical else palette["ink"]
        width = 3.0 if critical else 2.35
        lines.append(f'      <line id="edge-{index:02d}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{stroke}" stroke-width="{fmt(width)}" data-anim="edge" data-kind="{"critical" if critical else "outline"}"/>')
    lines.extend(['    </g>', '    <g id="nodes" data-layer="nodes">'])
    for node_id in visible_nodes:
        x, y, radius, fill_name, kind = nodes[node_id]
        radius = max(radius, 3.0)
        lines.append(f'      <circle id="node-{node_id}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="{palette[fill_name]}" stroke="#FFFFFF" stroke-width="1" data-anim="node" data-kind="{kind}"/>')
    lines.extend(['    </g>', '  </g>', '</svg>', ''])
    return "\n".join(lines)


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    outputs = {
        "percolia-bird-primary.svg": render_full(data, "primary"),
        "percolia-bird-mono.svg": render_full(data, "mono"),
        "percolia-bird-inverse.svg": render_full(data, "inverse"),
        "percolia-bird-compact.svg": render_compact(data),
    }
    for filename, content in outputs.items():
        (ROOT / filename).write_text(content, encoding="utf-8")
        print(f"wrote {filename}")


if __name__ == "__main__":
    main()
