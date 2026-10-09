from pathlib import Path
import numpy as np,json
r=Path(__file__).resolve().parent;data=r.parent/'naval_data';out=r/'input_with_background';out.mkdir(exist_ok=True)
roi=np.load(r/'input/roi.npz');p=roi['coords'];ids=roi['original_ids'];ref=roi['reference_id'];unknown=ref<0
vertices=np.load(data/'bloc_vertices.npy');background_ids=np.load(data/'bloc_components.npz')['component_7'];f=(data/'bloc_full.ply').open()
while f.readline().strip()!='end_header':pass
for _ in range(len(vertices)):f.readline()
faces=np.array([list(map(int,l.split()[1:])) for l in f if l.strip()],np.int32);bgfaces=faces[np.isin(faces[:,0],background_ids)];assert len(bgfaces)==104

def distance2(points,tri):
 a,b,c=tri;ab=b-a;ac=c-a;n=np.cross(ab,ac);n/=np.linalg.norm(n);ap=points-a;sd=np.einsum('ij,j->i',ap,n);proj=ap-sd[:,None]*n
 d00=np.dot(ab,ab);d01=np.dot(ab,ac);d11=np.dot(ac,ac);d20=np.einsum('ij,j->i',proj,ab);d21=np.einsum('ij,j->i',proj,ac);den=d00*d11-d01*d01
 u=(d11*d20-d01*d21)/den;v=(d00*d21-d01*d20)/den;inside=(u>=0)&(v>=0)&(u+v<=1);best=np.where(inside,sd*sd,np.inf)
 for x,y in [(a,b),(b,c),(c,a)]:
  e=y-x;t=np.clip(np.einsum('ij,j->i',points-x,e)/np.dot(e,e),0,1);d=points-(x+t[:,None]*e);best=np.minimum(best,np.einsum('ij,ij->i',d,d))
 return best
u=p[unknown];d2=np.full(len(u),np.inf)
for face in bgfaces:d2=np.minimum(d2,distance2(u,vertices[face]))
bg_u=d2<=.03**2;background=np.zeros(len(p),bool);background[np.flatnonzero(unknown)[bg_u]]=True;residual=unknown&~background
coords=p[residual];rids=ids[residual];meta=json.load(open(r/'input_metadata.json'));origin=np.array(meta['quantization']['origin_m']);unit=meta['quantization']['unit_m'];q=np.rint((coords-origin)/unit).astype('<u4');q.tofile(out/'residual.xyz.u32le');rids.astype('<u4').tofile(out/'residual.ids.u32le');np.save(out/'residual_coords.npy',coords);np.save(out/'residual_original_ids.npy',rids)
np.savez_compressed(out/'roi.npz',coords=p,original_ids=ids,reference_id=ref,background=background)
meta['background_prior']={'source_mesh':'Background (component7), identified by FBX name; 104 original triangles','source_sha256':'18405ab5a78149749f6146dbc91ea8cfbb939eedfeca4c6053748ecf51f72d3f','distance':'minimum Euclidean point-to-finite-triangle distance; orthogonal interior projection and clipped edge distances','tolerance_m':.03,'semantics':'known surrounding environment, ignored context; distinct from14structureAABBs','removed_from_residual_points':int(background.sum()),'uses_anomaly_meshes':False};meta['residual_points_before_background']=meta['residual_points'];meta['residual_points']=len(coords);meta['quantization']['unique_sites']=len(np.unique(q,axis=0));meta['quantization']['max_l2_error_m']=float(np.linalg.norm(origin+q.astype(float)*unit-coords,axis=1).max());meta['input_folder']='input_with_background'
(r/'input_with_background_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps({'roi_points':len(p),'reference_points':int((ref>=0).sum()),'background_points':int(background.sum()),'residual_points':len(coords),'unique_sites':meta['quantization']['unique_sites']},indent=2))
