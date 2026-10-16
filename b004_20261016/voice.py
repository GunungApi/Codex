"""HEION-B004: retained narration and independent waveform transcript."""
from pathlib import Path
import json,time,hashlib,wave,requests,subprocess
ROOT=Path('b004/audio/raw');ROOT.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:50021'
TEXTS=[
'百億年以上、生きてきた星。誕生日を見ていないのに、どうして年齢が分かるんだろう。',
'手掛かりは、星の揺れ。内部を伝わる波が、明るさに、ほんの小さな変化を生む。',
'望遠鏡で光を測り続け、その揺れを、いくつもの周期に分けて調べる。',
'星の中身が変わると、波の伝わり方も変わる。温度や成分も使って、観測に合う進化の模型を探すんだ。',
'これが、星震学。ケプラー四百四十四の主星では、二千十五年の研究で、およそ百十二億年と推定された。',
'光の小さな揺れから、中身を探り、生まれてからの時間を読む。静かな星にも、長い生涯が隠れている。'
]
READINGS=[('百億年以上','ヒャクオクネンイジョウ',0),('年齢','ネンレイ',0),('手掛かり','テガカリ',2),('内部','ナイブ',1),('望遠鏡','ボウエンキョウ',0),('周期','シュウキ',1),('成分','セイブン',1),('観測','カンソク',0),('模型','モケイ',0),('星震学','セイシンガク',3),('四百四十四','ヨンヒャクヨンジュウヨン',0),('主星','シュセイ',0),('二千十五年','ニセンジュウゴネン',0),('百十二億年','ヒャクジュウニオクネン',0),('推定','スイテイ',0),('生涯','ショウガイ',1)]
for attempt in range(100):
    try:
        r=requests.get(BASE+'/speakers',timeout=5)
        if r.ok:break
    except requests.RequestException:pass
    time.sleep(2)
r.raise_for_status();person=next(s for s in r.json() if s['name']=='四国めたん');sid=next(s['id'] for s in person['styles'] if s['name']=='ノーマル')
for word,kana,accent in READINGS:
    requests.post(BASE+'/user_dict_word',params=dict(surface=word,pronunciation=kana,accent_type=accent,priority=8),timeout=30).raise_for_status()
records=[]
for i,text in enumerate(TEXTS,1):
    r=requests.post(BASE+'/audio_query',params=dict(text=text,speaker=sid),timeout=90);r.raise_for_status();q=r.json()
    q.update(speedScale=1.01,pitchScale=-.015,intonationScale=1.08,volumeScale=1.,prePhonemeLength=.15,postPhonemeLength=.25,outputSamplingRate=48000,outputStereo=False)
    r=requests.post(BASE+'/synthesis',params=dict(speaker=sid),json=q,timeout=150);r.raise_for_status();p=ROOT/f'{i:02d}.wav';p.write_bytes(r.content)
    with wave.open(str(p),'rb') as w:
        count=w.getnframes();sr=w.getframerate();assert sr==48000 and w.getnchannels()==1 and w.getsampwidth()==2
        assert len(w.readframes(count))==count*2
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
