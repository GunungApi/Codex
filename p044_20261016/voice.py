"""P044 narration using the approved P043 voice pipeline; no credentials in source."""
from pathlib import Path
import runpy
source=Path('p043_20261015/voice.py').read_text(encoding='utf-8')
source=source.replace("ROOT=Path('p043/audio/raw')", "ROOT=Path('p044/audio/raw')")
a=source.index('TEXTS=[');b=source.index('for attempt in range(100):')
texts=[
'太陽が生まれる、何十億年も前。別の星の周りでは、もう岩の世界が歴史を刻んでいた。',
'この大地を見てみよう。溶けた岩から熱が逃げ、表面が少しずつ固まっていく。',
'そのあいだも、空の主星は光り続ける。太陽より小さな星には、寿命が数百億年に及ぶものもある。',
'その星も、惑星を連れて銀河を巡る。大地、星、銀河。変化にかかる時間は、それぞれ違う。',
'同じ時代の中で、いくつもの歴史が重なっている。太陽系を待つことなく、世界は続いてきたんだ。',
'材料だったものは、大地になった。ここから先、この世界はどんな景色を重ねるんだろう。'
]
readings=[('太陽','タイヨウ',1),('何十億年','ナンジュウオクネン',3),('数百億年','スウヒャクオクネン',4),('大地','ダイチ',1),('表面','ヒョウメン',3),('主星','シュセイ',0),('寿命','ジュミョウ',1),('惑星','ワクセイ',0),('銀河','ギンガ',1),('時代','ジダイ',0),('歴史','レキシ',0),('材料','ザイリョウ',3),('景色','ケシキ',1),('太陽系','タイヨウケイ',0)]
source=source[:a]+'TEXTS='+repr(texts)+'\nREADINGS='+repr(readings)+'\n'+source[b:]
Path('p044_20261016/voice_expanded.py').write_text(source,encoding='utf-8')
exec(compile(source,'p044_20261016/voice_expanded.py','exec'))
