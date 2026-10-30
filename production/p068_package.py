from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess
from PIL import Image
import p068_finish as F
ROOT=F.ROOT;PREFIX=F.PREFIX
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'deliverables').glob('*.mp4')}
assert len(before)==2
for p in sorted((ROOT/'review').glob('encoded_*.jpg')):
 with Image.open(p) as im:rgb=im.convert('RGB')
 tmp=p.with_suffix('.normalized.jpg');rgb.save(tmp,format='JPEG',quality=96,progressive=False);tmp.replace(p)
F.review('final')
for name in ['p068_scene.py','p068_finish.py','p068_refine.py','p068_action.py','p068_prepare.sh','p068_package.py']:
 shutil.copy(Path(__file__).with_name(name),ROOT/'source'/name)
(ROOT/'source/REEDIT.txt').write_text('p068_v1として作業フォルダへ展開。source内の全Pythonコードを同じディレクトリに置く。P068_FONTにNoto Sans CJK JPの場所を指定。python source/p068_action.py shot 0（0〜9）、python source/p068_action.py assemble。取得済みの原音・master.wav・timeline.jsonをそのまま引き継ぐ。再生成は任意。フォント・音声エンジン・声モデルは配布しない。\n',encoding='utf-8')
qa=json.loads((ROOT/'review/verification.json').read_text())
qa['preflight_visual_review']={'first_pass_pictures_inspected':20,'refined_critical_pictures_inspected':8,'corrections':['水に漂い、／周囲とやり取りする。の改行修正','主役の流体に沿う移動と回転を拡大','有機物の通り道を分離','年代を示す線を細胞から離す','暖かな水の流れを説明表示付きで追加'],'completed_video_frames_review':'pending'}
qa['generated_final_video_hashes']=before
F.dump(ROOT/'review/verification.json',qa)
text=ROOT/'deliverables'/f'{PREFIX}_script_and_sources.txt'
s=text.read_text();s+='\n\n試作の目視調整：20画面を確認後、動きの増幅、年代線と細胞の分離、字幕改行を修正。修正後の重要8画面を再確認。完成動画の目視記録は別途追加。暖かな水を示す光の線は説明用。\n'
s+='\n制作一式の画像変換を修正。完成した動画ファイルは再描画・再圧縮せず保持。\n';text.write_text(s,encoding='utf-8')
for p in (ROOT/'deliverables').glob('*.mp4'):
 assert hashlib.sha256(p.read_bytes()).hexdigest()==before[p.name]
 subprocess.run(['ffmpeg','-v','error','-i',str(p),'-map','0:v','-map','0:a','-f','null','-'],check=True)
archive=ROOT/'deliverables'/f'{PREFIX}_production.zip'
entries=[]
for p in ROOT.rglob('*'):
 if p.is_file() and p.suffix.lower() not in ['.ttf','.ttc','.otf','.docx','.pyc','.zip'] and not any(x.endswith('_ooxml') for x in p.parts) and 'voice_data' not in p.parts:
  entries.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
F.dump(ROOT/'review/manifest.json',entries)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
 for p in ROOT.rglob('*'):
  if p.is_file() and p!=archive and p.suffix.lower() not in ['.ttf','.ttc','.otf','.docx','.pyc'] and not any(x.endswith('_ooxml') for x in p.parts) and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(ROOT)))
print('FINAL_VERIFICATION',json.dumps(qa,ensure_ascii=False),flush=True)
print('DELIVERABLES',json.dumps([{'name':p.name,'bytes':p.stat().st_size} for p in (ROOT/'deliverables').iterdir()],ensure_ascii=False),flush=True)
