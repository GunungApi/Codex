"""P041: build the edit from original speech, never from character counts."""
from pathlib import Path
import json, re, math, hashlib, wave, subprocess, shutil
import numpy as np
from scipy.ndimage import maximum_filter1d, gaussian_filter1d
from PIL import ImageFont
ROOT=Path('p041'); FPS=24; SR=48000
for folder in ['audio','captions','validation','assets','code','clips','reference']:
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
def put(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readwav(p):
    with wave.open(str(p),'rb') as f:
        assert f.getframerate()==SR and f.getnchannels()==1 and f.getsampwidth()==2
        return np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').copy()
def writewav(p,a):
    a=np.asarray(a);channels=1 if a.ndim==1 else a.shape[1]
    with wave.open(str(p),'wb') as f:
        f.setnchannels(channels);f.setsampwidth(2);f.setframerate(SR);f.writeframes(np.clip(a*32767,-32768,32767).astype('<i2').tobytes())
def phrase_clock(q):
    speed=q['speedScale']; t=round(q['prePhonemeLength']/speed*93.75)/93.75
    groups=[];moras=[];begin=t;kana=''
    for ap in q['accent_phrases']:
        for m in ap['moras']:
            st=t
            for field in ['consonant_length','vowel_length']:
                if m.get(field) is not None:t+=round(m[field]/speed*93.75)/93.75
            moras.append(dict(text=m['text'],start=st,end=t,vowel=m['vowel']))
            kana+=m['text']
        if ap.get('is_interrogative') and ap['moras'][-1]['pitch']>0:
            t+=round(.15/speed*93.75)/93.75
        pause=ap.get('pause_mora')
        if pause:
            groups.append(dict(start=begin,end=t,kana=kana));kana=''
            length=q.get('pauseLength') if q.get('pauseLength') is not None else pause['vowel_length']
            t+=round(length*q.get('pauseLengthScale',1)/speed*93.75)/93.75;begin=t
    if kana:groups.append(dict(start=begin,end=t,kana=kana))
    t+=round(q['postPhonemeLength']/speed*93.75)/93.75
    return groups,moras,round(t*SR)
# Each range indexes real pause-delimited phoneme groups, not characters.
SPEC=[
[(0,2,'太陽が生まれる前から、\n五つの惑星が回っていた。','Five planets were already orbiting\nbefore the Sun was born.'),(2,4,'ケプラー444。','Kepler-444.'),(4,5,'どれほど古いんだろう。','How ancient is this system?')],
[(0,3,'この星の年齢は、推定\nおよそ112億年。','Its star is estimated to be\nabout 11.2 billion years old.'),(3,5,'太陽系のおよそ46億年と、\n比べてみよう。','Compare that with our Solar System:\nabout 4.6 billion years.')],
[(0,1,'太陽が生まれた時点で、','When the Sun was born,'),(1,3,'この星系は、\nすでにおよそ66億歳。','this system was already\nabout 6.6 billion years old.'),(3,5,'地球の今の年齢よりも、\n長い時間だ。','Longer than Earth\nhas existed today.')],
[(0,2,'惑星は五つとも、\n地球より小さい。','All five planets\nare smaller than Earth.'),(2,4,'内側の一つは、\n水星ほど。','The innermost is\nabout the size of Mercury.'),(4,6,'外側の一つも、\n金星より小さい。','Even the outermost\nis smaller than Venus.')],
[(0,2,'しかも、五つとも、','And all five'),(2,3,'10日もかからず\n星を一周する。','complete an orbit\nin less than ten days.'),(3,5,'星のすぐ近くに、\nぎゅっと集まった惑星系だ。','A tightly packed system,\nvery close to its star.')],
[(0,1,'若い宇宙にも、','Even in the young universe,'),(1,2,'小さな惑星の世界は\n育っていた。','worlds with small planets\nwere already forming.'),(2,4,'太陽系は、\nその長い歴史の、','Our Solar System'),(4,5,'ずっと後から登場したんだ。','arrived much later\nin that long history.')]
]
records=json.loads((ROOT/'audio/raw/retrieval.json').read_text());segments=[];captions=[];checks=[];cursor=.35
for i,(rec,spec) in enumerate(zip(records,SPEC),1):
    p=ROOT/'audio/raw'/rec['file'];a=readwav(p);assert sha(p)==rec['sha256']
    q=json.loads((p.parent/f'{i:02d}_query.json').read_text());groups,moras,n=phrase_clock(q)
    assert n==len(a),(i,n,len(a))
    expected=max(e[1] for e in spec);assert len(groups)==expected,(i,len(groups),expected,groups)
    start=round(cursor*SR)/SR;end=start+len(a)/SR
    segment=dict(id=i,file=rec['file'],start=start,end=end,duration=len(a)/SR,text=rec['text'],groups=groups,kana=rec['kana'])
    segments.append(segment)
    for lo,hi,ja,en in spec:
        captions.append(dict(start=max(0,start+groups[lo]['start']-.065),end=start+groups[hi-1]['end']+.155,ja=ja,en=en,segment=i,groups=[lo,hi]))
    checks.append(dict(id=i,sha256=sha(p),samples=len(a),phoneme_samples=n,all_samples_match=True,kana=rec['kana'],pause_groups=groups))
    cursor=math.ceil((end+.62)*FPS)/FPS
end_voice=segments[-1]['end'];frames=math.ceil((end_voice+4.4)*FPS);duration=frames/FPS
# Phoneme-clocked shot boundaries, quantized once to video frames.
def gs(seg,g):return segments[seg]['start']+segments[seg]['groups'][g]['start']
bounds=[0,gs(0,2),segments[1]['start'],segments[2]['start'],segments[3]['start'],gs(3,2),gs(3,4),segments[4]['start'],segments[5]['start'],gs(5,2),end_voice,duration]
kind=['opening','orbits','ages','early','five','mercury','venus','revolution','young','hero','ending']
bf=[round(t*FPS) for t in bounds];bf[-1]=frames
assert all(b>a for a,b in zip(bf,bf[1:]))
shots=[dict(id=i,kind=k,start_frame=bf[i],end_frame=bf[i+1],start=bf[i]/FPS,end=bf[i+1]/FPS) for i,k in enumerate(kind)]
plan=dict(id='HEION-P041',version=1,width=1080,height=1920,fps=FPS,frames=frames,duration=duration,narration=segments,captions=captions,shots=shots,seed=410041,observed_phases=False,drawn_orbits='circular explanatory approximation',model_note='星と惑星の大きさを拡大／外観は想像')
put(ROOT/'timeline.json',plan)
put(ROOT/'assets/system.json',dict(names=['b','c','d','e','f'],period_days=[3.6,4.55,6.19,7.74,9.74],radius_earth=[.403,.497,.530,.546,.741],semimajor_au=[.04178,.04881,.06,.0696,.0811],star_age_gyr=11.2,star_age_error_gyr=1.,solar_age_gyr=4.6,elapsed_before_sun_gyr=6.6,source_year=2015,checked='2026-10-15',reference_radii={'Mercury':.383,'Venus':.949,'Earth':1.0},notes=['Rounded periods for presentation; not an ephemeris.','Planet appearances are illustrative, not observed maps.','Only A and its five planets are shown; the distant BC companion is outside the view.']))
put(ROOT/'validation/original_audio_integrity.json',checks)
# Subtitle files have one shared source for both languages and ASS.
def stamp(t,ass=False):
    unit=100 if ass else 1000;n=round(t*unit);h,n=divmod(n,3600*unit);m,n=divmod(n,60*unit);s,f=divmod(n,unit)
    return f'{h}:{m:02d}:{s:02d}.{f:02d}' if ass else f'{h:02d}:{m:02d}:{s:02d},{f:03d}'
for lang in ['ja','en']:
    (ROOT/f'captions/heionreki_p041_v1_{lang}.srt').write_text('\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c[lang]}' for i,c in enumerate(captions,1))+'\n',encoding='utf-8')
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',64,index=0)
layout=[]
ass=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','WrapStyle: 2','ScaledBorderAndShadow: yes','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding','Style: Main,Noto Sans CJK JP,64,&H00F8F7F2,&H00EED775,&HFF000000,&HFF000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
for c in captions:
    widths=[font.getlength(s) for s in c['ja'].split('\n')];assert max(widths)<=956,(c['ja'],widths)
    en_cps=len(c['en'].replace('\n',''))/(c['end']-c['start']);layout.append(dict(text=c['ja'],max_width=max(widths),english_cps=en_cps))
    a,b=stamp(c['start'],True),stamp(c['end'],True)
    ass.append(f'Dialogue: 0,{a},{b},Main,,0,0,0,,{{\\an7\\pos(45,1432)\\p1\\c&H21150B&\\alpha&H38&\\fad(140,120)}}m 0 0 l 990 0 990 230 0 230{{\\p0}}')
    ass.append(f'Dialogue: 1,{a},{b},Main,,0,0,0,,{{\\an7\\pos(63,1454)\\p1\\c&HEED775&\\fad(140,120)}}m 0 0 l 3 0 3 183 0 183{{\\p0}}')
    text=c['ja'].replace('\n',r'\N')
    ass.append(f'Dialogue: 2,{a},{b},Main,,0,0,0,,{{\\an5\\move(548,1558,548,1542,0,180)\\fscx98\\fscy98\\t(0,180,\\fscx100\\fscy100)\\fad(140,120)}}{text}')
(ROOT/'captions/heionreki_p041_v1_ja.ass').write_text('\n'.join(ass)+'\n',encoding='utf-8')
put(ROOT/'validation/subtitle_layout.json',layout)
# Keep the received PCM untouched; process a separate narration copy.
n=round(duration*SR);dry=np.zeros(n,dtype=np.float64)
for s in segments:
    a=readwav(ROOT/'audio/raw'/s['file']);p=round(s['start']*SR);dry[p:p+len(a)]=a/32768.
writewav(ROOT/'audio/narration_unprocessed.wav',dry)
subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/'audio/narration_unprocessed.wav'),'-af','highpass=f=55,acompressor=threshold=0.4:ratio=2:attack=12:release=150:makeup=1.1','-ar','48000',str(ROOT/'audio/narration_processed.wav')],check=True)
processed=readwav(ROOT/'audio/narration_processed.wav')/32768.;assert len(processed)==n
clock=np.arange(n)/SR;music=np.zeros((n,2));fx=np.zeros_like(music)
chords=[[146.832,220.,293.665,349.228],[130.813,195.998,261.626,329.628],[174.614,220.,261.626,349.228],[146.832,220.,293.665,440.]]
for j in range(8):
    st=j*duration/8;en=min(duration,st+duration/8+2.2);sel=(clock>=st)&(clock<en);tt=clock[sel]-st
    env=np.minimum(tt/1.8,1)*np.minimum((en-st-tt)/2.2,1);env=np.clip(env,0,1)**2
    for k,f in enumerate(chords[j%4]):
        for side,detune in enumerate([-.0007,.0007]):
            phase=2*np.pi*f*(1+detune)*tt
            signal=np.sin(phase)+.16*np.sin(2*phase+.4)+.065*np.sin(3*phase)
            music[sel,side]+=.013*env*signal/(1+.27*k)
# Sparse, purposeful chimes at the comparison and final orbit, not every movement.
for st,f in [(shots[2]['start']+.35,880.),(shots[3]['start']+1.,659.25),(shots[7]['end']-.65,987.77),(shots[10]['start']+.15,523.25)]:
    sel=(clock>=st)&(clock<st+2.8);tt=clock[sel]-st;env=(1-np.exp(-tt*30))*np.exp(-tt*2.2)
    ch=.036*env*(np.sin(2*np.pi*f*tt)+.25*np.sin(2*np.pi*f*2.002*tt));fx[sel,0]+=ch;fx[sel,1]+=ch*.93
active=np.abs(dry)>0.006;bins=active[:n//240*240].reshape(-1,240).max(1).astype(float)
env=gaussian_filter1d(maximum_filter1d(bins,size=65),sigma=15);duck=np.interp(clock,np.arange(len(env))*.005,env,left=0,right=0)
music*= (1-.72*duck)[:,None]
fade=np.minimum(clock/1.8,1)*np.minimum((duration-clock)/2.3,1);music*=np.clip(fade,0,1)[:,None]
writewav(ROOT/'audio/music.wav',music);writewav(ROOT/'audio/effects.wav',fx)
mix=processed[:,None]*np.ones((1,2))+music+fx;assert np.max(np.abs(mix))<1
writewav(ROOT/'audio/mix_before_normalization.wav',mix)
cmd=['ffmpeg','-hide_banner','-i',str(ROOT/'audio/mix_before_normalization.wav'),'-af','loudnorm=I=-16:TP=-2:LRA=10:print_format=json','-f','null','-']
log=subprocess.run(cmd,capture_output=True,text=True,check=True).stderr
m=json.loads(log[log.rfind('{'):]);put(ROOT/'validation/loudness_first_pass.json',m)
filt=f'loudnorm=I=-16:TP=-2:LRA=10:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true'
subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/'audio/mix_before_normalization.wav'),'-af',filt,'-ar','48000','-c:a','pcm_s24le',str(ROOT/'audio/master.wav')],check=True)
subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/'audio/master.wav'),'-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart',str(ROOT/'audio/master.m4a')],check=True)
for p in Path('p041_20261015').glob('*.py'):shutil.copy2(p,ROOT/'code'/p.name)
print('EDIT_READY',json.dumps(dict(duration=duration,frames=frames,shots=shots,original_audio=[s['duration'] for s in segments],caption_count=len(captions)),ensure_ascii=False),flush=True)
