"""Native 1080x1920 P068 underwater cinematography.
Original cell reconstructions, mineral scenery, procedural materials and lighting.
Cells are illustrative, not measured Orwell organisms; no nuclei or chloroplasts.
Scene events are tied to the final speech timeline. Never use image-plane zoom as 3D.
"""
from pathlib import Path
import os,sys,math,json,subprocess,hashlib,shutil,zipfile
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1');os.environ.setdefault('LP_NUM_THREADS','3');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
import moderngl
ROOT=Path('p068_v1').resolve();W,H,FPS=1080,1920,24
for d in ['render','review','source','deliverables','assets','docs']:(ROOT/d).mkdir(parents=True,exist_ok=True)
FONT=os.environ.get('P068_FONT','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def unit(x):x=np.asarray(x,float);return x/max(1e-12,np.linalg.norm(x))
def mix(a,b,q):return np.asarray(a)*(1-q)+np.asarray(b)*q
def ease(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def ramp(t,a,b):return float(ease((t-a)/max(1e-6,b-a)))
def rot(x=0,y=0,z=0):
 cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def matrix(pos=(0,0,0),scale=1,angles=(0,0,0)):
 m=np.eye(4);m[:3,:3]=rot(*angles)@np.diag(np.broadcast_to(scale,(3,)));m[:3,3]=pos;return m

def perspective(fov=42):
 f=1/math.tan(math.radians(fov)/2);n=.08;z=150.;return np.array([[f/(W/H),0,0,0],[0,f,0,0],[0,0,(z+n)/(n-z),2*z*n/(n-z)],[0,0,-1,0]])
def look(eye,target):
 e=np.asarray(eye);f=unit(np.asarray(target)-e);s=unit(np.cross(f,[0,1,0]));u=np.cross(s,f);m=np.eye(4);m[:3,:3]=[s,u,-f];m[:3,3]=-m[:3,:3]@e;return m

def grid(ny,nx):
 a=np.arange(ny)[:,None]*(nx+1)+np.arange(nx)[None,:];b=a+nx+1;return np.stack([a,b,a+1,a+1,b,b+1],-1).reshape(-1).astype('i4')
def normals(p):
 n=np.cross(np.gradient(p,axis=1),np.gradient(p,axis=0));n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-9);return n

def sphere(ny=48,nx=72,kind='cell'):
 la,lo=np.meshgrid(np.linspace(-np.pi/2,np.pi/2,ny+1),np.linspace(-np.pi,np.pi,nx+1),indexing='ij')
 n=np.stack([np.cos(la)*np.cos(lo),np.sin(la),np.cos(la)*np.sin(lo)],-1)
 if kind=='cell':
  rough=.027*np.sin(lo*9+np.sin(la*7))*np.cos(la)**2+.011*np.sin(la*31+lo*4)*np.cos(la)
  p=n*(1+rough)[...,None];p[...,1]*=1.42;p[...,0]+=.06*np.sin(la*3)*np.cos(la)
 elif kind=='rock':
  rough=.16*np.sin(lo*3+la*5)+.08*np.cos(lo*7-la*4)+.04*np.sin(lo*17+la*21)
  p=n*(1+rough)[...,None];p[...,1]*=.72
 else:p=n.copy()
 nn=normals(p);sg=np.sum(nn*n,-1);nn*=np.where(sg<0,-1,1)[...,None];nn[0]=n[0];nn[-1]=n[-1]
 return np.concatenate([p,nn,n],-1).reshape(-1,9).astype('f4'),grid(ny,nx)

def floor(x,z):
 x,z=np.asarray(x),np.asarray(z)
 broad=-3.6+.22*np.sin(x*.43+z*.12)*np.cos(z*.31)+.13*np.sin(x*1.2+z*.7)*np.cos(z*1.4)
 ridges=1.8*np.exp(-((np.abs(x)-7)/2.1)**2)*(1+.18*np.sin(z*.27))
 detail=.07*np.sin(x*4.1+z*3.2)*np.sin(z*3.7-x*2.3)
 return broad+ridges+detail

def groundmesh():
 nx,nz=224,256;x,z=np.meshgrid(np.linspace(-35,35,nx+1),np.linspace(-65,26,nz+1));y=floor(x,z);e=.025
 n=np.stack([-(floor(x+e,z)-floor(x-e,z))/(2*e),np.ones_like(x),-(floor(x,z+e)-floor(x,z-e))/(2*e)],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
 p=np.stack([x,y,z],-1);return np.concatenate([p,n,p],-1).reshape(-1,9).astype('f4'),grid(nz,nx)

def tube(points,r=.028,sides=10):
 ps=np.array(points);vs=[];ix=[]
 for j,p in enumerate(ps):
  tangent=unit(ps[min(j+1,len(ps)-1)]-ps[max(j-1,0)]);right=unit(np.cross(tangent,[0,1,0]));up=unit(np.cross(right,tangent))
  if np.linalg.norm(right)<.1:right=np.array([1,0,0]);up=unit(np.cross(right,tangent))
  for k in range(sides+1):
   a=k/sides*2*np.pi;n=np.cos(a)*right+np.sin(a)*up;vs.append([*(p+r*n),*n,0,j/max(len(ps)-1,1),0])
 for j in range(len(ps)-1):
  for k in range(sides):a=j*(sides+1)+k;b=a+sides+1;ix.extend([a,b,a+1,a+1,b,b+1])
 return np.array(vs,'f4'),np.array(ix,'i4')

VERT='''#version 330
in vec3 pos;in vec3 normal;in vec3 local;uniform mat4 vp;uniform mat4 model;uniform float time;uniform int kind;
out vec3 P;out vec3 N;out vec3 L;
void main(){vec3 q=pos;if(kind==1){q*=1.+.008*sin(time*1.4+pos.y*5.);}vec4 w=model*vec4(q,1);P=w.xyz;N=normalize(transpose(inverse(mat3(model)))*normal);L=local;gl_Position=vp*w;}
'''
FRAG='''#version 330
in vec3 P;in vec3 N;in vec3 L;out vec4 frag;
uniform vec3 eye;uniform vec3 tint;uniform sampler2D detail;uniform sampler2D backplate;uniform float time;uniform float heat;uniform float reveal;uniform float energy;uniform float cut;uniform int kind;
float tex(vec3 p,float s){return (texture(detail,p.xy*s).r+texture(detail,p.zy*s).g+texture(detail,p.xz*s).b)/3.;}
vec3 fog(vec3 col){float d=length(eye-P);vec3 absorb=exp(-d*vec3(.042,.015,.009));vec3 water=vec3(.006,.045,.058);return col*absorb+water*(1.-absorb);}
void main(){vec3 n=normalize(N),v=normalize(eye-P);if(!gl_FrontFacing)n=-n;vec3 key=normalize(vec3(-.55,.9,.6)),fill=normalize(vec3(.6,.15,-.65));float nv=max(.001,dot(n,v));float rim=pow(1.-nv,3.);vec3 col=vec3(0);float rough=.52;
 if(kind==0){
  float q=tex(P,.29),fine=tex(P,1.7);vec3 weights=pow(abs(n),vec3(5));weights/=max(.001,weights.x+weights.y+weights.z);
  vec3 a=texture(detail,P.zy*.41).rgb,b=texture(detail,P.xz*.41).rgb,c=texture(detail,P.xy*.41).rgb;vec3 ds=(a*weights.x+b*weights.y+c*weights.z)-.5;
  n=normalize(n+vec3(ds.g,ds.b,ds.r)*.29);float crack=pow(1.-abs(sin(q*19.+P.y*.7)),16.);
  vec3 base=mix(vec3(.055,.075,.079),vec3(.21,.24,.205),q)*(.73+.3*fine)*(1.-crack*.35);
  float strata=.5+.5*sin(P.y*12.+q*4.);base*=.86+.14*strata;
  float nd=max(0.,dot(n,key));col=base*(vec3(.10,.28,.32)+vec3(.6,.88,.77)*nd);
  float caustic=pow(max(0.,sin(P.x*2.2+time*.72+sin(P.z*1.2))*sin(P.z*2.0-time*.6+sin(P.x*.8))),9.);
  col+=vec3(.07,.19,.18)*caustic*max(.05,n.y);
  float warm=exp(-length(P.xz-vec2(1,-5))*.32)*heat;
  col+=vec3(.20,.062,.008)*warm*(.3+.7*crack);
 }else if(kind==1){
  if(cut>0.01&&L.z>mix(1.,-.12,cut)&&L.x>.12)discard;
  float q=tex(L*3.1,.8),fine=tex(L*11.,1.3);
  n=normalize(n+vec3(sin(L.y*88.+q*3.),sin(L.z*74.+q),cos(L.x*91.+q))* .045);
  float nd=max(0.,dot(n,key));float through=pow(max(0.,dot(-n,key)),1.7);float sp=pow(max(0.,dot(n,normalize(key+v))),78.);
  vec2 uv=gl_FragCoord.xy/vec2(1080,1920);vec3 behind=texture(backplate,clamp(uv+n.xy*.009*(1.-rim),vec2(.001),vec2(.999))).rgb;
  vec3 wall=tint*(.48+.50*q);col=mix(behind,wall,.46+.27*rim);
  col*=.6+.9*nd;col+=tint*through*.44+vec3(.22,.56,.51)*rim;
  col+=vec3(.82,1.02,.86)*sp*.56;
  float pores=pow(max(0.,sin(L.x*92.+q*4)*sin(L.y*101.+q*2)*sin(L.z*95.)),8.);
  col+=tint*(pores*.20+fine*.065);
  float flow=pow(max(0.,cos(L.y*5.8-time*3.1)),8.);
  col+=vec3(.15,.40,.24)*flow*energy*(.25+.75*rim);
  if(!gl_FrontFacing)col*=.55;
 }else if(kind==2){
  float q=tex(L*2.,1.0);float nd=max(0.,dot(n,key));float sp=pow(max(0.,dot(n,normalize(key+v))),48.);
  col=tint*(.45+.65*nd+.22*q)+vec3(.6,.6,.4)*sp*.35;
 }else if(kind==3){
  float wave=.5+.5*sin(L.y*42.-time*4.);col=tint*(.48+.4*wave+energy*.5);
  if(L.y>reveal)discard;
 }else{col=tint;}
 col=fog(col);frag=vec4(col,1.);}
'''
QVERT='''#version 330
in vec2 p;out vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0,1);}
'''
BG='''#version 330
in vec2 uv;out vec4 frag;uniform float time;uniform float heat;uniform vec3 eye;
void main(){vec2 p=uv;float y=p.y;vec3 c=mix(vec3(.002,.013,.021),vec3(.018,.135,.157),pow(y,1.4));
 float rays=0.;for(int i=0;i<5;i++){float x=.10+float(i)*.21+.12*(1.-y)+.026*sin(time*.26+float(i));float d=(p.x-x)/(.014+.055*(1.-y));rays+=exp(-d*d)*(.3+.7*y);}
 c+=vec3(.035,.095,.094)*rays*.35;
 c+=vec3(.06,.017,.001)*heat*exp(-length((p-vec2(.68,.20))*vec2(2,1))*3.);
 frag=vec4(c,1);}
'''
PV='''#version 330
in vec3 pos;in vec4 color;uniform mat4 vp;uniform vec3 eye;out vec4 C;void main(){vec4 q=vp*vec4(pos,1);gl_Position=q;gl_PointSize=clamp(color.a*210./max(.3,q.w),1.,20.);float fog=exp(-length(eye-pos)*.026);C=vec4(color.rgb*fog,.7*fog);}
'''
PF='''#version 330
in vec4 C;out vec4 frag;void main(){vec2 q=gl_PointCoord-.5;float d=dot(q,q)*4.;if(d>1.)discard;float a=pow(1.-d,2.);frag=vec4(C.rgb,a*C.a);}
'''
POST='''#version 330
in vec2 uv;out vec4 frag;uniform sampler2D picture;uniform sampler2D depthtex;uniform float focus;uniform float time;
float dist(float z){float n=.08,f=150.;return 2.*n*f/(f+n-(z*2.-1.)*(f-n));}
vec3 tonemap(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}
void main(){float z=dist(texture(depthtex,uv).r);float blur=clamp(abs(z-focus)*.34-.25,0.,3.8);vec2 px=1./vec2(1080,1920);vec3 c=texture(picture,uv).rgb;vec3 b=c*2.;
 for(int i=0;i<8;i++){float a=float(i)*.785398;vec2 o=vec2(cos(a),sin(a))*px*blur;b+=texture(picture,clamp(uv+o,vec2(.001),vec2(.999))).rgb;}c=b/10.;
 float vign=1.-.25*pow(length((uv-.5)*vec2(1.,.8)),1.5);c=tonemap(c*1.45)*vign;c=pow(c,vec3(1./2.2));frag=vec4(c,1);}
'''

class Cinema:
 def __init__(self):
  self.c=moderngl.create_standalone_context(backend='egl');self.c.enable(moderngl.DEPTH_TEST);self.meshes={}
  self.p=self.c.program(vertex_shader=VERT,fragment_shader=FRAG);self.bg=self.c.program(vertex_shader=QVERT,fragment_shader=BG);self.post=self.c.program(vertex_shader=QVERT,fragment_shader=POST)
  quad=self.c.buffer(np.array([[-1,-1],[1,-1],[-1,1],[-1,1],[1,-1],[1,1]],'f4').tobytes());self.bgvao=self.c.simple_vertex_array(self.bg,quad,'p');self.postvao=self.c.simple_vertex_array(self.post,quad,'p')
  self.texture=self.c.texture((W,H),4,dtype='f2');self.depth=self.c.depth_texture((W,H));self.depth.compare_func='';self.fb=self.c.framebuffer([self.texture],self.depth)
  self.back=self.c.texture((W,H),4,dtype='f2');self.backfb=self.c.framebuffer([self.back]);self.output=self.c.simple_framebuffer((W,H),components=3)
  rng=np.random.default_rng(68031);N=512;arr=np.zeros((N,N,3),np.float32)
  for ch in range(3):
   for sig,wt in [(38,.35),(11,.28),(3,.23),(.7,.14)]:
    q=gaussian_filter(rng.random((N,N)).astype('f4'),sig,mode='wrap');q=(q-q.min())/max(1e-7,q.max()-q.min());arr[:,:,ch]+=q*wt
  self.tex=self.c.texture((N,N),3,(arr*255).astype('u1').tobytes());self.tex.build_mipmaps();self.tex.filter=(moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR)
  self.mesh('cell',*sphere(80,128,'cell'));self.mesh('smallcell',*sphere(28,44,'cell'));self.mesh('rock',*sphere(32,48,'rock'));self.mesh('dot',*sphere(12,18,'plain'));self.mesh('terrain',*groundmesh())
  ps=[[x,.4+.22*np.sin(x*.7),-.4] for x in np.linspace(-3.2,3.2,128)];self.mesh('timepath',*tube(ps,.036,8))
  self.points_seed=rng.uniform([-14,-2,-35],[14,9,7],(260,3));self.points_col=np.tile([.20,.38,.36,.25],(260,1));self.points_col[:,3]=rng.uniform(.10,.28,260)
  self.pointprog=self.c.program(vertex_shader=PV,fragment_shader=PF);self.pointbuffer=self.c.buffer(reserve=260*7*4);self.pointvao=self.c.vertex_array(self.pointprog,[(self.pointbuffer,'3f 4f','pos','color')])
  self.rocks=[]
  for j in range(42):
   x=float(rng.uniform(-10,10));z=float(rng.uniform(-24,9));s=float(rng.uniform(.25,1.3));y=float(floor(x,z))+.35*s
   self.rocks.append(matrix([x,y,z],[s*1.2,s*.8,s],rng.uniform(0,1,3)))
  self.granules=rng.uniform(-.55,.55,(24,3));self.granules[:,1]*=1.5
  self.tex.use(0);self.p['detail']=0;self.back.use(1);self.p['backplate']=1
  print('RENDERER',self.c.info.get('GL_RENDERER'),flush=True)
 def mesh(self,name,v,ix):
  vb=self.c.buffer(v.tobytes());ib=self.c.buffer(ix.tobytes());self.meshes[name]=self.c.vertex_array(self.p,[(vb,'3f 3f 3f','pos','normal','local')],ib)
 def uniform(self,p,k,v):
  if k not in p:return
  if isinstance(v,np.ndarray) and v.ndim==2:p[k].write(v.T.astype('f4').tobytes())
  else:p[k].value=tuple(float(x) for x in v) if isinstance(v,(list,tuple,np.ndarray)) else v
 def draw(self,name,kind,model=None,tint=(.12,.41,.34),cut=0,energy=0,reveal=1):
  self.uniform(self.p,'model',np.eye(4) if model is None else model);self.p['kind']=kind;self.p['tint'].value=tint;self.p['cut']=float(cut);self.p['energy']=float(energy);self.p['reveal']=float(reveal);self.meshes[name].render()
 def frame(self,t,tl,s):
  cfg=arrange(t,tl,s);eye=np.array(cfg['eye']);vp=perspective(cfg['fov'])@look(eye,cfg['target']);self.vp=vp
  self.fb.use();self.fb.clear(0,0,0,1);self.c.disable(moderngl.DEPTH_TEST)
  for k,v in [('time',t),('heat',cfg['heat']),('eye',eye)]:self.uniform(self.bg,k,v)
  self.bgvao.render();self.c.enable(moderngl.DEPTH_TEST)
  for k,v in [('vp',vp),('eye',eye),('time',t),('heat',cfg['heat'])]:self.uniform(self.p,k,v)
  self.draw('terrain',0)
  for m in self.rocks:self.draw('rock',0,m)
  # Foreground mineral flanks produce real occlusion and parallax, below hero cells.
  for x,z,sc in [(-4.1,3.2,2.0),(4.5,1.6,1.65),(-5.5,-6,1.8)]:
   y=float(floor(x,z))+.38*sc;self.draw('rock',0,matrix([x,y,z],[sc,sc,sc*1.2],[.2,.7,.3]))
  self.c.copy_framebuffer(self.backfb,self.fb);self.fb.use();self.tex.use(0);self.back.use(1)
  if s==7:
   self.draw('timepath',3,tint=(.15,.50,.62),reveal=cfg['progress'],energy=.1)
  # Organisms are separately placed meshes. Their forms are original reconstructions.
  cells=cfg['cells'];checks=[]
  for i,c in sorted(enumerate(cells),key=lambda ic:np.linalg.norm(eye-np.array(ic[1]['p'])),reverse=True):
   pos=np.array(c['p']);scale=np.array(c['scale']);angles=c['angles'];m=matrix(pos,scale,angles)
   if c.get('cut',0)>.05:
    for j,g in enumerate(self.granules):
     q=pos+rot(*angles)@(g*scale);self.draw('dot',2,matrix(q,.040+(j%3)*.006),tint=(.25,.48,.35))
   self.draw('cell' if c.get('hero') else 'smallcell',1,m,tint=c['color'],cut=c.get('cut',0),energy=c.get('energy',0))
   if c.get('hero'):
    q=vp@np.r_[pos,1];nd=q[:3]/q[3];xy=[float((nd[0]+1)*W/2),float((1-nd[1])*H/2)]
    clearance=float(pos[1]-1.5*max(scale)-floor(pos[0],pos[2]));checks.append({'center_px':xy,'clearance':clearance,'p':pos.tolist(),'r':float(max(scale)*1.5)})
  # Organic material symbols move along separate lanes; passage through the shell is intentional.
  for c in cfg['food']:
   p=np.array(c['p']);r=c['r'];self.draw('dot',2,matrix(p,[r*.8,r,r*.85]),tint=(.76,.38,.075))
   self.draw('dot',2,matrix(p+[r*.85,r*.50,0],r*.58),tint=(.94,.61,.18))
  # Floating detritus is a depth-tested 3D particle field, not an image overlay.
  pp=self.points_seed.copy();pp[:,0]+=.3*np.sin(t*.35+pp[:,2]*.13);pp[:,1]+=.12*np.sin(t*.4+pp[:,0]);pp[:,2]=((pp[:,2]+t*.09+35)%42)-35
  self.pointbuffer.write(np.concatenate([pp,self.points_col],-1).astype('f4').tobytes());self.uniform(self.pointprog,'vp',vp);self.uniform(self.pointprog,'eye',eye)
  self.c.enable(moderngl.BLEND|moderngl.PROGRAM_POINT_SIZE);self.c.blend_func=moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA;self.pointvao.render(mode=moderngl.POINTS);self.c.disable(moderngl.BLEND)
  self.output.use();self.c.disable(moderngl.DEPTH_TEST);self.texture.use(2);self.depth.use(3);self.post['picture']=2;self.post['depthtex']=3;self.post['focus']=float(np.linalg.norm(eye-np.array(cfg['target'])));self.post['time']=t;self.postvao.render();self.c.enable(moderngl.DEPTH_TEST)
  im=Image.frombytes('RGB',(W,H),self.output.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  gaps=[float(np.linalg.norm(np.array(a['p'])-b['p'])-a['r']-b['r']) for i,a in enumerate(checks) for b in checks[i+1:]]
  qa={'camera_clearance':float(eye[1]-floor(eye[0],eye[2])),'hero_checks':checks,'minimum_hero_bounding_gap':min(gaps) if gaps else None,'event':cfg['event'],'food_count':len(cfg['food'])}
  return im,qa,cfg

COLORS=[(.10,.47,.37),(.16,.40,.49),(.43,.43,.17),(.16,.46,.40)]
def cell(p,scale=.75,angle=0,hero=False,color=0,energy=.1,cut=0):
 sc=np.broadcast_to(scale,(3,)).astype(float).tolist();return {'p':list(p),'scale':sc,'angles':[.12,angle*.30,angle],'hero':hero,'color':COLORS[color%4],'energy':energy,'cut':cut}
def arrange(t,tl,s):
 a,b=tl['boundaries'][s:s+2];u=float(np.clip((t-a)/(b-a),0,1));tt=t-a;cs=[c for c in tl['cues'] if c['scene']==s];second=cs[1]['start'];split=ramp(t,second-.18,second+.5)
 C={'eye':[0,1.8,10.4],'target':[0,.45,0],'fov':42.,'heat':0.,'cells':[],'food':[],'progress':u,'event':'','u':u,'scene':s,'second':second}
 drift=.08*np.sin(t*.75);angle=.25+.18*np.sin(t*.31)
 if s==0:
  q=ramp(tt,0,1.25);C['eye']=mix([1.2,2.4,16.2],[.25,1.5,9.1],q).tolist();C['target']=[0,.5,0]
  C['cells']=[cell([-.1,.5+drift,0],.83,angle,True),cell([2.7,-.7,-4],.55,-.5),cell([-2.8,2.3,-6],.60,.6)]
  C['event']='dive_into_scale' if tt<1.25 else ('living_cell_revealed' if t<second else 'surface_and_exchange_highlight')
  C['cells'][0]['energy']=.2+.55*split
 elif s==1:
  C['eye']=[-.3,2.,15.];C['target']=[0,.2,0]
  C['cells']=[cell([-1.65,-.5+drift,0],.79,-.38,True),cell([1.7,1.+drift,-1.0],.74,.34,True,1),cell([.2,-1.1,-7],.5,.7)]
  C['event']='named_world' if t<second else 'early_life_epoch_revealed'
 elif s==2:
  q=ramp(tt,.05,1.1);C['eye']=mix([1.0,2.2,15.],[.25,1.45,9.5],q).tolist();C['target']=[0,.4,0]
  C['cells']=[cell([-.75,.35+drift,0],.77,angle,True),cell([1.45,2.3,-2.2],.57,-.6,True,1),cell([1.65,-1.2,-3.2],.55,.7,True,3)]
  C['event']='macro_focus_push' if tt<1.1 else 'distinct_microbes_revealed'
 elif s==3:
  C['eye']=[.7,1.2,9.3];C['cells']=[cell([0,.55+drift,0],.90,.30+.28*u,True,0,.10+.5*split)]
  C['event']='textured_cell_surface' if t<second else 'environmental_exchange'
 elif s==4:
  C['eye']=[.4,1.2,9.4];C['cells']=[cell([-.35,.50+drift,0],.93,.12,True,0,.20+.75*split,ramp(tt,.45,1.1)*.82)]
  C['event']='cutaway_and_uptake' if t<second else 'material_and_energy_use'
 elif s==5:
  C['eye']=[-.4,1.6,12.5];C['target']=[0,.4,0]
  C['cells']=[cell([-1.5,.8+drift,0],.73,-.35,True,0,.45),cell([1.7,-.2+drift,-.8],.68,.5,True,1,.35)]
  C['event']='anaerobic_material_exchange' if t<second else 'living_neighbors'
 elif s==6:
  q=ramp(t,second-.25,second+.65);C['eye']=mix([4.5,3.7,16.],[.6,1.7,10.3],q).tolist();C['target']=[.1,.35,-1.5];C['heat']=.78
  C['cells']=[cell([0,.4+drift,-1.4],.82,.24,True,2,.5),cell([-2.8,-.4,-4],.5,-.6),cell([2.7,.7,-6],.54,.8)]
  C['event']='warm_mineral_landscape' if t<second else 'heat_loving_inhabitant'
 elif s==7:
  C['eye']=[0,2.4,17.];C['target']=[0,.2,0];C['progress']=.2+.8*ramp(t,a+.25,b-.25)
  C['cells']=[cell([-2.1,-.6+drift,-1],.65,-.3,True),cell([2.,1.6+drift,-3],.62,.3,True,1)]
  C['event']='uncertain_origin_interval' if t<second else 'entry_to_recorded_epoch'
 elif s==8:
  q=ramp(tt,.1,1.2);C['eye']=mix([-1.2,2.4,14.],[.3,1.9,12.6],q).tolist();C['target']=[0,.3,0]
  C['cells']=[cell([-2.,.7+drift,-.5],.70,-.3,True),cell([1.5,1.7+drift,-2],.65,.4,True,1),cell([.9,-1.+drift,-1],.58,.7,True,3)]
  C['event']='mineral_and_water_parallax' if t<second else 'ongoing_organic_exchange'
 else:
  q=ramp(t,a+.6,b-.25);C['eye']=mix([.2,1.8,10.5],[1.5,4.6,23.],q).tolist();C['target']=[0,.2,-2]
  C['cells']=[cell([-1.8,.5+drift,-1],.70,-.3,True),cell([1.7,1.3+drift,-2],.67,.35,True,1),cell([.5,-1.+drift,-1.3],.56,.7,True,3)]
  C['event']='tiny_inhabitants_to_ocean' if t<second else 'world_history_continues'
 # Flow along independent lanes, synchronized but not falsely represented as exact biology.
 if s in [0,2,3,4,5,6,8,9]:
  h=C['cells'][0];cp=np.array(h['p']);sc=h['scale'][0]
  for j in range(7):
   cyc=(tt*.55+j*.137)%1.;x=2.65-3.45*cyc;y=.70*np.sin(j*2.0)+.08*np.sin(t+j);z=.18*np.cos(j*1.7)
   if s!=4 and x<sc*.6:continue
   if s==4 and x<-.20:continue
   C['food'].append({'p':(cp+[x,y,z+sc*.65]).tolist(),'r':.070+(j%3)*.010})
 # Each principal object is kept above the mineral surface.
 for c in C['cells']:
  y0=float(floor(c['p'][0],c['p'][2]))+1.5*max(c['scale'])+.18;c['p'][1]=max(c['p'][1],y0)
 C['event_phase']=min(3,int(tt/1.25));return C

CAPTIONS={
'この海には、地球が生まれる前から、':['この海には、','地球が生まれる前から、'],
'約七十三億年前から、初期生命の時代へ。':['約七十三億年前から、','初期生命の時代へ。'],
'主役は、単純なつくりの微生物。':['主役は、単純なつくりの','微生物。'],
'生きるための材料と、エネルギーを得る。':['生きるための材料と、','エネルギーを得る。'],
'最初に生まれた、正確な時刻は分からない。':['最初に生まれた、','正確な時刻は分からない。'],
'ここで見るのは、初期生命の時代の入口だ。':['ここで見るのは、','初期生命の時代の入口だ。'],
'岩と水が変わる、そのかたわらで、':['岩と水が変わる、','そのかたわらで、']}
class Typography:
 def __init__(self):
  self.fonts={};assert Path(FONT).exists(),FONT
  a=np.zeros((H,W,4),np.uint8);a[:,:,:3]=[1,9,13];yy=np.arange(H);al=np.maximum(np.clip((300-yy)/300,0,1)*125,np.clip((yy-1370)/400,0,1)*145);a[:,:,3]=al[:,None].astype('u1');self.shade=Image.fromarray(a)
 def font(self,n):
  if n not in self.fonts:self.fonts[n]=ImageFont.truetype(FONT,n)
  return self.fonts[n]
 def text(self,d,txt,x,y,size=42,col=(242,247,248,255),anchor='mm'):
  d.text((x,y),txt,font=self.font(size),fill=col,anchor=anchor,stroke_width=1,stroke_fill=(2,10,15,col[-1]))
 def lines(self,text):
  if text in CAPTIONS:return CAPTIONS[text]
  if self.font(64).getlength(text)<=930:return [text]
  opts=[i for i in range(1,len(text)) if self.font(64).getlength(text[:i])<=930 and self.font(64).getlength(text[i:])<=930 and text[i] not in '、。ー']
  assert opts,('Subtitle width',text);i=min(opts,key=lambda j:abs(len(text[:j])-len(text[j:]))-(3 if text[j-1]=='、' else 0));return [text[:i],text[i:]]
 def overlay(self,im,t,cfg,tl):
  s=cfg['scene'];a,b=tl['boundaries'][s:s+2];second=cfg['second'];out=im.convert('RGBA');out.alpha_composite(self.shade);layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
  self.text(d,'平穏暦全史  ／  前史068',66,133,29,(205,226,229,235),'lm')
  head={0:'地球より古い、生命の海',1:'惑星オーウェル',2:'微小な世界へ',3:'初期の微生物',4:'外の材料を、内側へ',5:'酸素を使わない暮らし',6:'熱を好む、小さな住人',7:'初期生命の時代の入口',8:'岩と水、そして生命',9:'小さな命から、長い歴史へ'}[s]
  self.text(d,head,540,246,43,(225,242,239,255))
  if s==1 and t>=second-.05:
   q=ramp(t,second-.05,second+.28);self.text(d,'約73億年前～',540,410+18*(1-q),78,(246,208,132,round(255*q)))
   self.text(d,'初期生命の時代',540,502,37,(220,235,237,round(255*q)))
  if s==4:
   q=ramp(t,a+.45,a+.85);self.text(d,'有機物',856,612,42,(249,197,112,round(255*q)))
   if t>=second:self.text(d,'材料 ＋ エネルギー',540,1335,43,(149,230,205,round(255*ramp(t,second,second+.3))))
  if s==6 and t<second:self.text(d,'暖かな水',810,1120,37,(247,195,130,255))
  if s==7:
   txt='起源の正確な時刻は未詳' if t<second else '約73億年前～'
   self.text(d,txt,540,455,49 if t<second else 75,(241,217,166,255))
  cue=next((c for c in tl['cues'] if c['start']-.06<=t<c['end']+.14),None)
  if cue:
   alpha=min(ramp(t,cue['start']-.06,cue['start']+.08),1-ramp(t,cue['end']+.02,cue['end']+.14));rise=16*(1-ramp(t,cue['start']-.06,cue['start']+.12));ls=self.lines(cue['text']);cy=1552+rise;hh=len(ls)*87+32
   d.rounded_rectangle((61,cy-hh/2,1019,cy+hh/2),radius=17,fill=(2,13,20,round(150*alpha)))
   for j,line in enumerate(ls):self.text(d,line,540,cy+(j-(len(ls)-1)/2)*87,64,(242,247,248,round(255*alpha)))
  foot='オリオン腕の設定  ·  姿・色・縮尺は説明用の再現'
  if s in [4,5]:foot='取り込みと働きの模型  ·  色と光は説明用の表現'
  if s==6:foot='生息環境の再現例  ·  生命の起源の場所を示すものではない'
  if s==7:foot='年代は時代区分の目安  ·  起源の正確な日付とは区別'
  self.text(d,foot,540,1782,23,(171,205,214,235));out.alpha_composite(layer);return out.convert('RGB')

def shot(s,preview=False):
 tl=json.loads((ROOT/'timeline.json').read_text());a=round(tl['boundaries'][s]*FPS);b=round(tl['boundaries'][s+1]*FPS)
 samples=sorted(set(a+round((b-a-1)*u) for u in [.08,.29,.53,.77,.95]));ids=samples if preview else range(a,b)
 r=Cinema();typ=Typography();proc=None;log=(ROOT/'review'/f'encode_{s:02}.log').open('w');states=[];last=None
 if not preview:proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-threads','3',str(ROOT/'render'/f'shot_{s:02}.mp4')],stdin=subprocess.PIPE,stderr=log)
 try:
  for f in ids:
   t=f/FPS;raw,qa,cfg=r.frame(t,tl,s);out=typ.overlay(raw,t,cfg,tl);tiny=np.asarray(raw.crop((65,330,1015,1435)).resize((190,221)),dtype=np.int16);delta=float(np.abs(tiny-last).mean()) if last is not None else 0.;last=tiny
   bad=[]
   if qa['camera_clearance']<.3:bad.append('camera_intersects_ground')
   for h in qa['hero_checks']:
    if h['clearance']<0:bad.append('main_cell_intersects_ground')
    if not (65<h['center_px'][0]<1015 and 325<h['center_px'][1]<1395):bad.append('main_cell_center_outside_safe_region')
   if qa['minimum_hero_bounding_gap'] is not None and qa['minimum_hero_bounding_gap']<-.05:bad.append('main_cell_bounding_volumes_overlap')
   row={'frame':f,'time':t,'scene':s,'delta':delta,'mean_luma':float(tiny.mean()),'issues':bad,**qa};states.append(row)
   if f in samples:out.save(ROOT/'review'/f'p068_s{s:02}_f{f:04}.jpg',quality=95)
   if proc:proc.stdin.write(out.tobytes())
   if preview or (f-a)%24==0:print('FRAME',s,f-a,'of',b-a,'EVENT',cfg['event'],'QA',bad,flush=True)
  if proc:proc.stdin.close();assert proc.wait()==0
 finally:log.close()
 dump(ROOT/'review'/f'{"preview" if preview else "states"}_{s:02}.json',states)
 errors=[x for x in states if x['issues']]
 if errors:raise RuntimeError(json.dumps(errors[:2]))
 print('SHOT_COMPLETE',s,len(states),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='shot':shot(int(sys.argv[2]))
 elif sys.argv[1]=='preview':
  for s in range(10):shot(s,True)
 else:raise ValueError(sys.argv[1])
