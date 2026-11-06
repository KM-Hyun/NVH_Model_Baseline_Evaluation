"""Verify/extract original sources and recreate the local baseline dataset."""
from pathlib import Path
import argparse,json,hashlib,tarfile,shutil,subprocess,sys
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=P/'generated');parser.add_argument('--verify-only',action='store_true');parser.add_argument('--extract-only',action='store_true');args=parser.parse_args()
manifest=json.loads((P/'source_manifest.json').read_text());archive=P/'source_audio.tar.gz'
h=hashlib.sha256()
with archive.open('rb') as f:
 for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
if h.hexdigest()!=manifest['archive_sha256']:raise RuntimeError('Archive SHA256 mismatch; run git lfs pull and check the download')
print('Archive SHA256 verified',flush=True)
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers()
 for m in members:
  if m.issym() or m.islnk() or not (args.output/m.name).resolve().is_relative_to(args.output.resolve()) or not m.isfile():raise RuntimeError('Unexpected archive member')
 if args.verify_only:
  expected={r['path']:r for r in manifest['files']}
  for m in members:
   if m.name in expected:
    data=t.extractfile(m).read();r=expected.pop(m.name)
    if len(data)!=r['bytes'] or hashlib.sha256(data).hexdigest()!=r['sha256']:raise RuntimeError('Member checksum mismatch: '+m.name)
  if expected:raise RuntimeError('Missing source members')
  print('All original source-file checksums verified');raise SystemExit(0)
 args.output.mkdir(parents=True,exist_ok=True)
 for m in members:
  dest=args.output/m.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('wb') as f:shutil.copyfileobj(t.extractfile(m),f)
out=args.output/'data/NVH_Model_Baseline_Evaluation';out.mkdir(parents=True,exist_ok=True)
for name in ['prepare.py','분할검증.py']:shutil.copyfile(P/name,out/name)
print('Original sources extracted to',args.output.resolve(),flush=True)
if not args.extract_only:
 subprocess.run([sys.executable,str(out/'prepare.py')],check=True)
 subprocess.run([sys.executable,str(out/'분할검증.py')],check=True)
 print('Dataset ready:',out.resolve())
