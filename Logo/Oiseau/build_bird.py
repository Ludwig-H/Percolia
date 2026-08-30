#!/usr/bin/env python3
"""Generate the parametric Percolia network bird.

The wing surface is sampled from a continuous kinematic model. Each SVG
contains stable data attributes and an embedded copy of the model so that the
browser controller can recompute the geometry frame by frame.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "bird_model.json"


def fmt(value: float) -> str:
    if abs(value) < 5e-8:
        value = 0.0
    return f"{value:.4f}".rstrip("0").rstrip(".")


def load_model() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def deg(value: float) -> float:
    return math.radians(value)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def catmull(points: Sequence[tuple[float, float]], t: float) -> tuple[float, float]:
    n = len(points)
    scaled = min(max(t, 0.0), 0.999999999) * (n - 1)
    i = min(n - 2, int(scaled))
    u = scaled - i
    p0 = points[max(0, i - 1)]
    p1 = points[i]
    p2 = points[i + 1]
    p3 = points[min(n - 1, i + 2)]

    def component(k: int) -> float:
        return 0.5 * (
            2 * p1[k]
            + (-p0[k] + p2[k]) * u
            + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u * u
            + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u * u * u
        )

    return component(0), component(1)


def local_wing_frame(model: dict, phase: float, openness: float) -> dict:
    wing = model["wing"]
    flight = wing["flight"]
    perched = wing["perched"]
    theta = math.tau * phase
    theta2 = 2 * theta + deg(flight["stroke_h2_phase_deg"])
    fold_raw = 0.5 * (1 + math.sin(theta + deg(flight["fold_phase_deg"])))
    fold = fold_raw ** flight["fold_exponent"]

    stroke_flight = (
        flight["stroke_center_deg"]
        + flight["stroke_h1_deg"] * math.cos(theta)
        + flight["stroke_h2_deg"] * math.cos(theta2)
    )
    sweep_flight = flight["sweep_center_deg"] + flight["sweep_amp_deg"] * math.sin(
        theta + deg(flight["sweep_phase_deg"])
    )
    elbow_flight = flight["elbow_base_deg"] + flight["elbow_fold_deg"] * fold
    wrist_flight = flight["wrist_base_deg"] + flight["wrist_fold_deg"] * fold
    pronation_flight = flight["pronation_deg"] * math.sin(
        theta + deg(flight["pronation_phase_deg"])
    )

    return {
        "stroke": lerp(perched["stroke_deg"], stroke_flight, openness),
        "sweep": lerp(perched["sweep_deg"], sweep_flight, openness),
        "elbow": lerp(perched["elbow_deg"], elbow_flight, openness),
        "wrist": lerp(perched["wrist_deg"], wrist_flight, openness),
        "pronation": lerp(perched["pronation_deg"], pronation_flight, openness),
        "span_scale": lerp(perched["span_scale"], 1.0, openness),
        "chord_scale": lerp(perched["chord_scale"], 1.0, openness),
    }


def local_skeleton(model: dict, frame: dict) -> list[tuple[float, float]]:
    l1, l2, l3 = [length * frame["span_scale"] for length in model["wing"]["segment_lengths"]]
    a0 = deg(frame["sweep"])
    a1 = a0 + deg(frame["elbow"])
    a2 = a1 + deg(frame["wrist"])
    s = (0.0, 0.0)
    e = (l1 * math.cos(a0), l1 * math.sin(a0))
    w = (e[0] + l2 * math.cos(a1), e[1] + l2 * math.sin(a1))
    tip = (w[0] + l3 * math.cos(a2), w[1] + l3 * math.sin(a2))
    return [s, e, w, tip]


def chord(model: dict, station: float, scale: float) -> float:
    wing = model["wing"]
    base = wing["root_chord"] * ((1 - station) ** wing["chord_exponent"])
    bulge = 1 + wing["chord_bulge"] * math.sin(math.pi * station)
    return (base * bulge + wing["tip_chord"] * (1 - station)) * scale


def project_point(model: dict, side: str, local: tuple[float, float], z_twist: float, stroke_deg: float) -> tuple[float, float]:
    sign = -1.0 if side == "near" else 1.0
    shoulder = model["wing"]["shoulders"][side]
    u, v = local
    # Local u is span, v is sweep toward the tail. Rotate the wing plane around
    # the body x-axis. Multiplying the stroke by side keeps both wings on the
    # same physical up/down half-cycle.
    phi = deg(stroke_deg * sign)
    body_x = shoulder[0] - v
    lateral = shoulder[1] + sign * u
    vertical = shoulder[2] + z_twist
    rel_y = lateral - shoulder[1]
    rel_z = vertical - shoulder[2]
    y3 = shoulder[1] + rel_y * math.cos(phi) - rel_z * math.sin(phi)
    z3 = shoulder[2] + rel_y * math.sin(phi) + rel_z * math.cos(phi)
    camera = model["wing"]["camera"]
    screen_x = body_x + camera.get("x_from_y", 0.0) * y3 + camera["x_from_z"] * z3
    screen_y = camera["y_from_y"] * y3 + camera["y_from_z"] * z3
    return screen_x, screen_y


def wing_geometry(model: dict, side: str, phase: float, openness: float) -> dict:
    frame = local_wing_frame(model, phase, openness)
    skeleton = local_skeleton(model, frame)
    stations = model["wing"]["stations"]
    leading_local: list[tuple[float, float]] = []
    trailing_local: list[tuple[float, float]] = []
    for station in stations:
        lead = catmull(skeleton, station)
        eps = 1e-3
        before = catmull(skeleton, max(0.0, station - eps))
        after = catmull(skeleton, min(1.0, station + eps))
        tangent = (after[0] - before[0], after[1] - before[1])
        norm = math.hypot(*tangent) or 1.0
        # Use a continuous rearward normal. A sign test on the geometric
        # normal creates a visible discontinuity when the tangent crosses the
        # vertical direction during a folded upstroke.
        normal_raw = (-0.35 * tangent[1] / norm, 1.0)
        normal_norm = math.hypot(*normal_raw) or 1.0
        normal = (normal_raw[0] / normal_norm, normal_raw[1] / normal_norm)
        c = chord(model, station, frame["chord_scale"])
        leading_local.append((lead[0] - normal[0] * c * 0.16, lead[1] - normal[1] * c * 0.16))
        trailing_local.append((lead[0] + normal[0] * c * 0.84, lead[1] + normal[1] * c * 0.84))

    pronation = deg(frame["pronation"])
    leading = []
    trailing = []
    for station, lead, trail in zip(stations, leading_local, trailing_local):
        c = chord(model, station, frame["chord_scale"])
        twist = math.sin(pronation) * c * (0.12 + 0.26 * station)
        leading.append(project_point(model, side, lead, -twist * 0.12, frame["stroke"]))
        trailing.append(project_point(model, side, trail, twist, frame["stroke"]))

    joints_local = {
        "shoulder": skeleton[0],
        "elbow": skeleton[1],
        "wrist": skeleton[2],
        "tip": skeleton[3],
    }
    joints = {
        name: project_point(model, side, point, 0.0, frame["stroke"])
        for name, point in joints_local.items()
    }
    return {"leading": leading, "trailing": trailing, "joints": joints, "frame": frame}


def smooth_open_path(points: Sequence[tuple[float, float]]) -> str:
    if len(points) < 2:
        return ""
    parts = [f"M {fmt(points[0][0])} {fmt(points[0][1])}"]
    n = len(points)
    for i in range(n - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        parts.append(
            f"C {fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}"
        )
    return " ".join(parts)


def wing_outline(geometry: dict) -> str:
    leading = geometry["leading"]
    trailing = list(reversed(geometry["trailing"]))
    return smooth_open_path(leading) + " L " + f"{fmt(trailing[0][0])} {fmt(trailing[0][1])} " + " ".join(
        smooth_open_path(trailing).split()[3:]
    ) + " Z"


def render_wing(model: dict, side: str, variant: str, phase: float, openness: float, compact: bool) -> str:
    geometry = wing_geometry(model, side, phase, openness)
    leading = geometry["leading"]
    trailing = geometry["trailing"]
    palette = model["palette"]
    ink = palette["white"] if variant == "inverse" else palette["ink"]
    blue = ink if variant == "mono" else palette["blue"]
    cyan = ink if variant == "mono" else palette["cyan"]
    opacity = 0.90 if side == "near" else 0.24
    if compact:
        opacity = 0.0
    fill = cyan if side == "near" else blue
    outline = wing_outline(geometry)
    out = [
        f'    <g id="wing-{side}" data-wing="{side}" opacity="{fmt(opacity)}">',
        f'      <path id="wing-{side}-surface" data-wing-outline="{side}" d="{outline}" fill="{fill}" fill-opacity="0.038" stroke="{ink}" stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>',
        f'      <g id="wing-{side}-faces" data-wing-faces="{side}">',
    ]
    for i in range(len(leading) - 1):
        a, b = leading[i], leading[i + 1]
        c, d = trailing[i + 1], trailing[i]
        tones = (cyan, blue) if (i + (0 if side == "near" else 1)) % 2 == 0 else (blue, cyan)
        out.append(
            f'        <polygon data-wing-face="{side}:{i}:a" points="{fmt(a[0])},{fmt(a[1])} {fmt(b[0])},{fmt(b[1])} {fmt(d[0])},{fmt(d[1])}" fill="{tones[0]}" fill-opacity="0.038"/>'
        )
        out.append(
            f'        <polygon data-wing-face="{side}:{i}:b" points="{fmt(b[0])},{fmt(b[1])} {fmt(c[0])},{fmt(c[1])} {fmt(d[0])},{fmt(d[1])}" fill="{tones[1]}" fill-opacity="0.032"/>'
        )
    out.extend([
        "      </g>",
        f'      <g id="wing-{side}-mesh" data-wing-mesh="{side}" fill="none" stroke="{ink}" stroke-width="0.9" stroke-opacity="0.48" stroke-linecap="round" vector-effect="non-scaling-stroke">',
    ])
    for i in range(len(leading)):
        out.append(
            f'        <line data-wing-spar="{side}:{i}" x1="{fmt(leading[i][0])}" y1="{fmt(leading[i][1])}" x2="{fmt(trailing[i][0])}" y2="{fmt(trailing[i][1])}"/>'
        )
    for i in range(len(leading) - 1):
        a = trailing[i] if i % 2 == 0 else leading[i]
        b = leading[i + 1] if i % 2 == 0 else trailing[i + 1]
        out.append(
            f'        <line data-wing-diagonal="{side}:{i}" x1="{fmt(a[0])}" y1="{fmt(a[1])}" x2="{fmt(b[0])}" y2="{fmt(b[1])}"/>'
        )
    out.append("      </g>")
    out.append(f'      <g id="wing-{side}-joints" data-wing-joints="{side}">')
    joint_tones = {"shoulder": cyan, "elbow": blue, "wrist": cyan, "tip": blue}
    radii = {"shoulder": 2.0, "elbow": 1.7, "wrist": 1.7, "tip": 1.45}
    for name in ("shoulder", "elbow", "wrist", "tip"):
        x, y = geometry["joints"][name]
        out.append(
            f'        <circle data-wing-joint="{side}:{name}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radii[name])}" fill="{joint_tones[name]}"/>'
        )
    out.extend(["      </g>", "    </g>"])
    return "\n".join(out)


def render_body(model: dict, variant: str) -> str:
    body = model["body"]
    palette = model["palette"]
    ink = palette["white"] if variant == "inverse" else palette["ink"]
    blue = ink if variant == "mono" else palette["blue"]
    cyan = ink if variant == "mono" else palette["cyan"]
    tone = {"ink": ink, "blue": blue, "cyan": cyan}
    out = [f'    <g id="bird-body" data-part="body">']
    for index, tail_path in enumerate(body.get("tail_paths", []), 1):
        tail_fill = cyan if index == 1 else blue
        out.append(
            f'      <path id="tail-feather-{index}" d="{tail_path}" fill="{tail_fill}" fill-opacity="0.035" stroke="{ink}" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        )
    out.extend([
        f'      <path id="body-outline" d="{body["outline"]}" fill="{ink}" fill-opacity="0.018" stroke="{ink}" stroke-width="{fmt(body["outline_width"])}" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>',
        '      <g id="body-faces" data-layer="faces">',
    ])
    nodes = body["nodes"]
    for face_id, ids, fill, opacity in body["faces"]:
        pts = " ".join(f"{fmt(nodes[n][0])},{fmt(nodes[n][1])}" for n in ids)
        out.append(
            f'        <polygon id="{face_id}" points="{pts}" fill="{tone[fill]}" fill-opacity="{fmt(opacity)}" data-anim="face" data-phase="2"/>'
        )
    out.extend([
        "      </g>",
        f'      <g id="body-edges" data-layer="edges" fill="none" stroke-linecap="round" stroke-linejoin="round">',
    ])
    styles = {"outline": (1.2, ink, 0.86), "mesh": (0.85, ink, 0.55), "critical": (1.35, blue, 0.9)}
    for i, (a, b, kind) in enumerate(body["edges"], 1):
        x1, y1 = nodes[a][:2]
        x2, y2 = nodes[b][:2]
        width, stroke, opacity = styles[kind]
        out.append(
            f'        <line id="body-edge-{i:02d}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{stroke}" stroke-width="{fmt(width)}" stroke-opacity="{fmt(opacity)}" data-anim="edge" data-kind="{kind}" data-phase="2" vector-effect="non-scaling-stroke"/>'
        )
    out.extend(["      </g>", '      <g id="body-nodes" data-layer="nodes">'])
    for node_id, (x, y, radius, fill, kind) in nodes.items():
        out.append(
            f'        <circle id="body-node-{node_id}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="{tone[fill]}" data-anim="node" data-kind="{kind}" data-phase="2"/>'
        )
    out.extend(["      </g>", "    </g>"])
    return "\n".join(out)


def render_folded_wing(model: dict, variant: str, visible: bool) -> str:
    mesh = model["folded_wing"]
    palette = model["palette"]
    ink = palette["white"] if variant == "inverse" else palette["ink"]
    blue = ink if variant == "mono" else palette["blue"]
    cyan = ink if variant == "mono" else palette["cyan"]
    tone = {"ink": ink, "blue": blue, "cyan": cyan}
    nodes = mesh["nodes"]
    out = [
        f'    <g id="folded-wing" data-folded-wing="true" opacity="{1 if visible else 0}">',
        f'      <path d="{mesh["outline"]}" fill="{cyan}" fill-opacity="0.045" stroke="{ink}" stroke-width="1.25" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>',
        '      <g data-layer="faces">',
    ]
    for face_id, ids, fill, opacity in mesh["faces"]:
        pts = " ".join(f"{fmt(nodes[n][0])},{fmt(nodes[n][1])}" for n in ids)
        out.append(f'        <polygon id="{face_id}" points="{pts}" fill="{tone[fill]}" fill-opacity="{fmt(opacity)}" data-anim="face" data-phase="2"/>')
    out.extend(['      </g>', '      <g data-layer="edges" fill="none" stroke-linecap="round" stroke-linejoin="round">'])
    styles = {"outline": (1.05, ink, .82), "mesh": (.75, ink, .48), "critical": (1.15, blue, .85)}
    for i, (a,b,kind) in enumerate(mesh["edges"],1):
        x1,y1=nodes[a][:2]; x2,y2=nodes[b][:2]; width,stroke,opacity=styles[kind]
        out.append(f'        <line id="folded-edge-{i:02d}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{stroke}" stroke-width="{fmt(width)}" stroke-opacity="{fmt(opacity)}" data-anim="edge" data-kind="{kind}" data-phase="2" vector-effect="non-scaling-stroke"/>')
    out.extend(['      </g>', '      <g data-layer="nodes">'])
    for node_id,(x,y,r,fill,kind) in nodes.items():
        out.append(f'        <circle id="folded-node-{node_id}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{tone[fill]}" data-anim="node" data-kind="{kind}" data-phase="2"/>')
    out.extend(['      </g>', '    </g>'])
    return "\n".join(out)

def render_legs(model: dict, variant: str, compact: bool) -> str:
    palette = model["palette"]
    ink = palette["white"] if variant == "inverse" else palette["ink"]
    out = ['    <g id="bird-legs" data-part="legs" fill="none" stroke-linecap="round" stroke-linejoin="round">']
    for side, leg in model["legs"].items():
        opacity = 0.82 if side == "near" else 0.42
        if not compact:
            opacity *= 0.4
        hip, knee, ankle = leg["hip"], leg["knee"], leg["ankle"]
        out.append(f'      <g id="leg-{side}" data-leg="{side}" opacity="{fmt(opacity)}">')
        out.append(
            f'        <polyline points="{fmt(hip[0])},{fmt(hip[1])} {fmt(knee[0])},{fmt(knee[1])} {fmt(ankle[0])},{fmt(ankle[1])}" stroke="{ink}" stroke-width="1.15" vector-effect="non-scaling-stroke"/>'
        )
        for x, y in leg["toes"]:
            out.append(
                f'        <line x1="{fmt(ankle[0])}" y1="{fmt(ankle[1])}" x2="{fmt(x)}" y2="{fmt(y)}" stroke="{ink}" stroke-width="0.85" vector-effect="non-scaling-stroke"/>'
            )
        out.append("      </g>")
    out.append("    </g>")
    return "\n".join(out)


def render_lidar(model: dict, variant: str) -> str:
    palette = model["palette"]
    blue = palette["ink"] if variant == "mono" else palette["blue"]
    cyan = palette["ink"] if variant == "mono" else palette["cyan"]
    x, y = model["body"]["scan_origin"]
    return "\n".join(
        [
            f'    <g id="lidar-scan" data-layer="lidar" transform="translate({fmt(x)} {fmt(y)})" opacity="0" pointer-events="none">',
            '      <g id="lidar-sweep" data-lidar-sweep="true">',
            f'        <path d="M 0 0 L 62 -10 A 63 63 0 0 1 62 10 Z" fill="{cyan}" fill-opacity="0.11"/>',
            f'        <line x1="0" y1="0" x2="66" y2="0" stroke="{blue}" stroke-width="1.1" stroke-linecap="round" vector-effect="non-scaling-stroke"/>',
            "      </g>",
            f'      <circle id="lidar-return" cx="69" cy="0" r="2.2" fill="{cyan}" opacity="0"/>',
            f'      <circle id="lidar-ring" cx="69" cy="0" r="2.5" fill="none" stroke="{cyan}" stroke-width="0.9" opacity="0" vector-effect="non-scaling-stroke"/>',
            "    </g>",
        ]
    )


def render_scatter(model: dict, variant: str) -> str:
    palette = model["palette"]
    tone = lambda name: palette["ink"] if variant == "mono" else (palette["white"] if variant == "inverse" and name == "ink" else palette[name])
    dots = [(-116, -57, 0.9, "cyan"), (-101, -72, 0.75, "ink"), (-86, -54, 0.95, "blue"), (-119, 47, 0.7, "blue"), (-96, 59, 0.9, "cyan"), (-78, 50, 0.65, "ink")]
    out = ['    <g id="bird-scatter" data-layer="scatter" opacity="0.38">']
    for i, (x, y, radius, color) in enumerate(dots, 1):
        out.append(
            f'      <circle id="scatter-{i:02d}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="{tone(color)}" data-anim="scatter"/>'
        )
    out.append("    </g>")
    return "\n".join(out)


def render_bird(model: dict, variant: str, compact: bool = False) -> str:
    palette = model["palette"]
    background = palette["ink"] if variant == "inverse" else None
    viewbox = [-118, -70, 248, 132] if compact else model["viewBox"]
    x, y, w, h = viewbox
    phase = 0.12
    openness = 0.0 if compact else 1.0
    title = "Oiseau-réseau paramétrique Percolia"
    desc = "Un oiseau géométrique aux ailes continues, générées par cinématique et projection 3D."
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x)} {fmt(y)} {fmt(w)} {fmt(h)}" role="img" aria-labelledby="title desc" class="percolia-bird">',
        f'  <title id="title">{html.escape(title)}</title>',
        f'  <desc id="desc">{html.escape(desc)}</desc>',
    ]
    if background:
        out.append(f'  <rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="{background}"/>')
    model_json = html.escape(json.dumps(model, ensure_ascii=False, separators=(",", ":")))
    out.append(
        f'  <g id="percolia-bird" data-percolia-bird="true" data-model-version="{html.escape(model["version"])}">'
    )
    out.append(f'    <metadata id="percolia-bird-model">{model_json}</metadata>')
    if not compact:
        out.append(render_scatter(model, variant))
    out.append('    <g id="bird-rig" data-part="rig">')
    out.append(render_wing(model, "far", variant, phase, openness, compact))
    out.append(render_legs(model, variant, compact))
    out.append(render_body(model, variant))
    out.append(render_folded_wing(model, variant, compact))
    out.append(render_wing(model, "near", variant, phase, openness, compact))
    out.append(render_lidar(model, variant))
    out.append("    </g>")
    out.extend(["  </g>", "</svg>", ""])
    return "\n".join(out)


def main() -> None:
    model = load_model()
    outputs = {
        "percolia-bird-primary.svg": render_bird(model, "primary"),
        "percolia-bird-mono.svg": render_bird(model, "mono"),
        "percolia-bird-inverse.svg": render_bird(model, "inverse"),
        "percolia-bird-compact.svg": render_bird(model, "primary", compact=True),
    }
    for name, content in outputs.items():
        (ROOT / name).write_text(content, encoding="utf-8")
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
