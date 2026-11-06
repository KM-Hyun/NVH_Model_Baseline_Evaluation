"""Build aligned two/three-source datasets; no per-segment normalization."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/nvh-matplotlib')
import json,csv,time,math
import numpy as np,soundfile as sf
from scipy.signal import resample_poly,stft
import matplotlib
matplotlib.use('Agg')
from matplotlib import colormaps
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;R=P.parents[1];FS=10000;N=150000;HOP=37500;FFT=5000;FHOP=2000
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font=ImageFont.truetype(FONT,19)
def savejson(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def status(stage,**kw):savejson(P/'progress.json',dict(stage=stage,updated_unix=time.time(),**kw))
def readmono(path):
 y,sr=sf.read(path,dtype='float32',always_2d=True);y=y.mean(1);g=math.gcd(sr,FS)
 return resample_poly(y,FS//g,sr//g).astype('float32') if sr!=FS else y
status('preparing')
fanpath=R/'data/266180__acertingart__hood-fan.mp3';fan=readmono(fanpath);length=len(fan);duration=length/FS
manifest=json.loads((R/'data/CocoChorales/all_pairs_manifest.json').read_text());selected=[];a=[];b=[];position=0
for key,row in sorted(manifest['tracks'].items()):
 if row['split']!='train':continue
 src=R/'data/CocoChorales/pairs/train'/row['track'];fp=src/'flute.wav';cp=src/'clarinet.wav'
 if not fp.exists() or not cp.exists():continue
 x=readmono(fp);y=readmono(cp);assert len(x)==len(y)
 count=min(len(x),length-position)
 if count<=0:break
 a.append(x[:count]);b.append(y[:count]);selected.append(dict(track=row['track'],original_split='train',start_frame=position,end_frame=position+count,start_seconds=position/FS,end_seconds=(position+count)/FS,source_flute=str(fp),source_clarinet=str(cp)));position+=count
 if position==length:break
assert position==length,'Not enough unique paired audio'
flute=np.concatenate(a);clarinet=np.concatenate(b);del a,b
raw=[flute,clarinet,fan];rms=[float(np.sqrt(np.mean(y.astype('float64')**2))) for y in raw]
# Equal full-recording RMS for all three sources, same source gains for both tasks.
for i,y in enumerate(raw):y/=rms[i]
mix2=flute+clarinet;mix3=mix2+fan
gain=.95/max(float(np.max(abs(y))) for y in [*raw,mix2,mix3])
for y in [*raw,mix2,mix3]:y*=gain
signals=dict(flute=flute,clarinet=clarinet,hood_fan=fan,mixture_2=mix2,mixture_3=mix3)
full=P/'full_audio';full.mkdir(exist_ok=True)
for name,y in signals.items():sf.write(full/(name+'.wav'),y,FS,subtype='FLOAT')
savejson(P/'source_tracks.json',selected)
freq=np.fft.rfftfreq(FFT,1/FS).astype('float32');times=(np.arange(73)*FHOP+FFT/2)/FS
np.save(P/'frequencies_hz.npy',freq);np.save(P/'frame_times_seconds.npy',times)
starts=list(range(0,length-N+1,HOP));rows=[];joins=np.array([r['end_frame'] for r in selected[:-1]])
# Chronological splits with guard windows to prevent waveform overlap leakage.
cut1=min(joins,key=lambda x:abs(x-length*.8));cut2=min(joins,key=lambda x:abs(x-length*.9))
for idx,start in enumerate(starts):
 sid=f'sample_{idx:04d}';end=start+N;d=P/'samples'/sid;d.mkdir(parents=True,exist_ok=True)
 split='train' if end<=cut1 else 'validation' if start>=cut1 and end<=cut2 else 'test' if start>=cut2 else 'excluded_boundary'
 tracks=[r['track'] for r in selected if r['start_frame']<end and r['end_frame']>start]
 crossing=bool(np.any((joins>start)&(joins<end)))
 spect={};power={}
 for name,y in signals.items():
  clip=y[start:end];sf.write(d/(name+'.wav'),clip,FS,subtype='FLOAT')
  f,t,z=stft(clip,FS,window='hann',nperseg=FFT,noverlap=FFT-FHOP,nfft=FFT,boundary=None,padded=False,scaling='spectrum')
  assert z.shape==(2501,73) and np.allclose(t,times)
  mag=np.abs(z).astype('float32');powr=mag**2;powr[1:-1]*=2
  energy=powr.mean(axis=1);np.save(d/(name+'_stft_magnitude.npy'),mag);np.save(d/(name+'_energy_average.npy'),energy);np.save(d/(name+'_rms_spectrum.npy'),np.sqrt(energy))
  spect[name]=powr;power[name]=energy
 # Same color reference for all five panels within this sample; linear frequency STFT.
 ref=max(float(v.max()) for v in spect.values());panels=[]
 labels={'flute':'플루트','clarinet':'클라리넷','hood_fan':'후드 팬','mixture_2':'2소스 혼합음','mixture_3':'3소스 혼합음'}
 for name,powr in spect.items():
  db=10*np.log10(np.maximum(powr/max(ref,1e-20),1e-10));rgba=colormaps['magma'](np.clip((db+80)/80,0,1));img=Image.fromarray((rgba[::-1,:,:3]*255).astype('uint8')).resize((730,350),Image.Resampling.NEAREST)
  canvas=Image.new('RGB',(810,420),'white');canvas.paste(img,(65,35));draw=ImageDraw.Draw(canvas);draw.text((65,4),f'{labels[name]} · {start/FS:.2f}~{end/FS:.2f}초',font=font,fill='black')
  for hz in [0,1000,2000,3000,4000,5000]:draw.text((5,365-hz/5000*340),str(hz),font=font,fill='black')
  for sec in [0,5,10,15]:draw.text((65+sec/15*700,387),str(sec),font=font,fill='black')
  draw.text((350,387),'시간(초)',font=font,fill='black');canvas.save(d/(name+'_spectrogram.png'));panels.append(canvas)
 for task,names in [('Source_2',['flute','clarinet','mixture_2']),('Source_3',['flute','clarinet','hood_fan','mixture_3'])]:
  td=P/task/sid;td.mkdir(parents=True,exist_ok=True)
  for name in names:
   for suffix in ['.wav','_stft_magnitude.npy','_energy_average.npy','_rms_spectrum.npy','_spectrogram.png']:
    link=td/(name+suffix)
    if not link.exists():link.symlink_to(Path('../../samples')/sid/(name+suffix))
 if idx in [0,30,60]:
  overview=Image.new('RGB',(1620,1260),'white')
  for i,im in enumerate(panels):overview.paste(im,((i%2)*810,(i//2)*420))
  overview.save(P/f'preview_{sid}.png')
 assert np.max(np.abs(mix3[start:end]-(flute[start:end]+clarinet[start:end]+fan[start:end])))<1e-5
 rows.append(dict(sample_id=sid,start_seconds=start/FS,end_seconds=end/FS,split=split,track_join=crossing,instrument_tracks=';'.join(tracks)))
 if idx%20==0:status('processing',completed_samples=idx+1,total_samples=len(starts));print(idx+1,len(starts),flush=True)
with (P/'samples.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
counts={k:sum(r['split']==k for r in rows) for k in ['train','validation','test','excluded_boundary']}
config=dict(sample_rate=FS,duration_seconds=duration,source_samples=length,segment_seconds=15,segment_overlap=.75,segment_hop_seconds=3.75,n_fft=5000,fft_window_seconds=.5,fft_overlap=.6,fft_hop_seconds=.2,fft_window='periodic Hann',resolution_hz=2,stft_shape=[2501,73],magnitude_scaling='abs(rfft(windowed signal))/sum(window)',energy_average='mean_t(one_sided_power); interior frequencies doubled; DC/Nyquist not doubled',rms_spectrum='sqrt(energy_average)',full_recording_rms=rms,shared_gain=gain,normalization='full-recording equal RMS, shared peak gain; no segment peak or power compression',sample_count=len(rows),splits=counts,track_count=len(selected),tail_unused_seconds=(length-(starts[-1]+N))/FS)
savejson(P/'config.json',config)
(P/'README.md').write_text('''# NVH Model Baseline Evaluation\n\nSource_2: flute + clarinet. Source_3: flute + clarinet + hood_fan. Source_2/3各フォルダはsamples/の共有ファイルへの相対シンボリックリンクで重複保存を回避。\n\n전체 길이는 후드 팬에 맞춤. 후드 팬은 stereo 평균으로 mono 변환. 10kHz로 anti-alias 리샘플링: Nyquist5kHz, FFT5000점→2Hz 간격, FFT윈도0.5초/Hann, overlap60%(hop0.2초). 15초/overlap75%(hop3.75초), 마지막15초미만 구간 제외. 구간당2501주파수×73프레임. STFT magnitude와 Energy Average 파워 스펙트럼(2501,), sqrt평균파워 RMS spectrum 함께 제공. Energy Average는 시간 프레임의 파워 평균이며 시간축 없는1차원; magnitude 평균·복소FFT평균과 다름. 스펙트로그램은 평균전 STFT 파워. 그림의5소스는 구간별 공통최대 대비-80~0dB, 선형주파수축. 학습수치는 dB가 아닌 선형값. 주파수빈2Hz는 주기적Hann의 실제 분해능/대역폭과 같다는 뜻 아님.\n\n악기별동기화 유지해 서로 다른 원본곡을 순차 연결, 반복없음. 연결부 crossfade/무음제거 없음; 샘플별 track_join 표시, source_tracks.json에 경계. 경계구간은 별도 제외할 수 있음. 3개 원음의 전체RMS 동일 조정 후 두혼합음및모든정답에 같은공통gain 적용(원본음압 보존아님). 소스별 구간 최대정규화 없음. WAV FLOAT32. 파형합검증완료. magnitude/power는 위상때문에 소스별단순합과 일치하지 않음.\n\n학습/검증/평가 80/10/10 시간구간 분할, 경계 넘는 중첩샘플은excluded_boundary. 원본 악기곡 경계에 가까운 위치로 분할 경계를 조정해 동일 곡의 분할 간 중복을 방지. 후드 팬도 하나의녹음이며 미지기기 검증이 아님. 원본CocoChorales train에서 추출한 사용자정의분할.\n\n파일: full_audio/전체5파형; samples.csv/샘플목록; samples/개별WAV와STFT npy, energy_average npy,rms_spectrum npy,PNG; Source_2/3 과제별파일; config.json/조건; preview_sample*.png/미리보기. 원본데이터는변경하지않음.\n\nCocoChorales CC BY4.0 https://magenta.tensorflow.org/datasets/cocochorales / 후드팬 https://freesound.org/people/acertingart/sounds/266180/ 원본라이선스참조.\n'''.replace('Source_2/3各フォルダはsamples/の共有ファイルへの相対シンボリックリンクで重複保存を回避。','Source_2/3는 samples/의 공유 파일을 상대 링크로 참조.'))
html=['<meta charset="utf-8"><h1>2소스 / 3소스 미리듣기</h1>']
for idx in [0,30,60]:
 sid=f'sample_{idx:04d}';html.append(f'<h2>{sid}</h2><img width="900" src="preview_{sid}.png">')
 for name in signals:html.append(f'<p>{name}</p><audio controls preload="none" src="samples/{sid}/{name}.wav"></audio>')
(P/'청취목록.html').write_text('\n'.join(html));status('complete',completed_samples=len(rows),total_samples=len(rows),duration_seconds=duration,splits=counts);print(json.dumps(config),flush=True)
