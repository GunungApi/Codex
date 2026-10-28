"""Update P067 v4 documentation after the final encoded frames were inspected.
This step never redraws or recompresses a video and never ships font files.
Requires the explicit, separately recorded completed review JSON.
"""
from pathlib import Path
import json,zipfile,shutil,hashlib
D=Path('checked_delivery');D.mkdir(exist_ok=True)
source=Path('incoming_delivery')
for p in source.iterdir():
 if p.is_file():shutil.copy2(p,D/p.name)
review=json.loads(Path('production/orwell_v4_completed_review.json').read_text())
assert review['final_encoded_stills_reviewed']==20
assert review['continuous_video_playback_reviewed'] is False
assert review['auditory_listening_performed'] is False
archive=D/'heionreki_p067_v4_production.zip'
work=Path('checked_project');work.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
 for info in z.infolist():
  p=Path(info.filename)
  assert not p.is_absolute() and '..' not in p.parts
  z.extract(info,work)
qa_path=work/'review/verification.json';qa=json.loads(qa_path.read_text())
qa.update(visual_inspection_performed=True,visual_inspection_scope='20 encoded caption frames across all 10 scenes; 28 earlier preflight frames and 4 v3 comparison frames',continuous_preview_watched=False,auditory_listening_performed=False,completed_review_record='review/completed_visual_review.json')
qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
(work/'review/completed_visual_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
notes=D/'heionreki_p067_v4_script_and_sources.txt';text=notes.read_text()
text+='\n\n【最終工程の確認記録・それ以前の自動記録に対する更新】\n完成MP4から抽出した20枚（全20字幕区間・全10場面）を実画像で目視。先行試作28枚と前版比較4枚も確認。字幕の収まり、火口の見え方、岩と溶岩の描き分け、年代の順次表示、泡の輪郭、海面から水中への位置関係を点検した。連続再生による全編試写と耳による試聴は未実施。読みは修正済み合成記録を継承し、AAC音声が旧版と同一であることをデータで確認。\n'
text+=json.dumps(review,ensure_ascii=False,indent=2)+'\n'
notes.write_text(text,encoding='utf-8')
(work/'deliverables').mkdir(exist_ok=True);shutil.copy2(notes,work/'deliverables'/notes.name)
# Source files and current machine reports are packaged with the actual footage.
shutil.copy2('production/orwell_v4_delivery_qa.py',work/'source/orwell_v4_delivery_qa.py')
shutil.copy2('production/orwell_v4_completed_review.json',work/'source/orwell_v4_completed_review.json')
manifest=[]
for p in work.rglob('*'):
 if p.is_file() and p.suffix.lower() not in ['.zip','.ttf','.otf','.ttc'] and p!=work/'review/manifest.json' and 'review_ooxml' not in p.parts:
  manifest.append({'path':str(p.relative_to(work)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(work/'review/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('*.mp4')}
archive.unlink()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
 for p in work.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.zip','.ttf','.otf','.ttc'] and 'review_ooxml' not in p.parts and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(work)))
after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('*.mp4')}
assert before==after
with zipfile.ZipFile(archive) as z:
 assert not any(Path(n).suffix.lower() in ['.ttf','.otf','.ttc'] for n in z.namelist())
print('COMPLETED_REVIEW',json.dumps(review,ensure_ascii=False),flush=True)
print('DELIVERY_VIDEO_BYTES_UNCHANGED',True,flush=True)
print('FINAL_DELIVERY_FILES',json.dumps([{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(D.iterdir()) if p.is_file()],ensure_ascii=False),flush=True)
