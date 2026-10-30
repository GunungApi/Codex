"""P068: source-grounded early microbial Orwell. Runtime media remain in artifacts.
Reuse the approved VOICEVOX Shikoku Metan voice and exact decoder-time procedure.
No fonts, voice engine/model, or credentials are redistributed with the episode.
"""
from pathlib import Path
import os,sys,json,math,types,subprocess,urllib.request,hashlib,time,shutil
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt
ROOT=Path('p068_v1').resolve(); SR=48000; FPS=24
for sub in ['audio/raw','assets','render','review','source','docs','deliverables']:(ROOT/sub).mkdir(parents=True,exist_ok=True)
PARTS=[
('この海には、地球が生まれる前から、','In this ocean, before Earth was born,',0),
('生命がいた。','life already existed.',0),
('オリオン腕の惑星、オーウェル。','Orwell, a planet in the Orion’s Arm setting.',1),
('約七十三億年前から、初期生命の時代へ。','Its early-life period begins around 7.3 billion years ago.',1),
('海の中へ、ぐっと近づこう。','Let us look closer, beneath the water.',2),
('小さな住人たちが、見えてくる。','Tiny inhabitants come into view.',2),
('主役は、単純なつくりの微生物。','The inhabitants are simple microorganisms.',3),
('水に漂い、周囲とやり取りする。','They drift and exchange material with their surroundings.',3),
('周りの有機物を取り込み、','They take up surrounding organic material',4),
('生きるための材料と、エネルギーを得る。','to obtain material and energy for living.',4),
('酸素を使わずに生きる。','They live without using oxygen.',5),
('そんな生命が、この海にいた。','Such organisms inhabited this ocean.',5),
('火山活動は、まだ盛ん。','Volcanic activity was still intense.',6),
('熱を好む住人も、多かった。','Many inhabitants thrived in heat.',6),
('最初に生まれた、正確な時刻は分からない。','The exact time of the first life remains unknown.',7),
('ここで見るのは、初期生命の時代の入口だ。','We are visiting the opening of its early-life period.',7),
('岩と水が変わる、そのかたわらで、','Alongside the changing rocks and water,',8),
('小さな命の営みが続いていた。','the activities of tiny life continued.',8),
('地球より先に始まった、','Beginning long before Earth,',9),
('この海の、大きな物語。','a vast story in a microscopic world.',9)]
READINGS={'オリオン腕':'オリオンわん','七十三億年前':'ななじゅうさんおくねんまえ','初期生命':'しょきせいめい','微生物':'びせいぶつ','有機物':'ゆうきぶつ','周囲':'しゅうい','取り込み':'とりこみ','酸素':'さんそ','火山活動':'かざんかつどう','営み':'いとなみ','入口':'いりぐち','オーウェル':'オーウェル'}
SOURCES=[
 {'id':'O1','title':'Orwell, Geological Periods','author':'TSSL','publisher':'Orion’s Arm Universe Project','url':'https://www.orionsarm.com/eg-article/546a05829e265','checked':'2026-10-30','supports':'Period boundary around 7.3 billion years ago; simple bacterial life; exact origin of life unknown. The boundary is not a precise birthday.'},
 {'id':'O2','title':'The Early Evolutionary History of Orwell','author':'TSSL','publisher':'Orion’s Arm Universe Project','url':'https://www.orionsarm.com/eg-article/54749a15e55ef','checked':'2026-10-30','supports':'Earliest organisms prokaryotic and heterotrophic; early anaerobic setting; persistent volcanism and high temperature; many organisms thermophilic. Later organelles, photosynthesis and macroscopic animals excluded.'},
 {'id':'P1','title':'平穏暦全史 第3巻 詳細制作計画 第1.0版 P068','supports':'Project framing, scope, source separation, simple cell reconstruction and organic material uptake.'}]
def dump(path,obj):Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args,**kw):return subprocess.run(args,check=True,**kw)
def acquire_runtime():
 cache=Path('runtime');cache.mkdir(exist_ok=True)
 url='https://github.com/VOICEVOX/voicevox_engine/releases/download/0.25.2/voicevox_engine-linux-cpu-x64-0.25.2.vvpp'
 pieces=[(0,129169125,'engine_range_0.bin','4da9d1e2dbb883d7a9732d3232e50f7a1e726d744d24b278f5dedeacbfd89141'),(1689641293,1911613160,'engine_range_1.bin','839b6f1b1846157fee6d680b083741ece4e31045a31e9952bb1441773b0cbd2e')]
 for a,b,name,sha in pieces:
  dest=cache/name
  if not dest.exists():
   for attempt in range(3):
    try:
     req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}','User-Agent':'OrionArmProduction/1.0'})
     with urllib.request.urlopen(req,timeout=120) as response:
      if response.status!=206:raise RuntimeError('Official runtime did not honor range request')
      with dest.open('wb') as f:shutil.copyfileobj(response,f,1024*1024)
     assert dest.stat().st_size==b-a+1
     assert hashlib.sha256(dest.read_bytes()).hexdigest()==sha
     break
    except Exception:
     dest.unlink(missing_ok=True)
     if attempt==2:raise
     time.sleep(2)
  assert hashlib.sha256(dest.read_bytes()).hexdigest()==sha
  print('RUNTIME_PART_VERIFIED',name,dest.stat().st_size,flush=True)
 core=cache/'voicevox_core_0.16.1.zip'
 if not core.exists():
  with urllib.request.urlopen('https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.1/voicevox_core-linux-x64-0.16.1.zip',timeout=120) as response,core.open('wb') as f:shutil.copyfileobj(response,f,1024*1024)

def music(tl,narration):
 n=len(narration);t=np.arange(n,dtype=np.float64)/SR;rng=np.random.default_rng(68030)
 bed=np.zeros(n);fx=np.zeros(n)
 for j,freq in enumerate([98.,146.832,196.,246.942,293.665]):
  bed+=.006*np.sin(2*np.pi*freq*t+.5*np.sin(t*.19+j))*(.65+.35*np.sin(t*.11+j)**2)
 air=sosfilt(butter(2,[220,3500],fs=SR,btype='bandpass',output='sos'),rng.standard_normal(n))
 bed+=air*.002
 events=[]
 for i,c in enumerate(tl['cues']):
  if i in [1,5,8,9,13,15,18]:
   st=c['start'];length=.65 if i!=8 else .42;k=min(n-round(st*SR),round(length*SR));u=np.arange(k)/SR
   sweep=sosfilt(butter(2,[140,2800],fs=SR,btype='bandpass',output='sos'),rng.standard_normal(k))
   env=np.sin(np.pi*u/length)**2*np.exp(-u*3)
   wave=(sweep*.022+np.sin(2*np.pi*(110*u+210*u*u))*.018)*env
   a=round(st*SR);fx[a:a+k]+=wave;events.append({'cue':i+1,'time':st,'kind':'restrained discovery or transfer accent'})
 # The underscore follows speech; it never competes with narration.
 env=sosfilt(butter(2,7,fs=SR,output='sos'),np.abs(narration));duck=np.clip(1-env*20,.25,1)
 fade=np.minimum(1,t/.7)*np.minimum(1,(tl['duration']-t)/.8)
 music_stereo=np.stack([bed,bed*.96+np.roll(air,500)*.0005],-1)*duck[:,None]*fade[:,None]
 sf.write(ROOT/'audio/music.wav',music_stereo,SR,subtype='PCM_24');sf.write(ROOT/'audio/effects.wav',fx,SR,subtype='PCM_24')
 mix=np.stack([narration,narration],-1)*.92+music_stereo+fx[:,None]
 sf.write(ROOT/'audio/mix_before_normalization.wav',mix,SR,subtype='PCM_24')
 first=subprocess.run(['ffmpeg','-hide_banner','-i',str(ROOT/'audio/mix_before_normalization.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 log=first.stderr;stats=json.loads(log[log.rfind('{'):log.rfind('}')+1]);dump(ROOT/'review/loudness_first_pass.json',stats)
 filt='loudnorm=I=-16:TP=-1.5:LRA=9:linear=true:measured_I='+stats['input_i']+':measured_TP='+stats['input_tp']+':measured_LRA='+stats['input_lra']+':measured_thresh='+stats['input_thresh']+':offset='+stats['target_offset']
 run(['ffmpeg','-y','-v','error','-i',str(ROOT/'audio/mix_before_normalization.wav'),'-af',filt,'-ar','48000','-c:a','pcm_s24le',str(ROOT/'audio/master.wav')])
 dump(ROOT/'audio/effect_events.json',events)

def voice():
 acquire_runtime()
 src=Path(__file__).with_name('p064_v2_film.py').read_text();src=src[:src.index("VERT='''")]
 src=src.replace("ROOT=Path('p064_v2').resolve()","ROOT=Path('p068_v1').resolve()")
 src=src.replace("spoken=text.replace('尾は','おは').replace('二重に','にじゅうに')","spoken=text\n   for original,reading in READINGS.items():spoken=spoken.replace(original,reading)")
 # Slightly quicker delivery, preserving phrase-level breaths and the approved voice.
 src=src.replace('speedScale=1.03','speedScale=1.08')
 module=types.ModuleType('p068_voice');module.__file__=__file__;module.READINGS=READINGS
 exec(compile(src,'p068_approved_voice_infrastructure','exec'),module.__dict__);module.PARTS=PARTS
 tl,narration=module.voice();music(tl,narration)
 dump(ROOT/'docs/sources.json',SOURCES);dump(ROOT/'docs/pronunciation_dictionary.json',READINGS)
 kana=''.join(c['kana'] for c in tl['cues']);normalized=''.join(ch for ch in kana if 'ァ'<=ch<='ヺ' or ch=='ー')
 for reading in ['オリオンワン','ナナジュウサンオクネンマエ','ビセイブツ','ユウキブツ','サンソ','カザンカツドウ']:
  assert reading in normalized,('Reading check failed',reading,normalized)
 dump(ROOT/'review/readings_verified.json',{'checks':['オリオン腕＝オリオンわん','七十三億年前＝ななじゅうさんおくねんまえ','微生物＝びせいぶつ','有機物＝ゆうきぶつ','酸素＝さんそ'],'method':'Generated synthesis kana plus actual waveform sample counts; no claim of auditory listening.','passed':True})
 shutil.copy(__file__,ROOT/'source/p068_audio.py');shutil.copy(Path(__file__).with_name('p064_v2_film.py'),ROOT/'source/p064_v2_film.py')
 print('P068_AUDIO_READY',json.dumps({'duration':tl['duration'],'frames':round(tl['duration']*24),'max_gap':tl['max_query_speech_gap'],'cues':len(tl['cues'])}),flush=True)
if __name__=='__main__':voice()
