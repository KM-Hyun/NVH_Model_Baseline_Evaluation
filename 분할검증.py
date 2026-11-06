from pathlib import Path
import json,csv
import numpy as np,soundfile as sf
P=Path(__file__).resolve().parent;cfg=json.loads((P/'config.json').read_text());tracks=json.loads((P/'source_tracks.json').read_text());length=cfg['source_samples'];boundaries=[r['end_frame'] for r in tracks[:-1]];c1=min(boundaries,key=lambda x:abs(x-length*.8));c2=min(boundaries,key=lambda x:abs(x-length*.9))
with (P/'samples.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
for r in rows:
 a=round(float(r['start_seconds'])*10000);b=round(float(r['end_seconds'])*10000);r['split']='train' if b<=c1 else 'validation' if a>=c1 and b<=c2 else 'test' if a>=c2 else 'excluded_boundary'
with (P/'samples.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
sets={}
for split in ['train','validation','test']:
 sets[split]={t for r in rows if r['split']==split for t in r['instrument_tracks'].split(';')}
assert not sets['train']&sets['validation'] and not sets['train']&sets['test'] and not sets['validation']&sets['test']
for a,b in [('train','validation'),('validation','test')]:assert max(float(r['end_seconds']) for r in rows if r['split']==a)<=min(float(r['start_seconds']) for r in rows if r['split']==b)
for split in ['train','validation','test']:
 (P/(split+'_samples.txt')).write_text('\n'.join(r['sample_id'] for r in rows if r['split']==split)+'\n')
for idx in [0,len(rows)//2,len(rows)-1]:
 d=P/'samples'/rows[idx]['sample_id'];signals={k:sf.read(d/(k+'.wav'))[0] for k in ['flute','clarinet','hood_fan','mixture_2','mixture_3']}
 assert all(len(y)==150000 for y in signals.values())
 assert np.max(abs(signals['mixture_2']-signals['flute']-signals['clarinet']))<1e-6
 assert np.max(abs(signals['mixture_3']-signals['mixture_2']-signals['hood_fan']))<1e-6
 for k in signals:
  m=np.load(d/(k+'_stft_magnitude.npy'));e=np.load(d/(k+'_energy_average.npy'));assert m.shape==(2501,73) and e.shape==(2501,)
  p=m*m;p[1:-1]*=2;assert np.allclose(p.mean(1),e,rtol=1e-5,atol=1e-12)
  assert (P/'Source_2'/rows[idx]['sample_id']/'mixture_2.wav').exists()
counts={s:sum(r['split']==s for r in rows) for s in ['train','validation','test','excluded_boundary']};cfg.update(splits=counts,split_boundary_seconds=[c1/10000,c2/10000],split_strategy='chronological, snapped to original instrument-track boundaries; overlapping boundary windows excluded');(P/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2))
p=P/'README.md';s=p.read_text().replace('같은 원본곡이 인접분할에 걸칠 수 있어 미지곡일반화 평가로 해석하면 안 됨.','원본 악기곡 경계에 맞춰 분할하여 같은 곡이 서로 다른 분할에 들어가지 않도록 검증.');p.write_text(s)
status=json.loads((P/'progress.json').read_text());status['splits']=counts;(P/'progress.json').write_text(json.dumps(status,indent=2));(P/'validation.json').write_text(json.dumps(dict(passed=True,checks=['three sampled WAV sum checks','STFT shape and energy-average equivalence','no source track shared across splits','no waveform time overlap across splits','relative source links resolve'],splits=counts),indent=2));print(cfg)
