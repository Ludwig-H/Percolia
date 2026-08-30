#!/usr/bin/env python3
"""Apply the self-contained game-animation update, then remove the installer."""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parent / ".game_update"
PACKAGE = PACKAGE_DIR / "payload.zlib"
EXPECTED_SHA256 = "33706a194f496b573eb8fe0f26cffd66245b74a93ecac080b8f6f32938b399d4"
EXPECTED_FILES = 12

raw = PACKAGE.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if actual != EXPECTED_SHA256:
    raise RuntimeError(f"invalid game-animation payload: {actual}")

payload = json.loads(zlib.decompress(raw).decode("utf-8"))
if len(payload) != EXPECTED_FILES:
    raise RuntimeError(f"unexpected payload size: {len(payload)}")

for relative, encoded in payload.items():
    destination = REPO / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(base64.b64decode(encoded))

# Remove transient deployment material and bytecode before the workflow commits.
shutil.rmtree(PACKAGE_DIR)
for cache in (REPO / "Logo").rglob("__pycache__"):
    shutil.rmtree(cache)
Path(__file__).unlink()

print(f"applied {len(payload)} game-animation source files")
