"""HEION-C001 original narration. Reuses the validated P043 acquisition pipeline."""
from pathlib import Path
import ast,json
base=Path('p043_20261015/voice.py').read_text(encoding='utf-8')
texts=[
'銀河まるごと、誰かの作品だったら。オリオン腕には、長く暮らすために作り替えられた銀河がある。',
'主役は、ガスの巨大惑星や、恒星より軽い褐色矮星。明るい恒星は、ほんの一部だ。',
'材料を天体に蓄え、少しずつエネルギーへ変える。銀河全体が、未来のための貯蔵庫になる。',
'さらに、天体を近くへ集めた例もある。間隔が縮まれば、連絡を待つ時間も短くなる。',
'最も古い例は、およそ百億年。誰が、どんな歴史を重ねて作ったのか。遠未来の人々にも、謎が残る。',
'自然が育てた星空の向こうに、誰かが育て直した銀河がある。人類より前の宇宙にも、こんな物語があるんだ。'
]
readings=[('オリオン腕','オリオンワン',4),('銀河','ギンガ',1),('巨大惑星','キョダイワクセイ',4),('恒星','コウセイ',0),('褐色矮星','カッショクワイセイ',5),('天体','テンタイ',0),('蓄え','タクワエ',3),('貯蔵庫','チョゾウコ',2),('間隔','カンカク',0),('百億年','ヒャクオクネン',0),('遠未来','エンミライ',3),('星空','ホシゾラ',0),('人類','ジンルイ',1)]
tree=ast.parse(base)
for node in tree.body:
    if isinstance(node,ast.Assign):
        names=[t.id for t in node.targets if isinstance(t,ast.Name)]
        if 'TEXTS' in names:node.value=ast.parse(repr(texts),mode='eval').body
        if 'READINGS' in names:node.value=ast.parse(repr(readings),mode='eval').body
code=ast.unparse(tree).replace("p043/audio/raw","c001/audio/raw")
Path('c001_20261016/voice_expanded.py').write_text(code,encoding='utf-8')
exec(compile(code,'c001_20261016/voice_expanded.py','exec'))
