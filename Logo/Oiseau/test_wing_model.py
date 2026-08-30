#!/usr/bin/env python3
"""Numerical sanity tests for the parametric wing model."""
from __future__ import annotations
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("build_bird", ROOT / "build_bird.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
model = json.loads((ROOT / "source" / "bird_model.json").read_text(encoding="utf-8"))

assert model["wing"]["flight"]["period_ms"] >= 4000, "wingbeat is not slow"
stations = model["wing"]["stations"]
assert stations[0] == 0 and stations[-1] == 1
assert all(a < b for a, b in zip(stations, stations[1:])), "stations must be strictly increasing"
assert all(length > 0 for length in model["wing"]["segment_lengths"])

samples = []
for i in range(257):
    phase = i / 256
    for side in ("near", "far"):
        geometry = module.wing_geometry(model, side, phase, 1.0)
        points = geometry["leading"] + geometry["trailing"]
        assert all(math.isfinite(value) for point in points for value in point)
        assert len(points) == 2 * len(stations)
        for station in stations[:-1]:
            assert module.chord(model, station, 1.0) > 0
        samples.append((phase, side, points))

for side in ("near", "far"):
    start = module.wing_geometry(model, side, 0.0, 1.0)
    end = module.wing_geometry(model, side, 1.0, 1.0)
    error = max(math.dist(a, b) for a, b in zip(start["leading"] + start["trailing"], end["leading"] + end["trailing"]))
    assert error < 1e-7, f"cycle is not closed for {side}: {error}"

# Frame-to-frame continuity at 256 samples. Large jumps reveal a bad spline,
# angle wrap or projection singularity.
for side in ("near", "far"):
    previous = module.wing_geometry(model, side, 0.0, 1.0)
    for i in range(1, 257):
        current = module.wing_geometry(model, side, i / 256, 1.0)
        displacement = max(
            math.dist(a, b)
            for a, b in zip(previous["leading"] + previous["trailing"], current["leading"] + current["trailing"])
        )
        assert displacement < 5.0, f"discontinuous frame for {side}: {displacement}"
        previous = current

print("parametric wing model: OK")
