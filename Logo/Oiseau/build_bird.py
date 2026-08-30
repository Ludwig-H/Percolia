#!/usr/bin/env python3
"""Generate the Percolia network bird SVG variants.

The body/head/tail topology is restored from the first Percolia direction.
Only the wings are parametric: each frame is recomputed from a three-link
kinematic chain and converted back into the same triangulated network style.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "bird_model.json"


def fmt(value: float) -> str:
    if abs(value) < 5e-7:
        value = 0.0
    return f"{value:.3f}".rstrip("0").rstrip(".")


def load_model() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def color(name: str, palette: dict, variant: str) -> str:
    if variant == "mono":
        return palette["ink"]
    if variant == "inverse" and name == "ink":
        return palette["white"]
    return palette[name]


def add(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] + b[0], a[1] + b[1]


def sub(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] - b[0], a[1] - b[1]


def mul(a: tuple[float, float], scalar: float) -> tuple[float, float]:
    return a[0] * scalar, a[1] * scalar


def norm(a: tuple[float, float]) -> float:
    return math.hypot(a[0], a[1])


def unit(a: tuple[float, float]) -> tuple[float, float]:
    length = norm(a)
    if length < 1e-9:
        raise ValueError("null vector in wing geometry")
    return a[0] / length, a[1] / length


def normal(a: tuple[float, float]) -> tuple[float, float]:
    ux, uy = unit(a)
    return -uy, ux


def lerp_point(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def points_string(points: Iterable[tuple[float, float]]) -> str:
    return " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points)


def periodic_pose(model: dict, phase: float, side: str) -> dict:
    wing = model["wing"]
    phase = (phase + wing[f"{side}_phase_offset"]) % 1.0
    theta = math.tau * phase
    stroke = (
        wing["stroke_center_deg"]
        + wing["stroke_amplitude_deg"] * math.cos(theta)
        + wing["stroke_harmonic_deg"]
        * math.cos(2 * theta + math.radians(wing["stroke_harmonic_phase_deg"]))
    )
    # The wing is extended during the downstroke and folds during the
    # recovery stroke. The sine gate is smooth and exactly periodic.
    upstroke = ((1 - math.sin(theta + math.radians(wing["fold_phase_deg"]))) / 2) ** wing["fold_exponent"]
    return {
        "stroke_deg": stroke,
        "elbow_deg": wing["elbow_base_deg"] + wing["elbow_fold_deg"] * upstroke,
        "wrist_deg": wing["wrist_base_deg"] + wing["wrist_fold_deg"] * upstroke,
        "span_scale": wing[f"{side}_scale"],
        "chord_scale": math.sqrt(wing[f"{side}_scale"]),
    }


def folded_pose(model: dict, side: str) -> dict:
    pose = dict(model["wing"]["folded_pose"])
    pose["span_scale"] *= model["wing"][f"{side}_scale"]
    pose["chord_scale"] *= math.sqrt(model["wing"][f"{side}_scale"])
    return pose


def wing_geometry(model: dict, pose: dict, side: str) -> dict:
    wing = model["wing"]
    shoulder = tuple(wing["shoulders"][side])
    l1, l2, l3 = [length * pose["span_scale"] for length in wing["segment_lengths"]]
    a1 = math.radians(pose["stroke_deg"])
    a2 = a1 + math.radians(pose["elbow_deg"])
    a3 = a2 + math.radians(pose["wrist_deg"])

    s = shoulder
    e = add(s, (l1 * math.cos(a1), l1 * math.sin(a1)))
    w = add(e, (l2 * math.cos(a2), l2 * math.sin(a2)))
    t = add(w, (l3 * math.cos(a3), l3 * math.sin(a3)))
    joints = [s, e, w, t]

    tangents = [
        sub(e, s),
        add(unit(sub(e, s)), unit(sub(w, e))),
        add(unit(sub(w, e)), unit(sub(t, w))),
        sub(t, w),
    ]
    normals = [normal(vector) for vector in tangents]
    widths = [value * pose["chord_scale"] for value in wing["chords"]]
    lead_fraction = wing["leading_fraction"]
    leading = [sub(point, mul(nrm, width * lead_fraction)) for point, nrm, width in zip(joints, normals, widths)]
    trailing = [add(point, mul(nrm, width * (1 - lead_fraction))) for point, nrm, width in zip(joints, normals, widths)]

    # Seven boundary vertices, deliberately matching the graphic density of
    # the original bird. The tip is shared by leading and trailing edges.
    boundary = [leading[0], leading[1], leading[2], t, trailing[2], trailing[1], trailing[0]]
    core = (
        0.18 * s[0] + 0.33 * e[0] + 0.34 * w[0] + 0.15 * t[0],
        0.18 * s[1] + 0.33 * e[1] + 0.34 * w[1] + 0.15 * t[1],
    )
    return {"boundary": boundary, "core": core, "joints": joints}


def blend_geometry(a: dict, b: dict, t: float) -> dict:
    return {
        "boundary": [lerp_point(x, y, t) for x, y in zip(a["boundary"], b["boundary"])],
        "core": lerp_point(a["core"], b["core"], t),
        "joints": [lerp_point(x, y, t) for x, y in zip(a["joints"], b["joints"])],
    }


def svg_header(model: dict, variant: str, compact: bool) -> list[str]:
    palette = model["palette"]
    if compact:
        view_box = [55, 34, 520, 292]
    else:
        view_box = model["viewBox"]
    x, y, width, height = view_box
    background = palette["ink"] if variant == "inverse" else None
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x)} {fmt(y)} {fmt(width)} {fmt(height)}" role="img" aria-labelledby="title desc" class="percolia-bird">',
        '  <title id="title">Oiseau-réseau Percolia</title>',
        '  <desc id="desc">Le modèle d’oiseau en réseau initial, doté d’ailes cinématiques déformables.</desc>',
    ]
    if background:
        lines.append(f'  <rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(width)}" height="{fmt(height)}" fill="{background}"/>')
    metadata = json.dumps(model, ensure_ascii=False, separators=(",", ":"))
    lines.append(f'  <metadata id="percolia-network-model" data-network-model="true"><![CDATA[{metadata}]]></metadata>')
    return lines


def render_mesh(model: dict, variant: str) -> str:
    body = model["body"]
    palette = model["palette"]
    inverse = variant == "inverse"
    mono = variant == "mono"
    base = palette["white"] if inverse else palette["ink"]
    edge_styles = {
        "mesh": (1.25, base, 0.78),
        "outline": (1.85, base, 0.98),
        "critical": (2.15, palette["blue"] if not mono else base, 1.0),
    }
    lines = ['    <g id="bird-body-network" data-layer="body">', '      <g id="body-faces" data-layer="faces">']
    for face_id, node_ids, fill_name, opacity in body["faces"]:
        pts = [tuple(body["nodes"][node][:2]) for node in node_ids]
        lines.append(
            f'        <polygon id="{escape(face_id)}" points="{points_string(pts)}" fill="{color(fill_name, palette, variant)}" fill-opacity="{fmt(opacity)}" data-anim="face"/>'
        )
    lines.extend(['      </g>', '      <g id="body-edges" data-layer="edges" fill="none" stroke-linecap="round" stroke-linejoin="round">'])
    for index, (a, b, kind) in enumerate(body["edges"], 1):
        x1, y1 = body["nodes"][a][:2]
        x2, y2 = body["nodes"][b][:2]
        width, stroke, opacity = edge_styles[kind]
        lines.append(
            f'        <line id="body-edge-{index:02d}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{stroke}" stroke-opacity="{fmt(opacity)}" stroke-width="{fmt(width)}" data-anim="edge" data-kind="{kind}" vector-effect="non-scaling-stroke"/>'
        )
    lines.extend(['      </g>', '      <g id="body-nodes" data-layer="nodes">'])
    for node_id, (x, y, radius, fill_name, kind) in body["nodes"].items():
        node_stroke = palette["ink"] if inverse else palette["white"]
        if mono:
            node_stroke = palette["white"]
        lines.append(
            f'        <circle id="body-node-{escape(node_id)}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="{color(fill_name, palette, variant)}" stroke="{node_stroke}" stroke-width="0.75" data-anim="node" data-kind="{kind}" vector-effect="non-scaling-stroke"/>'
        )
    lines.extend(['      </g>', '    </g>'])
    return "\n".join(lines)


def render_scatter(model: dict, variant: str) -> str:
    palette = model["palette"]
    lines = ['    <g id="bird-scatter" data-layer="scatter" opacity="0.50">']
    for node_id, (x, y, radius, fill_name, _kind) in model["scatter"].items():
        lines.append(
            f'      <circle id="scatter-{escape(node_id)}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="{color(fill_name, palette, variant)}" data-anim="scatter"/>'
        )
    lines.append('    </g>')
    return "\n".join(lines)


def render_wing(model: dict, variant: str, side: str, geometry: dict, opacity: float) -> str:
    palette = model["palette"]
    inverse = variant == "inverse"
    mono = variant == "mono"
    ink = palette["white"] if inverse else palette["ink"]
    if mono:
        wing_colors = [ink] * 7
    else:
        wing_colors = [palette["cyan"], palette["blue"], palette["ink"], palette["cyan"], palette["blue"], palette["cyan"], palette["blue"]]
    boundary = geometry["boundary"]
    core = geometry["core"]
    group_opacity = opacity
    lines = [f'    <g id="wing-{side}" data-wing-side="{side}" opacity="{fmt(group_opacity)}">']
    lines.append(
        f'      <polygon id="wing-{side}-outline" data-wing-outline="true" points="{points_string(boundary)}" fill="{palette["mist"]}" fill-opacity="{fmt(0.25 if side == "near" else 0.16)}" stroke="{ink}" stroke-width="1.55" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
    )
    lines.append(f'      <g id="wing-{side}-faces" data-layer="faces">')
    for index in range(7):
        a = boundary[index]
        b = boundary[(index + 1) % 7]
        lines.append(
            f'        <polygon id="wing-{side}-face-{index:02d}" data-wing-face="{index}" points="{points_string([a, b, core])}" fill="{wing_colors[index]}" fill-opacity="{fmt(0.10 if side == "near" else 0.055)}"/>'
        )
    lines.append('      </g>')
    lines.append(f'      <g id="wing-{side}-edges" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for index in range(7):
        a = boundary[index]
        b = boundary[(index + 1) % 7]
        lines.append(
            f'        <line id="wing-{side}-boundary-{index:02d}" data-wing-boundary="{index}" x1="{fmt(a[0])}" y1="{fmt(a[1])}" x2="{fmt(b[0])}" y2="{fmt(b[1])}" stroke="{ink}" stroke-width="1.45" vector-effect="non-scaling-stroke"/>'
        )
        lines.append(
            f'        <line id="wing-{side}-spoke-{index:02d}" data-wing-spoke="{index}" x1="{fmt(a[0])}" y1="{fmt(a[1])}" x2="{fmt(core[0])}" y2="{fmt(core[1])}" stroke="{palette["blue"] if not mono and index in (1, 3, 5) else ink}" stroke-width="0.85" vector-effect="non-scaling-stroke"/>'
        )
    lines.append('      </g>')
    lines.append(f'      <g id="wing-{side}-nodes" data-layer="nodes">')
    for index, point in enumerate(boundary):
        fill = palette["cyan"] if not mono and index in (0, 3, 5) else palette["blue"] if not mono and index in (1, 4) else ink
        lines.append(
            f'        <circle id="wing-{side}-node-{index:02d}" data-wing-node="{index}" cx="{fmt(point[0])}" cy="{fmt(point[1])}" r="{fmt(2.7 if index == 3 else 2.25)}" fill="{fill}" stroke="{palette["white"]}" stroke-width="0.65" vector-effect="non-scaling-stroke"/>'
        )
    lines.append(
        f'        <circle id="wing-{side}-core" data-wing-core="true" cx="{fmt(core[0])}" cy="{fmt(core[1])}" r="3.4" fill="{palette["cyan"] if not mono else ink}" stroke="{palette["white"]}" stroke-width="0.75" vector-effect="non-scaling-stroke"/>'
    )
    lines.extend(['      </g>', '    </g>'])
    return "\n".join(lines)


def render_legs(model: dict, variant: str, tucked: bool) -> str:
    palette = model["palette"]
    stroke = palette["white"] if variant == "inverse" else palette["ink"]
    lines = ['    <g id="bird-legs" data-layer="legs" fill="none" stroke-linecap="round" stroke-linejoin="round">']
    for side, leg in model["legs"].items():
        opacity = 0.42 if side == "far" else 0.92
        hip = tuple(leg["hip"])
        knee = tuple(leg["knee"])
        ankle = tuple(leg["ankle"])
        if tucked:
            knee = lerp_point(hip, knee, 0.45)
            ankle = lerp_point(hip, ankle, 0.35)
        lines.append(f'      <g id="leg-{side}" data-leg="{side}" opacity="{fmt(opacity)}">')
        lines.append(
            f'        <polyline data-leg-main="true" points="{points_string([hip, knee, ankle])}" stroke="{stroke}" stroke-width="1.55" vector-effect="non-scaling-stroke"/>'
        )
        for index, toe in enumerate(leg["toes"]):
            toe_point = ankle if tucked else tuple(toe)
            lines.append(
                f'        <line data-leg-toe="{index}" x1="{fmt(ankle[0])}" y1="{fmt(ankle[1])}" x2="{fmt(toe_point[0])}" y2="{fmt(toe_point[1])}" stroke="{stroke}" stroke-width="1.05" vector-effect="non-scaling-stroke"/>'
            )
        lines.append('      </g>')
    lines.append('    </g>')
    return "\n".join(lines)


def render_lidar(model: dict) -> str:
    palette = model["palette"]
    beak = model["body"]["nodes"]["q1"][:2]
    x, y = beak
    return "\n".join(
        [
            f'    <g id="lidar-scan" data-lidar="true" transform="translate({fmt(x)} {fmt(y)})" opacity="0" pointer-events="none">',
            f'      <path data-lidar-beam="true" d="M 0 0 L 88 -17 A 90 90 0 0 1 88 17 Z" fill="{palette["cyan"]}" fill-opacity="0.14"/>',
            f'      <line data-lidar-ray="true" x1="0" y1="0" x2="94" y2="0" stroke="{palette["blue"]}" stroke-width="1.55" stroke-linecap="round" vector-effect="non-scaling-stroke"/>',
            f'      <circle data-lidar-return="true" cx="98" cy="0" r="3" fill="{palette["cyan"]}" opacity="0" filter="url(#scan-glow)"/>',
            '    </g>',
        ]
    )


def render_bird(model: dict, variant: str, compact: bool) -> str:
    lines = svg_header(model, variant, compact)
    lines.append('  <defs><filter id="scan-glow" x="-300%" y="-300%" width="600%" height="600%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    lines.append(f'  <g id="percolia-bird" data-percolia-bird="true" data-model-version="{escape(model["version"])}">')

    if compact:
        lines.append(render_mesh(model, variant))
        geometry = wing_geometry(model, folded_pose(model, "near"), "near")
        lines.append(render_wing(model, variant, "near", geometry, 0.96))
        lines.append(render_legs(model, variant, tucked=False))
    else:
        lines.append(render_scatter(model, variant))
        far_geometry = wing_geometry(model, periodic_pose(model, model["wing"]["glide_phase"], "far"), "far")
        near_geometry = wing_geometry(model, periodic_pose(model, model["wing"]["glide_phase"], "near"), "near")
        lines.append(render_wing(model, variant, "far", far_geometry, model["wing"]["far_opacity"]))
        lines.append(render_mesh(model, variant))
        lines.append(render_wing(model, variant, "near", near_geometry, 0.98))
        lines.append(render_legs(model, variant, tucked=True))
        lines.append(render_lidar(model))
    lines.extend(['  </g>', '</svg>', ''])
    return "\n".join(lines)


def main() -> None:
    model = load_model()
    outputs = {
        "percolia-bird-primary.svg": render_bird(model, "primary", False),
        "percolia-bird-mono.svg": render_bird(model, "mono", False),
        "percolia-bird-inverse.svg": render_bird(model, "inverse", False),
        "percolia-bird-compact.svg": render_bird(model, "primary", True),
    }
    for filename, content in outputs.items():
        (ROOT / filename).write_text(content, encoding="utf-8")
        print(f"wrote {filename}")


if __name__ == "__main__":
    main()
