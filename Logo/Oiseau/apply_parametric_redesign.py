#!/usr/bin/env python3
"""Install, once, the clean parametric bird redesign bundled for deployment."""
from __future__ import annotations

import base64
import io
import shutil
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAYLOAD_DIR = HERE / ".payload"

payload = "".join(
    path.read_text(encoding="utf-8")
    for path in sorted(PAYLOAD_DIR.glob("part*.txt"))
)
raw = base64.b64decode(payload)

with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
    root_resolved = ROOT.resolve()
    for member in archive.getmembers():
        target = (ROOT / member.name).resolve()
        if root_resolved not in target.parents and target != root_resolved:
            raise RuntimeError(f"unsafe archive path: {member.name}")
    archive.extractall(ROOT)

shutil.rmtree(PAYLOAD_DIR)
Path(__file__).unlink()
print("parametric redesign sources installed")
