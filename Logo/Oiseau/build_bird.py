#!/usr/bin/env python3
"""Generate Percolia's editable network-bird SVG assets.

The silhouette and triangulation follow the original Percolia network bird.
Animation data is embedded as JSON metadata.  A separate JavaScript controller
plays keyframed clips, root motion and the landing IK pass.
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
    value = norm(a)
    if value < 1e-9:
        raise ValueError("null vector in wing geometry")
    return a[0] / value, a[1] / value


def normal(a: tuple[float, float]) -> tuple[float, float]:
    x, y = unit(a)
    return -y, x


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp_point(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return lerp(a[0], b[0], t), lerp(a[1], b[1], t)


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
    recovery = ((1 - math.sin(theta + math.radians(wing["fold_phase_deg"]))) / 2) ** wing["fold_exponent"]
    return {
        "stroke_deg": stroke,
        "elbow_deg": wing["elbow_base_deg"] + wing["elbow_fold_deg"] * recovery,
        "wrist_deg": wing["wrist_base_deg"] + wing["wrist_fold_deg"] * recovery,
        "span_scale": wing[f"{side}_scale"],
        "chord_scale": math.sqrt(wing[f"{side}_scale"]),
    }


def folded_pose(model: dict, side: str) -> dict:
    pose = dict(model["wing"]["folded_pose"])
    pose["span_scale"] *= model["wing"][f"{side}_scale"]
    pose["chord_scale"] *= math.sqrt(model["wing"][f"{side}_scale"])
    return pose


def display_pose(model: dict, side: str) -> dict:
    pose = dict(model["wing"]["display_pose"])
    pose["span_scale"] *= model["wing"][f"{side}_scale"]
    pose["chord_scale"] *= math.sqrt(model["wing"][f"{side}_scale"])
    return pose


def _transform_by_bone(point, rest_a, rest_b, current_a, current_b):
    rest_vector=sub(rest_b,rest_a); current_vector=sub(current_b,current_a)
    rest_length=norm(rest_vector); current_length=norm(current_vector)
    if rest_length < 1e-9: raise ValueError("degenerate reference wing bone")
    scale=current_length/rest_length
    angle=math.atan2(current_vector[1],current_vector[0])-math.atan2(rest_vector[1],rest_vector[0])
    local=sub(point,rest_a); c=math.cos(angle); s=math.sin(angle)
    return add(current_a,(scale*(local[0]*c-local[1]*s),scale*(local[0]*s+local[1]*c)))

def _skin_point(point,weights,rest_joints,current_joints):
    if abs(sum(weights)-1)>1e-6: raise ValueError("wing skin weights must sum to one")
    result=(0.0,0.0)
    for index,weight in enumerate(weights):
        transformed=_transform_by_bone(point,rest_joints[index],rest_joints[index+1],current_joints[index],current_joints[index+1])
        result=add(result,mul(transformed,weight))
    return result

def wing_geometry(model: dict, pose: dict, side: str) -> dict:
    wing=model["wing"]; shoulder=tuple(wing["shoulders"][side])
    scale=pose["span_scale"]*wing[f"{side}_scale"] if pose.get("absolute_scale") else pose["span_scale"]
    l1,l2,l3=[length*scale for length in wing["segment_lengths"]]
    a1=math.radians(pose["stroke_deg"]); a2=a1+math.radians(pose["elbow_deg"]); a3=a2+math.radians(pose["wrist_deg"])
    s=shoulder; e=add(s,(l1*math.cos(a1),l1*math.sin(a1))); w=add(e,(l2*math.cos(a2),l2*math.sin(a2))); tip=add(w,(l3*math.cos(a3),l3*math.sin(a3)))
    joints=[s,e,w,tip]; reference=wing.get("reference_mesh")
    if reference:
        ref_shoulder=tuple(reference["joints"][0]); perspective=wing[f"{side}_scale"]
        map_ref=lambda point:add(shoulder,mul(sub(tuple(point),ref_shoulder),perspective))
        rest_joints=[map_ref(point) for point in reference["joints"]]
        rest_boundary=[map_ref(point) for point in reference["boundary"]]
        rest_core=map_ref(reference["core"])
        boundary=[_skin_point(point,weights,rest_joints,joints) for point,weights in zip(rest_boundary,reference["boundary_weights"])]
        core=_skin_point(rest_core,reference["core_weights"],rest_joints,joints)
        return {"boundary":boundary,"core":core,"joints":joints}
    tangents=[sub(e,s),add(unit(sub(e,s)),unit(sub(w,e))),add(unit(sub(w,e)),unit(sub(tip,w))),sub(tip,w)]
    normals=[normal(vector) for vector in tangents]; widths=[value*pose["chord_scale"] for value in wing["chords"]]
    lead=wing["leading_fraction"]
    leading=[sub(point,mul(nrm,width*lead)) for point,nrm,width in zip(joints,normals,widths)]
    trailing=[add(point,mul(nrm,width*(1-lead))) for point,nrm,width in zip(joints,normals,widths)]
    boundary=[leading[0],leading[1],leading[2],tip,trailing[2],trailing[1],trailing[0]]
    core=(.18*s[0]+.33*e[0]+.34*w[0]+.15*tip[0],.18*s[1]+.33*e[1]+.34*w[1]+.15*tip[1])
    return {"boundary":boundary,"core":core,"joints":joints}


def sample_clip(model: dict, clip_name: str, phase: float) -> dict:
    """Reference sampler for the separate animation-clips source."""
    library = json.loads((ROOT / "source" / "animation_clips.json").read_text(encoding="utf-8"))
    clip = library["clips"][clip_name]
    phase = phase % 1.0 if clip.get("loop") else max(0.0, min(1.0, phase))
    keys = clip["keyframes"]
    if phase <= keys[0]["t"]:
        return keys[0]
    if phase >= keys[-1]["t"]:
        return keys[-1]
    for left, right in zip(keys, keys[1:]):
        if left["t"] <= phase <= right["t"]:
            u = smoothstep((phase - left["t"]) / (right["t"] - left["t"]))
            return {
                "t": phase,
                "root": [lerp(a, b, u) for a, b in zip(left["root"], right["root"])],
                "wing": [lerp(a, b, u) for a, b in zip(left["wing"], right["wing"])],
                "legs": [lerp(a, b, u) for a, b in zip(left["legs"], right["legs"])],
            }
    raise AssertionError("unreachable")


def svg_header(model: dict, variant: str, compact: bool) -> list[str]:
    palette = model["palette"]
    view_box = [55, 34, 520, 292] if compact else model["viewBox"]
    x, y, width, height = view_box
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x)} {fmt(y)} {fmt(width)} {fmt(height)}" role="img" aria-labelledby="title desc" class="percolia-bird">',
        '  <title id="title">Oiseau-réseau Percolia</title>',
        '  <desc id="desc">Oiseau triangulé Percolia avec rig, clips keyframés et scan depuis la tête.</desc>',
    ]
    if variant == "inverse":
        lines.append(f'  <rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(width)}" height="{fmt(height)}" fill="{palette["ink"]}"/>')
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
        lines.append(f'        <polygon id="{escape(face_id)}" points="{points_string(pts)}" fill="{color(fill_name, palette, variant)}" fill-opacity="{fmt(opacity)}"/>')
    lines.extend(['      </g>', '      <g id="body-edges" data-layer="edges" fill="none" stroke-linecap="round" stroke-linejoin="round">'])
    for index, (a, b, kind) in enumerate(body["edges"], 1):
        x1, y1 = body["nodes"][a][:2]
        x2, y2 = body["nodes"][b][:2]
        width, stroke, opacity = edge_styles[kind]
        lines.append(f'        <line id="body-edge-{index:02d}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{stroke}" stroke-opacity="{fmt(opacity)}" stroke-width="{fmt(width)}" data-kind="{kind}" vector-effect="non-scaling-stroke"/>')
    lines.extend(['      </g>', '      <g id="body-nodes" data-layer="nodes">'])
    for node_id, (x, y, radius, fill_name, kind) in body["nodes"].items():
        node_stroke = palette["ink"] if inverse else palette["white"]
        if mono:
            node_stroke = palette["white"]
        lines.append(f'        <circle id="body-node-{escape(node_id)}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="{color(fill_name, palette, variant)}" stroke="{node_stroke}" stroke-width="0.75" data-kind="{kind}" vector-effect="non-scaling-stroke"/>')
    lines.extend(['      </g>', '    </g>'])
    return "\n".join(lines)


def render_scatter(model: dict, variant: str) -> str:
    palette = model["palette"]
    lines = ['    <g id="bird-scatter" data-layer="scatter" opacity="0.50">']
    for node_id, (x, y, radius, fill_name, _kind) in model["scatter"].items():
        lines.append(f'      <circle id="scatter-{escape(node_id)}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="{color(fill_name, palette, variant)}"/>')
    lines.append('    </g>')
    return "\n".join(lines)


def render_wing(model: dict, variant: str, side: str, geometry: dict, opacity: float) -> str:
    palette = model["palette"]
    inverse = variant == "inverse"
    mono = variant == "mono"
    ink = palette["white"] if inverse else palette["ink"]
    wing_colors = [ink] * 7 if mono else [palette["cyan"], palette["blue"], palette["ink"], palette["cyan"], palette["blue"], palette["cyan"], palette["blue"]]
    boundary, core = geometry["boundary"], geometry["core"]
    lines = [f'    <g id="wing-{side}" data-wing-side="{side}" opacity="{fmt(opacity)}">']
    lines.append(f'      <polygon data-wing-outline="true" points="{points_string(boundary)}" fill="{palette["mist"]}" fill-opacity="{fmt(0.25 if side == "near" else 0.16)}" stroke="{ink}" stroke-width="1.55" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
    lines.append('      <g data-layer="faces">')
    for index in range(7):
        a, b = boundary[index], boundary[(index + 1) % 7]
        lines.append(f'        <polygon data-wing-face="{index}" points="{points_string([a, b, core])}" fill="{wing_colors[index]}" fill-opacity="{fmt(0.10 if side == "near" else 0.055)}"/>')
    lines.extend(['      </g>', '      <g fill="none" stroke-linecap="round" stroke-linejoin="round">'])
    for index in range(7):
        a, b = boundary[index], boundary[(index + 1) % 7]
        spoke = palette["blue"] if not mono and index in (1, 3, 5) else ink
        lines.append(f'        <line data-wing-boundary="{index}" x1="{fmt(a[0])}" y1="{fmt(a[1])}" x2="{fmt(b[0])}" y2="{fmt(b[1])}" stroke="{ink}" stroke-width="1.45" vector-effect="non-scaling-stroke"/>')
        lines.append(f'        <line data-wing-spoke="{index}" x1="{fmt(a[0])}" y1="{fmt(a[1])}" x2="{fmt(core[0])}" y2="{fmt(core[1])}" stroke="{spoke}" stroke-width="0.85" vector-effect="non-scaling-stroke"/>')
    lines.extend(['      </g>', '      <g data-layer="nodes">'])
    for index, point in enumerate(boundary):
        fill = palette["cyan"] if not mono and index in (0, 3, 5) else palette["blue"] if not mono and index in (1, 4) else ink
        lines.append(f'        <circle data-wing-node="{index}" cx="{fmt(point[0])}" cy="{fmt(point[1])}" r="{fmt(2.7 if index == 3 else 2.25)}" fill="{fill}" stroke="{palette["white"]}" stroke-width="0.65" vector-effect="non-scaling-stroke"/>')
    lines.append(f'        <circle data-wing-core="true" cx="{fmt(core[0])}" cy="{fmt(core[1])}" r="3.4" fill="{palette["cyan"] if not mono else ink}" stroke="{palette["white"]}" stroke-width="0.7" vector-effect="non-scaling-stroke"/>')
    lines.extend(['      </g>', '    </g>'])
    return "\n".join(lines)


def render_legs(model: dict, variant: str, tucked: bool) -> str:
    palette = model["palette"]
    stroke = palette["white"] if variant == "inverse" else palette["ink"]
    lines = ['    <g id="bird-legs" data-layer="legs" fill="none" stroke-linecap="round" stroke-linejoin="round">']
    for side, leg in model["legs"].items():
        opacity = 0.42 if side == "far" else 0.92
        hip, knee, ankle = map(tuple, (leg["hip"], leg["knee"], leg["ankle"]))
        if tucked:
            knee = lerp_point(hip, knee, 0.45)
            ankle = lerp_point(hip, ankle, 0.35)
        lines.append(f'      <g data-leg="{side}" opacity="{fmt(opacity)}">')
        lines.append(f'        <polyline data-leg-main="true" points="{points_string([hip, knee, ankle])}" stroke="{stroke}" stroke-width="1.55" vector-effect="non-scaling-stroke"/>')
        for index, toe in enumerate(leg["toes"]):
            toe_point = ankle if tucked else tuple(toe)
            lines.append(f'        <line data-leg-toe="{index}" x1="{fmt(ankle[0])}" y1="{fmt(ankle[1])}" x2="{fmt(toe_point[0])}" y2="{fmt(toe_point[1])}" stroke="{stroke}" stroke-width="1.05" vector-effect="non-scaling-stroke"/>')
        lines.append('      </g>')
    lines.extend(['    </g>'])
    return "\n".join(lines)


def render_lidar(model: dict) -> str:
    palette = model["palette"]
    sensor_name = model.get("scan", {}).get("origin_node", "h5")
    x, y = model["body"]["nodes"][sensor_name][:2]
    return "\n".join([
        f'    <g id="lidar-scan" data-lidar="true" transform="translate({fmt(x)} {fmt(y)})" opacity="0" pointer-events="none">',
        f'      <path data-lidar-pulse="true" d="M 0 -4 A 4 4 0 1 1 0 4 A 4 4 0 1 1 0 -4" fill="none" stroke="{palette["cyan"]}" stroke-width="1.45" vector-effect="non-scaling-stroke"/>',
        f'      <line data-lidar-rays="true" x1="0" y1="-4" x2="0" y2="-18" stroke="{palette["blue"]}" stroke-width="1.35" stroke-linecap="round" vector-effect="non-scaling-stroke"/>',
        f'      <circle data-lidar-return="true" cx="0" cy="0" r="2.4" fill="{palette["cyan"]}" opacity="0" filter="url(#scan-glow)"/>',
        '    </g>',
    ])


def render_bird(model: dict, variant: str, compact: bool) -> str:
    lines = svg_header(model, variant, compact)
    lines.append('  <defs><filter id="scan-glow" x="-300%" y="-300%" width="600%" height="600%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    lines.append(f'  <g id="percolia-bird" data-percolia-bird="true" data-model-version="{escape(model["version"])}">')
    if compact:
        lines.append(render_mesh(model, variant))
        lines.append(render_wing(model, variant, "near", wing_geometry(model, folded_pose(model, "near"), "near"), 0.96))
        lines.append(render_legs(model, variant, tucked=False))
    else:
        lines.append(render_scatter(model, variant))
        pose_far = display_pose(model, "far")
        pose_near = display_pose(model, "near")
        lines.append(render_wing(model, variant, "far", wing_geometry(model, pose_far, "far"), model["wing"]["far_opacity"]))
        lines.append(render_mesh(model, variant))
        lines.append(render_wing(model, variant, "near", wing_geometry(model, pose_near, "near"), 0.98))
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
