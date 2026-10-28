"""Final P065 polish: preserve the narrated timeline; make input -> transfer -> product visible."""
from pathlib import Path
import json,sys,importlib.util,shutil
p=Path(__file__).with_name('p065_film.py');s=p.read_text()
a=s.index('def cell(');z=s.index('\ndef landscape(',a)
new='''def cell(r,t,center=(0,0,0),sc=1.,strength=1.,continuous=True,phase=0):
 c=np.array(center,float);r.mineral(c+[0,.25*sc,0],sc)
 for lane,y in enumerate([-1.05,.20,1.45]):
  f=(t*.26+lane/3+phase)%1
  # A complete causal cycle: donor arrives, electron traverses mineral,
  # acceptor changes at the other surface, then the product leaves.
  arrive=b.smooth(f,0,.44)
  donor_alpha=(1-b.smooth(f,.44,.56))*max(.10,strength)
  r.molecule(c+np.array([-3.05+2.0*arrive,y,.72])*sc,0,sc,alpha=donor_alpha,tag='donor')
  accept_alpha=(1-b.smooth(f,.57,.62))*max(.10,strength)
  r.molecule(c+np.array([2.98-2.0*b.smooth(f,0,.48),y,.72])*sc,1,sc,alpha=accept_alpha,tag='acceptor')
  if .42<f<.60 and strength>.08:
   e=b.smooth(f,.42,.60);r.ball(c+np.array([-.43+.86*e,y,.32])*sc,.088*sc,PALE,emit=1.35,alpha=strength)
  product_alpha=b.smooth(f,.62,.68)*max(.08,strength)
  leave=b.smooth(f,.65,1.)
  r.molecule(c+np.array([.98+2.0*leave,y+.30*leave,.72])*sc,2,sc,alpha=product_alpha,tag='product')
  pulse=max(0.,1-abs(f-.60)/.16)*strength
  r.ball(c+np.array([.49,y,.48])*sc,(.07+.19*pulse)*sc,GREEN,emit=1.8*pulse,alpha=.16+.74*pulse)
 if continuous:
  r.arrow_flow(c[0]-3.42*sc,c[1]+.2*sc,t,AMBER,sc,1,strength)
  r.arrow_flow(c[0]+3.42*sc,c[1]+.2*sc,t,CYAN,sc,-1,strength)
'''
s=s[:a]+new+s[z:]
a=s.index('def check_spacing(');z=s.index('\ndef do_voice(',a)
new='''def check_spacing(r):
 minimum=999.;projected_min=999.;pairs=0;outside=[]
 def project(p):
  v=r.vp@np.r_[p,1.];q=v[:2]/v[3];return np.array([(q[0]+1)*W/2,(1-q[1])*H/2])
 glyphs=[]
 for p,rad,tag in r.glyphs:
  if tag=='environment':continue
  center=project(p);rr=max(np.linalg.norm(project(p+axis*rad)-center) for axis in np.eye(3))
  glyphs.append((p,rad,center,rr))
  if center[0]-rr<55 or center[0]+rr>1025 or center[1]-rr<410 or center[1]+rr>1430:outside.append([tag,*center.tolist(),float(rr)])
 for i,(p,rad,center,rr) in enumerate(glyphs):
  for q,rad2,other,rr2 in glyphs[i+1:]:
   minimum=min(minimum,float(np.linalg.norm(p-q)-rad-rad2));projected_min=min(projected_min,float(np.linalg.norm(center-other)-rr-rr2));pairs+=1
 return {'minimum_symbol_sphere_clearance':None if minimum==999 else minimum,'minimum_projected_symbol_gap_pixels':None if projected_min==999 else projected_min,'symbols_outside_safe_area':outside,'pairs':pairs}
'''
s=s[:a]+new+s[z:]
# Include camera-projected spacing in the final report, in addition to world spacing.
s=s.replace("'human_continuous_viewing':False", "'minimum_projected_symbol_gap_pixels':min((x['minimum_projected_symbol_gap_pixels'] for x in states if x.get('minimum_projected_symbol_gap_pixels') is not None),default=None),'projected_overlap_frames':[x['frame'] for x in states if x.get('minimum_projected_symbol_gap_pixels') is not None and x['minimum_projected_symbol_gap_pixels']<-.1],'outside_safe_area_frames':[x['frame'] for x in states if x.get('symbols_outside_safe_area')],'human_continuous_viewing':False")
p.write_text(s)
R=Path('p065_v1')
readings=R/'review/readings.json'
if readings.exists():
 data=json.loads(readings.read_text());aliases={'鉱物':['コオブツ','コーブツ'],'供給':['キョオキュウ','キョーキュー'],'熱水':['ネッスイ'],'電子':['デンシ'],'海水':['カイスイ']}
 import re
 for word,row in data.items():
  row['accepted_phonetic_spellings']=aliases[word];row['checked']=all(any(k in re.sub(r"[\'_/？?、。]",'',v) for k in aliases[word]) for v in row['records']);row['human_listening']=False
 assert all(row['checked'] for row in data.values())
 readings.write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('P065 final causal paths, projected-symbol validation, and kana normalization ready',flush=True)
