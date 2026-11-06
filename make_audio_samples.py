#!/usr/bin/env python3
"""Create aligned source/mix WAV segments only (no STFT or images)."""
from pathlib import Path
from contextlib import ExitStack
import argparse,csv,json,math
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-dir',type=Path,default=ROOT/'full_audio')
 p.add_argument('--output',type=Path,default=ROOT/'audio_samples')
 p.add_argument('--sample-seconds',type=float,default=15)
 p.add_argument('--overlap',type=float,default=.75,help='Fraction, e.g. 0.75 = 75 percent')
 p.add_argument('--task',choices=['2','3','both'],default='both')
 p.add_argument('--limit',type=int,help='Optional number of first samples for a quick check')
 args=p.parse_args()
 if not math.isfinite(args.sample_seconds) or args.sample_seconds<=0 or not 0<=args.overlap<1:p.error('Use a positive sample duration and 0 <= overlap < 1')
 if args.limit is not None and args.limit<1:p.error('--limit must be positive')
 if args.output.exists() and any(args.output.iterdir()):p.error('Output directory is not empty. Choose a new --output path.')
 names=['flute','clarinet']+(['hood_fan'] if args.task!='2' else [])
 infos={n:sf.info(args.input_dir/(n+'.wav')) for n in names}
 first=infos['flute'];sr=first.samplerate;length=first.frames
 if any(i.channels!=1 or i.samplerate!=sr or i.frames!=length for i in infos.values()):p.error('Sources must be aligned mono WAVs with equal sample rates and lengths')
 n=round(args.sample_seconds*sr);hop=round(n*(1-args.overlap))
 if n<1 or hop<1 or n>length:p.error('Invalid window/hop for the available audio')
 starts=range(0,length-n+1,hop)
 if args.limit is not None:starts=list(starts)[:args.limit]
 # Reference metadata belongs specifically to the supplied full-length files.
 tracks=json.loads((ROOT/'source_tracks.json').read_text())
 if sr!=10000 or tracks[-1]['end_frame']!=length:p.error('This split metadata requires the supplied 10 kHz full_audio files')
 boundaries=[t['end_frame'] for t in tracks[:-1]];c1=min(boundaries,key=lambda x:abs(x-length*.8));c2=min(boundaries,key=lambda x:abs(x-length*.9))
 args.output.mkdir(parents=True,exist_ok=True);rows=[]
 tasks=['2','3'] if args.task=='both' else [args.task]
 with ExitStack() as stack:
  readers={name:stack.enter_context(sf.SoundFile(args.input_dir/(name+'.wav'))) for name in names}
  for idx,start in enumerate(starts):
   end=start+n;sid=f'sample_{idx:04d}';clips={}
   for name,f in readers.items():f.seek(start);clips[name]=f.read(n,dtype='float32');assert len(clips[name])==n
   split='train' if end<=c1 else 'validation' if start>=c1 and end<=c2 else 'test' if start>=c2 else 'excluded_boundary'
   active=[t['track'] for t in tracks if t['start_frame']<end and t['end_frame']>start]
   for task in tasks:
    dest=args.output/('Source_'+task)/sid;dest.mkdir(parents=True,exist_ok=True)
    sources=['flute','clarinet']+(['hood_fan'] if task=='3' else [])
    mixed=clips['flute']+clips['clarinet']
    if task=='3':mixed=mixed+clips['hood_fan']
    for name in sources:sf.write(dest/(name+'.wav'),clips[name],sr,subtype='FLOAT')
    sf.write(dest/'mixture.wav',mixed,sr,subtype='FLOAT')
    row=dict(task='Source_'+task,sample_id=sid,start_seconds=start/sr,end_seconds=end/sr,split=split,track_join=len(active)>1,instrument_tracks=';'.join(active),mixture=str((dest/'mixture.wav').relative_to(args.output)),flute=str((dest/'flute.wav').relative_to(args.output)),clarinet=str((dest/'clarinet.wav').relative_to(args.output)),hood_fan=str((dest/'hood_fan.wav').relative_to(args.output)) if task=='3' else '')
    rows.append(row)
   if (idx+1)%50==0:print(f'{idx+1}/{len(starts)} segments written',flush=True)
 with (args.output/'samples.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 for task in tasks:
  for split in ['train','validation','test']:
   (args.output/f'Source_{task}_{split}.txt').write_text('\n'.join(r['mixture'] for r in rows if r['task']=='Source_'+task and r['split']==split)+'\n')
 summary=dict(sample_rate=sr,channels=1,subtype='FLOAT',input_duration_seconds=length/sr,sample_seconds=n/sr,overlap=1-hop/n,hop_seconds=hop/sr,samples_per_task=len(starts),tasks=tasks,split_boundary_seconds=[c1/sr,c2/sr],split_counts_per_task={s:sum(r['split']==s and r['task']=='Source_'+tasks[0] for r in rows) for s in ['train','validation','test','excluded_boundary']},normalization='none; retain the full_audio source gains',mixing='sample-wise source sum; FLOAT32',original_track_boundaries_preserved=True)
 (args.output/'settings.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
