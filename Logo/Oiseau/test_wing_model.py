#!/usr/bin/env python3
"""Numerical and structural checks for the game-style network-bird rig."""
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

assert model["version"] == "1.0.0"
assert library["version"] == "1.0.0"
assert wing["period_ms"] >= 2800, "the cruise wingbeat must stay deliberately slow"
assert flight["one_shot"] is True
assert model["art_direction"]["preserve_palette"] is True
assert model["art_direction"]["preserve_network_silhouette"] is True
assert model["art_direction"]["scan_origin"] == "head_node_h5"
assert model["art_direction"]["beak_emission"] is False


def polygon_area(points: list[tuple[float, float]]) -> float:
    return abs(sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )) / 2


# The underlying network wing geometry remains closed, continuous and valid.
for side in ("near", "far"):
    start = build_bird.wing_geometry(model, build_bird.periodic_pose(model, 0.0, side), side)
    end = build_bird.wing_geometry(model, build_bird.periodic_pose(model, 1.0, side), side)
    for a, b in zip(start["boundary"], end["boundary"]):
        assert math.dist(a, b) < 1e-7

    previous = None
    max_step = 0.0
    for index in range(361):
        phase = index / 360
        pose = build_bird.periodic_pose(model, phase, side)
        geometry = build_bird.wing_geometry(model, pose, side)
        assert polygon_area(geometry["boundary"]) > 150
        assert all(math.isfinite(value) for point in geometry["boundary"] for value in point)
        expected = [length * pose["span_scale"] for length in wing["segment_lengths"]]
        measured = [math.dist(geometry["joints"][i], geometry["joints"][i + 1]) for i in range(3)]
        assert max(abs(a - b) for a, b in zip(expected, measured)) < 1e-6
        if previous is not None:
            max_step = max(max_step, max(
                math.dist(a, b)
                for a, b in zip(previous["boundary"], geometry["boundary"])
            ))
        previous = geometry
    assert max_step < 5.5


expected_states = [
    "perched",
    "anticipation",
    "push_off",
    "takeoff",
    "outbound",
    "empty",
    "inbound",
    "approach",
    "flare",
    "touchdown",
    "settle",
    "perched_final",
]
assert [item["state"] for item in library["timeline"]] == expected_states
assert all(item["duration_ms"] > 0 for item in library["timeline"])

required_clips = {
    "perched_idle",
    "anticipation_push",
    "push_off",
    "takeoff",
    "cruise",
    "approach",
    "flare",
    "touchdown",
    "settle",
}
assert required_clips <= set(library["clips"])

for name, clip in library["clips"].items():
    frames = clip["keyframes"]
    times = [frame["t"] for frame in frames]
    assert times == sorted(times), f"unsorted keyframes in {name}"
    assert times[0] == 0 and times[-1] == 1
    for frame in frames:
        assert len(frame["root"]) == 4
        assert len(frame["wing"]) == 5
        assert len(frame["legs"]) == 3
        assert all(math.isfinite(value) for track in ("root", "wing", "legs") for value in frame[track])
        assert frame["root"][3] > 0
        assert 0 < frame["wing"][3] <= 1.1
        assert 0 < frame["wing"][4] <= 1.1
        assert all(0 <= value <= 1 for value in frame["legs"])
    for event in clip.get("events", []):
        assert 0 <= event["t"] <= 1
        assert event["name"]


def event_time(clip_name: str, event_name: str) -> float:
    return next(
        event["t"]
        for event in library["clips"][clip_name]["events"]
        if event["name"] == event_name
    )


assert event_time("push_off", "toe_off") == 0.60
assert event_time("touchdown", "touchdown") < event_time("touchdown", "weight_transfer")
assert event_time("touchdown", "touchdown") == 0.72

# Root-motion continuity at clip boundaries.
def root_xy(clip: str, endpoint: int) -> list[float]:
    return library["clips"][clip]["keyframes"][endpoint]["root"][:2]


assert root_xy("approach", -1) == root_xy("flare", 0)
assert root_xy("flare", -1) == root_xy("touchdown", 0)
assert root_xy("touchdown", -1) == [0, 0]
assert all(frame["root"][:2] == [0, 0] for frame in library["clips"]["settle"]["keyframes"])

perch = flight["perch"]
inbound_end = library["world"]["inbound_curve"][-1]
approach_start = root_xy("approach", 0)
assert inbound_end == [perch[0] + approach_start[0], perch[1] + approach_start[1]]
assert library["world"]["outbound_curve"][0] == [415, 355]


def cubic_derivative(points: list[list[float]], t: float) -> tuple[float, float]:
    p0, p1, p2, p3 = points
    u = 1 - t
    return (
        3 * u * u * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0]),
        3 * u * u * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1]),
    )


for index in range(101):
    t = index / 100
    assert cubic_derivative(library["world"]["outbound_curve"], t)[0] > 0
    assert cubic_derivative(library["world"]["inbound_curve"], t)[0] < 0

js = (ROOT / "bird-animation.js").read_text(encoding="utf-8")
assert "solveTwoBone" in js
assert "motion warp" in js.lower() or "warp" in js.lower()
assert "toe_off" in js
assert "touchdown" in js
assert "model.body.nodes.h5" in js
assert "model.body.nodes.q1.slice" not in js
assert "staticOpacity" not in js

html = (ROOT / "demo.html").read_text(encoding="utf-8")
assert 'data-flight-bird="outbound"' in html
assert 'data-flight-bird="inbound"' in html
assert 'data-animation-clips="true"' in html
assert '<script src=' not in html
assert 'fetch(' not in html
assert 'PRÉPARATION' in html
assert 'TOE-OFF' in html
assert 'TOUCHDOWN' in html
assert 'PATTES VERROUILLÉES' in html

print("game-style network-bird animation: OK")

# The scan is head-mounted and no graphical element is emitted by the beak.
for svg_path in ROOT.glob("percolia-bird-*.svg"):
    svg_text = svg_path.read_text(encoding="utf-8").lower()
    assert 'data-lidar-ray="true"' not in svg_text
    assert "data-lidar-beam" not in svg_text
assert model["scan"]["origin_node"] == "h5"
assert model["palette"] == {
    "ink": "#082C4C", "blue": "#1C83D4", "cyan": "#20C9C4",
    "mist": "#EAF5F7", "white": "#FFFFFF", "slate": "#5D7385",
}
