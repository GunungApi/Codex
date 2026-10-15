from pathlib import Path
import json, shutil, re, hashlib, py_compile
HERE=Path(__file__).parent;ROOT=Path('p042')
for p in ['assets','validation','reference','code','clips','audio/raw','captions']:(ROOT/p).mkdir(parents=True,exist_ok=True)
src=Path('p041_20261015/prepare.py');shutil.copy2(src,HERE/'inherited_prepare.py')
base=Path('p041_20261015/render.py').read_text().replace("ROOT=Path('p041')","ROOT=Path('p042')")
(HERE/'base.py').write_text(base,encoding='utf-8')
# Equal radius, equal camera distance, with a safe frame margin around both silhouettes.
p=HERE/'render.py';s=p.read_text();s=s.replace("eye=[2.2-.5*s,1.1,12.0+.55*s] if k=='opening' else [1.7+.65*s,1.25,12.55]","eye=[0.,1.1+.15*s,13.5+.55*s] if k=='opening' else [0.,1.25+.2*s,14.05]")
p.write_text(s,encoding='utf-8')
# Keep the full comment marker when extracting the inherited subtitle generator.
p=HERE/'prepare.py';s=p.read_text();bad="sub=old.split('# Subtitle files')[1].split('# Keep the received PCM')[0]";good="sub='# Subtitle files'+old.split('# Subtitle files')[1].split('# Keep the received PCM')[0]"
assert bad in s or good in s;s=s.replace(bad,good);p.write_text(s,encoding='utf-8')
for p in HERE.glob('*.py'):py_compile.compile(str(p),doraise=True)
raw=ROOT/'audio/raw';rec=json.loads((raw/'retrieval.json').read_text())
def kana(x):return re.sub(r"[/_'、？。\s]",'',x)
terms={1:['ワクセエ','ウミ','カンキョオ'],2:['ニバイ','ヨンブンノイチ'],3:['タイキ','ハンシャ','キュウシュウ','チヒョウ'],4:['エキタイ','キアツ','スイジョウキ'],5:['タイキ','エキタイ','ハビタブルゾオン','セイメイ','ショウコ'],6:['ワクセエ','カンキョオ']}
audit=[]
for i,r in enumerate(rec,1):
    q=kana(r['kana']);checks=[dict(term=x,found=x in q) for x in terms[i]]
    assert all(x['found'] for x in checks),(i,q,checks)
    audit.append(dict(segment=i,kana=r['kana'],terms=checks,independent_transcript=json.loads((raw/f'{i:02d}_words.json').read_text())['segments'],actual_listening=False))
(ROOT/'validation/pronunciation_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'validation/inherited_sources.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('p041_20261015/render.py'),src]},indent=2))
print('BOOTSTRAP_READY',len(audit),'raw voice segments',flush=True)
