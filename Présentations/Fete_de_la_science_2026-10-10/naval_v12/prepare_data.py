from pathlib import Path
import json,hashlib
import numpy as np
root=Path(__file__).resolve().parent;data=root.parent/'naval_data';out=root/'input';out.mkdir(exist_ok=True)
scan=np.load(data/'scan_points.npy',mmap_mode='r');analysis=json.loads((data/'model_analysis.json').read_text());refs=analysis['reference_boxes']
roof=next(x for x in analysis['mesh_components'] if x['fbx_name']=='Cube_3')
refs=refs+[{'name':'Cube_3_CAD_AABB_margin0.03m','min':(np.array(roof['min'])-.03).tolist(),'max':(np.array(roof['max'])+.03).tolist(),'source':'FBX Cube_3 bounds; external declared margin'}]
lo=np.min([r['min'] for r in refs],axis=0)-.2;hi=np.max([r['max'] for r in refs],axis=0)+.2
ids=np.flatnonzero(np.all((scan>=lo)&(scan<=hi),axis=1));coords=np.asarray(scan[ids]);classes=np.full(len(ids),-1,np.int32);multiplicity=np.zeros(len(ids),np.uint8)
for c,r in enumerate(refs):
 mask=np.all((coords>=np.array(r['min']))&(coords<=np.array(r['max'])),axis=1);classes[(classes==-1)&mask]=c;multiplicity[mask]+=1
unknown=classes==-1;ucoords=coords[unknown];uids=ids[unknown]
# Isotropic quantization, same unit on all axes. No voxel sampling, every residual input point retained.
origin=ucoords.min(0);extent=float(np.max(ucoords.max(0)-origin));unit=extent/((1<<21)-1);q=np.rint((ucoords-origin)/unit).astype('<u4')
assert np.all(q<(1<<21));np.savez_compressed(out/'roi.npz',coords=coords,original_ids=ids,reference_id=classes,reference_multiplicity=multiplicity)
np.save(out/'residual_coords.npy',ucoords);np.save(out/'residual_original_ids.npy',uids)
q.tofile(out/'residual.xyz.u32le');uids.astype('<u4').tofile(out/'residual.ids.u32le')
# Small spatial representative pilot only for compilation/first timing, not used in the final result.
voxel=np.floor((ucoords-origin)/.10).astype(np.int32);_,pilot=np.unique(voxel,axis=0,return_index=True);pilot=np.sort(pilot)
q[pilot].tofile(out/'pilot.xyz.u32le');uids[pilot].astype('<u4').tofile(out/'pilot.ids.u32le')
meta={'source_scan_sha256':json.loads((data/'source_manifest.json').read_text())['scan']['sha256'],'scan_points':len(scan),'roi_points':len(coords),'reference_supported_points':int((~unknown).sum()),'residual_points':len(ucoords),'roi_bounds_m':{'min':lo.tolist(),'max':hi.tolist()},'prior_type':'AABB membership, same min/max rule as original Marie notebook; 14th box derived from identified CAD Cube_3 plus 3 cm margin','priors':refs,'sampling':{'method':'none','all_roi_points_preserved':True,'all_residual_points_input_to_v12':True},'quantization':{'bits':21,'origin_m':origin.tolist(),'unit_m':unit,'isotropic':True,'rounding':'numpy.rint ties to even','max_l2_error_m':float(np.linalg.norm(origin+q.astype(np.float64)*unit-ucoords,axis=1).max()),'unique_sites':len(np.unique(q,axis=0))},'pilot_points':len(pilot),'pilot_sampling':'first original point per 10 cm voxel; pilot only, not final output','preregistered_readout':{'Kmax':3,'radius_m':.04,'min_cluster_size':200,'intended_view':'native K1 tree closed cut exact single linkage; K3 incidence view experimental if supported','unknown_semantics':'candidate outside declared geometric reference, no anomaly ground truth used'}}
(root/'input_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps({k:meta[k] for k in ['scan_points','roi_points','reference_supported_points','residual_points','quantization','pilot_points','preregistered_readout']},indent=2))
