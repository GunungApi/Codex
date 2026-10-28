"""P067. Original 3-D visual reconstruction of the fictional early history of Orwell.
Uses the established P064 voice/mesh infrastructure. No external pictures or music.
Official dates and broad events are distinguished from invented scenic geometry.
"""
from pathlib import Path
import os,sys,types,math,json,re,shutil,subprocess,zipfile,hashlib
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','3')
os.environ.setdefault('OMP_NUM_THREADS','3')
import numpy as np
from PIL import Image,ImageDraw
import soundfile as sf
from scipy.signal import butter,sosfilt
BASE=Path(__file__).with_name('p064_v2_film.py')
source=BASE.read_text().replace("Path('p064_v2')","Path('p067_v1')").replace('前史064','前史067').replace('脂肪酸膜の模式表現  ·  大きさと時間を圧縮','オリオン腕の世界設定  ·  景観・時間を再構成').replace('多層の脂肪酸膜を使った模型実験の模式化','オリオン腕の世界設定  ·  景観・時間を再構成')
b=types.ModuleType('p067_infrastructure');b.__file__=str(BASE);sys.modules[b.__name__]=b
exec(compile(source,str(BASE),'exec'),b.__dict__)
R=b.ROOT;W,H,FPS,SR=1080,1920,24,48000;PREFIX='heionreki_p067_v1'
TITLE='八十億年前、別の世界が生まれた'
PARTS=[
('太陽がまだない時代に、','Before our Sun existed,',0),
('この惑星の歴史は、始まっていた。','the history of another world had begun.',0),
('オリオン腕の世界、オーウェル。','Orwell, a world in the Orion\'s Arm setting.',1),
('誕生は、約八十億年前。','Its formation began about eight billion years ago.',1),
('太陽が生まれるのは、約四十六億年前。','Our Sun formed about 4.6 billion years ago.',2),
('およそ三十四億年も、先に始まった世界だ。','Orwell\'s story began about 3.4 billion years earlier.',2),
('若い大地を、隕石がたたく。','Impacts strike the young surface.',3),
('火山から、溶岩が噴き上がる。','Volcanoes erupt lava.',3),
('地下から出た気体が、空へ広がる。','Outgassed material spreads into the sky.',4),
('厚い二酸化炭素の大気ができていく。','A thick carbon-dioxide atmosphere develops.',4),
('長い時間をかけて、','Over a long span of time,',5),
('海が、世界を包んでいく。','a world-spanning ocean forms.',5),
('さっきまでの火山も、','The same volcanic landscape',6),
('今度は、海の向こうに見える。','is now seen across the sea.',6),
('空と、熱と、水。','Atmosphere, heat, and water.',7),
('別々に見てきた働きが、一つの歴史になる。','The processes we explored become one world\'s history.',7),
('地球へ続く時間の、ずっと手前で、','Long before Earth\'s story began,',8),
('この海には、この世界の時間が流れていた。','this ocean already had a history of its own.',8),
('次は、この海の中へ。','Next, we enter this ocean',9),
('オーウェルの、生命の始まりを訪ねよう。','to explore the beginnings of life on Orwell.',9)]
HEADINGS=['太陽より前に、始まった世界','惑星オーウェル','太陽より、約34億年早い','衝突する。噴き上がる。','地下の材料が、空になる','海が、世界を包んでいく','同じ火山を、海から見る','空・熱・水が、歴史になる','地球より古い、この海へ','次は、生命の始まりへ']
b.PARTS=PARTS;b.HEADINGS=HEADINGS;b.TITLE=TITLE
READING={'八十億年前':'はちじゅうおくねんまえ','四十六億年前':'よんじゅうろくおくねんまえ','三十四億年':'さんじゅうよんおくねん','隕石':'いんせき','溶岩':'ようがん','二酸化炭素':'にさんかたんそ','噴き上がる':'ふきあがる','オーウェル':'オーウェル'}
vsrc=source[source.index('def voice():'):source.index("VERT='''")]
vsrc=vsrc.replace("spoken=text.replace('尾は','おは').replace('二重に','にじゅうに')","spoken=text\n   for original,reading in READING.items():spoken=spoken.replace(original,reading)")
b.READING=READING;exec(compile(vsrc,'p067_voice','exec'),b.__dict__)
CAPTIONS={
PARTS[1][0]:['この惑星の歴史は、','始まっていた。'],PARTS[2][0]:['オリオン腕の世界、','オーウェル。'],PARTS[4][0]:['太陽が生まれるのは、','約四十六億年前。'],PARTS[5][0]:['およそ三十四億年も、','先に始まった世界だ。'],PARTS[8][0]:['地下から出た気体が、','空へ広がる。'],PARTS[9][0]:['厚い二酸化炭素の','大気ができていく。'],PARTS[13][0]:['今度は、','海の向こうに見える。'],PARTS[15][0]:['別々に見てきた働きが、','一つの歴史になる。'],PARTS[16][0]:['地球へ続く時間の、','ずっと手前で、'],PARTS[17][0]:['この海には、この世界の','時間が流れていた。'],PARTS[19][0]:['オーウェルの、','生命の始まりを訪ねよう。']}
oldwrap=b.Renderer.wrap
b.Renderer.wrap=lambda self,text,size,maxw: CAPTIONS.get(text) or oldwrap(self,text,size,maxw)
SOURCES=[{'id':'O1','title':'TSSL, Orwell, Geological Periods, Orion\'s Arm Universe Project','url':'https://www.orionsarm.com/eg-article/546a05829e265','use':'Official fictional formation interval about 8.0 to 7.3 billion years ago. The origin-of-life date is not precisely known.'},{'id':'O2','title':'TSSL, The Early Evolutionary History of Orwell, Orion\'s Arm Universe Project','url':'https://www.orionsarm.com/eg-article/54749a15e55ef','use':'The NovaTerran period: bombardment, intense volcanism, outgassing of a thick CO2 atmosphere, narrowly avoiding runaway greenhouse, and a world-spanning ocean.'},{'id':'S1','title':'NASA Science, Sun Facts, Formation','url':'https://science.nasa.gov/sun/facts/','use':'The Sun formed about 4.6 billion years ago. The 3.4-billion-year comparison is subtraction of rounded ages.'}]
# The same local coordinates and relief are used throughout the volcanic landscape.
def ground(x,z):
 x=np.asarray(x);z=np.asarray(z)
 d=(x+1.8)**2+(z+4.5)**2
 e=(x-5.5)**2+(z+12.)**2
 return -.85+4.9*np.exp(-d/12.5)-1.6*np.exp(-d/.55)+3.1*np.exp(-e/17.)-.8*np.exp(-e/.8)+.22*np.sin(x*.83+z*.27)*np.sin(z*.67)+.075*np.sin(3.1*x-2.4*z)
def globe_field(n):
 x,y,z=np.moveaxis(n,-1,0)
 h=.49+.16*np.sin(x*3.7+z*2.6)*np.cos(y*3.2)+.12*np.sin(y*6.3-z*2.1)*np.cos(x*5.4)+.065*np.sin(z*14.2+x*3.7)*np.cos(y*10.1)+.025*np.sin(x*38-y*21+z*13)
 for v in [[-.28,.38,.88],[.72,-.16,.68],[-.76,-.5,.42]]:
  v=np.array(v);v/=np.linalg.norm(v);d=1-(n*v).sum(axis=-1);h+=.22*np.exp(-d/.013)-.11*np.exp(-d/.0011)
 return np.clip(h,.06,.98)
def faces_grid(ny,nx):
 a=np.arange(ny)[:,None]*(nx+1)+np.arange(nx)[None,:];c=a+nx+1
 return np.stack([a,c,a+1,a+1,c,c+1],axis=-1).ravel().astype('i4')
def planet_mesh():
 la,lo=np.meshgrid(np.linspace(-np.pi/2,np.pi/2,121),np.linspace(-np.pi,np.pi,241),indexing='ij');n=np.stack([np.cos(la)*np.cos(lo),np.sin(la),np.cos(la)*np.sin(lo)],-1);p=n*(2.55+.12*globe_field(n))[...,None]
 du=np.gradient(p,axis=1);dv=np.gradient(p,axis=0);nn=np.cross(du,dv);nn/=np.maximum(np.linalg.norm(nn,axis=-1,keepdims=True),1e-8)
 sign=np.sign((nn*n).sum(-1));nn*=np.where(sign==0,1,sign)[...,None];nn[0]=n[0];nn[-1]=n[-1]
 return np.concatenate([p,nn],axis=-1).reshape(-1,6).astype('f4'),faces_grid(120,240)
def terrain_mesh(water=False):
 nx,nz=(144,168) if not water else (112,128)
 x,z=np.meshgrid(np.linspace(-18,18,nx+1),np.linspace(-25,16,nz+1));y=np.zeros_like(x) if water else ground(x,z)
 if water:nn=np.stack([y,y+1,y],-1)
 else:
  e=.02;dx=(ground(x+e,z)-ground(x-e,z))/(2*e);dz=(ground(x,z+e)-ground(x,z-e))/(2*e);nn=np.stack([-dx,np.ones_like(x),-dz],-1);nn/=np.linalg.norm(nn,axis=-1,keepdims=True)
 return np.concatenate([np.stack([x,y,z],-1),nn],-1).reshape(-1,6).astype('f4'),faces_grid(nz,nx)
VERT='''#version 330
in vec3 pos;in vec3 normal;in vec4 m0;in vec4 m1;in vec4 m2;in vec4 m3;in vec4 color;in vec4 mat;
uniform mat4 vp;uniform float t;out vec3 P;out vec3 N;out vec3 L;out vec4 C;out vec4 M;
void main(){vec3 q=pos;vec3 nn=normal;if(mat.x>5.5&&mat.x<6.5){float a=1.65*q.x+.52*q.z-t*1.7;float b=.72*q.x-1.4*q.z+t*1.1;q.y+=.075*sin(a)+.045*sin(b);nn=normalize(vec3(-.124*cos(a)-.0324*cos(b),1.,-.039*cos(a)+.063*cos(b)));}mat4 m=mat4(m0,m1,m2,m3);vec4 p=m*vec4(q,1);L=q;P=p.xyz;N=normalize(transpose(inverse(mat3(m)))*nn);C=color;M=mat;gl_Position=vp*p;}
'''
FRAG='''#version 330
in vec3 P;in vec3 N;in vec3 L;in vec4 C;in vec4 M;uniform vec3 eye;uniform float t;uniform sampler2D geology;uniform sampler2D cloudmap;uniform float sky;uniform float heat;uniform float gas;uniform float water;out vec4 frag;
vec2 spherical(vec3 p){p=normalize(p);return vec2(atan(p.z,p.x)/6.2831853+.5,asin(clamp(p.y,-1.,1.))/3.14159265+.5);}
float terrain(vec2 p){float d=dot(p-vec2(-1.8,-4.5),p-vec2(-1.8,-4.5));float e=dot(p-vec2(5.5,-12.),p-vec2(5.5,-12.));return -.85+4.9*exp(-d/12.5)-1.6*exp(-d/.55)+3.1*exp(-e/17.)-.8*exp(-e/.8)+.22*sin(p.x*.83+p.y*.27)*sin(p.y*.67)+.075*sin(3.1*p.x-2.4*p.y);}
void main(){vec3 n=normalize(N),v=normalize(eye-P),l=normalize(vec3(-.55,.82,.8));float dl=max(0.,dot(n,l));float rim=pow(1.-abs(dot(n,v)),3.);float spec=pow(max(0.,dot(reflect(-l,n),v)),mix(100.,12.,M.y));vec3 c=C.rgb*(.19+.94*dl)+vec3(.9,.84,.72)*spec*.28+C.rgb*M.z;float a=C.a;
if(M.x>.5&&M.x<1.5){float gr=texture(geology,P.xz*.041).b;float fine=.5+.5*sin(P.x*33.+P.z*28.+sin(P.y*13.));c=C.rgb*(.44+.75*gr+.10*fine)*(.22+.98*dl);c+=vec3(.025,.045,.062)*rim;}
if(M.x>2.5&&M.x<3.5){vec2 uv=spherical(L);uv.x+=t*.0027+M.z*.013;float f=texture(cloudmap,uv).r;float dens=smoothstep(.47-.16*gas,.78-.07*gas,f);a*=dens;c=mix(vec3(.22,.23,.25),vec3(.94,.85,.70),pow(dl,.7))*(.76+.24*f);}
if(M.x>3.5&&M.x<4.5){c=mix(vec3(.43,.23,.11),vec3(.30,.60,.72),water);c*=.35+.8*dl+rim*.5;a*=pow(1.-abs(dot(n,v)),2.4)*(.35+.65*dl);}
if(M.x>4.5&&M.x<5.5){vec3 g=texture(geology,spherical(L)).rgb;float crack=pow(1.-abs(sin(g.b*21.+g.r*9.)),18.);c=mix(vec3(.12,.105,.092),vec3(.34,.27,.21),g.r)*(.19+.94*dl);c+=vec3(2.3,.25,.012)*crack*heat*(.75+.25*sin(g.r*31.+t*.9));c+=vec3(.026,.038,.052)*rim;}
if(M.x>5.5&&M.x<7.5){vec3 nn=n;if(M.x>6.5){float w=sin(P.x*36.+t*1.1)*cos(P.z*29.-t*.9);nn=normalize(n+vec3(w,.0,-w)*.035);}float fres=pow(1.-max(0.,abs(dot(nn,v))),4.);float sp=pow(max(0.,dot(reflect(-l,nn),v)),150.);c=mix(vec3(.012,.075,.11),vec3(.17,.33,.38),fres)*(.62+.38*dl)+vec3(1.15,.87,.48)*sp*.9;if(M.x<6.5){float dep=P.y-terrain(P.xz);float foam=(1.-smoothstep(.025,.28,abs(dep)))*(.55+.45*sin(t*1.5+P.x*3.+P.z*2.));c=mix(c,vec3(.55,.67,.65),foam*.7);}}
if(M.x>9.5&&M.x<10.5){float edge=pow(max(0.,1.-abs(dot(n,v))),2.);a*=.16+.84*(1.-edge);c=C.rgb*(.30+.85*dl);c+=vec3(.15,.045,.005)*heat*max(0.,1.-L.y);}
if(sky>.5){float dist=length(eye-P);vec3 fog=sky>1.5?vec3(.015,.16,.20):mix(vec3(.30,.24,.21),vec3(.43,.42,.37),water);float f=1.-exp(-dist*(sky>1.5?.065:.022));c=mix(c,fog,min(.83,f));}
frag=vec4(c,a);}
'''
BG='''#version 330
in vec2 uv;out vec4 frag;uniform float t;uniform float sky;uniform float water;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){vec2 q=uv-vec2(.5,.56);vec3 c=vec3(.002,.004,.009)+vec3(.018,.024,.034)*exp(-dot(q,q)*4.);vec2 grid=uv*vec2(140.,249.);vec2 id=floor(grid);float star=step(.989,hash(id))*pow(max(0.,1.-length(fract(grid)-.5)*2.5),7.);c+=star*(.22+.15*sin(hash(id+3.)*80.+t*.12));if(sky>.5){float h=smoothstep(.16,1.,uv.y);c=mix(vec3(.49,.39,.29),vec3(.12,.21,.28),h);c=mix(c,mix(vec3(.49,.48,.42),vec3(.11,.25,.32),h),water);float glow=exp(-length((uv-vec2(.16,.76))*vec2(1.,.65))*6.);c+=vec3(.55,.30,.10)*glow*.32;if(sky>1.5){c=mix(vec3(.008,.055,.08),vec3(.035,.23,.29),uv.y);float rays=pow(.5+.5*sin(uv.x*24.+uv.y*9.+t*.4),9.);c+=vec3(.015,.055,.058)*rays*uv.y;}}frag=vec4(c,1.);}
'''
b.VERT=VERT;b.FRAG=FRAG;b.BG=BG
LAVA=np.array([1.,.25,.025]);ROCK=np.array([.25,.25,.24]);FOAM=np.array([.50,.72,.73]);GOLD=np.array([1.,.64,.18])
class Scene(b.Renderer):
 def __init__(self):
  super().__init__();self.mesh('planet',*planet_mesh());self.mesh('land',*terrain_mesh());self.mesh('watermesh',*terrain_mesh(True));self.mesh('shellfixed',*b.sphere_mesh(128,72))
  v,idx=b.sphere_mesh(18,12);v[:,:3]*=(1+.14*np.sin(v[:,0]*13+v[:,2]*9)*np.sin(v[:,1]*17))[:,None];self.mesh('stone',v,idx)
  la,lo=np.meshgrid(np.linspace(-np.pi/2,np.pi/2,512),np.linspace(-np.pi,np.pi,1024),indexing='ij');n=np.stack([np.cos(la)*np.cos(lo),np.sin(la),np.cos(la)*np.sin(lo)],-1);h=globe_field(n);x,y,z=np.moveaxis(n,-1,0);fine=np.clip(.5+.17*np.sin(x*41+z*23)*np.sin(y*31-z*17)+.12*np.cos(x*83-y*61),0,1)
  g=np.stack([h,np.clip(h*.7+fine*.3,0,1),fine],-1);self.geo=self.c.texture((1024,512),3,(np.clip(g,0,1)*255).astype('u1').tobytes());self.geo.build_mipmaps();self.geo.use(1);self.p['geology']=1
  cl=np.clip(.5+.22*np.sin(x*5.2+y*3.1)*np.sin(z*8.3-x*2.2)+.13*np.sin(y*13.7+z*4.3)*np.cos(x*15.1)+.065*np.sin(x*39-z*23+y*19),0,1)
  self.cloud=self.c.texture((1024,512),1,(cl*255).astype('u1').tobytes());self.cloud.build_mipmaps();self.cloud.use(2);self.p['cloudmap']=2
  b.dump(R/'review/geometry_summary.json',{'planet_vertices':121*241,'terrain_vertices':145*169,'ocean_vertices':113*129,'seed':6701,'global_ocean_fraction_at_final_level':float((h<.79).mean()),'cloud_method':'Three textured 3-D spherical shells in global shots; lit translucent 3-D lobes in local plumes. No claim of path-traced volumetric simulation.'})
 def reset(self):
  super().reset();self.sky=0.;self.heat=1.;self.gas=.2;self.water=0.;self.checked_spheres=[];self.terrain_check=False;self.immersion=False;self.frame_notes=[]
 def frame(self,t,scene,cue):
  self.geo.use(1);self.cloud.use(2)
  for key,val in [('sky',self.sky),('heat',self.heat),('gas',self.gas),('water',self.water)]:self.p[key]=float(val)
  self.bg['sky']=float(self.sky);self.bg['water']=float(self.water)
  return super().frame(t,scene,cue)
 def globe(self,t,sea=0,heat=1,gas=.3,center=(0,.60,0),scale=1.,rotation=.0,checked=True):
  self.water=sea;self.heat=heat;self.gas=gas;rr=b.rot(y=rotation)
  self.add('planet',center,scale,ROCK,rotation=rr,kind=5,rough=.8)
  if sea>.01:self.add('shellfixed',center,(2.548+.122*sea)*scale,[.02,.17,.25],rotation=rr,kind=7,rough=.07)
  for j in range(3):self.add('shellfixed',center,(2.71+j*.026)*scale,[.7,.7,.68],alpha=(.11+.12*gas)/(1+j*.20),rotation=rr,kind=3,rough=.8,emit=j)
  self.add('shellfixed',center,2.83*scale,[.4,.5,.6],alpha=.28+.35*gas,kind=4,rotation=rr)
  if checked:self.checked_spheres.append((np.array(center),2.83*scale,'Orwell'))
 def plume(self,t,intensity=1.,center=(-1.8,0,-4.5),kind='vapor'):
  center=np.array(center,float);base=float(ground(center[0],center[2]));center[1]=base+.10
  for j in range(25):
   a=(t*.30+j*.139)%1.;ang=j*2.399;p=center+np.array([.22*np.sin(ang)+a*a*1.1,3.7*a,.22*np.cos(ang)+.25*a]);rad=.20+.50*a
   self.add('sphere',p,[rad,rad*1.15,rad], [.39,.37,.33] if kind=='ash' else [.65,.64,.58],alpha=intensity*(.30-.18*a),kind=10,rough=.95)
 def terrain(self,t,sea=-1.4,eruption=.5,vapor=.3,water_visible=False):
  self.sky=1.;self.water=1. if water_visible else 0.;self.heat=eruption;self.terrain_check=True
  self.add('land',(0,0,0),1,ROCK,kind=1,rough=.9)
  if water_visible:self.add('watermesh',(0,sea,0),1,[.03,.18,.22],kind=6,rough=.05)
  for k in range(5):
   pts=[]
   for j in range(27):
    f=j/26;x=-1.8+(k-2)*.28+np.sin(f*6+k)*(.07+.30*f);z=-4.5+5.0*f;y=float(ground(x,z))+.04;pts.append(np.array([x,y,z]))
   for j,(a,c) in enumerate(zip(pts,pts[1:])):
    bright=.65+.35*np.sin(t*2.1-j*.5+k);self.bar(a,c,.045+.025*(j/26),LAVA,emit=eruption*(.8+bright),rough=.4)
  if eruption>.03:
   yy=float(ground(-1.8,-4.5))
   for j in range(24):
    a=(t*.58+j*.133)%1.;ang=j*2.399;rad=.11+1.0*a;p=[-1.8+rad*np.cos(ang),yy+.15+5.3*a*(1-a),-4.5+rad*np.sin(ang)]
    self.ball(p,.055+.025*(j%3),LAVA,alpha=eruption*(1-.45*a),emit=1.7,rough=.25)
  if vapor>.01:self.plume(t,vapor,kind='ash' if not water_visible else 'vapor')
  # Foreground rocks remain genuinely placed on the shared height field.
  for i in range(14):
   x=-8+(i%5)*3.5;z=3+(i//5)*3.1;y=float(ground(x,z));self.add('stone',[x,y+.14,z],[.45+.12*(i%3),.45+.1*(i%2),.50],ROCK*.68,rough=.9,kind=1)
 def ring(self,center,radius,color,alpha=1.,plane='horizontal'):
  p=np.array(center);pts=[]
  for a in np.linspace(0,2*np.pi,61):pts.append(p+radius*(np.array([np.cos(a),0,np.sin(a)]) if plane=='horizontal' else np.array([np.cos(a),np.sin(a),0])))
  for a,c in zip(pts,pts[1:]):self.bar(a,c,.022,color,alpha=alpha,emit=.45)

def keytime(tl,cue_index,token=None):
 c=tl['cues'][cue_index]
 if not token:return c['start']
 clean=lambda s:re.sub(r'[^ァ-ヺー]','',s)
 target=clean(token);m=c['moras'];joined=''.join(x['kana'] for x in m);i=joined.find(target)
 if i<0:return c['start']
 n=0
 for x in m:
  if n+len(x['kana'])>i:return c['audio_start']+x['start']
  n+=len(x['kana'])
 return c['start']

def arrange(r,s,u,t,tl):
 r.reset();a,d=tl['boundaries'][s:s+2];local=t-a;dur=d-a;second=tl['cues'][s*2+1]['start'];r.semantic={'scene':s,'u':float(u)}
 if s in [0,1,5]:
  r.eye=np.array([.9*np.sin(.25+u*.32),1.0,19.9-.5*b.ease(u)]);r.target=np.array([0,.60,0])
  sea=0. if s!=5 else .79*b.smooth(t,tl['cues'][10]['start'],tl['cues'][11]['end']+.05)
  gas=.17 if s==0 else (.40 if s==1 else .60);heat=1.15 if s==0 else (.70 if s==1 else .70*(1-sea))
  r.globe(t,sea,heat,gas,rotation=.40+t*.038)
  if s==0:
   # Two impacts are isolated local effects, never full-screen flashes.
   for j,at in enumerate([a+.9,second+.35]):
    q=(t-at)/1.2;p=np.array([1.1-.6*j,1.8-.6*j,1.80]);p=p/np.linalg.norm(p)*2.66+np.array([0,.6,0]);start=p+np.array([2.2,3.8,2.1])
    if -.55<q<0:
     pos=b.lerp(start,p,b.ease((q+.55)/.55));r.add('stone',pos,.10,ROCK,kind=1);r.bar(pos,pos+[.45,.8,.45],.045,LAVA,emit=1.4)
    if 0<=q<.9:r.ball(p,.12+.35*b.ease(q/.9),LAVA,emit=1.8,alpha=max(0,.7*(1-q/.9)));r.semantic['impact_phase']=float(q)
  if s==1:
   q=b.smooth(t,second-.08,second+.75);r.text('約80億年前',540,480,80,(250,210,150),int(255*q));r.semantic['date_reveal']=q
  if s==5:
   r.text('長い時間を圧縮',540,454,32,(211,226,234));r.semantic.update(ocean_level=float(sea),terrain_identity='Orwell globe v1',gas=gas)
 elif s==2:
  r.eye=np.array([0,.5,18.5]);r.target=np.array([0,.5,0]);q=b.smooth(t,a+.15,d-.12)
  # A timeline, not a spatial arrangement of a Sun that already existed.
  r.bar([-2.15,2.0,0],[2.15,2.0,0],.035,GOLD,emit=.35);r.bar([-2.15,-1.95,0],[2.15,-1.95,0],.035,[.45,.71,.87],emit=.2)
  r.bar([-2.0,1.85,0],[-2.0,1.85-3.65*q,0],.045,GOLD,emit=.5)
  for j in range(9):
   y=1.8-j*.44;r.bar([-2.12,y,0],[-1.90,y,0],.018,[.40,.53,.58],emit=.1)
  r.ball([-2.0,1.85-3.65*q,0],.12,GOLD,emit=1)
  r.text('オーウェルの形成',540,520,40,(239,224,201));r.text('約80億年前',540,606,68,(250,210,150))
  r.text('太陽の形成',540,1112,40,(216,230,237));r.text('約46億年前',540,1195,68,(174,215,236))
  reveal=b.smooth(t,second-.05,second+.8);r.text('約34億年の差',580,875,68,(242,247,248),int(255*reveal));r.text('年代の比較',540,1350,30,(181,202,214));r.semantic.update(timeline_progress=q,difference_reveal=reveal)
 elif s==3:
  r.eye=np.array([6.4-1.8*b.ease(u),5.0,11.7-1.3*b.ease(u)]);r.target=np.array([-1.25,1.4,-4.1]);erupt=.18+.82*b.smooth(t,second-.06,second+1.0);r.terrain(t,eruption=erupt,vapor=.50)
  impact=keytime(tl,6,'インセキ')+.65;q=t-impact;cx,cz=2.4,-.8;cy=float(ground(cx,cz))
  if -1.<q<0:
   f=b.ease(q+1.);p=b.lerp([5,9,1.6],[cx,cy+.1,cz],f);r.add('stone',p,.18,ROCK,kind=1);r.bar(p,p+np.array([.75,1.5,.55]),.07,LAVA,emit=2)
  if 0<=q<2.:
   r.ring([cx,cy+.07,cz],.15+1.8*b.ease(q/2),LAVA,alpha=(1-q/2)*.9)
   for j in range(12):
    ang=j*2.4;rr=.2+.6*q;pos=[cx+rr*np.cos(ang),cy+.3+q*.6,cz+rr*np.sin(ang)];r.add('sphere',pos,[.25+.18*q]*3,[.39,.34,.27],alpha=.25*(1-q/2),kind=10)
  r.semantic.update(eruption=erupt,impact_elapsed=q)
 elif s==4:
  r.eye=np.array([3.8-1.1*u,5.8+1.0*u,8.8]);r.target=np.array([-1.5,2.7,-4.5]);q=b.smooth(t,a,d-.1);r.terrain(t,eruption=.65,vapor=.28+.70*q)
  for j in range(18):
   f=(t*.17+j*.173)%1.;x=-2.5+6*f;z=-8-(j%4)*2.2;y=6.1+(j//4)*.36;r.add('sphere',[x,y,z],[1.0,.44,.70],[.62,.59,.52],alpha=(.045+.09*q),kind=10,rough=.95)
  r.text('二酸化炭素を多く含む空',540,1330,38,(236,219,189),int(255*b.smooth(t,second,second+.5)));r.semantic.update(outgassing=q,cloud_coverage=.28+.70*q)
 elif s in [6,7,8]:
  r.eye=np.array([6.8-2.4*b.ease(u),4.25+.4*np.sin(u*np.pi),12.6-2.0*b.ease(u)]);r.target=np.array([-1.2,1.9,-5.2]);r.terrain(t,sea=1.35,eruption=.12 if s!=7 else .55,vapor=.50,water_visible=True)
  if s==6:r.text('同じ火口・同じ尾根',540,1320,38,(207,229,236))
  if s==7:
   # Three named processes receive separate visual emphasis tied to their words.
   c=tl['cues'][14];ph=[keytime(tl,14,'ソラ'),keytime(tl,14,'ネツ'),keytime(tl,14,'ミズ')]
   for j,(txt,xx,col) in enumerate([('空',300,(224,224,214)),('熱',540,(255,182,99)),('水',780,(126,220,239))]):
    alpha=b.smooth(t,ph[j]-.05,ph[j]+.25);r.text(txt,xx,1278,60,col,int(255*alpha))
   for j in range(8):
    f=(t*.36+j*.17)%1.;r.ball([-1.8+.2*np.sin(j),4.4+f*1.8,-4.5],.05,[.94,.62,.22],alpha=.25,emit=.7)
   r.semantic['processes_revealed']=[t>=x for x in ph]
  if s==8:
   r.eye=np.array([8.6-1.6*u,3.3,11.7-1.4*u]);r.target=np.array([-1.3,1.9,-5.8]);r.text('太陽系の誕生より前',540,1320,37,(207,231,239))
  r.semantic.update(water_level=1.35,wave_phase=t*1.7,plume_phase=t*.3,terrain_identity='Orwell local v1')
 else:
  q=b.smooth(t,a+.2,d-.55);r.eye=np.array([5.8-1.2*q,3.4-2.75*q,9.5-3.6*q]);r.target=np.array([-1.2,.6,-5.4]);r.terrain(t,sea=1.35,eruption=.05,vapor=.22,water_visible=True)
  r.immersion=True;r.sky=2. if r.eye[1]<1.40 else 1.;r.water=1.
  if r.sky>1.5:
   for j in range(18):
    f=(t*.38+j*.173)%1.;x=3.8+.28*np.sin(j*2.4);z=3.2+.5*np.cos(j*2.4);y=-.3+1.55*f;r.ball([x,y,z],.045+.035*(j%3),[.23,.53,.58],alpha=.40,rough=.12)
  r.semantic.update(immersion=q,camera_crosses_water_intentionally=True)
 r.semantic.update(camera=r.eye.tolist(),heat=r.heat,water=r.water,gas=r.gas)

def check_frame(r,scene):
 issues=[];min_camera=None;bounds=[]
 if r.terrain_check:
  min_camera=float(r.eye[1]-ground(r.eye[0],r.eye[2]));
  if min_camera<.45:issues.append('camera_ground_intersection')
 # No star is present beside Orwell; dates are a separate, explicitly labelled timeline.
 for c,rad,tag in r.checked_spheres:
  forward=b.unit(r.target-r.eye);right=b.unit(np.cross(forward,[0,1,0]));up=np.cross(right,forward);delta=c-r.eye;depth=float(np.dot(delta,forward));k=H/2/np.tan(np.deg2rad(37)/2)
  xx=W/2+k*np.dot(delta,right)/depth;yy=H/2-k*np.dot(delta,up)/depth;rr=k*rad/max(.1,depth-rad*.10)
  bb=[float(xx-rr),float(yy-rr),float(xx+rr),float(yy+rr)];bounds.append({'name':tag,'bounds':bb})
  if bb[0]<35 or bb[2]>1045 or bb[1]<370 or bb[3]>1450:issues.append('planet_safe_area')
 for text,x,y,size,col,alpha in r.labels:
  if alpha<20:continue
  width=r.fontobj(size).getlength(text)
  if x-width/2<48 or x+width/2>1032 or y-size*.6<375 or y+size*.6>1430:issues.append('label_safe_area:'+text)
 return {'issues':issues,'camera_ground_clearance':min_camera,'main_object_bounds':bounds}

def do_voice():
 tl,narr=b.voice();b.dump(R/'docs/sources.json',SOURCES)
 clean=lambda x:re.sub(r'[^ァ-ヺー]','',x)
 expected={'八十億年前':['ハチジュウオクネンマエ'],'四十六億年前':['ヨンジュウロクオクネンマエ'],'三十四億年':['サンジュウヨンオクネン'],'隕石':['インセキ'],'溶岩':['ヨオガン','ヨウガン'],'二酸化炭素':['ニサンカタンソ'],'オーウェル':['オーウェル','オオウェル']};checks=[]
 for word,variants in expected.items():
  got=[clean(c['kana']) for c in tl['cues'] if word in c['text']];ok=any(v in z for v in variants for z in got);checks.append({'word':word,'accepted_phonetic_spellings':variants,'readings':got,'query_reading_checked':ok})
 b.dump(R/'review/key_readings.json',checks);print('READING_CHECK',json.dumps(checks,ensure_ascii=False),flush=True)
 music(tl,narr);print('TIMELINE',tl['duration'],tl['max_query_speech_gap'],flush=True)

def music(tl,narr):
 T=tl['duration'];n=len(narr);tt=np.arange(n)/SR;bg=np.zeros((n,2),np.float32);rng=np.random.default_rng(6701)
 chords=[[110,164.814,220,293.665],[98,146.832,196,261.626],[130.813,195.998,261.626,329.628],[146.832,220,293.665,391.995]]
 for ci,notes in enumerate(chords):
  a=ci*T/4;d=(ci+1)*T/4;env=np.clip((tt-a)/.7,0,1)*np.clip((d+.7-tt)/1.,0,1)
  for j,f in enumerate(notes):
   tone=(np.sin(2*np.pi*f*tt)+.18*np.sin(2*np.pi*f*2.003*tt)+.08*np.sin(2*np.pi*f*3*tt))*env*.007;bg[:,j%2]+=tone;bg[:,1-j%2]+=tone*.68
 for beat,st in enumerate(np.arange(.2,T,.44)):
  a=round(st*SR);ln=min(round(.32*SR),n-a);x=np.arange(ln)/SR;f=chords[min(3,int(st/(T/4)))][beat%4]*2;env=np.exp(-x*12)*(1-np.exp(-x*100));v=np.sin(2*np.pi*f*x)*env*.018;bg[a:a+ln,beat%2]+=v;bg[a:a+ln,1-beat%2]+=v*.52
  if beat%4==0:bg[a:a+ln]+=((np.sin(2*np.pi*(58*x+23*x*x)))*np.exp(-x*13)*.048)[:,None]
 events=[]
 for s in range(10):
  st=tl['cues'][s*2+1]['start']+.04;at=round(st*SR);ln=min(round(.85*SR),n-at);x=np.arange(ln)/SR;noise=sosfilt(butter(2,[180,3200],btype='bandpass',fs=SR,output='sos'),rng.normal(0,1,ln));env=np.sin(np.pi*np.minimum(1,x/.85))**2
  effect=noise*env*(.055 if s in [3,4,6] else .027)+np.sin(2*np.pi*(63*x+19*x*x))*np.exp(-x*8)*.07;bg[at:at+ln]+=effect[:,None];events.append({'scene':s,'time':st,'event':'eruption, gas release, ocean reveal or epoch transition; designed sound'})
 gain=np.ones(n,np.float32)
 for c in tl['cues']:gain[max(0,round((c['start']-.10)*SR)):min(n,round((c['end']+.12)*SR))]=.35
 coarse=np.convolve(gain[::480],np.ones(7)/7,mode='same');gain=np.interp(np.arange(n),np.arange(len(coarse))*480,coarse).astype('f4');bg*=gain[:,None];bg*=(np.clip(tt/.2,0,1)*np.clip((T-tt)/.34,0,1))[:,None]
 sf.write(R/'audio/music_and_effects.wav',bg,SR,subtype='PCM_24');sf.write(R/'audio/mix_premaster.wav',bg+narr[:,None],SR,subtype='PCM_24');b.dump(R/'audio/sound_events.json',events)
 out=subprocess.run(['ffmpeg','-v','info','-i',str(R/'audio/mix_premaster.wav'),'-af','loudnorm=I=-16:TP=-2:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);m=json.loads(out.stderr[out.stderr.rfind('{'):out.stderr.rfind('}')+1]);b.dump(R/'audio/loudness_first_pass.json',m)
 filt='loudnorm=I=-16:TP=-2:LRA=9:linear=true:measured_I={input_i}:measured_LRA={input_lra}:measured_TP={input_tp}:measured_thresh={input_thresh}:offset={target_offset}'.format(**m)
 b.run(['ffmpeg','-y','-v','error','-i',str(R/'audio/mix_premaster.wav'),'-af',filt,'-ar','48000','-c:a','pcm_s24le',str(R/'audio/master.wav')])

def shot(s,preview=False):
 tl=json.loads((R/'timeline.json').read_text());r=Scene();start=round(tl['boundaries'][s]*FPS);end=round(tl['boundaries'][s+1]*FPS);states=[];old=None
 selected=sorted(set(start+round((end-start-1)*f) for f in [.08,.30,.58,.91]));indices=selected if preview else range(start,end)
 log=(R/'review'/f'ffmpeg_{s:02}.log').open('w');pipe=None
 if not preview:pipe=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','3',str(R/'render'/f'shot_{s:02}.mp4')],stdin=subprocess.PIPE,stderr=log)
 try:
  for f in indices:
   t=f/FPS;u=float(np.clip((t-tl['boundaries'][s])/(tl['boundaries'][s+1]-tl['boundaries'][s]),0,1));cue=next((c for c in tl['cues'] if c['start']-.07<=t<=c['end']+.16),None)
   arrange(r,s,u,t,tl);im,raw=r.frame(t,s,cue);qa=check_frame(r,s);tiny=np.asarray(raw.crop((45,405,1035,1435)).resize((198,206)),dtype=np.int16);diff=float(np.mean(np.abs(tiny-old))) if old is not None else 0.;old=tiny
   states.append({'frame':f,'scene':s,'raw_subject_delta':diff,**qa,'semantic':r.semantic})
   if pipe:pipe.stdin.write(im.tobytes())
   if f in selected:im.save(R/'review'/f'p067_scene_{s:02}_{f:04}.jpg',quality=94)
   if not preview and (f-start)%48==0:print('SHOT',s,'FRAME',f-start,'OF',end-start,'ISSUES',qa['issues'],flush=True)
  if pipe:pipe.stdin.close();assert pipe.wait()==0
 finally:log.close()
 b.dump(R/'review'/f'{"preview" if preview else "states"}_{s:02}.json',states)
 print('SCENE_CHECK',s,'sampled_frames',len(states),'issues',sum(bool(x['issues']) for x in states),flush=True)
 if any(x['issues'] for x in states):raise AssertionError([(x['frame'],x['issues']) for x in states if x['issues']][:8])

def assemble():
 tl=json.loads((R/'timeline.json').read_text());d=R/'deliverables';rr=Scene();b.subtitles(tl,rr)
 for suffix in ['ja.srt','ja.ass','en.srt']:(d/('heionreki_p064_v2_'+suffix)).rename(d/(PREFIX+'_'+suffix))
 listing=R/'render/concat.txt';listing.write_text(''.join("file '"+str((R/'render'/f'shot_{i:02}.mp4').resolve())+"'\n" for i in range(10)))
 picture=R/'render/full_picture.mp4';b.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(picture)])
 high=d/(PREFIX+'_high_1080x1920.mp4');light=d/(PREFIX+'_light_720x1280.mp4')
 b.run(['ffmpeg','-y','-v','error','-i',str(picture),'-i',str(R/'audio/master.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(tl['duration']),'-movflags','+faststart',str(high)])
 b.run(['ffmpeg','-y','-v','error','-i',str(high),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','fast','-crf','24','-threads','3','-c:a','copy','-movflags','+faststart',str(light)])
 probes={};hashes=[]
 for p in [high,light]:
  b.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-']);probe=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-show_format','-of','json',str(p)]));probes[p.name]=probe
  vs=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(vs['nb_frames'])==round(tl['duration']*FPS);audio=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','adts','-']);hashes.append(hashlib.sha256(audio).hexdigest())
 assert hashes[0]==hashes[1]
 out=subprocess.run(['ffmpeg','-v','info','-i',str(high),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);lm=json.loads(out.stderr[out.stderr.rfind('{'):out.stderr.rfind('}')+1])
 states=[]
 for i in range(10):states+=json.loads((R/'review'/f'states_{i:02}.json').read_text())
 assert len(states)==round(tl['duration']*FPS);bad=[{'frame':x['frame'],'issues':x['issues']} for x in states if x['issues']];assert not bad,bad[:5]
 vals=np.array([s['raw_subject_delta'] for s in states]);win=np.convolve(vals,np.ones(48)/48,mode='valid');clear=[x['camera_ground_clearance'] for x in states if x['camera_ground_clearance'] is not None]
 qa={'duration':tl['duration'],'frames':len(states),'native_resolution':[1080,1920],'fps':24,'audio_sample_rate':48000,'max_query_speech_gap':tl['max_query_speech_gap'],'geometry_issues':bad,'minimum_camera_ground_clearance_world_units':min(clear),'minimum_two_second_mean_raw_picture_difference':float(win.min()),'weak_windows':[int(i) for i,v in enumerate(win) if v<.015],'loudness':lm,'audio_payload_identical':True,'caption_count':len(tl['cues']),'visual_inspection':False,'human_continuous_viewing':False,'auditory_listening':False,'limitations':'Geometry checks cover camera/ground, the global planet and text safe areas. Eruptions, coasts, cloud layers and meteor contacts intentionally overlap. Pixel change includes scene motion and camera movement and is not a perceptual excitement score.'}
 b.dump(R/'review/verification.json',qa);b.dump(R/'review/media.json',probes);b.dump(R/'review/loudness.json',lm)
 for k,c in enumerate(tl['cues']):
  at=(c['start']+c['end'])/2;b.run(['ffmpeg','-y','-v','error','-ss',str(at),'-i',str(high),'-frames:v','1','-q:v','2',str(R/'review'/f'final_caption_{k+1:02}.jpg')])
 images=sorted((R/'review').glob('p067_scene_*.jpg'));sheet=Image.new('RGB',(1080,1920),(3,13,21))
 for i,p in enumerate(images[:40]):sheet.paste(Image.open(p).resize((135,240)),((i%8)*135,(i//8)*240))
 sheet.save(R/'review/contact_sheet.jpg',quality=94)
 notes='平穏暦全史・前史067 第1版\n'+TITLE+'\n制作日・資料確認日：2026-10-28\n\n'
 notes+=f"仕様：{tl['duration']:.3f}秒、1080×1920の直接描画、24fps、{len(states)}コマ。声・音楽・効果音・日本語字幕20区間。軽量版720×1280。\n\n台本：\n"+'\n'.join(x[0] for x in PARTS)
 notes+='\n\n公式設定と独自の景観再構成：\nオリオン腕は共同制作のSF世界。本作のオーウェルはその公式設定を紹介する。現実に観測された惑星ではない。形成期は約80億〜73億年前の区分。太陽形成約46億年前との差約34億年は丸めた値の引き算。精密な暦換算ではない。公式の後世から見た年齢と現代の観測基準の約1万年程度の差は、本作の億年単位の丸めに含む。\n初期の激しい衝突、火山活動、厚い二酸化炭素大気、全球的な海は原典に記載される。原典は暴走温室状態をかろうじて避けたとも記す。本作の気体の広がりから海への編集は数億年規模の変化の圧縮であり、二酸化炭素が増えるほど冷えるという因果説明にはしない。\n具体的な地形、火口の数・形・位置、衝突天体の軌道、溶岩流、波、雲の形・色は制作室による独自の景観再構成。公式の古地図・測定値・現在の地理の復元ではない。数値の気圧、特定の山脈名、新しい公式事件は設定しない。\n地形は実際の高さを持つ三角形メッシュ。海面も独立した変形メッシュで、同一の地形の低地を覆う。全球は高さのある球面メッシュと海面球を分離。大気は球面層、雲は濃度を持つ三層の球面と照明付きの立体ローブを使った近似。物理流体計算や完全な体積経路追跡を行った映像ではない。\n地表の裸の岩と火山、空、海を追う。植物、動物、都市、完成した微生物を先取りして置かない。最終の潜水は次回へ入る視点移動であり、ここで生命が見つかったとは示さない。\n字幕の読みやすさを保つため、上部に章案内、下部に語り字幕を配置。光の演出は局所的に限定し、全面の高速点滅は使わない。\n\n出典：\n'+'\n\n'.join(x['id']+' '+x['title']+'\n'+x['url']+'\n'+x['use'] for x in SOURCES)
 notes+='\n\n素材と権利の記録：\n公式記事の文章・画像・地図の転載なし。要点を独自の短い日本語解説とオリジナルの立体景観で紹介。設定の著者TSSLおよびOrion\'s Arm Universe Projectへ出典を付す。公式が本動画を承認・制作したという表記はしない。公開・投稿操作は本制作では行わない。\n音声：VOICEVOX 四国めたん・ノーマル（エンジン0.25.2／コア0.16.1／速度1.03）。原音・合成クエリ・拍時刻を保存。八十億年前、四十六億年前、三十四億年、隕石、溶岩、二酸化炭素の読みを指定して合成読みを照合。耳による試聴は未実施。\n音楽・効果音は独自の数式合成。フォントは環境のNoto Sans CJK JP。フォントファイルと音声モデルは配布物に含めない。\n\n検証：\n'+json.dumps(qa,ensure_ascii=False,indent=2)
 notes+='\n\n再編集：作業フォルダp067_v1に制作一式を展開し、source/p067_film.py shot 0〜9、assembleの順。映像だけの再制作では原音を維持。voiceは音声を作り直す場合のみ。ffmpeg、numpy、scipy、Pillow、soundfile、moderngl 5.12.0、glcontext 3.0.0、EGL、Noto Sans CJK JPが必要。\n'
 (d/(PREFIX+'_script_and_sources.txt')).write_text(notes,encoding='utf-8');shutil.copy(__file__,R/'source/p067_film.py');shutil.copy(BASE,R/'source/p064_v2_film.py');b.dump(R/'docs/sources.json',SOURCES)
 (R/'source/README.txt').write_text('作業場所の直下にp067_v1を置く。\npython source/p067_film.py shot 0\n各場面0〜9を描画後 python source/p067_film.py assemble\n音声・時間軸は同梱。フォントと音声モデルは別途取得。\n',encoding='utf-8')
 manifest=[]
 for p in sorted(R.rglob('*')):
  if p.is_file() and p.suffix not in ['.ttf','.otf','.ttc','.zip'] and 'voice_data' not in p.parts:manifest.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 b.dump(R/'review/manifest.json',manifest)
 archive=d/(PREFIX+'_production.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in R.rglob('*'):
   if p.is_file() and p!=archive and p.suffix not in ['.ttf','.otf','.ttc'] and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(R)))
 print('FINAL_VERIFICATION',json.dumps(qa,ensure_ascii=False),flush=True);print('DELIVERABLES',json.dumps([{'name':p.name,'bytes':p.stat().st_size} for p in d.iterdir()],ensure_ascii=False),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='voice':do_voice()
 elif mode=='preview':
  for i in range(10):shot(i,True)
 elif mode=='shot':shot(int(sys.argv[2]))
 elif mode=='assemble':assemble()
 else:raise ValueError(mode)
