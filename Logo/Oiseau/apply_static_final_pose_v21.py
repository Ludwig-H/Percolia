#!/usr/bin/env python3
"""One-shot migration: align the static logo bird with the final perched frame."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGO_ROOT = ROOT.parent


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"expected source block not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# The stable logo must be the final animation pose: inbound bird, facing left.
model_path = ROOT / "source" / "bird_model.json"
model = json.loads(model_path.read_text(encoding="utf-8"))
model["version"] = "2.1.0"
model["static_logo"] = {
    "clip": "perched_idle",
    "progress": 0.0,
    "mirror": True,
    "anchor": model["flight"].get("perched_anchor", [306, 285]),
    "include_far_wing": True,
    "description": "final inbound perched frame, facing left",
}
model["art_direction"]["static_logo_pose"] = "final inbound perch, facing left"
model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

clips_path = ROOT / "source" / "animation_clips.json"
clips = json.loads(clips_path.read_text(encoding="utf-8"))
clips["version"] = "2.1.0"
clips_path.write_text(json.dumps(clips, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

builder = ROOT / "build_bird.py"
replace_once(
    builder,
    '    view_box = [55, 34, 520, 292] if compact else model["viewBox"]',
    '    view_box = [32, 34, 544, 292] if compact else model["viewBox"]',
)
replace_once(
    builder,
    '''def display_pose(model: dict, side: str) -> dict:\n    pose = dict(model["wing"]["display_pose"])\n    pose["span_scale"] *= model["wing"][f"{side}_scale"]\n    pose["chord_scale"] *= math.sqrt(model["wing"][f"{side}_scale"])\n    return pose\n\n\ndef _transform_by_bone''',
    '''def display_pose(model: dict, side: str) -> dict:\n    pose = dict(model["wing"]["display_pose"])\n    pose["span_scale"] *= model["wing"][f"{side}_scale"]\n    pose["chord_scale"] *= math.sqrt(model["wing"][f"{side}_scale"])\n    return pose\n\n\ndef static_perched_pose(model: dict, side: str) -> dict:\n    \"\"\"Return the exact wing pose used by the final perched animation frame.\"\"\"\n    config = model.get("static_logo", {})\n    frame = sample_clip(\n        model,\n        config.get("clip", "perched_idle"),\n        float(config.get("progress", 0.0)),\n    )\n    stroke, elbow, wrist, span, chord = frame["wing"]\n    side_scale = model["wing"][f"{side}_scale"]\n    return {\n        "stroke_deg": stroke + (-2.0 if side == "far" else 0.0),\n        "elbow_deg": elbow + (1.0 if side == "far" else 0.0),\n        "wrist_deg": wrist + (1.5 if side == "far" else 0.0),\n        "span_scale": span * side_scale,\n        "chord_scale": chord * math.sqrt(side_scale),\n    }\n\n\ndef _transform_by_bone''',
)
replace_once(
    builder,
    '''    lines.append(f'  <g id="percolia-bird" data-percolia-bird="true" data-model-version="{escape(model["version"])}">')\n    if compact:\n        lines.append(render_mesh(model, variant))\n        lines.append(render_wing(model, variant, "near", wing_geometry(model, folded_pose(model, "near"), "near"), 0.96))\n        lines.append(render_legs(model, variant, tucked=False))\n    else:''',
    '''    static_logo = model.get("static_logo", {})\n    transform = ""\n    if compact and static_logo.get("mirror", False):\n        anchor = static_logo.get("anchor", model["flight"].get("perched_anchor", [306, 285]))\n        transform = f' transform="translate({fmt(2 * anchor[0])} 0) scale(-1 1)"'\n    lines.append(f'  <g id="percolia-bird" data-percolia-bird="true" data-model-version="{escape(model["version"])}"{transform}>')\n    if compact:\n        pose_far = static_perched_pose(model, "far")\n        pose_near = static_perched_pose(model, "near")\n        if static_logo.get("include_far_wing", True):\n            lines.append(render_wing(\n                model, variant, "far", wing_geometry(model, pose_far, "far"),\n                model["wing"]["far_opacity"],\n            ))\n        lines.append(render_mesh(model, variant))\n        lines.append(render_wing(model, variant, "near", wing_geometry(model, pose_near, "near"), 0.98))\n        lines.append(render_legs(model, variant, tucked=False))\n    else:''',
)

lockups = LOGO_ROOT / "build_lockups.py"
replace_once(
    lockups,
    '"Mot-symbole en petites capitales avec le modèle d’oiseau-réseau initial, perché sur le P.",',
    '"Mot-symbole en petites capitales avec l’oiseau-réseau dans la pose finale, tourné vers la gauche et perché sur le P.",',
)
replace_once(
    lockups,
    '# Local foot point (306,285) is mapped to the top of the P.',
    '# The mirrored final pose keeps the local perch point (306,285) fixed on the P.',
)
replace_once(
    lockups,
    '"Signature centrée avec le petit oiseau-réseau perché sur le P.")',
    '"Signature centrée avec l’oiseau-réseau de la pose finale, tourné vers la gauche et perché sur le P.")',
)
replace_once(
    lockups,
    '"P distinctif, petites capitales et retour au premier oiseau-réseau.",',
    '"P distinctif, petites capitales et pose finale de l’oiseau-réseau tournée vers la gauche.",',
)
replace_once(
    lockups,
    '<text class="text small" x="92" y="124">Retour au modèle d’oiseau en réseau initial, avec ailes déformables et vol directionnel.</text>',
    '<text class="text small" x="92" y="124">Le logo statique reprend la dernière pose de l’animation : l’oiseau est perché et regarde vers la gauche.</text>',
)

readme = ROOT / "README.md"
readme_text = readme.read_text(encoding="utf-8")
marker = "## Principes géométriques\n"
section = '''## Logo statique\n\nLes signatures principales utilisent désormais la **dernière pose de l’animation** : le second oiseau, arrivé depuis la droite, reste perché sur le `P` et regarde vers la gauche. La pose provient directement du clip `perched_idle`, avec les deux ailes visibles. Le miroir est effectué autour du point d’appui, de sorte que les pattes restent exactement au même endroit sur le `P`.\n\n'''
if section not in readme_text:
    if marker not in readme_text:
        raise RuntimeError("README insertion marker missing")
    readme_text = readme_text.replace(marker, section + marker, 1)
readme.write_text(readme_text, encoding="utf-8")

source_readme = ROOT / "source" / "README.md"
source_text = source_readme.read_text(encoding="utf-8")
source_text = source_text.replace(
    "les points d’ancrage et les contraintes graphiques.",
    "les points d’ancrage, les contraintes graphiques et la pose finale utilisée par le logo statique.",
)
if "`static_logo`" not in source_text:
    source_text += "\nLe bloc `static_logo` désigne le clip, le point d’appui et le miroir horizontal de la pose finale exportée.\n"
source_readme.write_text(source_text, encoding="utf-8")

test = ROOT / "test_wing_model.py"
replace_once(test, 'assert model["version"] == "2.0.0"', 'assert model["version"] == "2.1.0"')
replace_once(test, 'assert library["version"] == "2.0.0"', 'assert library["version"] == "2.1.0"')
replace_once(
    test,
    '''assert flight["one_shot"] is True\n\n# Rotation is around the network's visual centre, not around its feet.''',
    '''assert flight["one_shot"] is True\n\nstatic_logo = model["static_logo"]\nassert static_logo["clip"] == "perched_idle"\nassert static_logo["progress"] == 0.0\nassert static_logo["mirror"] is True\nassert static_logo["include_far_wing"] is True\nassert static_logo["anchor"] == flight["perched_anchor"]\nassert library["timeline"][-1]["state"] == "perched_final"\nassert library["timeline"][-1]["mirror"] is True\n\n# Rotation is around the network's visual centre, not around its feet.''',
)
replace_once(
    test,
    '''assert 'data-animation-clips="true"' in html\n\nfor svg_path in ROOT.glob("percolia-bird-*.svg"):''',
    '''assert 'data-animation-clips="true"' in html\nassert 'translate(612 0) scale(-1 1)' in html\n\ncompact_svg = (ROOT / "percolia-bird-compact.svg").read_text(encoding="utf-8")\nassert 'transform="translate(612 0) scale(-1 1)"' in compact_svg\nassert 'id="wing-far"' in compact_svg\nassert 'id="wing-near"' in compact_svg\nlockup = (ROOT.parent / "percolia-lockup-horizontal.svg").read_text(encoding="utf-8")\nassert 'translate(612 0) scale(-1 1)' in lockup\n\nfor svg_path in ROOT.glob("percolia-bird-*.svg"):''',
)
replace_once(
    test,
    'print("canonical Percolia network-bird v2: OK")',
    'print("canonical Percolia network-bird v2.1, final static pose: OK")',
)

# Keep the repository clean after the workflow commits the canonical sources.
Path(__file__).unlink()
print("applied static final-pose migration v2.1")
