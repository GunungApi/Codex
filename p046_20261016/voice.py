"""P046: new narration, original PCM, pronunciation metadata and independent ASR."""
from pathlib import Path
TEXTS=[
'この空から、宇宙へ出ていく粒子がある。同じ惑星なのに、なぜ逃げやすさが違うんだろう。',
'同じ温度で、軽い粒子と、重い粒子を比べよう。速さにはばらつきがあるけれど、軽い種類ほど、速く動きやすい。',
'舞台は、空のずっと高いところ。粒子どうしが、あまりぶつからない場所だ。',
'ここで遅い粒子は、重力に引かれて戻る。十分に速く、外へ向かう粒子は、遠くへ抜けていく。',
'同じ種類でも、温度を上げると、速い粒子が増える。逃げるために必要な速さを、超えやすくなるんだ。',
'空が残るかは、重力と、粒子の種類と、上空の温度で変わる。惑星の空にも、材料の出入りがあるんだね。'
]
READINGS=[('粒子','リュウシ',1),('重力','ジュウリョク',1),('上空','ジョウクウ',0),('温度','オンド',1),('種類','シュルイ',1),('惑星','ワクセイ',0),('希薄','キハク',0),('束縛','ソクバク',0),('出入り','デイリ',1),('星空','ホシゾラ',0)]
src=Path('p043_20261015/voice.py').read_text(encoding='utf-8')
a=src.index('TEXTS=');b=src.index('for attempt in range')
src=src[:a]+'TEXTS='+repr(TEXTS)+'\nREADINGS='+repr(READINGS)+'\n'+src[b:]
src=src.replace("ROOT=Path('p043/audio/raw')","ROOT=Path('p046/audio/raw')").replace('P043 original narration','P046 original narration')
Path('p046_20261016/voice_expanded.py').write_text(src,encoding='utf-8')
exec(compile(src,'p046_20261016/voice_expanded.py','exec'))
