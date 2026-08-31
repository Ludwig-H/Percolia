#!/usr/bin/env python3
"""Structural and numerical checks for the canonical Percolia bird v2."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "source" / "bird_model.json"
CLIPS_PATH = ROOT / "source" / "animation_clips.json"

spec = importlib.util.spec_from_file_location("build_bird", ROOT / "build_bird.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import build_bird.py")
build_bird = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_bird)

model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
library = json.loads(CLIPS_PATH.read_text(encoding="utf-8"))
wing = model["wing"]
flight = model["flight"]

assert model["version"] == "2.1.0"
assert library["version"] == "2.1.0"
assert model["palette"] == {
    "ink": "#082C4C", "blue": "#1C83D4", "cyan": "#20C9C4",
    "mist": "#EAF5F7", "white": "#FFFFFF", "slate": "#5D7385",
}
assert model["art_direction"]["beak_emission"] is False
assert model["scan"]["origin_node"] == "h5"
assert flight["one_shot"] is True

static_logo = model["static_logo"]
assert static_logo["clip"] == "perched_idle"
assert static_logo["progress"] == 0.0
assert static_logo["mirror"] is True
assert static_logo["include_far_wing"] is True
assert static_logo["anchor"] == flight["perched_anchor"]
assert library["timeline"][-1]["state"] == "perched_final"
assert library["timeline"][-1]["mirror"] is True

# Rotation is around the network's visual centre, not around its feet.
body_points = [values[:2] for values in model["body"]["nodes"].values()]
centroid = [sum(point[i] for point in body_points) / len(body_points) for i in (0, 1)]
assert math.dist(centroid, flight["visual_anchor"]) < 5
assert flight["perched_anchor"][1] - flight["visual_anchor"][1] > 90
assert "flight_anchor" not in flight

# Resting wings are folded by pose, not miniaturised.
folded = wing["folded_pose"]
assert folded["span_scale"] >= 0.95
assert folded["chord_scale"] >= 0.99
assert 135 <= folded["stroke_deg"] <= 155
assert wing["shape_preservation"]["mode"] == "rigid_outline_articulated_network"
assert wing["shape_preservation"]["boundary_articulation_weight"] <= 0.03
assert wing["shape_preservation"]["interior_articulation_weight"] <= 0.25
for frame in library["clips"]["perched_idle"]["keyframes"]:
    assert frame["wing"][3] >= 0.95
    assert frame["wing"][4] >= 0.99


def perimeter(points):
    return sum(math.dist(points[i], points[(i + 1) % len(points)]) for i in range(len(points)))


def shape_signature(points):
    p = perimeter(points)
    return [
        math.dist(points[i], points[j]) / p
        for i in range(len(points))
        for j in range(i + 1, len(points))
    ]

reference = [tuple(point) for point in wing["reference_mesh"]["boundary"]]
rest_geometry = build_bird.wing_geometry(model, folded, "near")
assert perimeter(rest_geometry["boundary"]) / perimeter(reference) > 0.93

# The airborne outline is effectively invariant up to similarity.
reference_signature = None
max_delta = 0.0
for index in range(181):
    sample = build_bird.sample_clip(model, "cruise", index / 180)
    track = sample["wing"]
    pose = {
        "stroke_deg": track[0], "elbow_deg": track[1], "wrist_deg": track[2],
        "span_scale": track[3], "chord_scale": track[4],
    }
    signature = shape_signature(build_bird.wing_geometry(model, pose, "near")["boundary"])
    if reference_signature is None:
        reference_signature = signature
    else:
        max_delta = max(max_delta, max(abs(a - b) for a, b in zip(reference_signature, signature)))
assert max_delta < 0.012, max_delta

# All airborne clips keep full wing dimensions.
for clip_name in ("push_off", "takeoff", "cruise", "approach", "flare"):
    for frame in library["clips"][clip_name]["keyframes"]:
        assert frame["wing"][3] >= 0.99
        assert frame["wing"][4] >= 0.99

# A relative path begins at the exact take-off endpoint. Its first handle has
# the same direction as the terminal authored root motion; y never turns down.
world = library["world"]
assert "outbound_curve" not in world
points = world["outbound_curve_offsets"]
assert points[0] == [0, 0] and len(points) == 4
assert all(points[i + 1][0] > points[i][0] for i in range(3))
assert all(points[i + 1][1] <= points[i][1] for i in range(3))
takeoff = library["clips"]["takeoff"]["keyframes"]
terminal = [takeoff[-1]["root"][i] - takeoff[-2]["root"][i] for i in (0, 1)]
handle = points[1]
dot = sum(a * b for a, b in zip(terminal, handle)) / (math.hypot(*terminal) * math.hypot(*handle))
assert dot > 0.999
assert takeoff[-1]["wing"] == library["clips"]["cruise"]["keyframes"][0]["wing"]
assert all(takeoff[i + 1]["root"][1] <= takeoff[i]["root"][1] for i in range(len(takeoff) - 1))

# State machine and contact events remain intact.
expected_states = [
    "perched", "anticipation", "push_off", "takeoff", "outbound", "empty",
    "inbound", "approach", "flare", "touchdown", "settle", "perched_final",
]
assert [item["state"] for item in library["timeline"]] == expected_states
assert any(event["name"] == "toe_off" for event in library["clips"]["push_off"]["events"])
assert any(event["name"] == "touchdown" for event in library["clips"]["touchdown"]["events"])

js = (ROOT / "bird-animation.js").read_text(encoding="utf-8")
assert "resolvedOutboundCurve" in js
assert "outbound_curve_offsets" in js
assert "model.flight.visual_anchor" in js
assert "boundaryArticulation" in js
assert "outbound.place(\n            position" in js
assert "const fade = 1 - smoothstep(0.93" not in js
assert "takeoff_bridge_start" not in js
assert "outbound_exit_lift_px" not in js
assert "model.body.nodes.h5" in js
assert "model.body.nodes.q1.slice" not in js

html = (ROOT / "demo.html").read_text(encoding="utf-8")
assert '<script src=' not in html
assert 'fetch(' not in html
assert 'data-flight-bird="outbound"' in html
assert 'data-flight-bird="inbound"' in html
assert 'data-animation-clips="true"' in html
assert 'translate(612 0) scale(-1 1)' in html

compact_svg = (ROOT / "percolia-bird-compact.svg").read_text(encoding="utf-8")
assert 'transform="translate(612 0) scale(-1 1)"' in compact_svg
assert 'id="wing-far"' in compact_svg
assert 'id="wing-near"' in compact_svg
lockup = (ROOT.parent / "percolia-lockup-horizontal.svg").read_text(encoding="utf-8")
assert 'translate(612 0) scale(-1 1)' in lockup

for svg_path in ROOT.glob("percolia-bird-*.svg"):
    text = svg_path.read_text(encoding="utf-8").lower()
    assert 'data-lidar-ray="true"' not in text
    assert "data-lidar-beam" not in text

print("canonical Percolia network-bird v2.1, final static pose: OK")
