#!/usr/bin/env python3
"""Numerical checks for the directional network-bird model."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "source" / "bird_model.json"

spec = importlib.util.spec_from_file_location("build_bird", ROOT / "build_bird.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import build_bird.py")
build_bird = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_bird)

model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
wing = model["wing"]
flight = model["flight"]

assert model["version"] == "0.9.0"
assert wing["period_ms"] >= 2800, "wingbeat must remain deliberately slow"
assert flight["one_shot"] is True
assert list(flight["timeline_ms"]) == [
    "initial_perch",
    "preload",
    "takeoff",
    "outbound",
    "empty",
    "inbound",
    "flare",
    "touchdown",
    "settle",
    "final_hold",
]
assert flight["timeline_ms"]["preload"] >= 450
assert flight["timeline_ms"]["flare"] >= 850
assert flight["timeline_ms"]["touchdown"] >= 500
assert flight["timeline_ms"]["settle"] >= 650


def polygon_area(points: list[tuple[float, float]]) -> float:
    return abs(sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )) / 2


for side in ("near", "far"):
    start = build_bird.wing_geometry(model, build_bird.periodic_pose(model, 0.0, side), side)
    end = build_bird.wing_geometry(model, build_bird.periodic_pose(model, 1.0, side), side)
    for a, b in zip(start["boundary"], end["boundary"]):
        assert math.dist(a, b) < 1e-7, "wing cycle must close exactly"

    previous = None
    max_step = 0.0
    tip_y: list[float] = []
    for index in range(361):
        phase = index / 360
        pose = build_bird.periodic_pose(model, phase, side)
        geometry = build_bird.wing_geometry(model, pose, side)
        assert polygon_area(geometry["boundary"]) > 150, "wing must keep a positive visible area"
        assert all(math.isfinite(value) for point in geometry["boundary"] for value in point)
        joints = geometry["joints"]
        expected = [length * pose["span_scale"] for length in wing["segment_lengths"]]
        measured = [math.dist(joints[i], joints[i + 1]) for i in range(3)]
        assert max(abs(a - b) for a, b in zip(expected, measured)) < 1e-6
        tip_y.append(joints[-1][1])
        if previous is not None:
            max_step = max(max_step, max(math.dist(a, b) for a, b in zip(previous["boundary"], geometry["boundary"])))
        previous = geometry
    assert max(tip_y) - min(tip_y) > 120, "the wing must visibly flap"
    assert max_step < 5.5, "frame-to-frame deformation must stay continuous"


def cubic_derivative(points: list[list[float]], t: float) -> tuple[float, float]:
    p0, p1, p2, p3 = points
    u = 1 - t
    return (
        3 * u * u * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0]),
        3 * u * u * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1]),
    )


def direction_cosine(a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] * b[0] + a[1] * b[1]) / (math.hypot(*a) * math.hypot(*b))


for phase in range(101):
    t = phase / 100
    takeoff = cubic_derivative(flight["takeoff_curve"], t)
    outbound = cubic_derivative(flight["outbound_curve"], t)
    inbound = cubic_derivative(flight["inbound_curve"], t)
    flare = cubic_derivative(flight["flare_curve"], t)
    touchdown = cubic_derivative(flight["touchdown_curve"], t)
    assert takeoff[0] > 0 and takeoff[1] < 0
    assert outbound[0] > 0, "outbound bird must only move left-to-right"
    assert inbound[0] < 0, "inbound bird must only move right-to-left"
    assert flare[0] < 0 and flare[1] > 0
    assert touchdown[0] <= 1e-9 and touchdown[1] > 0

assert flight["takeoff_curve"][-1] == flight["outbound_curve"][0]
assert flight["inbound_curve"][-1] == flight["flare_curve"][0]
assert flight["flare_curve"][-1] == flight["touchdown_curve"][0]

for first, second in (
    (flight["takeoff_curve"], flight["outbound_curve"]),
    (flight["inbound_curve"], flight["flare_curve"]),
    (flight["flare_curve"], flight["touchdown_curve"]),
):
    assert direction_cosine(cubic_derivative(first, 1.0), cubic_derivative(second, 0.0)) > 0.95

perch = flight["perch"]
perched_anchor = flight["perched_anchor"]
flight_anchor = flight["flight_anchor"]
scale = flight["perched_scale"]
expected_contact_position = [
    perch[0] - (perched_anchor[0] - flight_anchor[0]) * scale,
    perch[1] - (perched_anchor[1] - flight_anchor[1]) * scale,
]
angle = math.radians(flight["takeoff_pitch_deg"])
local_x = (perched_anchor[0] - flight_anchor[0]) * scale
local_y = (perched_anchor[1] - flight_anchor[1]) * scale
rotated_x = local_x * math.cos(angle) - local_y * math.sin(angle)
rotated_y = local_x * math.sin(angle) + local_y * math.cos(angle)
expected_release_position = [
    perch[0] - rotated_x,
    perch[1] - flight["takeoff_release_lift"] - rotated_y,
]
assert max(abs(a - b) for a, b in zip(flight["takeoff_curve"][0], expected_release_position)) < 1e-3
assert max(abs(a - b) for a, b in zip(flight["touchdown_curve"][-1], expected_contact_position)) < 1e-9
assert flight["outbound_curve"][-1][0] > flight["stage_viewBox"][2]
assert flight["inbound_curve"][0][0] > flight["stage_viewBox"][2]

html = (ROOT / "demo.html").read_text(encoding="utf-8")
assert 'data-flight-bird="outbound"' in html
assert 'data-flight-bird="inbound"' in html
assert '<script src=' not in html
assert 'fetch(' not in html
assert 'un autre arrive depuis la direction opposée' in html
for label in ("PRÉPARATION", "ARRONDI", "CONTACT", "STABILISATION"):
    assert label in html

print("directional network-bird model: OK")
