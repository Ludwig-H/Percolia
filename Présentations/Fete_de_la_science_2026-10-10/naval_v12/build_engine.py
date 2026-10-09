from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent;src=root/'source/morsehgp3D_v12';build=root/'build';build.mkdir(exist_ok=True)
files=sorted(src.glob('src/**/*.cpp'));print('compile units',len(files),flush=True)
base=['g++','-std=c++20','-O3','-DNDEBUG','-DMHGP12_COORD_BITS=21','-Wall','-Wextra','-Wpedantic','-Werror','-pthread','-I'+str(src/'src')]
def compile_one(path):
 obj=build/(path.relative_to(src).as_posix().replace('/','_')+'.o');cmd=base+['-c',str(path),'-o',str(obj)]
 if not obj.exists():
  r=subprocess.run(cmd,capture_output=True,text=True)
  if r.returncode:raise RuntimeError(str(path)+'\n'+r.stderr)
 return obj
start=time.monotonic(); objects=[]
with ThreadPoolExecutor(max_workers=6) as pool:
 for i,f in enumerate(as_completed([pool.submit(compile_one,p) for p in files]),1):
  objects.append(f.result())
  if i%10==0:print('compiled',i,'/',len(files),flush=True)
cmd=base+[str(src/'bench/full_probe.cpp')]+[str(o) for o in sorted(objects)]+['-o',str(build/'mhgp12_full_probe')]
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode:raise RuntimeError(r.stderr)
(root/'build_manifest.json').write_text(json.dumps({'source_commit':'ac2d5bab814e84db6e1c9340f54995aa9cda58aa','compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'flags':base[1:],'units':[str(p.relative_to(src)) for p in files],'compile_seconds':time.monotonic()-start,'executable_sha256':hashlib.sha256((build/'mhgp12_full_probe').read_bytes()).hexdigest()},indent=2))
print('built',round(time.monotonic()-start,2),'seconds',flush=True)
