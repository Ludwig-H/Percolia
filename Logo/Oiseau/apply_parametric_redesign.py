#!/usr/bin/env python3
"""Install, once, the clean parametric bird redesign bundled for deployment."""
from __future__ import annotations

import base64
import hashlib
import io
import shutil
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAYLOAD_DIR = HERE / ".payload"
EXPECTED_LENGTH = 31460
EXPECTED_SHA256 = "fdd07b21af69903d6557630d1b42a546c19e43db891cdd7c006613a07f26b882"

payload = "".join(
    path.read_text(encoding="utf-8")
    for path in sorted(PAYLOAD_DIR.glob("part*.txt"))
)
if len(payload) != EXPECTED_LENGTH:
    raise RuntimeError(f"incomplete payload: {len(payload)} characters")
if hashlib.sha256(payload.encode("ascii")).hexdigest() != EXPECTED_SHA256:
    raise RuntimeError("payload integrity check failed")

raw = base64.b64decode(payload)
with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
    root_resolved = ROOT.resolve()
    for member in archive.getmembers():
        target = (ROOT / member.name).resolve()
        if root_resolved not in target.parents and target != root_resolved:
            raise RuntimeError(f"unsafe archive path: {member.name}")
    archive.extractall(ROOT, filter="data")

shutil.rmtree(PAYLOAD_DIR)
Path(__file__).unlink()
print("parametric redesign sources installed")
