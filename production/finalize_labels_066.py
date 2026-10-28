"""Final measured label clearance repair for P066, preserving all audio and timing."""
from pathlib import Path
import json
p=Path(__file__).with_name('p066_film.py')
s=p.read_text()
a="['親','次のコピー','さらに次'][j],870,615+j*291,32"
c="['親','次のコピー','さらに次'][j],930,615+j*291,32"
assert a in s or c in s
s=s.replace(a,c)
s=s.replace("qa['polish_revision']=3","qa['polish_revision']=4")
p.write_text(s)
root=Path('p066_v1')
(root/'docs').mkdir(exist_ok=True,parents=True)
(root/'docs/final_clearance_change.json').write_text(json.dumps({'scene':4,'old_label_center_x':870,'new_label_center_x':930,'reason':'The actual font-metric audit found a terminal bead intersecting the label in frames 527 through 608. Re-render that shot and rerun unchanged overlap criteria.','audio_changed':False,'timing_changed':False},ensure_ascii=False,indent=2))
print('P066 scene 4 label margin corrected; audio and frame timing retained.',flush=True)
