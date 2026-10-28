import importlib.util,json,sys
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p065_film.py');spec=importlib.util.spec_from_file_location('p065_movie',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tl=json.loads((m.R/'timeline.json').read_text());r=m.Scene();N=round(tl['duration']*24);allrows=[]
for scene in range(10):
 a,z=tl['boundaries'][scene:scene+2];start=round(a*24);end=round(z*24);second=[c for c in tl['cues'] if c['scene']==scene][1]['start'];split=(second-a)/(z-a)
 file=m.R/'review'/f'states_{scene:02}.json';rows=json.loads(file.read_text());byframe={x['frame']:x for x in rows}
 for f in range(start,end):
  t=f/24;u=(t-a)/(z-a);r.reset();r.scene_start=a;m.arrange(r,scene,u,t,split)
  eye=r.eye;forward=m.b.unit(r.target-eye);right=m.b.unit(np.cross(forward,[0,1,0]));up=np.cross(right,forward);v=np.eye(4);v[:3,:3]=[right,up,-forward];v[:3,3]=-v[:3,:3]@eye
  k=1/np.tan(np.radians(37)/2);near=.1;far=100;proj=np.zeros((4,4));proj[0,0]=k/(1080/1920);proj[1,1]=k;proj[2,2]=(far+near)/(near-far);proj[2,3]=2*far*near/(near-far);proj[3,2]=-1;r.vp=proj@v
  byframe[f].update(m.check_spacing(r));allrows.append(byframe[f])
 file.write_text(json.dumps(list(byframe.values()),ensure_ascii=False))
negative=[x['frame'] for x in allrows if x.get('minimum_projected_symbol_gap_pixels') is not None and x['minimum_projected_symbol_gap_pixels']<-.1]
outside=[x['frame'] for x in allrows if x.get('symbols_outside_safe_area')]
report={'frames':len(allrows),'minimum_projected_symbol_gap_pixels':min(x['minimum_projected_symbol_gap_pixels'] for x in allrows if x.get('minimum_projected_symbol_gap_pixels') is not None),'overlap_frames':negative,'outside_safe_area_frames':outside,'scope':'Independent material symbols in explanatory scenes; intentional bonded atoms, reaction contacts and background chimney scenery are excluded. This is geometric checking, not human visual review.'}
assert len(allrows)==N
m.b.dump(m.R/'review/projection_audit.json',report)
print('PROJECTION_AUDIT',json.dumps(report,ensure_ascii=False),flush=True)
assert not negative,('Projected material overlap',negative[:20])
assert not outside,('Material outside composition safe area',outside[:20])
