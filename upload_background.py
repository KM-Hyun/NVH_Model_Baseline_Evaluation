"""Run publication independently; continuously persist progress and final result."""
from pathlib import Path
import subprocess,os,json,re,time,signal,datetime,fcntl
P=Path(__file__).resolve().parent
lock=(P/'upload_background.lock').open('w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('An upload job is already running')
state=dict(stage='starting',pid=os.getpid(),started_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),repository='https://github.com/KM-Hyun/NVH_Model_Baseline_Evaluation')
def save():
 state['updated_unix']=time.time();tmp=P/'upload_status.tmp';tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2));tmp.replace(P/'upload_status.json')
save();(P/'upload_background.pid').write_text(str(os.getpid()))
env=os.environ.copy();env.pop('GH_DEBUG',None);env['GIT_LFS_FORCE_PROGRESS']='1';env['GIT_LFS_PROGRESS']=str(P/'upload_progress.log')
subprocess.run(['git','config','--local','lfs.concurrenttransfers','8'],cwd=P,check=True)
p=subprocess.Popen(['bash','publish.sh'],cwd=P,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
state.update(stage='uploading',child_pid=p.pid);save();buffer=bytearray();rate_limited=False
with (P/'upload.log').open('a',buffering=1) as log:
 log.write('\n=== Background upload resumed '+state['started_at']+'; concurrent transfers=8 ===\n')
 while True:
  c=p.stdout.read(1)
  if not c:break
  if c not in (b'\r',b'\n'):buffer.extend(c);continue
  if not buffer:continue
  line=buffer.decode('utf-8',errors='replace');buffer.clear();log.write(line+'\n')
  m=re.search(r'Uploading LFS objects:\s*(\d+)%\s*\((\d+)/(\d+)\),\s*(.*)',line)
  if m:state.update(percent=int(m[1]),objects_uploaded=int(m[2]),objects_total=int(m[3]),transfer_summary=m[4]);save()
  if 'API rate limit exceeded' in line or 'rate limit' in line.lower():
   rate_limited=True;state.update(stage='rate_limited',error=line);save();os.killpg(p.pid,signal.SIGTERM);break
 if buffer:log.write(buffer.decode(errors='replace')+'\n')
 rc=p.wait();state['exit_code']=rc
 if not rate_limited:state['stage']='complete' if rc==0 else 'error'
 state['finished_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat();save()
 log.write('=== Background upload finished: '+state['stage']+'; exit='+str(rc)+' ===\n')
