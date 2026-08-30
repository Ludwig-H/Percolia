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

assert model["version"] == "0.8.0"
assert wing["period_ms"] >= 2800, "wingbeat must remain deliberately slow"
assert flight["one_shot"] is True


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
        geometry = build_bird.wing_geometry(model, build_bird.periodic_pose(model, phase, side), side)
        assert polygon_area(geometry["boundary"]) > 150, "wing must keep a positive visible area"
        assert all(math.isfinite(value) for point in geometry["boundary"] for value in point)
        joints = geometry["joints"]
        expected = [length * build_bird.periodic_pose(model, phase, side)["span_scale"] for length in wing["segment_lengths"]]
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


for phase in range(101):
    t = phase / 100
    assert cubic_derivative(flight["takeoff_curve"], t)[0] > 0
    assert cubic_derivative(flight["outbound_curve"], t)[0] > 0, "outbound bird must only move left-to-right"
    assert cubic_derivative(flight["inbound_curve"], t)[0] < 0, "inbound bird must only move right-to-left"
    assert cubic_derivative(flight["landing_curve"], t)[0] <= 0

assert flight["takeoff_curve"][0] == flight["perch"]
assert flight["landing_curve"][-1] == flight["perch"]
assert flight["outbound_curve"][-1][0] > flight["stage_viewBox"][2]
assert flight["inbound_curve"][0][0] > flight["stage_viewBox"][2]

html = (ROOT / "demo.html").read_text(encoding="utf-8")
assert 'data-flight-bird="outbound"' in html
assert 'data-flight-bird="inbound"' in html
assert '<script src=' not in html
assert 'fetch(' not in html
assert 'un autre arrive depuis la direction opposée' in html

print("directional network-bird model: OK")
