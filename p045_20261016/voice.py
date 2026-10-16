"""P045 narration; same established voice as preceding films, new text and dictionary."""
from pathlib import Path
import re
src=Path('p043_20261015/voice.py').read_text()
texts=[
'この空の材料は、地面の下からもやってくる。火山は、どうやって空へ気体を渡すんだろう。',
'溶けた岩石、マグマには、水や炭素を含む成分が溶け込んでいる。',
'炭酸水のふたを開けると、泡が出るよね。マグマも、上へ進んで圧力が下がると、気体が分かれやすくなる。',
'生まれた気泡は、膨らみながら上昇する。火口から出た気体は、周囲の空へ広がっていく。',
'水蒸気や二酸化炭素など。出てくる気体の種類や量は、地下の材料や温度によって変わる。',
'こうして、惑星の内側が、大気の材料を補っていく。地平線の向こうの火山も、この空につながっているんだ。'
]
readings=[('空','ソラ',1),('火山','カザン',1),('気体','キタイ',0),('岩石','ガンセキ',0),('炭素','タンソ',1),('成分','セイブン',1),('炭酸水','タンサンスイ',3),('圧力','アツリョク',2),('気泡','キホオ',0),('上昇','ジョオショオ',0),('火口','カコオ',0),('水蒸気','スイジョオキ',3),('二酸化炭素','ニサンカタンソ',4),('大気','タイキ',1),('地平線','チヘイセン',0),('惑星','ワクセイ',0)]
src=src.replace("ROOT=Path('p043/audio/raw')","ROOT=Path('p045/audio/raw')")
src=re.sub(r'TEXTS=\[.*?\]\nREADINGS=', 'TEXTS='+repr(texts)+'\nREADINGS=',src,count=1,flags=re.S)
src=re.sub(r'READINGS=\[.*?\]\nfor attempt', 'READINGS='+repr(readings)+'\nfor attempt',src,count=1,flags=re.S)
Path('p045_20261016/voice_expanded.py').write_text(src,encoding='utf-8')
exec(compile(src,'p045_20261016/voice_expanded.py','exec'))
