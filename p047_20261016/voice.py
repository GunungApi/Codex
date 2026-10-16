"""P047 narration: inherit the established voice and archive waveform timing."""
from pathlib import Path
import json
texts=[
'星の光で、惑星の空が宇宙へ失われることがある。何が起きているんだろう。',
'まず、上空の水蒸気。紫外線を吸収すると、水分子の結びつきが切れ、水素などに分かれる。',
'さらに、紫外線やエックス線が上空を加熱する。軽い水素は、条件がそろうと宇宙へ逃げていく。',
'別の条件で、流れが十分強ければ、重い酸素も衝突で押され、一緒に運ばれる。',
'地上に届く明るさが似ていても、紫外線の強さは違う。大気に何が残るかは、星の光の中身にも左右される。',
'水素が失われれば、水を作る材料も減っていく。空の上での小さな変化が、世界の長い未来につながるんだ。'
]
readings=[('星の光','ホシノヒカリ',4),('惑星','ワクセイ',0),('上空','ジョウクウ',0),('水蒸気','スイジョウキ',3),('紫外線','シガイセン',2),('吸収','キュウシュウ',0),('水分子','ミズブンシ',3),('水素','スイソ',1),('酸素','サンソ',1),('衝突','ショウトツ',0),('加熱','カネツ',0),('地上','チジョウ',0),('大気','タイキ',1),('未来','ミライ',1),('光分解','ヒカリブンカイ',4)]
src=Path('p043_20261015/voice.py').read_text()
src=src.replace("Path('p043/audio/raw')","Path('p047/audio/raw')")
a=src.index('TEXTS=');b=src.index('for attempt in range(100):')
src=src[:a]+'TEXTS='+repr(texts)+'\nREADINGS='+repr(readings)+'\n'+src[b:]
Path('p047_20261016/voice_expanded.py').write_text(src)
exec(compile(src,'p047_voice_expanded.py','exec'))
