#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BIRD = ROOT / 'Logo' / 'Oiseau'

model_path = BIRD / 'source' / 'bird_model.json'
model = json.loads(model_path.read_text(encoding='utf-8'))
model['version'] = '1.1.0'
wing = model['wing']
ref_joints = [[306.0,184.0],[254.0,164.0],[212.0,118.0],[192.0,54.0]]
lengths = [math.dist(a,b) for a,b in zip(ref_joints, ref_joints[1:])]
angles = [math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])) % 360 for a,b in zip(ref_joints,ref_joints[1:])]
wing.update({
  'shoulders': {'near':[306.0,184.0], 'far':[290.0,179.0]},
  'segment_lengths': lengths,
  'chords': [30.0,42.0,29.0,1.6],
  'far_phase_offset': 0.018,
  'near_scale': 1.0,
  'far_scale': 0.88,
  'far_opacity': 0.27,
  'leading_fraction': 0.34,
  'glide_phase': 0.08,
  'display_pose': {
    'stroke_deg': angles[0], 'elbow_deg': angles[1]-angles[0],
    'wrist_deg': angles[2]-angles[1], 'span_scale':1.0, 'chord_scale':1.0,
  },
  'reference_mesh': {
    'joints': ref_joints,
    'boundary': [[306.0,184.0],[330.0,146.0],[292.0,104.0],[192.0,54.0],[170.0,96.0],[220.0,144.0],[262.0,158.0]],
    'core': [244.0,126.0],
    'boundary_weights': [[1,0,0],[.82,.18,0],[.12,.78,.10],[0,0,1],[0,.16,.84],[.10,.64,.26],[.74,.26,0]],
    'core_weights': [.18,.62,.20],
  },
})
wing['folded_pose'] = {'stroke_deg':176.0,'elbow_deg':38.0,'wrist_deg':48.0,'span_scale':.58,'chord_scale':.72}
model['art_direction'].update({
  'reference_profile':'original_upright_network_bird',
  'wing_deformation':'linear_blend_skinning',
  'preserve_reference_wing_mesh':True,
})
model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

clips_path = BIRD / 'source' / 'animation_clips.json'
lib = json.loads(clips_path.read_text(encoding='utf-8'))
lib['version'] = '1.1.0'
for entry in lib['timeline']:
    if entry['state']=='anticipation': entry['duration_ms']=760
    elif entry['state']=='push_off': entry['duration_ms']=600
    elif entry['state']=='takeoff': entry['duration_ms']=1450
    elif entry['state']=='inbound': entry['duration_ms']=4400
blend = {'anticipation':140,'push_off':110,'takeoff':170,'outbound':260,'approach':260,'flare':150,'touchdown':120,'settle':160,'perched_final':180}
for entry in lib['timeline']:
    if entry['state'] in blend: entry['blend_in_ms']=blend[entry['state']]

lib['clips']['perched_idle']['keyframes'] = [
 {'t':0.0,'root':[0,0,0,1],'wing':[176,38,48,.58,.72],'legs':[0,.05,1]},
 {'t':.5,'root':[0,0,.45,1],'wing':[174,39,49,.58,.72],'legs':[0,.08,1]},
 {'t':1.0,'root':[0,0,0,1],'wing':[176,38,48,.58,.72],'legs':[0,.05,1]},
]
lib['clips']['anticipation_push']['keyframes'] = [
 {'t':0.0,'root':[0,0,0,1],'wing':[176,38,48,.58,.72],'legs':[0,.08,1]},
 {'t':.30,'root':[0,0,-1.5,.995],'wing':[184,31,36,.68,.79],'legs':[0,.24,1]},
 {'t':.68,'root':[0,0,-6.5,1.0],'wing':[218,18,16,.88,.94],'legs':[0,1.0,1]},
 {'t':1.0,'root':[0,0,-11,1.015],'wing':[238,12,10,1,1],'legs':[0,.72,1]},
]
lib['clips']['anticipation_push']['events']=[{'t':.68,'name':'maximum_crouch'}]
lib['clips']['push_off']['keyframes'] = [
 {'t':0.0,'root':[0,0,-11,1.015],'wing':[238,12,10,1,1],'legs':[0,.72,1]},
 {'t':.28,'root':[0,0,-15,1.02],'wing':[230,9,7,1,1],'legs':[0,.34,1]},
 {'t':.50,'root':[0,0,-19,1.03],'wing':[196,8,6,1,1],'legs':[0,0,1]},
 {'t':.58,'root':[8,-12,-20,1.035],'wing':[174,9,7,1,1],'legs':[.18,0,0]},
 {'t':1.0,'root':[40,-62,-18,1.03],'wing':[138,11,9,1,1],'legs':[.75,0,0]},
]
lib['clips']['push_off']['events']=[{'t':.52,'name':'toe_off'}]
lib['clips']['takeoff']['keyframes'] = [
 {'t':0.0,'root':[0,0,-18,1.03],'wing':[138,11,9,1,1],'legs':[.75,0,0]},
 {'t':.18,'root':[23,-50,-20,1.04],'wing':[188,25,30,.80,.86],'legs':[.90,0,0]},
 {'t':.40,'root':[55,-108,-22,1.05],'wing':[238,12,10,1.02,1],'legs':[1,0,0]},
 {'t':.59,'root':[82,-149,-23,1.03],'wing':[143,9,7,1,1],'legs':[1,0,0]},
 {'t':.80,'root':[108,-178,-22,1.01],'wing':[206,26,34,.80,.86],'legs':[1,0,0]},
 {'t':1.0,'root':[140,-196,-20,1.0],'wing':[232,10,7,1,1],'legs':[1,0,0]},
]
lib['clips']['takeoff']['events']=[{'t':.59,'name':'second_power_stroke'}]
lib['clips']['cruise']['keyframes'] = [
 {'t':0.0,'root':[0,-2,-2,1],'wing':[232,10,7,1,1],'legs':[1,0,0]},
 {'t':.22,'root':[0,0,-1,1],'wing':[190,9,7,1,1],'legs':[1,0,0]},
 {'t':.48,'root':[0,4,1,1],'wing':[142,12,10,1,1],'legs':[1,0,0]},
 {'t':.72,'root':[0,1,0,1],'wing':[184,34,48,.74,.82],'legs':[1,0,0]},
 {'t':1.0,'root':[0,-2,-2,1],'wing':[232,10,7,1,1],'legs':[1,0,0]},
]
approach = lib['clips']['approach']['keyframes']
approach[0]['root'][2] = -11
approach[0]['wing'] = [208,16,16,1,1]
approach[1]['root'][2] = -7
approach[2]['root'][2] = -1
lib['world']['outbound_curve']=[[415,355],[635,258],[1015,160],[1460,128]]
lib['world']['inbound_curve']=[[1460,198],[1120,216],[690,315],[505,360]]
clips_path.write_text(json.dumps(lib, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
Path(__file__).unlink()
print('model and clips refined to v1.1')
