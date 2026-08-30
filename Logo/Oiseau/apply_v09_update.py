#!/usr/bin/env python3
"""One-shot installer for the v0.9 bird kinematics update."""
from __future__ import annotations

import base64
import hashlib
import io
import shutil
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAYLOAD = HERE / ".v09_update"
EXPECTED_SHA256 = "cde8ab1888c01aa15de649a8a0f71873c3227151c6b85a1010e58018d5f793fa"

encoded = "".join(path.read_text(encoding="ascii") for path in sorted(PAYLOAD.glob("part*.txt")))
raw = base64.b64decode(encoded, validate=True)
if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
    raise RuntimeError("v0.9 payload integrity check failed")

root_resolved = ROOT.resolve()
with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
    for member in archive.getmembers():
        target = (ROOT / member.name).resolve()
        if target != root_resolved and root_resolved not in target.parents:
            raise RuntimeError(f"unsafe archive path: {member.name}")
    archive.extractall(ROOT, filter="data")

shutil.rmtree(PAYLOAD)
Path(__file__).unlink()
print("v0.9 bird kinematics sources installed")
