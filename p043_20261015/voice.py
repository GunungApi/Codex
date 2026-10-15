"""P043 original narration, retained waveforms, synthesis phonemes and independent ASR."""
from pathlib import Path
import json,time,hashlib,wave,requests,subprocess
ROOT=Path('p043/audio/raw'); ROOT.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:50021'
TEXTS=[
'この星空には、別の銀河で生まれた星も混ざっている。どうして、そんな昔のことが分かるんだろう。',
'まず、星の動き。細長い道を似たように巡る、星の集まりを探す。',
'次に、光を色ごとに分ける。暗い線の位置や深さから、鉄などの成分の割合を調べる。',
'明るさなどを星の進化模型と比べ、年齢も推定する。動き、成分、年齢。三つを重ねて、過去を読むんだ。',
'こうして見えてきたのが、ガイア・エンケラドゥス。およそ百億年前、天の川と合体したと考えられる銀河だ。',
'重力で引き離された星々は、今も天の川を巡っている。夜空の光は、昔の出会いを覚えている。'
]
READINGS=[('星空','ホシゾラ',0),('天の川','アマノガワ',3),('星々','ホシボシ',2),('銀河','ギンガ',1),('成分','セイブン',1),('割合','ワリアイ',0),('年齢','ネンレイ',0),('進化模型','シンカモケイ',4),('推定','スイテイ',0),('ガイア・エンケラドゥス','ガイアエンケラドゥス',7),('百億年前','ヒャクオクネンマエ',0),('合体','ガッタイ',0),('重力','ジュウリョク',1),('夜空','ヨゾラ',1)]
for attempt in range(100):
    try:
        r=requests.get(BASE+'/speakers',timeout=5)
        if r.ok: break
    except requests.RequestException: pass
    time.sleep(2)
r.raise_for_status(); person=next(s for s in r.json() if s['name']=='四国めたん'); sid=next(s['id'] for s in person['styles'] if s['name']=='ノーマル')
for word,kana,accent in READINGS:
    requests.post(BASE+'/user_dict_word',params=dict(surface=word,pronunciation=kana,accent_type=accent,priority=8),timeout=30).raise_for_status()
records=[]
for i,text in enumerate(TEXTS,1):
    r=requests.post(BASE+'/audio_query',params=dict(text=text,speaker=sid),timeout=90); r.raise_for_status(); q=r.json()
    q.update(speedScale=1.01,pitchScale=-.015,intonationScale=1.08,volumeScale=1.,prePhonemeLength=.15,postPhonemeLength=.25,outputSamplingRate=48000,outputStereo=False)
    r=requests.post(BASE+'/synthesis',params=dict(speaker=sid),json=q,timeout=150); r.raise_for_status(); p=ROOT/f'{i:02d}.wav'; p.write_bytes(r.content)
    with wave.open(str(p),'rb') as w:
        count=w.getnframes(); sr=w.getframerate(); assert sr==48000 and w.getnchannels()==1 and w.getsampwidth()==2
        assert len(w.readframes(count))==2*count
    (ROOT/f'{i:02d}_query.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
    records.append(dict(file=p.name,text=text,duration=count/sr,samples=count,sha256=hashlib.sha256(r.content).hexdigest(),kana=q.get('kana')))
    print('ORIGINAL',i,count/sr,q.get('kana'),flush=True)
(ROOT/'retrieval.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'voice.json').write_text(json.dumps(dict(engine='VOICEVOX',engine_version=requests.get(BASE+'/version').json(),speaker='四国めたん',style='ノーマル',selected_style_id=sid,credit='VOICEVOX:四国めたん',readings=READINGS),ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'engine_image_digest.txt').write_text(subprocess.check_output(['docker','inspect','--format={{.Image}}','voicevox'],text=True))
from faster_whisper import WhisperModel
model=WhisperModel('large-v3-turbo',device='cpu',compute_type='int8',cpu_threads=4)
for p in sorted(ROOT.glob('*.wav')):
    segments,info=model.transcribe(str(p),language='ja',word_timestamps=True,beam_size=5,vad_filter=False)
    result=dict(file=p.name,duration=info.duration,model='large-v3-turbo',segments=[dict(start=s.start,end=s.end,text=s.text,words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in s.words]) for s in segments])
    (p.parent/f'{p.stem}_words.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('TRANSCRIPT',p.name,[s['text'] for s in result['segments']],flush=True)
print('VOICE_READY',sum(r['duration'] for r in records),flush=True)
