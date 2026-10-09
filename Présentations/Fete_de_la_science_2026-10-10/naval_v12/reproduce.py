"""Replay the pinned v12 tower and external coverage from the published input snapshot.

The ROI and the geometry-filtered input mask are preserved in result.npz.
prepare_data.py / prepare_background.py document the original preprocessing.
This runner does not use published candidate labels to select components.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
import numpy as np

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source-dir',type=Path,help='Predownloaded morsehgp3D_v12 folder; otherwise fetch pinned sources');ap.add_argument('--work-dir',type=Path,help='New empty replay directory');args=ap.parse_args();here=Path(__file__).resolve().parent;report=json.load(open(here/'naval_v12_report.json'));work=args.work_dir or Path(tempfile.mkdtemp(prefix='naval-v12-replay-'))
 if work.exists() and any(work.iterdir()):raise RuntimeError('Replay directory must be empty; existing files are preserved')
 work.mkdir(parents=True,exist_ok=True)
 for name in ['source_tree.json','download_source.py','build_engine.py','export_prior.cpp','export_full_only.cpp']:shutil.copy2(here/name,work/name)
 if args.source_dir:shutil.copytree(args.source_dir,work/'source/morsehgp3D_v12')
 else:subprocess.run([sys.executable,str(work/'download_source.py')],cwd=work.parent,check=True)
 tree=json.load(open(work/'source_tree.json'));source=work/'source'
 for item in tree['files']:
  raw=(source/item['path']).read_bytes();got=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  if got!=item['sha']:raise RuntimeError('Upstream source mismatch: '+item['path'])
 subprocess.run([sys.executable,str(work/'build_engine.py')],check=True)
 base=['g++','-std=c++20','-O3','-DNDEBUG','-DMHGP12_COORD_BITS=21','-Wall','-Wextra','-Wpedantic','-Werror','-pthread','-I'+str(work/'source/morsehgp3D_v12/src')];objects=[str(p) for p in sorted((work/'build').glob('*.o'))]
 for name in ['export_prior','export_full_only']:subprocess.run(base+[str(work/(name+'.cpp'))]+objects+['-o',str(work/'build'/name)],check=True)
 published=np.load(here/'result.npz');mask=published['v12_input_mask'];coords=published['coords'][mask];ids=published['original_ids'][mask];q=report['input']['quantization'];origin=np.array(q['origin_m']);unit=q['unit_m'];xyz=np.rint((coords-origin)/unit).astype('<u4')
 if not np.array_equal(xyz,published['quantized_coords'][mask]):raise RuntimeError('Published quantization mismatch')
 xyz.tofile(work/'xyz.u32le');ids.astype('<u4').tofile(work/'ids.u32le');sel=report['selection'];cmd=[str(work/'build/export_prior'),str(work/'xyz.u32le'),str(work/'ids.u32le'),'3','8',str(work/'replay'),sel['cut_radius_squared_quantized_numerator'],sel['cut_radius_squared_quantized_denominator']];subprocess.run(cmd,check=True)
 stats=json.load(open(work/'replay.stats.json'));cut=np.loadtxt(work/'replay.cut_k3_incidences.tsv',skiprows=1,dtype=np.uint32)
 if len(cut)!=stats['cut_strong_incidences']:raise RuntimeError('Incomplete cut export')
 pairs=np.unique(cut[:,:2],axis=0);nodes,counts=np.unique(pairs[:,1],return_counts=True);selected=nodes[counts>=report['parameters']['min_cluster_size_original_points']];pairs=pairs[np.isin(pairs[:,1],selected)];sites=np.loadtxt(work/'replay.sites.tsv',skiprows=1,dtype=np.uint32);site_ids=np.empty(len(ids),np.uint32);site_ids[sites[:,0]]=sites[:,1]
 actual=np.column_stack((site_ids[pairs[:,0]],pairs[:,1]));expected=np.column_stack((published['original_ids'][published['class_id']==1],published['cluster_id'][published['class_id']==1]));actual=actual[np.lexsort((actual[:,1],actual[:,0]))];expected=expected[np.lexsort((expected[:,1],expected[:,0]))]
 if not np.array_equal(actual,expected):raise RuntimeError('Candidate memberships differ from published result')
 # Separate native exporter avoids mixing transactionally synced FULL with diagnostic text streams.
 subprocess.run([str(work/'build/export_full_only'),str(work/'xyz.u32le'),str(work/'ids.u32le'),'3','8',str(work/'full')],check=True)
 digest=sha(work/'full/full.bin')
 if digest!=report['hierarchy']['uncompressed_sha256']:raise RuntimeError('Native FULL digest mismatch')
 result={'status':'passed','input_points':len(ids),'Kmax':3,'native_FULL_sha256':digest,'candidate_memberships_identical':True,'selected_components':len(selected),'geometry_stage':'published original ROI and geometry-filtered mask replayed; see preparation scripts for original prior computation'};(work/'replay_check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
