from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import urllib.request,hashlib,json,time
root=Path(__file__).resolve().parent; manifest=json.loads((root/'source_tree.json').read_text());commit=manifest['commit']; done=[]
def download(t):
 path=root/'source'/t['path'];path.parent.mkdir(parents=True,exist_ok=True)
 url='https://raw.githubusercontent.com/Ludwig-H/E-HGP/'+commit+'/'+t['path']
 if path.exists():raw=path.read_bytes()
 else:
  for attempt in range(3):
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=18) as f:raw=f.read()
    break
   except Exception:
    if attempt==2:raise
  path.write_bytes(raw)
 sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if sha!=t['sha']:raise RuntimeError('Git blob mismatch: '+t['path'])
 return {'path':t['path'],'git_blob':sha,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
with ThreadPoolExecutor(max_workers=8) as pool:
 futures={pool.submit(download,t):t for t in manifest['files']}
 for i,f in enumerate(as_completed(futures),1):
  try:done.append(f.result())
  except Exception as e:print('FAILED',futures[f]['path'],str(e),flush=True)
  if i%25==0:print('downloaded',i,'/',len(futures),flush=True)
(root/'download_manifest.json').write_text(json.dumps({'commit':commit,'files':sorted(done,key=lambda x:x['path'])},indent=2))
print('verified',len(done),'/',len(manifest['files']),flush=True)
if len(done)!=len(manifest['files']):raise SystemExit(1)
