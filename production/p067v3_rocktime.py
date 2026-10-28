"""P067 v3: fractured volcanic surfaces and a spatial chronology sequence.
Preserves the approved voice, timing and source-backed script. All terrain, materials,
and time-path geometry are original explanatory art. Generated media stay in artifacts.
"""
from pathlib import Path
import os, sys, json, math, shutil, zipfile, hashlib, subprocess
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','3')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree, ConvexHull
from PIL import Image, ImageDraw
import moderngl
import p067v2_scene as S

ROOT=Path('p067_v3').resolve()
for folder in ['assets','render','review','source','deliverables','docs','audio']:
 (ROOT/folder).mkdir(parents=True,exist_ok=True)
S.ROOT=ROOT
OLD_GEOGRAPHY=S.Geography
OLD_CINEMA=S.Cinema
OLD_CONFIG=S.config

class Geography(OLD_GEOGRAPHY):
 def height(self,x,z):
  x,z=np.broadcast_arrays(np.asarray(x),np.asarray(z))
  h=super().height(x,z)
  rad=np.sqrt(x*x+(z+18.)**2);ang=np.arctan2(z+18.,x)
  # Broken caldera rim, broad scarps and irregular scree; no repeated tooth pattern.
  rim=np.exp(-((rad-4.9)/2.5)**2)
  ledges=(self.noise(x,z,2.3)-.5)*1.35+(self.noise(x,z,6.2)-.5)*.34
  breakage=np.zeros_like(rad)
  for a,w,depth in [(-2.55,.20,-.92),(-.37,.15,-1.12),(1.05,.24,.47),(2.16,.19,-.65)]:
   delta=np.arctan2(np.sin(ang-a),np.cos(ang-a));breakage+=depth*np.exp(-(delta/w)**2)
  flanks=np.exp(-rad/26.)*(1.-np.exp(-rad/4.))
  rubble=(self.noise(x,z,3.4)-.5)*.52+(self.noise(x,z,10.4)-.5)*.14
  return h+rim*(ledges+breakage)+flanks*rubble
 def terrain(self):
  nx,nz=512,640
  x,z=np.meshgrid(np.linspace(-110,110,nx+1),np.linspace(-145,100,nz+1))
  y=self.height(x,z);e=.055
  dx=(self.height(x+e,z)-self.height(x-e,z))/(2*e)
  dz=(self.height(x,z+e)-self.height(x,z-e))/(2*e)
  n=np.stack([-dx,np.ones_like(x),-dz],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
  uv=np.stack([(x+110)/220,(z+145)/245],-1)
  v=np.concatenate([np.stack([x,y,z],-1),n,uv],-1).reshape(-1,8).astype('f4')
  return v,S.grid_indices(nz,nx)

S.Geography=Geography

def basalt_texture():
 rng=np.random.default_rng(670305);N=1024
 yy,xx=np.mgrid[0:N,0:N].astype('f4')
 seed=rng.uniform(0,N,(96,2));tiles=np.concatenate([seed+[i*N,j*N] for i in [-1,0,1] for j in [-1,0,1]])
 tree=cKDTree(tiles)
 warp=[]
 for _ in range(2):
  q=gaussian_filter(rng.standard_normal((N,N)).astype('f4'),15,mode='wrap');warp.append(q/(q.std()+1e-6)*8)
 pts=np.stack([xx+warp[0],yy+warp[1]],-1).reshape(-1,2)
 dist,_=tree.query(pts,k=2,workers=2);edge=(dist[:,1]-dist[:,0]).reshape(N,N)
 fracture=np.exp(-edge/2.8).astype('f4')
 body=np.zeros((N,N),np.float32)
 for sigma,weight in [(42,.40),(12,.27),(3.5,.20),(.9,.09),(.15,.04)]:
  q=gaussian_filter(rng.random((N,N)).astype('f4'),sigma,mode='wrap');q=(q-q.mean())/(q.std()+1e-6);body+=q*weight
 relief=np.clip(.53+body*.14-fracture*.26,0,1)
 dy,dx=np.gradient(relief)
 # R: tonal relief, G/B: normal slopes, A: open joints. Other materials keep old maps.
 tex=np.stack([relief,np.clip(.5-dx*4.4,0,1),np.clip(.5-dy*4.4,0,1),fracture],-1)
 return (np.clip(tex,0,1)*255).astype('u1')

def fractured_rock(seed=9):
 rng=np.random.default_rng(seed);p=rng.normal(size=(56,3));p/=np.linalg.norm(p,axis=1,keepdims=True)
 p*=rng.uniform(.77,1.12,(len(p),1));p[:,1]=np.clip(p[:,1],-.72,.72)
 hull=ConvexHull(p);verts=[];ids=[]
 for tri in hull.simplices:
  pts=p[tri].copy();n=S.unit(np.cross(pts[1]-pts[0],pts[2]-pts[0]))
  if np.dot(n,pts.mean(axis=0))<0:pts=pts[[0,2,1]];n=-n
  start=len(verts)
  for v in pts:verts.append([*v,*n,0.,0.])
  ids.extend([start,start+1,start+2])
 return np.array(verts,'f4'),np.array(ids,'i4')

ROCK_SHADER=r'''if(kind==0||kind==3){
 vec3 gn=normalize(N),weights=pow(abs(gn),vec3(6.));weights/=max(.0001,weights.x+weights.y+weights.z);
 vec4 tx=texture(rocktex,P.zy*.061),ty=texture(rocktex,P.xz*.061),tz=texture(rocktex,P.xy*.061);
 vec4 q=tx*weights.x+ty*weights.y+tz*weights.z;
 vec4 fx=texture(rocktex,P.zy*.253),fy=texture(rocktex,P.xz*.253),fz=texture(rocktex,P.xy*.253);
 vec4 fine=fx*weights.x+fy*weights.y+fz*weights.z;
 vec3 perturb=vec3(0.,tx.b-.5,tx.g-.5)*weights.x+vec3(ty.g-.5,0.,ty.b-.5)*weights.y+vec3(tz.g-.5,tz.b-.5,0.)*weights.z;
 vec3 micro=vec3(0.,fx.b-.5,fx.g-.5)*weights.x+vec3(fy.g-.5,0.,fy.b-.5)*weights.y+vec3(fz.g-.5,fz.b-.5,0.)*weights.z;
 n=normalize(gn+perturb*.86+micro*.22);
 float joint=clamp(q.a*.88+fine.a*.15,0.,1.);
 float level=P.y*.43+texture(detailtex,P.xz*.012).r*.53;
 float layer=1.-smoothstep(.025,.095,abs(fract(level)-.5));
 float ash=smoothstep(.48,.90,gn.y)*smoothstep(.45,.68,q.r);
 float oxidized=smoothstep(.56,.72,texture(detailtex,vec2(P.y*.017,P.x*.006+P.z*.009)).r);
 vec3 base=mix(vec3(.065,.074,.081),vec3(.23,.225,.207),clamp(q.r*1.35-.10,0.,1.));
 base=mix(base,vec3(.215,.118,.060),oxidized*.37);
 base=mix(base,vec3(.30,.284,.251),ash*.25);
 base*=mix(.28,1.,1.-joint*.81)*(1.-layer*.16)*(.85+.28*fine.r);
 float damp=(1.-smoothstep(sea+.15,sea+1.65,P.y))*wet;base*=mix(1.,.60,damp);
 float sh=shadow();float ao=clamp(1.-joint*.54-layer*.10,.30,1.);
 col=base*(vec3(.30,.38,.48)*ao+vec3(1.44,1.24,1.00)*max(0.,dot(n,l))*sh);
 col+=vec3(.023,.035,.052)*max(.15,gn.y)*ao;
 vec3 hvec=normalize(l+v);float spec=pow(max(0.,dot(n,hvec)),mix(17.,72.,damp));
 col+=vec3(.17,.18,.18)*spec*sh*(.19+.50*damp)*(1.-joint);
 float rad=length(P.xz-vec2(0,-18));float glow=exp(-rad*.19)*exp(-abs(P.y-12.)*.20);
 col+=vec3(.42,.070,.009)*glow*heat*(.40+.60*ao);
}'''

start=S.FRAG.index('if(kind==0||kind==3)');end=S.FRAG.index('else if(kind==1)',start)
S.FRAG=S.FRAG[:start]+ROCK_SHADER+'\n'+S.FRAG[end:]
S.FRAG=S.FRAG.replace('uniform mat4 reflectvp;out vec4 frag;','uniform sampler2D rocktex;uniform mat4 reflectvp;out vec4 frag;')
S.FRAG=S.FRAG.replace('for(int i=0;i<4;i++){vec2 o=vec2(i%2,i/2)-.5;', 'for(int i=0;i<9;i++){vec2 o=vec2(i%3,i/3)-1.;').replace('return s*.25;','return s/9.;')
S.FRAG=S.FRAG.replace('else{col=tint.rgb;}',r'''else if(kind==10){
 vec4 f=texture(detailtex,UV*vec2(4,2)+vec2(time*.014,0));
 float limb=pow(max(0.,dot(n,v)),.40);float gran=.68+.50*f.r;
 col=mix(vec3(2.8,.52,.045),vec3(5.8,2.5,.65),limb)*gran;
}else if(kind==11){float pulse=.72+.28*sin(UV.y*18.-time*7.);col=tint.rgb*pulse;}
else{col=tint.rgb;}''')
# Slightly more smoke integration; soft highlight bloom remains localized.
S.COMPOSITE=S.COMPOSITE.replace('/36.','/44.').replace('i<36','i<44')
S.COMPOSITE=S.COMPOSITE.replace('vec3 col=texture(picture,uv).rgb;',r'''vec3 col=texture(picture,uv).rgb;
vec2 pix=1./vec2(textureSize(picture,0));vec3 bloom=vec3(0);
for(int k=0;k<8;k++){float a=float(k)*.785398;vec2 p=uv+vec2(cos(a),sin(a))*pix*6.;bloom+=max(vec3(0),texture(picture,p).rgb-1.4);}
col+=bloom*.018;''')

A=np.array([-5.,.75,-5.]);B=np.array([5.,-.65,5.])
def time_path(u):
 return A*(1-u)+B*u+np.array([0.,1.1*np.sin(np.pi*u),-.80*np.sin(np.pi*u)])
def tube_path(points,radius=.035,sides=8):
 pts=np.array(points,float);v=[];idx=[]
 for j,p in enumerate(pts):
  tangent=S.unit(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)])
  right=S.unit(np.cross(tangent,[0,1,0]));up=S.unit(np.cross(right,tangent))
  for k in range(sides+1):
   a=2*np.pi*k/sides;n=np.cos(a)*right+np.sin(a)*up;v.append([*(p+n*radius),*n,k/sides,j/max(1,len(pts)-1)])
 for j in range(len(pts)-1):
  for k in range(sides):a=j*(sides+1)+k;b=a+sides+1;idx.extend([a,b,a+1,a+1,b,b+1])
 return np.array(v,'f4'),np.array(idx,'i4')
def ring_geometry(rad=1.,count=120):
 return tube_path([[rad*np.cos(a),rad*np.sin(a),0.] for a in np.linspace(0,2*np.pi,count)],.016,6)

class Cinema(OLD_CINEMA):
 def __init__(self):
  super().__init__()
  data=basalt_texture();self.basalt=self.c.texture((1024,1024),4,data.tobytes());self.basalt.build_mipmaps();self.basalt.filter=(moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR)
  Image.fromarray(data[:,:,:3]).save(ROOT/'assets/basalt_relief_normal_channels.png')
  self.mesh('rock',*fractured_rock(67031))
  self.mesh('rimblock',*fractured_rock(67032))
  rng=np.random.default_rng(670304);self.rimrocks=[]
  for j in range(126):
   ang=float(rng.uniform(0,2*np.pi));rad=float(rng.uniform(4.1,8.0));x=rad*np.cos(ang);z=-18+rad*np.sin(ang);y=float(self.g.height(x,z));sc=float(rng.uniform(.12,.53))
   self.rimrocks.append(S.matrix([x,y-.06,z],[sc*1.7,sc*.72,sc],float(rng.uniform(0,6.28))))
  self.sun=S.unit([-.64,.49,.57]);self.lightvp=S.ortho(-105,105,-120,120,1,360)@S.look(self.sun*170+[0,0,-25],[0,0,-25]);self.render_shadow()
  self.sf.use()
  for m in self.rimrocks:self.put(self.sp,'model',m);self.meshes['rimblock'][1].render()
  for off,name in [(-.18,'rail_left'),(.18,'rail_right')]:
   pts=[time_path(u)+np.array([off,0.,0.]) for u in np.linspace(0,1,170)];self.mesh(name,*tube_path(pts,.028,8))
  self.mesh('timehalo',*ring_geometry(1.))
  self.mesh('tick',*tube_path([[-.30,0,0],[.30,0,0]],.018,6))
  self._timeline_cfg=None
 def setcommon(self,cfg,t,eye,vp):
  super().setcommon(cfg,t,eye,vp)
  self.basalt.use(8);self.put(self.prog,'rocktex',8)
 def world(self,cfg,t,with_water=True):
  if cfg.get('time_scene',False):
   self.time_world(cfg,t);return
  super().world(cfg,t,with_water)
  if not cfg['orbital']:
   for m in self.rimrocks:self.draw('rimblock',3,m)
 def time_world(self,cfg,t):
  u=cfg['u'];progress=cfg['time_progress'];a=A+[0,.85,0];b=B+[0,.85,0]
  self.draw('rail_left',11,tint=(.38,.98,1.35,1));self.draw('rail_right',11,tint=(1.4,.57,.12,1))
  for j in range(18):
   q=j/17;p=time_path(q);self.draw('tick',8,S.matrix(p),tint=(.20,.37,.46,1))
  self.draw('planet',4,S.matrix(a,.235,angle=.30+t*.045))
  self.draw('sphere',10,S.matrix(b,.67,angle=t*.08))
  self.draw('timehalo',8,S.matrix(a,[1.0,1.0,1.0]),tint=(.65,.31,.10,1))
  self.draw('timehalo',8,S.matrix(b,[.98,.98,.98]),tint=(.24,.60,.85,1))
  # A forward travelling pulse encodes chronological progress, not physical flight.
  for j in range(14):
   q=progress-j*.012
   if 0<=q<=1:self.draw('grain',8,S.matrix(time_path(q),.048*(1-j/20)),tint=(1.6,1.1,.42,1))
  for j in range(5):
   q=(t*.16+j*.2)%1;p=time_path(q)+[0,.06,0];self.draw('grain',8,S.matrix(p,.025),tint=(.34,.75,1.15,1))
 def frame(self,cfg,t):
  im,qa=super().frame(cfg,t)
  qa['basalt_material']='triplanar fractured basalt, stratification, roughness and moist-zone specular'
  qa['time_scene']=bool(cfg.get('time_scene',False))
  if cfg.get('time_scene',False):
   eye=np.array(cfg['eye']);vp=S.perspective(cfg['fov'],S.W/S.H)@S.look(eye,cfg['target']);cent=[]
   for p in [A+[0,.85,0],B+[0,.85,0]]:
    h=vp@np.r_[p,1.];nd=h[:3]/h[3];cent.append([(nd[0]+1)*S.W/2,(1-nd[1])*S.H/2])
   qa['chronology_centers_px']=cent;qa['chronology_years']=[8000000000,4600000000]
  return im,qa

_GEOCHECK=None
def config(t,tl):
 global _GEOCHECK
 c=OLD_CONFIG(t,tl)
 if c['scene']==2:
  a,d=tl['boundaries'][2:4];second=tl['cues'][5]['start'];q=S.ramp(t,second-.15,d-.20)
  c.update(time_scene=True,orbital=True,eye=S.mix([7.8,4.0,22.5],[9.,6.0,29.5],q).tolist(),target=S.mix([1.5,.4,2.5],[0.,.55,0.],q).tolist(),fov=39.,heat=.62,wet=.15,ocean=0.,time_progress=S.ramp(t,a+.15,second+.65),event='travel_and_reveal_3_4_billion_year_interval')
 elif not c['orbital']:
  if _GEOCHECK is None:_GEOCHECK=Geography()
  eye=np.array(c['eye'],float);floor=float(_GEOCHECK.height(eye[0],eye[2]))
  if eye[1]<floor+.90:eye[1]=floor+.90;c['eye']=eye.tolist()
 return c

S.Cinema=Cinema;S.config=config
import p067v2_finish as F
F.PREFIX='heionreki_p067_v3'
BASE_TYPO=F.Typography
class Typography(BASE_TYPO):
 def overlay(self,im,t,cfg,tl):
  if cfg['scene']!=2:return super().overlay(im,t,cfg,tl)
  out=im.convert('RGBA');out.alpha_composite(self.shade);d=ImageDraw.Draw(out,'RGBA')
  self.text(d,'平穏暦全史  ／  前史067',68,128,29,(217,230,236,240),'lm')
  self.text(d,'同じ宇宙、違う始まり',540,255,42,(215,232,240,255))
  a,b=tl['boundaries'][2:4];second=tl['cues'][5]['start']
  eye=np.array(cfg['eye']);vp=S.perspective(cfg['fov'],S.W/S.H)@S.look(eye,cfg['target']);boxes=[]
  for p,title,age,col in [(A+[0,.85,0],'オーウェルの形成','約80億年前',(255,206,133,255)),(B+[0,.85,0],'太陽の形成','約46億年前',(181,227,248,255))]:
   h=vp@np.r_[p,1.];v=h[:3]/h[3];x=float(np.clip((v[0]+1)*S.W/2,225,855));y=float(np.clip((1-v[1])*S.H/2+110,690,1275))
   self.text(d,title,x,y,31,col);self.text(d,age,x,y+58,46,col)
   boxes.append([x-180,y-24,x+180,y+90])
  q=S.ramp(t,second-.06,second+.42);op=round(255*q)
  self.text(d,'約34億年',540,455,88,(255,224,165,op));self.text(d,'先に始まった世界',540,548,39,(231,240,245,op))
  cue=next((c for c in tl['cues'] if c['start']-.07<=t<=c['end']+.16),None)
  if cue:
   op=min(S.ramp(t,cue['start']-.07,cue['start']+.08),1-S.ramp(t,cue['end']+.04,cue['end']+.16));rise=16*(1-S.ramp(t,cue['start']-.07,cue['start']+.11));lines=self.lines(cue['text']);cy=1550+rise;hh=87*len(lines)+32
   d.rounded_rectangle((60,cy-hh/2,1020,cy+hh/2),radius=17,fill=(3,12,20,round(145*op)))
   for j,line in enumerate(lines):self.text(d,line,540,cy+(j-(len(lines)-1)/2)*87,64,(242,247,248,round(255*op)))
  self.text(d,'年代の比較  ·  光の道と奥行きは時間を表す演出',540,1788,24,(187,205,214,235))
  if max(boxes[0][0],boxes[1][0])<min(boxes[0][2],boxes[1][2]) and max(boxes[0][1],boxes[1][1])<min(boxes[0][3],boxes[1][3]):
   raise RuntimeError('Chronology labels intersect: '+str(boxes))
  return out.convert('RGB')
F.Typography=Typography

def finish():
 F.assemble()
 tl=F.timeline();qa=json.loads((ROOT/'review/verification.json').read_text())
 qa.update(revision='v3-rocktime',terrain_triangles=655360,independent_rock_material_map=[1024,1024],triplanar_material=True,chronology_is_spatial_geometry=True,chronology_label_collision_checks='every rendered frame in scene 2',science_and_voice_changed=False)
 F.dump(ROOT/'review/verification.json',qa)
 note=ROOT/'deliverables'/f'{F.PREFIX}_script_and_sources.txt'
 text=note.read_text().replace('前史067 第2版','前史067 第3版').replace('344064','655360')
 text+='\n\n第3版の追加改訂：\n火山の地形を細分化し、非対称の欠けた火口縁・斜面の岩屑・角張った玄武岩ブロックを追加。岩石専用の割れ目と凹凸を持つ材質を、三方向から投影して急斜面の伸びを軽減。暗い玄武岩、変質層、火山灰、濡れた岩を区別。元の海・溶岩用材質は別途保持。地層や岩肌は景観の再構成であり、現地観測データではない。\n平面の年代パネルを撤去し、立体の光路・奥行き・年代の異なる二つの小さな再現模型・前へ進む光で約34億年の隔たりを示す。光路の距離や飛行速度は物理的な距離・速度ではない。二つの天体模型は別々の年代を比較しており、同時代の隣接天体の配置ではない。\n原音、発音記録、字幕の本文と時刻、完成AAC音声を引き継いだ。追加の音声生成・課金サービス・画像生成を使用していない。\n'
 text+='\n第3版の検査結果：\n'+json.dumps(qa,ensure_ascii=False,indent=2)
 note.write_text(text,encoding='utf-8')
 shutil.copy(__file__,ROOT/'source'/Path(__file__).name)
 (ROOT/'source/REEDIT.txt').write_text('p067_v3として作業フォルダへ展開。source内のp067v3_rocktime.py、p067v2_scene.py、p067v2_finish.pyを同一フォルダに置く。依存関係numpy scipy Pillow moderngl glcontext、ffmpeg、EGL、Noto Sans CJK JP。P067_FONTで書体パスを指定。python source/p067v3_rocktime.py shot N（0..9）、続けてassemble。音声を再生成しない場合は同梱の完成MP4をoriginal_previewへ配置。フォント・声モデルを配布しない。\n',encoding='utf-8')
 # The archive generated by the inherited finisher is replaced only after validation.
 archive=ROOT/'deliverables'/f'{F.PREFIX}_production.zip';archive.unlink()
 files=[]
 for p in ROOT.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.ttf','.otf','.ttc','.zip']:
   files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 F.dump(ROOT/'review/manifest.json',files)
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in ROOT.rglob('*'):
   if p.is_file() and p!=archive and p.suffix.lower() not in ['.ttf','.otf','.ttc'] and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(ROOT)))
 print('V3_FINAL',json.dumps(qa,ensure_ascii=False),flush=True)
 print('V3_DELIVERABLES',json.dumps([{'name':p.name,'bytes':p.stat().st_size} for p in (ROOT/'deliverables').iterdir()],ensure_ascii=False),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':F.prepare()
 elif mode=='shot':F.shot(int(sys.argv[2]))
 elif mode=='preview':
  for i in [0,2,3,4,6,9]:F.shot(i,True)
 elif mode=='testclip':
  F.shot(2);F.shot(3)
 elif mode=='assemble':finish()
 else:raise ValueError(mode)
