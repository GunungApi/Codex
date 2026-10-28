"""HEION-P065 v1. Original 3-D educational film; no third-party picture assets.
This is a qualitative process model, not a numerical reconstruction of a vent.
Voice runtime and fonts are dependencies and must not enter the delivery ZIP.
"""
import os,sys,json,math,shutil,subprocess,hashlib,zipfile,inspect,re
from pathlib import Path
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','3')
os.environ.setdefault('OMP_NUM_THREADS','3')
ROOT=Path(os.environ.get('P065_ROOT','p065_v1')).resolve()
os.environ['P064_ROOT']=str(ROOT)
import p064_v2_film as f
import numpy as np
from PIL import Image,ImageDraw
import moderngl
W,H,FPS,SR=1080,1920,24,48000
ID='heionreki_p065_v1'
TITLE='反応を続けるには、「差」がいる'
PARTS=[
('熱い水があれば、','If the water is hot,',0),
('反応はずっと続くのだろうか。','will reactions keep going forever?',0),
('海底の熱水と、周りの海水。','Hydrothermal fluid meets the surrounding seawater.',1),
('二つの水は、含む物質が違う。','The two fluids contain different substances.',1),
('電子を渡しやすい物質と、','Some substances can donate electrons,',2),
('受け取って変わる物質がある。','while others can accept them and change.',2),
('間に、電気を通す鉱物があると、','An electrically conductive mineral between them',3),
('電子が、その中を移動できる。','can carry electrons through the rock.',3),
('この化学的な差が、','This chemical disequilibrium',4),
('反応を進める力になる。','can drive chemical reactions.',4),
('流れを止めて、混ざっていくと、','If supply stops and the fluids mix,',5),
('使える差は、小さくなっていく。','the available difference diminishes.',5),
('同じ反応を進める力も、弱まる。','The driving force for that reaction also weakens.',6),
('そこで、新しい水を送り続けよう。','Now keep supplying fresh fluid.',6),
('熱水が材料を補い、海水も入れ替わる。','Hydrothermal fluid replenishes reactants, as seawater is renewed.',7),
('こうして、化学的な差を保てる。','These flows can maintain the chemical disequilibrium.',7),
('できたものが流れて、次の材料が来る。','Products move away, and fresh reactants arrive.',8),
('反応を支えるのは、つながった流れ。','Connected flows can sustain the reactions.',8),
('生命につながる化学は、','How could chemistry leading toward life',9),
('この流れの中で、どう育つのだろう。','develop within these continuing flows?',9)]
f.PARTS=PARTS
HEADINGS=['熱いだけで、続く？','出会う、二つの水','電子を渡す。受け取る。','鉱物が、道になる','化学的な差で、反応が進む','供給を止めると？','止める／続ける','新しい水が、差を保つ','できたものは、その先へ','反応を支える、流れ']
GOLD=np.array([.94,.47,.105]);CYAN=np.array([.10,.65,.82]);MINT=np.array([.17,.85,.56]);WHITE=np.array([.88,.96,1.]);STONE=np.array([.20,.23,.24]);BRONZE=np.array([.40,.30,.16]);NEUTRAL=np.array([.25,.39,.43])
ease=f.ease;smooth=f.smooth;lerp=f.lerp;unit=f.unit;rot=f.rot;dump=f.dump;run=f.run
SOURCES=[
{'id':'S1','title':'Kitadai et al. (2019), Metals likely promoted protometabolism in early ocean alkaline hydrothermal systems','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6584212/','doi':'10.1126/sciadv.aav7848','scope':'導電性硫化物を通じた電子移動、電気化学的に生成した金属と硫化物による有機反応の促進。自然の候補環境と室内実験を区別。'},
{'id':'S2','title':'ELSI (2019-06-21), Electricity-driven undersea reactions may have been important for the emergence of life','url':'https://wpi.elsi.jp/en/news_events/highlights/2019/20190621_nkitadai.html','scope':'熱水と海水の組成差、導電性鉱物、生命前の化学に関する研究当事者の解説。'},
{'id':'S3','title':'Yamamoto et al. (2017), Spontaneous and Widespread Electricity Generation in Natural Deep-Sea Hydrothermal Fields','url':'https://pubmed.ncbi.nlm.nih.gov/28378459/','doi':'10.1002/anie.201701768','scope':'現代の自然熱水域の電気化学調査。現代の酸素に富む海水を古代海洋へそのまま転用しない。'}]
for d in ['audio/raw','source','render','review','docs','deliverables']:(ROOT/d).mkdir(parents=True,exist_ok=True)

def cube_mesh():
 vv=[];ii=[]
 for axis in range(3):
  for side in [-1,1]:
   n=np.zeros(3);n[axis]=side;other=[i for i in range(3) if i!=axis];off=len(vv)
   for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
    p=np.zeros(3);p[axis]=side;p[other[0]]=a;p[other[1]]=b;vv.append([*p,*n])
   ii += [off,off+1,off+2,off,off+2,off+3]
 return np.array(vv,'f4'),np.array(ii,'i4')

def rock_mesh(seed=1):
 v,idx=f.sphere_mesh(12,8);rng=np.random.default_rng(seed)
 for row in v:
  x,y,z=row[:3];r=1+.10*math.sin(5*x+2*y)*math.cos(6*z-y)+.06*math.sin(12*y+3*z);row[:3]*=r
 # True face normals preserve faceted geological surfaces.
 vv=[];ii=[]
 for j in range(0,len(idx),3):
  pts=v[idx[j:j+3],:3];n=unit(np.cross(pts[1]-pts[0],pts[2]-pts[0]))
  if np.dot(n,np.mean(pts,axis=0))<0:n=-n
  for p in pts:ii.append(len(vv));vv.append([*p,*n])
 return np.array(vv,'f4'),np.array(ii,'i4')

def terrain_mesh():
 xs=np.linspace(-13,13,65);zs=np.linspace(-11,8,49);vv=[];ii=[]
 def height(x,z):return -3.50+.19*math.sin(x*.7+z*.4)+.13*math.cos(z*.9-x*.3)+.08*math.sin(x*2.2+z*1.8)
 for z in zs:
  for x in xs:
   e=.02;dx=(height(x+e,z)-height(x-e,z))/(2*e);dz=(height(x,z+e)-height(x,z-e))/(2*e);vv.append([x,height(x,z),z,*unit([-dx,1,-dz])])
 for j in range(len(zs)-1):
  for i in range(len(xs)-1):k=j*len(xs)+i;l=k+len(xs);ii.extend([k,l,k+1,k+1,l,l+1])
 return np.array(vv,'f4'),np.array(ii,'i4')

class Renderer(f.Renderer):
 def __init__(self):
  super().__init__();self.mesh('cube',*cube_mesh());self.mesh('rock',*rock_mesh());self.mesh('terrain',*terrain_mesh());self.packets=[]
 def reset(self):
  super().reset();self.packets=[];self.effect=0.;self.note='色・粒子・電子の道は説明用';self.eye=np.array([.4,1.7,20.]);self.target=np.array([0,.2,0.]);self.events=[]
 def marker(self,p,kind=0,scale=1.,alpha=1.,highlight=0.,track=True,tag='material'):
  p=np.asarray(p,float);r=.17*scale
  if track and alpha>.9:self.packets.append((tag,p.tolist(),.29*scale))
  if kind==0:
   self.ball(p+[-.105*scale,0,0],r,GOLD,alpha=alpha,rough=.16,emit=highlight*.5);self.ball(p+[.105*scale,0,0],r,GOLD,alpha=alpha,rough=.16,emit=highlight*.5)
  elif kind==1:
   self.add('cube',p,[r,r,r],CYAN,alpha=alpha,rotation=rot(.35,.3,.4),rough=.13,emit=highlight*.5)
   self.ball(p+[.20*scale,.10*scale,0],.075*scale,WHITE,alpha=alpha)
  elif kind==2:
   self.add('cube',p,[r,r,r],MINT,alpha=alpha,rotation=rot(.4,.4,.4),rough=.13,emit=highlight*.5)
   self.ball(p+[.20*scale,.10*scale,0],.075*scale,WHITE,alpha=alpha)
 def ribbon(self,pts,width,col,alpha=.45):
  for a,b in zip(pts,pts[1:]):self.bar(a,b,width,col,alpha=alpha,rough=.45,emit=.18)
 def arrow(self,a,b,col=CYAN,width=.055,alpha=1):
  a=np.asarray(a);b=np.asarray(b);self.bar(a,b,width,col,alpha=alpha,emit=.4);d=unit(b-a);side=unit(np.cross(d,[0,0,1]));p=b-d*.35
  self.bar(b,p+side*.20,width,col,alpha=alpha,emit=.4);self.bar(b,p-side*.20,width,col,alpha=alpha,emit=.4)
 def label3(self,text,p,size=38,color=(237,247,249)):
  self.labels.append(('world',text,np.asarray(p),size,color))
 def mineral(self,center=(0,.4,0),sx=.73,sy=2.2,sz=.45,open_cut=False):
  p=np.asarray(center,float)
  self.add('cube',p,[sx,sy,sz],STONE,rough=.82)
  for j in range(11):
   yy=-sy+(j+.5)*2*sy/11;xx=.18*math.sin(j*2.7)
   self.add('rock',p+[xx,yy,-.12],[sx*(.88+.12*math.sin(j)),sy/5,.58],BRONZE*(.85+.12*math.cos(j*3)),rotation=rot(.13*j,.17*j,.07*j),rough=.75)
  # The front face is a schematic exposed section, never a fabricated wire.
  for i in range(18):
   xx=(i%3-1)*sx*.58;yy=(i//3-2.5)*sy*.29
   self.add('cube',p+[xx,yy,sz+.025],[sx*.15,sy*.052,.035],[.44,.39,.24],rotation=rot(0,0,.3*math.sin(i)),rough=.52)
 def electron(self,p,scale=.085,alpha=1.):
  self.ball(p,scale,WHITE,alpha=alpha,emit=2.3,rough=.12);self.ball(p,scale*1.7,GOLD,alpha=alpha*.17,emit=1.8)
 def frame(self,t,scene,cue):
  c=self.c;self.f.use();c.viewport=(0,0,W,H);self.f.clear(0,0,0,1,depth=1);c.disable(moderngl.DEPTH_TEST|moderngl.BLEND|moderngl.CULL_FACE);self.bg['t']=t;self.bgv.render(moderngl.TRIANGLE_STRIP)
  eye=self.eye;fw=unit(self.target-eye);right=unit(np.cross(fw,[0,1,0]));up=np.cross(right,fw);v=np.eye(4);v[:3,:3]=[right,up,-fw];v[:3,3]=-v[:3,:3]@eye
  k=1/np.tan(np.radians(37)/2);near=.1;far=100;pr=np.zeros((4,4));pr[0,0]=k/(W/H);pr[1,1]=k;pr[2,2]=(far+near)/(near-far);pr[2,3]=2*far*near/(near-far);pr[3,2]=-1;self.vp=pr@v
  self.p['vp'].write(self.vp.T.astype('f4').tobytes());self.p['eye']=tuple(eye);self.p['t']=t;c.enable(moderngl.DEPTH_TEST)
  for translucent in [False,True]:
   if translucent:c.enable(moderngl.BLEND);c.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA);self.f.depth_mask=False
   for name,(vao,_,_) in self.meshes.items():
    rows=[]
    for n,m,col,a,mat in self.items:
     if n==name and (a<.995)==translucent:rows.append([*m.T.reshape(-1),*col,a,*mat])
    if rows:self.ib.write(np.array(rows,'f4').tobytes());vao.render(instances=len(rows))
   if translucent:self.f.depth_mask=True;c.disable(moderngl.BLEND)
  c.disable(moderngl.DEPTH_TEST);self.out.use();self.color.use(0);self.pv.render(moderngl.TRIANGLE_STRIP)
  img=Image.frombytes('RGB',(W,H),self.out.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM);raw=img.copy();d=ImageDraw.Draw(img,'RGBA')
  self.drawtext(d,'平穏暦全史  ／  前史065',540,142,29,(205,225,233,255));d.rounded_rectangle((474,192,606,196),radius=2,fill=(117,215,238,200))
  self.drawtext(d,HEADINGS[scene],540,308,46,(238,248,250,255))
  for a in self.labels:
   if a[0]=='world':
    _,txt,p0,size,col=a;q=self.vp@np.array([*p0,1.]);xx=(q[0]/q[3]+1)*W/2;yy=(1-q[1]/q[3])*H/2;self.drawtext(d,txt,xx,yy,size,(*col,255))
   else:
    txt,x,y,size,col,alpha=a;self.drawtext(d,txt,x,y,size,(*col,alpha))
  self.drawtext(d,self.note,540,1772,25,(157,187,199,235))
  if cue:
   st=cue['start'];en=cue['end'];op=min(smooth(t,st-.07,st+.08),1-smooth(t,en+.04,en+.16));rise=16*(1-smooth(t,st-.07,st+.11));lines=CAPTION_LINES.get(cue['id'],self.wrap(cue['text'],64,880));assert len(lines)<=2
   cy=1548+rise;bh=len(lines)*85+38;d.rounded_rectangle((74,cy-bh/2,1006,cy+bh/2),radius=18,fill=(3,14,24,int(210*op)));d.rounded_rectangle((100,cy-bh/2+18,105,cy+bh/2-18),radius=2,fill=(117,215,238,int(210*op)))
   for j,line in enumerate(lines):self.drawtext(d,line,552,cy+(j-(len(lines)-1)/2)*85,64,(242,247,248,int(255*op)))
  return img,raw

CAPTION_LINES={2:['反応はずっと','続くのだろうか。'],3:['海底の熱水と、','周りの海水。'],4:['二つの水は、','含む物質が違う。'],5:['電子を渡しやすい','物質と、'],6:['受け取って変わる','物質がある。'],7:['間に、電気を通す','鉱物があると、'],8:['電子が、その中を','移動できる。'],11:['流れを止めて、','混ざっていくと、'],12:['使える差は、','小さくなっていく。'],13:['同じ反応を進める力も、','弱まる。'],14:['そこで、新しい水を','送り続けよう。'],15:['熱水が材料を補い、','海水も入れ替わる。'],16:['こうして、','化学的な差を保てる。'],17:['できたものが流れて、','次の材料が来る。'],18:['反応を支えるのは、','つながった流れ。'],20:['この流れの中で、','どう育つのだろう。']}

def vent(r,t,u,ending=False):
 r.eye=np.array([1.4+(.5 if ending else -.6)*ease(u),3.4,18.8-1.0*ease(u)]);r.target=np.array([0,.3,0]);r.add('terrain',[0,0,0],1,[.10,.15,.17],rough=.95)
 for j in range(24):
  a=j*2.399;x=6.5*math.sin(a);z=-5.2+6.1*(j%7)/7
  r.add('rock',[x,-3.2,z],[.65+(j%3)*.27,.27+(j%4)*.12,.5],STONE,rotation=rot(.2*j,.16*j,.1*j),rough=.87)
 for k,(cx,cz,h,rad) in enumerate([(0,0,4.6,.82),(-2.65,-1.4,2.6,.63),(2.5,-2.8,3.4,.70)]):
  for j in range(8):
   y=-3.2+h*j/8;r.add('rock',[cx+.11*math.sin(j*1.7+k),y,cz],[rad*(1-.045*j),h/7,rad*.75],BRONZE*(.72+.12*math.sin(j)),rotation=rot(.12*j,.4*j,.04*j),rough=.8)
  top=-3.2+h
  for j in range(17):
   q=(j/17+t*.19)%1;y=top+.23+q*3.6;x=cx+.35*math.sin(q*6+t*.45)*q;z=cz+.2*math.cos(q*7)
   r.ball([x,y,z],.12+.28*q,[.38,.59,.62],alpha=.12*(1-q),rough=.95)
  for j in range(4):
   q=(j/4+t*.22)%1;p=np.array([cx+.3*math.sin(q*4+t*.6),top+.3+q*3.,cz+.55]);r.marker(p,0,.43,track=False)
 # A large material packet tracks the meaningful transfer at the foreground vent.
 q=(t*.34)%1.;p=[-3.3+6.6*q,.6+.75*math.sin(q*math.pi),1.0];r.marker(p,1 if q<.56 else 2,.85,track=True,tag='hero')
 if ending:
  for j in range(3):
   q=(t*.34+j/3)%1.;r.electron([-.65+1.3*q,.3+.45*math.sin(q*4),.88],.07)
  r.text('差を保つ流れが、反応をつなぐ',540,1260,43)
 else:r.text('海底の熱水環境',540,1265,40)
 r.note='地形・光・時間は説明用の再現';r.semantic={'vent_flow':float(q),'chemical_transfer':True}

def boundary(r,t,progress=1.,electrons=True,flow=1.,mixed=0.,center=(0,.5,0),scale=1.,comparison=False):
 c=np.asarray(center);sc=scale
 def p(x,y,z=0):return c+np.array([x,y,z])*sc
 r.mineral(c,sx=.63*sc,sy=1.95*sc,sz=.35*sc)
 # The fluids are a contextual volume behind the readable symbols.
 lc=lerp(GOLD,NEUTRAL,mixed);rc=lerp(CYAN,NEUTRAL,mixed)
 r.add('cube',p(-1.95,0,-.75),[1.05*sc,2.02*sc,.1],lc,alpha=.10,rough=.8);r.add('cube',p(1.95,0,-.75),[1.05*sc,2.02*sc,.1],rc,alpha=.10,rough=.8)
 for side in [-1,1]:
  r.ribbon([p(side*2.65,-2.35),p(side*2.60,-1),p(side*2.70,.7),p(side*2.62,2.15)],.035*sc,lc if side<0 else rc,.55)
  for j in range(3):
   phase=(t*.32*max(.15,flow)+j/3)%1.;y=-1.65+phase*3.3 if side<0 else 1.65-phase*3.3;x=side*(2.55+.11*math.sin(phase*6.))
   kind=0 if side<0 else 1
   if mixed>.1 and j==1:kind=1-kind
   r.marker(p(x,y,.3),kind,.65*sc,track=True,tag='supply')
  if not comparison:r.label3('熱水側' if side<0 else '海水側',p(side*2.06,2.75),39,color=(245,194,116) if side<0 else (135,220,244))
 if electrons:
  for j in range(3):
   phase=(t*.56+j/3)%1.;x=-.58+phase*1.16;y=.60*math.sin(phase*5.2)
   alpha=progress*(1-mixed)*flow
   r.electron(p(x,y,.48),.080*sc,alpha)
   if alpha>.2:r.arrow(p(-.95,.60,.45),p(-.68,.60,.45),WHITE,.022*sc,alpha)
 r.semantic={'fluid_flow':float(flow),'difference_relative':float(1-mixed),'electron_visibility':float(progress*(1-mixed)*flow)}

def reaction(r,t,strength=1.,center=(0,.3,0),scale=1.,large=False):
 c=np.asarray(center);sc=scale
 r.mineral(c,sx=.51*sc,sy=1.7*sc,sz=.30*sc)
 for lane,y in enumerate([1.0,-1.0]):
  phase=(t*.43+lane*.5)%1.;x=-2.65+phase*5.3
  # Each lane contains one generic substance symbol; it changes state at the surface.
  kind=1 if x<.80 else 2;r.marker(c+np.array([x,y,.68])*sc,kind,.86*sc,highlight=(1-abs(x-.8)/.4)*strength if abs(x-.8)<.4 else 0,tag='reaction')
  for j in range(2):
   q=(phase+j*.45)%1.;r.electron(c+np.array([-.58+q*1.16,y*.55,.43])*sc,.075*sc,strength)
  r.arrow(c+np.array([-2.5,y-.45,.45])*sc,c+np.array([-1.2,y-.45,.45])*sc,CYAN,.032*sc,.75)
  r.arrow(c+np.array([1.15,y-.45,.45])*sc,c+np.array([2.5,y-.45,.45])*sc,MINT,.032*sc,.75)
 r.label3('反応前',c+[-2.2*sc,2.35*sc,0],37,(141,225,247));r.label3('反応後',c+[2.2*sc,2.35*sc,0],37,(139,241,188))
 r.semantic={'reaction_phase':float((t*.43)%1),'driving_strength':strength,'state_change_at_surface':True}

def arrange(r,s,u,t,split):
 cueq=smooth(u,max(.0,split-.05),min(.98,split+.13))
 if s in [0,9]:vent(r,t,u,s==9);return
 if s==1:
  r.eye=np.array([.6,2.1,20.]);boundary(r,t,progress=smooth(u,.18,.50),electrons=False)
  r.text('含む物質が違う',540,1270,46,alpha=int(255*smooth(u,split-.04,split+.12)))
 elif s==2:
  r.eye=np.array([.2,1.4,18.7]);r.marker([-2.0,1.2,.2],0,2.2,highlight=smooth(u,.10,.34));r.marker([2.0,1.2,.2],1,2.2,highlight=cueq)
  r.label3('電子を渡す',[-2.,2.55,0],37,(246,192,113));r.label3('受け取る',[2.,2.55,0],37,(140,225,245))
  r.arrow([-1.3,.2,.2],[1.3,.2,.2],WHITE,.05,smooth(u,.15,.45))
  q=(t*.50)%1;r.electron([-1.35+q*2.7,.2,.5],.115,smooth(u,.2,.45));r.marker([2.,-1.5,.2],2,1.4,alpha=cueq)
  r.text('物質どうしの、電子の受け渡し',540,1280,39);r.semantic={'donor_emphasis':smooth(u,.1,.34),'acceptor_emphasis':cueq,'electron_path':q}
 elif s==3:
  r.eye=np.array([1.1,1.6,19.]);boundary(r,t,progress=cueq,electrons=True)
  r.text('電気を通す鉱物',540,1230,42);r.note='電子の道を強調した断面模型'
  r.semantic['mineral_reveal']=smooth(u,0,.25)
 elif s==4:
  r.eye=np.array([.1,1.1,18.5]);reaction(r,t,strength=.6+.4*cueq)
  r.text('化学的な差  →  反応を進める力',540,1250,39)
 elif s==5:
  r.eye=np.array([0,1.7,20.]);mix=smooth(u,.13,.90);boundary(r,t,flow=1-.85*smooth(u,.05,.30),mixed=mix)
  # Comparison scalar is explicitly relative, not experimental data.
  r.text('新しい供給を止める',540,1170,39)
  for j in range(12):
   col=GOLD if j/12<1-mix else NEUTRAL*.3;r.add('cube',[-2.6+j*.47,-2.9,.3],[.17,.15,.055],col,emit=.3 if j/12<1-mix else 0)
  r.text('使える差',540,1330,35);r.semantic['supply_stop']=smooth(u,.05,.30);r.note='差の大きさは定性的な比較'
 elif s==6:
  r.eye=np.array([0,1.8,21.]);a=np.array([0,2.25,0]);b=np.array([0,-1.35,0]);q=cueq
  boundary(r,t,center=a,scale=.61,flow=.12,mixed=.94,comparison=True)
  top=dict(r.semantic);boundary(r,t,center=b,scale=.61,flow=.12+.88*q,mixed=.85*(1-q),comparison=True)
  r.text('供給を止めた模型',540,520,38,color=(180,195,204));r.text('供給を続ける模型',540,1010,38,color=(131,231,212));r.note='同じ形・同じ比較条件で、供給だけを変更'
  r.semantic.update({'stopped_model':top,'continued_supply':q})
 elif s==7:
  r.eye=np.array([.8,2.0,20.]);boundary(r,t,progress=1.,electrons=True)
  for side,col in [(-1,GOLD),(1,CYAN)]:
   a=np.array([side*3.0,-2.6,.2]);b=np.array([side*2.6,-1.9,.2]);r.arrow(a,b,col,.055)
  r.text('供給と入れ替わりが、差を保つ',540,1280,39)
  r.semantic['renewal_pulse']=float((t*.65)%1.)
 elif s==8:
  r.eye=np.array([.5,1.6,19.4]);reaction(r,t)
  # Products depart; they never teleport back to become reactants on screen.
  for j in range(2):
   q=(t*.27+j*.5)%1.;r.marker([1.2+q*1.5,2.4+q*.75,-.1],2,.55,track=False)
  r.text('材料が来る  →  反応  →  運ばれる',540,1280,38);r.semantic['product_export']=float((t*.27)%1.)


def voice():
 # Reuse the validated synthesis pipeline and exactly the same speaker/settings.
 timeline,narration=f.voice()
 for c in timeline['cues']:
  for token,reading in [('熱水','ネッスイ'),('鉱物','コーブツ'),('電子','デンシ'),('反応','ハンノー')]:
   if token in c['text']:
    kana=re.sub(r"[_'/?、]",'',c['kana'])
    if reading not in kana:print('READING_REVIEW',c['id'],token,c['kana'],flush=True)
 f.music(timeline,narration)
 dump(ROOT/'docs/sources.json',SOURCES)
 print('VOICE_READY',timeline['duration'],timeline['max_query_speech_gap'],flush=True)

def captions(tl,r):
 out=ROOT/'deliverables';ja=[];en=[]
 ass=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','WrapStyle: 2','ScaledBorderAndShadow: yes','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding','Style: Default,Noto Sans CJK JP,64,&H00F8F7F2,&H00EED775,&HBB180E03,&HBB180E03,1,0,0,0,100,100,0,0,3,14,0,5,70,70,200,1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 for c in tl['cues']:
  a=max(0,c['start']-.07);b=c['end']+.16;lines=CAPTION_LINES.get(c['id'],r.wrap(c['text'],64,880))
  assert ''.join(lines)==c['text'];assert all(r.fontobj(64).getlength(line)<=880 for line in lines)
  ja.append(str(c['id'])+'\n'+f.ts(a)+' --> '+f.ts(b)+'\n'+'\n'.join(lines)+'\n');en.append(str(c['id'])+'\n'+f.ts(a)+' --> '+f.ts(b)+'\n'+c['en']+'\n')
  text=r'{\move(552,1564,552,1548,0,180)\fad(140,120)}'+r'\N'.join(lines);ass.append(f'Dialogue: 0,{f.ts(a,True)},{f.ts(b,True)},Default,,0,0,0,,{text}')
 for suffix,txt in [('ja.srt','\n'.join(ja)),('en.srt','\n'.join(en)),('ja.ass','\n'.join(ass))]:(out/(ID+'_'+suffix)).write_text(txt,encoding='utf-8')

def shot(scene,preview=False):
 tl=json.loads((ROOT/'timeline.json').read_text());r=Renderer();captions(tl,r);a,b=tl['boundaries'][scene:scene+2];first=math.ceil(a*FPS-1e-7);last=min(round(tl['duration']*FPS),math.ceil(b*FPS-1e-7));cc=[c for c in tl['cues'] if c['scene']==scene];split=(cc[1]['start']-a)/(b-a)
 frames=[round(first+(last-first-1)*q) for q in [.12,.36,.60,.84]] if preview else range(first,last)
 path=ROOT/f'render/scene_{scene:02}.mp4';p=None
 if not preview:p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','2',str(path)],stdin=subprocess.PIPE)
 states=[];pics=[];prev=None
 for frame in frames:
  t=frame/FPS;u=(t-a)/(b-a);cue=next((c for c in tl['cues'] if c['start']-.07<=t<=c['end']+.16),None);r.reset();arrange(r,scene,u,t,split);im,raw=r.frame(t,scene,cue)
  if p:p.stdin.write(im.tobytes())
  tiny=np.asarray(raw.crop((90,420,990,1390)).resize((180,194)),dtype=np.int16);delta=float(np.mean(np.abs(tiny-prev))) if prev is not None else 0;prev=tiny
  projected=[]
  for tag,pos,rad in r.packets:
   q=r.vp@np.array([*pos,1.]);xy=np.array([(q[0]/q[3]+1)*W/2,(1-q[1]/q[3])*H/2]);pr=1/math.tan(math.radians(37)/2)*H*.5*rad/q[3];projected.append((tag,np.asarray(pos),rad,xy,pr))
  g3=[];g2=[]
  for i,x in enumerate(projected):
   for y in projected[i+1:]:g3.append(float(np.linalg.norm(x[1]-y[1])-x[2]-y[2]));g2.append(float(np.linalg.norm(x[3]-y[3])-x[4]-y[4]))
  states.append({'frame':frame,'time':t,'scene':scene,'raw_subject_mean_delta':delta,'minimum_material_gap_3d':min(g3) if g3 else None,'minimum_material_gap_screen_px':min(g2) if g2 else None,'semantic':r.semantic})
  if preview or frame in [round(first+(last-first-1)*q) for q in [.12,.36,.60,.84]]:
   name=f'scene_{scene:02}_{frame:04}.jpg';im.save(ROOT/'review'/name,quality=93);pics.append(name)
  if frame%48==0:print('FRAME',scene,frame-first,last-first,flush=True)
 if p:p.stdin.close();assert p.wait()==0
 dump(ROOT/f'review/scene_{scene:02}_states.json',states);dump(ROOT/f'review/scene_{scene:02}_pictures.json',pics)
 print('SHOT_OK',scene,len(states),min([s['minimum_material_gap_screen_px'] for s in states if s['minimum_material_gap_screen_px'] is not None] or [999]),flush=True)

def assemble():
 tl=json.loads((ROOT/'timeline.json').read_text());out=ROOT/'deliverables';parts=[ROOT/f'render/scene_{s:02}.mp4' for s in range(10)];assert all(p.exists() for p in parts)
 cat=ROOT/'render/concat.txt';cat.write_text('\n'.join("file '"+str(p)+"'" for p in parts));native=ROOT/'render/native_picture.mp4';run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(cat),'-c','copy',str(native)])
 high=out/(ID+'_high_1080x1920.mp4');light=out/(ID+'_light_720x1280.mp4')
 run(['ffmpeg','-y','-v','error','-i',str(native),'-i',str(ROOT/'audio/master.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar',str(SR),'-t',str(tl['duration']),'-movflags','+faststart',str(high)])
 run(['ffmpeg','-y','-v','error','-i',str(high),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','fast','-crf','24','-threads','3','-c:a','copy','-movflags','+faststart',str(light)])
 r=Renderer();captions(tl,r);states=[];pictures=[]
 for s in range(10):states+=json.loads((ROOT/f'review/scene_{s:02}_states.json').read_text());pictures+=json.loads((ROOT/f'review/scene_{s:02}_pictures.json').read_text())
 assert [x['frame'] for x in states]==list(range(round(tl['duration']*FPS)))
 vals=np.array([x['raw_subject_mean_delta'] for x in states]);window=np.convolve(vals,np.ones(48)/48,mode='valid')
 gap3=[x['minimum_material_gap_3d'] for x in states if x['minimum_material_gap_3d'] is not None];gap2=[x['minimum_material_gap_screen_px'] for x in states if x['minimum_material_gap_screen_px'] is not None]
 report={'duration':tl['duration'],'frames':len(states),'native_resolution':[1080,1920],'fps':24,'voice_max_gap_from_synthesis_seconds':tl['max_query_speech_gap'],'minimum_material_separation_3d':min(gap3),'minimum_material_separation_projected_px':min(gap2),'material_overlap_frames':[x['frame'] for x in states if x['minimum_material_gap_screen_px'] is not None and x['minimum_material_gap_screen_px']<0],'minimum_two_second_subject_change':float(window.min()),'weak_motion_windows':[int(i) for i,v in enumerate(window) if v<.015],'scope':'Distinct highlighted substance symbols are tested in world and projection space. Internal bonded beads, electrons travelling through a conductive mineral, and background fluid/terrain are intentional. Pixel change flags are not perceptual proof.','listening_performed':False,'continuous_visual_screening_performed':False}
 dump(ROOT/'review/frame_states.json',states);dump(ROOT/'review/quality_report.json',report)
 sheet=Image.new('RGB',(1080,3072),(7,17,25))
 for i,n in enumerate(pictures):sheet.paste(Image.open(ROOT/'review'/n).resize((216,384)),((i%5)*216,(i//5)*384))
 sheet.save(ROOT/'review/contact_sheet.jpg',quality=93)
 media={}
 for path in [high,light]:
  run(['ffmpeg','-v','error','-i',str(path),'-f','null','-']);pr=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-show_format','-of','json',str(path)]));media[path.name]=pr
  vs=next(x for x in pr['streams'] if x['codec_type']=='video');assert int(vs['nb_frames'])==len(states);assert any(x['codec_type']=='audio' for x in pr['streams'])
 lm=subprocess.run(['ffmpeg','-v','info','-i',str(high),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);loud=json.loads(lm.stderr[lm.stderr.rfind('{'):lm.stderr.rfind('}')+1]);dump(ROOT/'review/export_loudness.json',loud);dump(ROOT/'review/final_media.json',media)
 # Decode actual completed files again to make the review frames reflect subtitles and muxed output.
 for i,tt in enumerate([c['start']+.4 for c in tl['cues']]):run(['ffmpeg','-y','-v','error','-ss',str(tt),'-i',str(high),'-frames:v','1','-q:v','2',str(ROOT/f'review/final_{i:02}.jpg')])
 notes='平穏暦全史・前史065 第1版\n'+TITLE+'\n制作日・資料確認日：2026年10月28日\n\n仕様：'+str(tl['duration'])+'秒、1080×1920を直接3D描画、24fps。軽量版720×1280。\n\n台本\n'+'\n'.join(x[0] for x in PARTS)
 notes+='\n\n科学と演出\n・熱水と海水の酸化還元の差と導電性鉱物が中心。温度差による濃縮を示す回ではない。\n・金色の二珠と水色の角型は異なる物質群の記号。緑は反応後。特定の分子式・反応式の原子模型ではない。白い点は電子の移動の可視化であり、粒子の実寸や軌跡の実測ではない。\n・自然の鉱物内に現代の電線を設置した描写ではない。電子の通り道を断面の手前へ強調して示す。\n・供給停止と混合の比較は、使える差の減少を示す定性的模式模型。平衡でも微視的反応が消滅するという意味ではなく、同じ正味の反応を駆動する力の低下を示す。\n・流れは反応物の補給と生成物の移送を含む。すべての熱水反応がこの条件だけで永久に続くと主張しない。\n・高温だけで有用な反応が成立するとは限らない。鉱物・反応物・電位・化学条件が重要。生命の起源の場所の確定や生命の完成は示さない。\n・現代の自然環境の測定と初期海洋を模す実験を区別し、現代の酸素に富む海水を初期海洋へ置かない。\n・光る点、流線、相対的な差の目盛り、時間圧縮は説明演出。測定グラフではない。\n\n演出\n十場面を、海底景観、境界、電子受け渡し、鉱物断面、反応、供給停止、同条件比較、供給再開、生成物搬出、海底全景へ組む。大きな意味の変化は語りに同期し、進行中も物質が動く。カメラの揺れや字幕だけで動きを稼がない。\n\n音声：VOICEVOX 四国めたん、ノーマル、話速0.96。発音辞書の確認は合成のカナと音素時間の照合。人による耳での試聴は未実施。\n音楽・効果音：数式合成のオリジナル。話している間は背景を下げる。\n\n出典\n'
 for src in SOURCES:notes+=src['id']+' '+src['title']+'\n'+src['url']+'\n'+src['scope']+'\n\n'
 notes+='\n検査結果\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n完成音量\n'+json.dumps(loud,indent=2)
 (out/(ID+'_script_and_sources.txt')).write_text(notes,encoding='utf-8');(ROOT/'docs/sources.json').write_text(json.dumps(SOURCES,ensure_ascii=False,indent=2));(ROOT/'README_再編集.md').write_text('# 前史065\n音声→10場面の3D描画→合成→検査の制作一式。\n`python source/p065_film.py voice`、`shot 0`から`shot 9`、`assemble`。音声変更がなければ保存済み原音とtimeline.jsonを利用。\nPython 3.13、numpy、scipy、Pillow、soundfile、moderngl 5.12、glcontext 3、FFmpeg、Mesa EGL、Noto Sans CJK JP太字。フォントと声モデルは同梱しない。\n',encoding='utf-8')
 for source in [Path(__file__),Path(f.__file__)]:shutil.copy(source,ROOT/'source'/source.name)
 (ROOT/'source/requirements.txt').write_text('numpy\nscipy\nPillow\nsoundfile\nmoderngl==5.12.0\nglcontext==3.0.0\n')
 archive=out/(ID+'_production.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in sorted(ROOT.rglob('*')):
   if p.is_file() and p!=archive and '__pycache__' not in str(p) and 'voice_data' not in str(p) and p.suffix not in ['.ttf','.ttc','.otf'] and p.stat().st_size<100_000_000:z.write(p,'HEION-P065-v1/'+str(p.relative_to(ROOT)))
 print('FINAL_REPORT',json.dumps(report,ensure_ascii=False),flush=True);print('EXPORT_LOUDNESS',json.dumps(loud),flush=True);print('FILES',[(p.name,p.stat().st_size) for p in out.iterdir()],flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='voice':voice()
 elif mode=='shot':shot(int(sys.argv[2]))
 elif mode=='preview':
  for s in range(10):shot(s,True)
 elif mode=='assemble':assemble()
 else:raise ValueError(mode)
