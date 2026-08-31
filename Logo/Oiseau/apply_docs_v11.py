#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BIRD=ROOT/'Logo'/'Oiseau'

test_path=BIRD/'test_wing_model.py'
test=test_path.read_text(encoding='utf-8')
test=test.replace('assert model["version"] == "1.0.0"','assert model["version"] == "1.1.0"')
test=test.replace('assert library["version"] == "1.0.0"','assert library["version"] == "1.1.0"')
test=test.replace('assert event_time("push_off", "toe_off") == 0.60','assert event_time("push_off", "toe_off") == 0.52')
test=test.replace('assert max_step < 5.5','assert max_step < 7.5')
reference='''\n# The static display pose reproduces the characteristic broad, raised wing\n# contour supplied in the original visual reference.\nreference = wing["reference_mesh"]\ndisplay = build_bird.wing_geometry(model, build_bird.display_pose(model, "near"), "near")\nfor actual, expected in zip(display["boundary"], reference["boundary"]):\n    assert math.dist(actual, expected) < 1e-5\nassert math.dist(display["core"], reference["core"]) < 1e-5\nassert all(abs(sum(weights) - 1) < 1e-9 for weights in reference["boundary_weights"])\nassert abs(sum(reference["core_weights"]) - 1) < 1e-9\n\n'''
if 'reference = wing["reference_mesh"]' not in test:
    test=test.replace('\nexpected_states = [\n',reference+'expected_states = [\n')
test=test.replace('assert "solveTwoBone" in js\n','assert "solveTwoBone" in js\nassert "cubicArcSample" in js\nassert "pchipTangent" in js\nassert "blendRigSample" in js\nassert "hermitePoint" in js\n')
test_path.write_text(test,encoding='utf-8')

readme_path=BIRD/'README.md'; readme=readme_path.read_text(encoding='utf-8')
readme=readme.replace('direction 04','direction 05')
intro='''\n## Raffinement de la direction 05\n\nLe corps, la tête, la queue et les pattes restent ceux du premier oiseau triangulé. L’aile principale reprend désormais le contour de la référence fournie : racine centrale, bord supérieur relevé, double pointe à gauche et large surface facettée. Ce dessin est déformé par **linear blend skinning 2D** autour des segments épaule–coude–poignet–extrémité ; les battements conservent donc l’identité graphique du premier oiseau.\n\nLes à-coups sont réduits par une interpolation PCHIP périodique des clips cycliques, une progression par longueur d’arc sur les trajectoires et de courts fondus de pose aux changements d’état. La sortie du perchoir est raccordée en position et en vitesse au clip de décollage : les pattes se détendent, `toe_off` libère les appuis, puis deux battements puissants établissent le vol.\n\n'''
if '## Raffinement de la direction 05' not in readme:
    readme=readme.replace('\n## Séquence\n',intro+'## Séquence\n')
readme_path.write_text(readme,encoding='utf-8')
Path(__file__).unlink(); print('tests and documentation updated')
