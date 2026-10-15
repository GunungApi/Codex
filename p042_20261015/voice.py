"""Generate original narration for HEION-P042 using the established voice."""
from pathlib import Path
import json, time, hashlib, wave, requests, subprocess
ROOT=Path('p042/audio/raw'); ROOT.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:50021'
TEXTS=[
'小さな惑星が見つかった。そこに、海もあるだろうか。同じ大きさでも、環境で景色は変わる。',
'まず、星から届く光。同じ星なら、距離が二倍になると、受け取る光は四分の一。',
'次は、大気。光を反射し、地面から出る熱を吸収して、ふたたび放つ。その働きで、地表の温度が変わる。',
'水が液体でいられるかは、温度と気圧しだい。氷も、流れる水も、水蒸気も、同じ水の違う姿だ。',
'適切な大気のもとで、地表に液体の水がありうる距離の帯。これが、ハビタブルゾーン。生命の証拠は、さらに別に探す。',
'惑星を見つけた先に、環境を知る旅がある。古い世界に、何が続いてきたのか。その中身を、確かめに行こう。'
]
READINGS=[('惑星','ワクセイ',0),('液体','エキタイ',0),('気圧','キアツ',0),('水蒸気','スイジョウキ',3),('大気','タイキ',1),('地表','チヒョウ',0),('二倍','ニバイ',0),('四分の一','ヨンブンノイチ',1),('反射','ハンシャ',0),('吸収','キュウシュウ',0),('生命','セイメイ',1),('証拠','ショウコ',0)]
for attempt in range(100):
    try:
        r=requests.get(BASE+'/speakers',timeout=5)
        if r.ok:break
    except requests.RequestException:pass
    time.sleep(2)
r.raise_for_status(); person=next(s for s in r.json() if s['name']=='四国めたん'); sid=next(s['id'] for s in person['styles'] if s['name']=='ノーマル')
for word,kana,accent in READINGS:
    requests.post(BASE+'/user_dict_word',params=dict(surface=word,pronunciation=kana,accent_type=accent,priority=8),timeout=30).raise_for_status()
records=[]
for i,text in enumerate(TEXTS,1):
    r=requests.post(BASE+'/audio_query',params=dict(text=text,speaker=sid),timeout=90);r.raise_for_status();q=r.json()
    q.update(speedScale=1.01,pitchScale=-.015,intonationScale=1.08,volumeScale=1.,prePhonemeLength=.15,postPhonemeLength=.25,outputSamplingRate=48000,outputStereo=False)
    r=requests.post(BASE+'/synthesis',params=dict(speaker=sid),json=q,timeout=150);r.raise_for_status();p=ROOT/f'{i:02d}.wav';p.write_bytes(r.content)
    with wave.open(str(p),'rb') as w:
        count=w.getnframes();sr=w.getframerate();assert sr==48000 and w.getnchannels()==1 and w.getsampwidth()==2
        assert len(w.readframes(count))==2*count
    (ROOT/f'{i:02d}_query.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
    records.append(dict(file=p.name,text=text,duration=count/sr,samples=count,sha256=hashlib.sha256(r.content).hexdigest(),kana=q.get('kana')))
    print('ORIGINAL',i,count/sr,q.get('kana'),flush=True)
(ROOT/'retrieval.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'voice.json').write_text(json.dumps(dict(engine='VOICEVOX',engine_version=requests.get(BASE+'/version').json(),speaker='四国めたん',style='ノーマル',selected_style_id=sid,credit='VOICEVOX:四国めたん',readings=READINGS),ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'engine_image_digest.txt').write_text(subprocess.check_output(['docker','inspect','--format={{.Image}}','voicevox'],text=True))
# An independent waveform transcript supplements, rather than replaces, the checked text.
from faster_whisper import WhisperModel
model=WhisperModel('large-v3-turbo',device='cpu',compute_type='int8',cpu_threads=4)
for p in sorted(ROOT.glob('*.wav')):
    segments,info=model.transcribe(str(p),language='ja',word_timestamps=True,beam_size=5,vad_filter=False)
    result=dict(file=p.name,duration=info.duration,model='large-v3-turbo',segments=[dict(start=s.start,end=s.end,text=s.text,words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in s.words]) for s in segments])
    (p.parent/f'{p.stem}_words.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('TRANSCRIPT',p.name,[s['text'] for s in result['segments']],flush=True)
print('VOICE_READY',sum(r['duration'] for r in records),flush=True)
