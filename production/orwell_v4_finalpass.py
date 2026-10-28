"""Final visible-detail pass for P067 v4, after reviewing rendered preview pages.
Only local landscape scenes are redrawn. All voice and the spatial timeline are retained.
"""
from pathlib import Path
import sys,json,math,shutil,zipfile,hashlib
import numpy as np
import moderngl
import p067v4_polish as Q
K=Q.K;S=Q.S;F=Q.F;ROOT=Q.ROOT;V=Q.V;P=Q.P

# Break up the previously solid pale arc into porous, irregular wet foam.
old='col=tint.rgb*(.45+.65*max(0.,dot(n,l)));alpha=tint.a;'
new=r'''float grains=texture(detailtex,P.xz*1.2+vec2(time*.043,-time*.027)).r;
float fine=texture(detailtex,P.xz*3.7+vec2(-time*.016,time*.018)).r;
float edge=smoothstep(0.,.18,UV.y)*(1.-smoothstep(.70,1.,UV.y));
float breakup=smoothstep(.43,.62,grains*.64+fine*.36);
alpha=tint.a*edge*breakup;
if(alpha<.024)discard;
col=tint.rgb*(.50+.55*max(0.,dot(n,l)));'''
assert old in S.FRAG;S.FRAG=S.FRAG.replace(old,new)
# The low part of the smoke has a clear interior window to reveal the molten lake.
S.COMPOSITE=S.COMPOSITE.replace('float d=density(p);if(d>.002)', 'float d=density(p)*mix(.30,.76,smoothstep(14.,42.,p.y));if(d>.002)')
S.COMPOSITE=S.COMPOSITE.replace('vec3(1.3,.16,.009)', 'vec3(.72,.075,.004)')

BASE_CONFIG=Q.config
def config(t,tl):
 c=BASE_CONFIG(t,tl);s=c['scene'];a,d=tl['boundaries'][s:s+2];sec=tl['cues'][s*2+1]['start']
 if s==0 and not c['orbital']:
  q=S.ramp(t,a,sec);c['eye']=S.mix([10.,39.,-5.],[6.3,37.,-9.],q).tolist();c['target']=[0,12.0,-18];c['fov']=47.
 elif s==3 and t>=sec:
  q=S.ramp(t,sec,d);c['eye']=S.mix([9.,39.,-7.5],[5.5,37.8,-11.],q).tolist();c['target']=[0,12.0,-18];c['fov']=48.
 elif s==7 and c['event']=='heat_detail':c['eye']=[6.5,37.5,-9.];c['target']=[0,12,-18];c['fov']=47.
 return c

class Cinema(Q.Cinema):
 def __init__(self):
  super().__init__()
  # Seat the rim blocks into sloping ground over their footprint, not only at their centre.
  for m in self.rimrocks:
   x,z=m[0,3],m[2,3];sx=float(np.linalg.norm(m[:3,0]));sz=float(np.linalg.norm(m[:3,2]));sy=float(np.linalg.norm(m[:3,1]))
   vals=[float(self.g.height(x+dx*sx*.72,z+dz*sz*.72)) for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]]
   m[1,3]=min(vals)+sy*.12
  # Smaller foreground rock leaves more of the volcano visible, its bottom remains grounded.
  newrocks=[]
  for x,z,sx,sz,top in [(-12.,24.,1.65,1.80,6.3),(-4.,8.,1.35,1.55,6.7)]:
   bottom=float(self.g.height(x,z))-.12;cy=(bottom+top)/2;sy=(top-bottom)/1.44
   newrocks.append((S.matrix([x,cy,z],[sx,sy,sz],.25),[x,cy,z],[sx*1.18,sy*.75,sz*1.18]))
  self.shore_rocks=newrocks
  self.render_shadow();self.sf.use()
  for m in self.rimrocks:self.put(self.sp,'model',m);self.meshes['rimblock'][1].render()
  for m,_,_ in self.shore_rocks:self.put(self.sp,'model',m);self.meshes['rock'][1].render()
  # Replace the simple half-ring with an irregular, undulating foam mesh.
  vv=[];ii=[]
  for j in range(97):
   f=j/96;ang=.10+(np.pi-.20)*f;wav=.075*np.sin(ang*11)+.045*np.sin(ang*23+.8)
   for outer in [0,1]:
    rr=2.70+.48*outer+wav;yy=.032*np.sin(ang*13+outer*.8)
    vv.append([rr*np.cos(ang),yy,rr*np.sin(ang),0,1,0,f,outer])
  for j in range(96):k=2*j;ii.extend([k,k+1,k+2,k+1,k+3,k+2])
  self.mesh('brokenfoam',np.array(vv,'f4'),np.array(ii,'i4'))
 def surf(self,cfg,t):
  if not cfg['water_visible'] or cfg['orbital'] or cfg['eye'][1]<cfg['sea']:return
  sea=cfg['sea'];phase=float(cfg.get('wavephase',t));ctx=self.c
  ctx.enable(moderngl.BLEND);ctx.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA);ctx.depth_mask=False
  for k,(_,ctr,radii) in enumerate(self.shore_rocks):
   age=(phase-k*.48)%1.65;fade=max(0.,1-age/1.65);sc=.67 if k==0 else .56
   pos=np.array([ctr[0],sea+.055+.12*np.sin(age*5),ctr[2]])
   self.draw('brokenfoam',13,S.matrix(pos,[sc*(1+.20*age),1,sc*(1+.20*age)]),tint=(.73,.87,.90,.88*fade))
   # Scatter small, varied spray droplets instead of an evenly spaced picket line.
   if age<1.08:
    for j in range(29):
     ang=.18+(np.pi-.36)*((j*.61803398875)%1);r=(2.75+.43*age)*sc;v=1.45+.75*((j*.414213562)%1)
     local=age-.04*((j*7)%5)
     if local<0:continue
     yy=sea+.055+v*local-2.8*local*local
     if yy<sea+.02:continue
     p=[ctr[0]+r*np.cos(ang),yy,ctr[2]+r*np.sin(ang)];rad=.016+.019*((j*11)%7)/6
     # Ordinary lit mesh, no long luminous trails on the water droplets.
     self.draw('grain',8,S.matrix(p,[rad,rad*1.6,rad]),tint=(.34,.46,.51,1))
  ctx.depth_mask=True;ctx.disable(moderngl.BLEND)

F.Cinema=Cinema;F.config=config

def assemble():
 Q.assemble()
 qa=json.loads((ROOT/'review/verification.json').read_text())
 qa.update(visual_review_stage='v3 comparison and 28 v4 preflight images inspected; final encoded review recorded separately',foam_breakup_revised=True,crater_lower_plume_thinned=True,rim_block_footprint_grounding=True,foreground_rock_occlusion_reduced=True)
 F.dump(ROOT/'review/verification.json',qa)
 note=ROOT/'deliverables'/f'{F.PREFIX}_script_and_sources.txt';text=note.read_text();text+='\n第4版の試作目視からの最終修正：火口近景・年代進行・海の広がり・海岸・潜水の28枚を確認。泡の帯を不均一な密度と凹凸を持つ細かな泡へ変更。しぶきの間隔と大きさを不規則化。前景岩を小さくし、火山を隠しにくくした。火口縁の岩は足元の複数点を調べて斜面へ埋め込み、噴煙下部の密度を下げて火口の中を見せる。\n'
 note.write_text(text,encoding='utf-8');shutil.copy(__file__,ROOT/'source'/Path(__file__).name)
 with (ROOT/'source/REEDIT.txt').open('a',encoding='utf-8') as f:f.write('\n最終版の実行入口：orwell_v4_finalpass.py。ほかの6本と同じsource内へ配置。\n')
 archive=ROOT/'deliverables'/f'{F.PREFIX}_production.zip';archive.unlink()
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in ROOT.rglob('*'):
   if p.is_file() and p!=archive and p.suffix.lower() not in ['.ttf','.otf','.ttc','.zip'] and 'review_ooxml' not in p.parts and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(ROOT)))
 print('REVIEWPASS_QA',json.dumps(qa,ensure_ascii=False),flush=True)
 print('REVIEWPASS_FILES',json.dumps([{'name':p.name,'bytes':p.stat().st_size} for p in (ROOT/'deliverables').iterdir()],ensure_ascii=False),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':P.acquire_assets();F.prepare()
 elif mode=='shot':F.shot(int(sys.argv[2]))
 elif mode=='preview':
  for s in [0,3,6,9]:F.shot(s,True)
  K.review_package()
 elif mode=='assemble':assemble()
 else:raise ValueError(mode)
