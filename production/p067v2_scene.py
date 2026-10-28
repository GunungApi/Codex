"""Original P067 v2 3-D renderer. No image-generation service or picture backplates.
All units, geography, illumination, fluids and camera paths are artistic reconstructions.
Native image: 1080x1920. Reflection buffer: 540x960, a secondary render pass only.
Cloud and ash density are ray-marched in world space; no smoke-ball geometry.
"""
from pathlib import Path
import os, math, json
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','3')
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
import moderngl
from PIL import Image
W,H,FPS=1080,1920,24
ROOT=Path('p067_v2').resolve()
for s in ['assets','render','review','source','deliverables','docs','audio']:(ROOT/s).mkdir(parents=True,exist_ok=True)
SEED=670202

def unit(v):
 v=np.asarray(v,dtype=float);return v/max(float(np.linalg.norm(v)),1e-9)
def ease(x):
 x=float(np.clip(x,0,1));return x*x*(3-2*x)
def ramp(x,a,b):return ease((x-a)/max(1e-5,b-a))
def mix(a,b,t):return np.asarray(a)*(1-t)+np.asarray(b)*t
def look(eye,target):
 f=unit(np.asarray(target)-eye);r=unit(np.cross(f,[0,1,0]));u=np.cross(r,f);m=np.eye(4);m[:3,:3]=[r,u,-f];m[:3,3]=-m[:3,:3]@eye;return m

def perspective(deg,aspect,near=.15,far=600):
 k=1/math.tan(math.radians(deg)/2);m=np.zeros((4,4));m[0,0]=k/aspect;m[1,1]=k;m[2,2]=(far+near)/(near-far);m[2,3]=2*far*near/(near-far);m[3,2]=-1;return m

def ortho(a,b,c,d,n,f):
 m=np.eye(4);m[0,0]=2/(b-a);m[1,1]=2/(d-c);m[2,2]=-2/(f-n);m[0,3]=-(b+a)/(b-a);m[1,3]=-(d+c)/(d-c);m[2,3]=-(f+n)/(f-n);return m

def matrix(pos=(0,0,0),scale=(1,1,1),angle=0):
 m=np.eye(4);co,si=np.cos(angle),np.sin(angle);m[:3,:3]=np.array([[co,0,si],[0,1,0],[-si,0,co]])@np.diag(np.broadcast_to(scale,(3,)));m[:3,3]=pos;return m

def grid_indices(nz,nx):
 a=np.arange(nz)[:,None]*(nx+1)+np.arange(nx)[None,:];b=a+nx+1;return np.stack([a,b,a+1,a+1,b,b+1],-1).ravel().astype('i4')

class Geography:
 def __init__(self):
  rng=np.random.default_rng(SEED)
  self.field=rng.random((256,256)).astype('f4')
  self.field=gaussian_filter(self.field,1.3,mode='wrap');self.field=(self.field-self.field.min())/(self.field.max()-self.field.min())
  q=rng.random((64,64,64)).astype('f4');q=gaussian_filter(q,1.4,mode='wrap');q=(q-q.min())/(q.max()-q.min());self.volume=q.astype('f4')
 def noise(self,x,z,scale=1):
  xx,zz=np.broadcast_arrays(np.asarray(x)*scale,np.asarray(z)*scale);sh=xx.shape
  return map_coordinates(self.field,np.array([(zz.ravel()+128)%256,(xx.ravel()+128)%256]),order=1,mode='wrap').reshape(sh)
 def height(self,x,z):
  x,z=np.broadcast_arrays(np.asarray(x),np.asarray(z));base=-2.7+.8*(self.noise(x,z,.35)-.5)+.7*(self.noise(x,z,1.3)-.5)
  # Asymmetric layered volcanic flanks, deep caldera and radial erosion channels.
  for cx,cz,hh,rr in [(0,-18,28,19),(42,-78,21,22),(-51,-96,16,24)]:
   dx=x-cx;dz=z-cz;rad=np.sqrt(dx*dx+dz*dz);ang=np.arctan2(dz,dx)
   radius=rad*(1+.06*np.sin(ang*3+.4)+.035*np.sin(ang*7))
   cone=hh*np.exp(-np.power(radius/rr,1.22));bowl=13.0*(hh/28)*np.exp(-np.power(rad/(4.05*rr/19),6))
   gullies=(.5+.5*np.sin(ang*23+2.2*self.noise(x,z,.8)))**6
   erosion=1.75*gullies*(1-np.exp(-rad/5))*np.exp(-rad/(rr*1.8))
   rough=(self.noise(x,z,1.6)-.5)*1.0+(self.noise(x,z,4.8)-.5)*.32
   base+=cone-bowl-erosion+rough*np.exp(-rad/(rr*2))
  # Foreground basalt shelves and broken shore promontories.
  base+=3.7*np.exp(-((x+15)/9)**2-((z-28)/18)**2)
  base+=2.9*np.exp(-((x-21)/8)**2-((z-9)/16)**2)
  ridge=(1-np.abs(2*self.noise(x,z,.95)-1))**3
  base+=.9*ridge+.20*(self.noise(x,z,9)-.5)
  return base
 def terrain(self):
  nx,nz=384,448;x,z=np.meshgrid(np.linspace(-110,110,nx+1),np.linspace(-145,100,nz+1));y=self.height(x,z);e=.07
  dx=(self.height(x+e,z)-self.height(x-e,z))/(2*e);dz=(self.height(x,z+e)-self.height(x,z-e))/(2*e);n=np.stack([-dx,np.ones_like(x),-dz],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
  uv=np.stack([(x+110)/220,(z+145)/245],-1);v=np.concatenate([np.stack([x,y,z],-1),n,uv],-1).reshape(-1,8).astype('f4')
  return v,grid_indices(nz,nx)
 def height_texture(self):
  x,z=np.meshgrid(np.linspace(-110,110,1024),np.linspace(-145,100,1024));return self.height(x,z).astype('f4')
 def detail_texture(self):
  rng=np.random.default_rng(SEED+1);sz=1024;acc=np.zeros((sz,sz),np.float32);ws=0
  for sig,w in [(65,.46),(23,.27),(7,.15),(2,.08),(.45,.04)]:
   v=gaussian_filter(rng.random((sz,sz)).astype('f4'),sig,mode='wrap');v=(v-v.mean())/(v.std()+1e-6);acc+=v*w;ws+=w
  acc=np.clip(.5+acc*.18,0,1);dy,dx=np.gradient(acc);tex=np.stack([acc,np.clip(.5+dx*9,0,1),np.clip(.5+dy*9,0,1),rng.random((sz,sz))],-1);return (tex*255).astype('u1')

def sphere(nx=128,ny=80,geo=None,planet=False):
 lat,lon=np.meshgrid(np.linspace(-np.pi/2,np.pi/2,ny+1),np.linspace(0,2*np.pi,nx+1),indexing='ij');n=np.stack([np.cos(lat)*np.cos(lon),np.sin(lat),np.cos(lat)*np.sin(lon)],-1);uv=np.stack([lon/(2*np.pi),lat/np.pi+.5],-1)
 if planet:
  h=planet_height(n,geo);p=n*(3+.085*h)[...,None]
  dz=np.gradient(p,axis=0);dx=np.gradient(p,axis=1);nn=np.cross(dx,dz);nn/=np.maximum(np.linalg.norm(nn,axis=-1,keepdims=True),1e-8);sg=np.where((nn*n).sum(-1)<0,-1,1);nn*=sg[...,None];nn[0]=n[0];nn[-1]=n[-1]
 else:p=n;nn=n
 return np.concatenate([p,nn,uv],-1).reshape(-1,8).astype('f4'),grid_indices(ny,nx)

def planet_height(n,g):
 shape=n.shape[:-1];out=np.zeros(shape)
 for freq,weight in [(1.5,.45),(3.7,.28),(9.1,.15),(22.7,.08),(55,.04)]:
  coord=((n+1.3)*freq*12)%64;v=map_coordinates(g.volume,coord.reshape(-1,3).T,order=1,mode='wrap').reshape(shape);out+=weight*v
 return np.clip((out-.26)/.46,0,1)

def planet_map(g):
 la,lo=np.meshgrid(np.linspace(-np.pi/2,np.pi/2,768),np.linspace(0,2*np.pi,1536),indexing='ij');n=np.stack([np.cos(la)*np.cos(lo),np.sin(la),np.cos(la)*np.sin(lo)],-1);h=planet_height(n,g)
 cl=map_coordinates(g.volume,(((n+1.8)*22)%64).reshape(-1,3).T,order=1,mode='wrap').reshape(h.shape)
 out=np.stack([h,cl,np.clip(1-abs(2*cl-1),0,1),np.ones_like(h)],-1);return (out*255).astype('u1')

def water_mesh():
 nx,nz=128,160;x,z=np.meshgrid(np.linspace(-330,330,nx+1),np.linspace(-330,330,nz+1));y=x*0;n=np.stack([y,y+1,y],-1);uv=np.stack([x/20,z/20],-1);return np.concatenate([np.stack([x,y,z],-1),n,uv],-1).reshape(-1,8).astype('f4'),grid_indices(nz,nx)

def lava_mesh(g):
 verts=[];ids=[]
 # Each channel is a raised, ground-following ribbon, not a floating luminous tube.
 for ch,ang in enumerate([.65,1.22,2.62,4.75]):
  start=len(verts)
  for j in range(161):
   u=j/160;rad=4.25+25*u;a=ang+.10*np.sin(u*5+ch)+.04*np.sin(u*17)
   xx=rad*np.cos(a);zz=-18+rad*np.sin(a);wid=(.13+.22*np.sin(np.pi*u)+.15*u)
   for side in [-1,1]:
    x=xx+side*wid*np.cos(a+np.pi/2);z=zz+side*wid*np.sin(a+np.pi/2);y=float(g.height(x,z))+.11
    verts.append([x,y,z,0,1,0,(side+1)/2,u*15+ch*4])
  for j in range(160):k=start+j*2;ids.extend([k,k+1,k+2,k+1,k+3,k+2])
 # Crater lake shares the caldera center and sits below the jagged rim.
 h=float(g.height(0,-18))+.18;start=len(verts);verts.append([0,h,-18,0,1,0,.5,.5])
 for i in range(97):
  a=i/96*2*np.pi;rad=2.78*(1+.07*np.sin(a*9));verts.append([rad*np.cos(a),h,-18+rad*np.sin(a),0,1,0,.5+.5*np.cos(a),.5+.5*np.sin(a)])
 for i in range(96):ids.extend([start,start+i+1,start+i+2])
 return np.array(verts,'f4'),np.array(ids,'i4')

VERT='''#version 330
in vec3 a_pos;in vec3 a_norm;in vec2 a_uv;
uniform mat4 model;uniform mat4 vp;uniform mat4 lightvp;uniform float time;uniform int kind;uniform float sea;
out vec3 P;out vec3 N;out vec3 L;out vec2 UV;out vec4 LP;
void main(){vec3 p=a_pos,n=a_norm;
if(kind==2){float a=p.x*.24+p.z*.12-time*1.5;float b=p.x*-.14+p.z*.31-time*1.95;float c=p.x*.61-p.z*.33-time*2.6;float d=p.x*.95+p.z*.73-time*3.4;p.y=sea+.18*sin(a)+.12*sin(b)+.055*sin(c)+.026*sin(d);n=normalize(vec3(-.0432*cos(a)+.0168*cos(b)-.03355*cos(c)-.0247*cos(d),1.,-.0216*cos(a)-.0372*cos(b)+.01815*cos(c)-.01898*cos(d)));}
vec4 w=model*vec4(p,1);P=w.xyz;L=p;N=normalize(transpose(inverse(mat3(model)))*n);UV=a_uv;LP=lightvp*w;gl_Position=vp*w;}
'''
FRAG='''#version 330
in vec3 P;in vec3 N;in vec3 L;in vec2 UV;in vec4 LP;
uniform vec3 eye;uniform vec3 sun;uniform int kind;uniform float time;uniform float sea;uniform float heat;uniform float wet;uniform float ocean;uniform vec4 tint;
uniform sampler2D detailtex;uniform sampler2D heighttex;uniform sampler2D shadowtex;uniform sampler2D reflectiontex;uniform sampler2D planettex;
uniform mat4 reflectvp;out vec4 frag;
float shadow(){vec3 q=LP.xyz/LP.w*.5+.5;if(any(lessThan(q,vec3(0)))||any(greaterThan(q,vec3(1))))return 1.;float s=0.;vec2 e=1./vec2(textureSize(shadowtex,0));for(int i=0;i<4;i++){vec2 o=vec2(i%2,i/2)-.5;float d=texture(shadowtex,q.xy+o*e*2.).r;s+=q.z-.0014<d?1.:.16;}return s*.25;}
vec3 skycol(vec3 d){float h=max(0.,d.y);vec3 c=mix(vec3(.55,.43,.33),vec3(.09,.19,.27),pow(h,.45));float s=max(0.,dot(d,sun));return c+vec3(1.,.65,.30)*pow(s,130.)*.9;}
float groundh(vec2 p){vec2 uv=(p-vec2(-110,-145))/vec2(220,245);return texture(heighttex,clamp(uv,0.,1.)).r;}
void main(){vec3 n=normalize(N),v=normalize(eye-P),l=sun;vec3 col=vec3(.1);float alpha=tint.a;float sunlit=max(0.,dot(n,l));
if(kind==0||kind==3){vec4 tex=texture(detailtex,P.xz*.025+P.yy*.006);vec4 fine=texture(detailtex,P.xz*.19);n=normalize(n+vec3((fine.g-.5)*.46,0.,(fine.b-.5)*.46));float slope=1.-max(0.,n.y);float strata=texture(detailtex,vec2(P.y*.043,P.x*.012+P.z*.008)).r;vec3 basalt=mix(vec3(.065,.070,.073),vec3(.22,.205,.18),tex.r);basalt=mix(basalt,vec3(.235,.15,.09),pow(strata,5.)*.38);basalt*=.8+.4*fine.r;float damp=1.-smoothstep(sea+.2,sea+1.9,P.y);basalt*=mix(1.,.58,damp*wet);float sh=shadow();col=basalt*(.35+1.40*max(0.,dot(n,l))*sh)+vec3(.026,.045,.061)*max(.2,n.y);float glow=heat*exp(-length(P.xz-vec2(0,-18))*.12)*exp(-abs(P.y-12.)*.16);col+=vec3(.36,.055,.006)*glow;}
else if(kind==1){vec4 q=texture(detailtex,vec2(UV.x*.20,UV.y*.09-time*.032));float crust=smoothstep(.41,.65,q.r);float vein=1.-smoothstep(.07,.22,abs(q.r-.49));vec3 hot=mix(vec3(2.8,.22,.012),vec3(7.,1.8,.10),q.r);col=mix(hot,vec3(.025,.018,.014),crust*.90)*(.45+.55*heat);col+=vec3(2.,.27,.008)*vein;}
else if(kind==2){vec4 q=texture(detailtex,P.xz*.11+vec2(time*.007,time*.003));n=normalize(n+vec3(q.g-.5,0.,q.b-.5)*.24);float depth=max(0.,sea-groundh(P.xz));vec3 base=mix(vec3(.025,.20,.17),vec3(.006,.038,.060),1.-exp(-depth*.21));vec3 R=reflect(-v,n);vec4 rp=reflectvp*vec4(P,1);vec2 uv=rp.xy/rp.w*.5+.5+n.xz*.021;vec3 refl=texture(reflectiontex,clamp(uv,.002,.998)).rgb;float fres=.025+.975*pow(1.-max(0.,dot(n,v)),5.);col=mix(base,refl,clamp(fres,.035,.93));float sp=pow(max(0.,dot(reflect(-l,n),v)),160.);col+=vec3(1.7,1.13,.60)*sp;float shore=exp(-depth*2.4)*smoothstep(.28,.75,q.r);float crests=pow(max(0.,sin(P.x*.24+P.z*.12-time*1.5)),18.)*smoothstep(.64,.90,q.r)*.17;col=mix(col,vec3(.62,.76,.74),clamp(shore*.7+crests,0.,.85));if(eye.y<sea){col=mix(vec3(.012,.10,.13),skycol(refract(-v,-n,.75)),.23);}}
else if(kind==4){vec4 g=texture(planettex,UV);vec4 f=texture(detailtex,UV*vec2(6,3));n=normalize(n+(f.gba-.5)*.045);float csh=texture(planettex,UV+vec2(.007,.004)).g;col=mix(vec3(.07,.065,.058),vec3(.29,.22,.16),g.r)*(.11+1.15*max(0.,dot(n,l)))*(1.-smoothstep(.55,.73,csh)*.25*wet);float crack=pow(1.-abs(2.*f.r-1.),28.)*smoothstep(.4,.75,g.b);col+=vec3(3.8,.35,.006)*crack*heat;}
else if(kind==5){vec4 f=texture(detailtex,UV*vec2(8,4)+time*.0008);n=normalize(n+(f.gba-.5)*.025);col=vec3(.013,.085,.13)*(.16+1.2*max(0.,dot(n,l)));float spec=pow(max(0.,dot(reflect(-l,n),v)),100.);col+=vec3(.85,.78,.58)*spec;}
else if(kind==6){vec2 uv=UV+vec2(time*.0013,0);vec4 g=texture(planettex,uv);float d=smoothstep(.46,.72,g.g)*(.40+.6*wet);col=mix(vec3(.12,.15,.19),vec3(.82,.76,.64),max(0.,dot(n,l)))*(.85+.15*g.b);alpha*=d;}
else if(kind==7){float rim=pow(1.-abs(dot(n,v)),3.);col=mix(vec3(.36,.16,.055),vec3(.10,.34,.50),wet);col*=.55+1.7*max(0.,dot(n,l));alpha*=rim;}
else{col=tint.rgb;}
if(kind<4){float dst=length(eye-P);vec3 fog=vec3(.32,.35,.34);float den=.0027;if(eye.y<sea){den=.062;fog=vec3(.007,.11,.15);}col=mix(col,fog,1.-exp(-dst*den));}
frag=vec4(col,alpha);}
'''
SHADOWV='''#version 330
in vec3 a_pos;uniform mat4 lightvp;uniform mat4 model;void main(){gl_Position=lightvp*model*vec4(a_pos,1);}
'''
SHADOWF='''#version 330
void main(){}
'''
QUADV='''#version 330
in vec2 q;out vec2 uv;void main(){uv=q*.5+.5;gl_Position=vec4(q,0,1);}
'''
SKY='''#version 330
in vec2 uv;out vec4 frag;uniform mat4 invvp;uniform vec3 eye;uniform vec3 sun;uniform float time;uniform int orbital;uniform sampler3D noise3;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){vec4 h=invvp*vec4(uv*2.-1.,1,1);vec3 rd=normalize(h.xyz/h.w-eye);vec3 col;
if(orbital==1){col=vec3(.0015,.003,.007);vec2 cell=floor(uv*vec2(520,930));float r=hash(cell);vec2 d=fract(uv*vec2(520,930))-.5;float star=exp(-dot(d,d)*45.)*step(.9982,r);col+=vec3(.7,.8,1.)*star*.75;col+=vec3(.004,.005,.01)*exp(-pow((uv.x+.5*uv.y-.6)*4.,2.));}
else{float y=max(0.,rd.y);col=mix(vec3(.59,.47,.35),vec3(.07,.15,.23),pow(y,.45));float s=max(0.,dot(rd,sun));col+=vec3(1.15,.70,.32)*pow(s,200.);col+=vec3(.18,.105,.045)*pow(s,9.);if(rd.y>.015){vec3 p=eye+rd*(92.-eye.y)/rd.y;float n=texture(noise3,p*.003+vec3(time*.0005,0,0)).r;float n2=texture(noise3,p*.008+vec3(0,0,time*.0004)).r;float den=smoothstep(.43,.64,n*.72+n2*.28);float lit=texture(noise3,(p+sun*9.)*.003+vec3(time*.0005,0,0)).r;col=mix(col,mix(vec3(.19,.22,.24),vec3(.76,.71,.61),clamp(1.3-lit,0,1)),den*.92);}}
frag=vec4(col,1);}
'''
COMPOSITE='''#version 330
in vec2 uv;out vec4 frag;uniform sampler2D picture;uniform sampler2D depthmap;uniform sampler3D noise3;uniform mat4 invvp;uniform vec3 eye;uniform vec3 sun;uniform float time;uniform float eruption;uniform float sea;uniform int orbital;
vec2 hitbox(vec3 ro,vec3 rd,vec3 lo,vec3 hi){vec3 inv=1./rd;vec3 a=(lo-ro)*inv,b=(hi-ro)*inv;vec3 mn=min(a,b),mx=max(a,b);return vec2(max(max(mn.x,mn.y),mn.z),min(min(mx.x,mx.y),mx.z));}
float density(vec3 p){float y=p.y-11.;if(y<0.||y>68.)return 0.;vec2 ctr=vec2(.075*y+.0011*y*y,-18.+.024*y);float w=1.15+.13*y+.0016*y*y;float shape=exp(-dot(p.xz-ctr,p.xz-ctr)/(w*w));vec3 a=p*.049+vec3(.012*time,-.052*time,.006*time);float n=texture(noise3,a).r*.68+texture(noise3,a*2.75).r*.32;return shape*smoothstep(.24,.65,n)*smoothstep(0.,3.,y)*(1.-smoothstep(49.,68.,y))*(.12+.38*eruption);}
vec3 aces(vec3 c){return clamp((c*(2.51*c+.03))/(c*(2.43*c+.59)+.14),0.,1.);}
void main(){vec3 col=texture(picture,uv).rgb;vec4 a=invvp*vec4(uv*2.-1.,1,1);vec3 rd=normalize(a.xyz/a.w-eye);float dep=texture(depthmap,uv).r;vec4 hit=invvp*vec4(uv*2.-1.,dep*2.-1.,1);float maxdist=dep>.99999?600.:length(hit.xyz/hit.w-eye);
if(orbital==0&&eye.y>sea){vec2 tb=hitbox(eye,rd,vec3(-19,11,-44),vec3(28,80,12));float start=max(0.,tb.x),end=min(tb.y,maxdist);if(end>start){float stepd=(end-start)/36.;float jitter=fract(sin(dot(gl_FragCoord.xy,vec2(12.9898,78.233)))*43758.5453);vec3 sum=vec3(0);float trans=1.;for(int i=0;i<36;i++){vec3 p=eye+rd*(start+(float(i)+jitter)*stepd);float d=density(p);if(d>.002){float atten=exp(-(density(p+sun*3.)+density(p+sun*8.))*4.);vec3 lit=mix(vec3(.12,.15,.18),vec3(.69,.65,.55),atten);lit+=vec3(1.3,.16,.009)*exp(-max(0.,p.y-12.)*.18)*eruption;float aa=1.-exp(-d*stepd);sum+=trans*aa*lit;trans*=1.-aa;if(trans<.018)break;}}col=col*trans+sum;}}
if(eye.y<sea&&orbital==0){float rays=pow(max(0.,sin(rd.x*21.+rd.z*11.+time*.2)),18.);col+=vec3(.02,.08,.09)*rays*.3;}
float vig=1.-.13*smoothstep(.27,.85,length((uv-.5)*vec2(.8,1.)));col=pow(aces(max(col,vec3(0))*.93)*vig,vec3(1./2.2));frag=vec4(col,1);}
'''

class Cinema:
 def __init__(self):
  self.g=Geography();self.c=moderngl.create_standalone_context(backend='egl',require=330);print('RENDERER',self.c.info['GL_RENDERER'],flush=True)
  c=self.c;self.prog=c.program(vertex_shader=VERT,fragment_shader=FRAG);self.sp=c.program(vertex_shader=SHADOWV,fragment_shader=SHADOWF);self.sky=c.program(vertex_shader=QUADV,fragment_shader=SKY);self.comp=c.program(vertex_shader=QUADV,fragment_shader=COMPOSITE)
  q=c.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());self.skyvao=c.vertex_array(self.sky,[(q,'2f','q')]);self.compvao=c.vertex_array(self.comp,[(q,'2f','q')])
  self.color=c.texture((W,H),4,dtype='f2');self.depth=c.depth_texture((W,H));self.depth.compare_func='';self.main=c.framebuffer([self.color],self.depth)
  self.refl=c.texture((W//2,H//2),4,dtype='f2');self.refl.filter=(moderngl.LINEAR,moderngl.LINEAR);self.rf=c.framebuffer([self.refl],c.depth_renderbuffer((W//2,H//2)))
  self.out=c.simple_framebuffer((W,H),components=3);self.shadow=c.depth_texture((2048,2048));self.shadow.compare_func='';self.shadow.repeat_x=False;self.shadow.repeat_y=False;self.sf=c.framebuffer(depth_attachment=self.shadow)
  self.detail=c.texture((1024,1024),4,self.g.detail_texture().tobytes());self.detail.build_mipmaps();self.detail.filter=(moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR)
  self.ht=c.texture((1024,1024),1,self.g.height_texture().tobytes(),dtype='f4');self.ht.filter=(moderngl.LINEAR,moderngl.LINEAR);self.ht.repeat_x=False;self.ht.repeat_y=False
  self.n3=c.texture3d((64,64,64),1,(self.g.volume*255).astype('u1').tobytes());self.n3.filter=(moderngl.LINEAR,moderngl.LINEAR);self.n3.repeat_x=True;self.n3.repeat_y=True;self.n3.repeat_z=True
  self.pt=c.texture((1536,768),4,planet_map(self.g).tobytes());self.pt.build_mipmaps();self.pt.filter=(moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR)
  self.meshes={};self.mesh('land',*self.g.terrain());self.mesh('water',*water_mesh());self.mesh('lava',*lava_mesh(self.g));self.mesh('planet',*sphere(192,128,self.g,True));self.mesh('sphere',*sphere(96,64));self.mesh('grain',*sphere(12,8))
  # Angular foreground rock geometry has actual surface relief, not spherical billboards.
  rv,ri=sphere(16,10);p=rv[:,:3];rad=1+.18*np.sin(p[:,0]*17+p[:,1]*9)*np.sin(p[:,2]*13-p[:,1]*7);rv[:,:3]*=rad[:,None];self.mesh('rock',rv,ri)
  self.rocks=[];rng=np.random.default_rng(SEED+15)
  for i in range(75):
   x=float(rng.uniform(-55,55));z=float(rng.uniform(-65,55));s=float(rng.uniform(.3,1.5));y=float(self.g.height(x,z));self.rocks.append(matrix([x,y+.1,z],[s*1.4,s*.6,s],rng.uniform(0,6.28)))
  self.sun=unit([-.44,.64,.57]);self.lightvp=ortho(-115,115,-125,125,1,360)@look(self.sun*170+[0,0,-25],[0,0,-25]);self.render_shadow()
  self.frames=0
 def mesh(self,name,v,idx):
  vb=self.c.buffer(v.tobytes());ib=self.c.buffer(idx.tobytes());va=self.c.vertex_array(self.prog,[(vb,'3f 3f 2f','a_pos','a_norm','a_uv')],ib);sv=self.c.vertex_array(self.sp,[(vb,'3f 20x','a_pos')],ib);self.meshes[name]=(va,sv,vb,ib,len(idx)//3)
 def put(self,p,name,v):
  if name not in p:return
  if isinstance(v,np.ndarray) and v.ndim==2:p[name].write(v.T.astype('f4').tobytes())
  elif isinstance(v,np.ndarray):p[name].value=tuple(v.tolist())
  else:p[name].value=v
 def draw(self,name,kind,model=None,tint=(1,1,1,1)):
  self.put(self.prog,'kind',kind);self.put(self.prog,'model',np.eye(4) if model is None else model);self.put(self.prog,'tint',tint);self.meshes[name][0].render()
 def render_shadow(self):
  c=self.c;self.sf.use();c.viewport=(0,0,2048,2048);self.sf.clear(depth=1);c.enable(moderngl.DEPTH_TEST);c.disable(moderngl.BLEND|moderngl.CULL_FACE);self.put(self.sp,'lightvp',self.lightvp);self.put(self.sp,'model',np.eye(4));self.meshes['land'][1].render()
  for m in self.rocks:self.put(self.sp,'model',m);self.meshes['rock'][1].render()
 def setcommon(self,cfg,t,eye,vp):
  p=self.prog
  for name,val in [('vp',vp),('lightvp',self.lightvp),('eye',eye),('sun',self.sun),('time',t),('sea',cfg['sea']),('heat',cfg['heat']),('wet',cfg['wet']),('ocean',cfg.get('ocean',0)),('reflectvp',getattr(self,'reflectvp',vp))]:self.put(p,name,val)
  for tex,slot,n in [(self.detail,0,'detailtex'),(self.ht,1,'heighttex'),(self.shadow,2,'shadowtex'),(self.refl,3,'reflectiontex'),(self.pt,4,'planettex')]:tex.use(slot);self.put(p,n,slot)
 def background(self,cfg,t,eye,vp):
  c=self.c;c.disable(moderngl.DEPTH_TEST|moderngl.BLEND|moderngl.CULL_FACE)
  for name,val in [('invvp',np.linalg.inv(vp)),('eye',eye),('sun',self.sun),('time',t),('orbital',int(cfg['orbital'])),('noise3',5)]:self.put(self.sky,name,val)
  self.n3.use(5);self.skyvao.render(moderngl.TRIANGLE_STRIP);c.enable(moderngl.DEPTH_TEST)
 def world(self,cfg,t,with_water=True):
  c=self.c
  if cfg['orbital']:
   rot=matrix(angle=cfg['turn']);self.draw('planet',4,rot)
   if cfg['ocean']>.01:self.draw('sphere',5,rot@matrix(scale=3+.085*cfg['ocean']))
   c.enable(moderngl.BLEND);c.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA);c.depth_mask=False
   for k in range(3):self.draw('sphere',6,rot@matrix(scale=3.10+k*.014),tint=(1,1,1,.24))
   self.draw('sphere',7,matrix(scale=3.17),tint=(1,1,1,.32));c.depth_mask=True;c.disable(moderngl.BLEND)
  else:
   self.draw('land',0)
   for m in self.rocks:self.draw('rock',3,m)
   self.draw('lava',1)
   # Hot ballistic ejecta. Emission supplies readable physical-scale highlights.
   if cfg['eruption']>.04:
    base=float(self.g.height(0,-18))+.25
    for i in range(44):
     age=(t*.82+i*.137)%1.9;ang=i*2.39996;speed=1.8+(i%7)*.22;peak=(6+5*cfg['eruption']);y=base+peak*age-4.3*age*age
     x=math.cos(ang)*speed*age;z=-18+math.sin(ang)*speed*age
     if y>float(self.g.height(x,z))+.2:self.draw('grain',8,matrix([x,y,z],.055+(i%3)*.017),tint=(3.9,.55,.025,1))
   if cfg.get('impact',-5)>-1. and cfg.get('impact',-5)<2.2:
    q=cfg['impact'];cx,cz=20.,10.;cy=float(self.g.height(cx,cz))
    if q<0:
     p=mix([30,38,29],[cx,cy+.2,cz],ease(q+1));self.draw('rock',8,matrix(p,.34),tint=(5.,1.5,.12,1))
    else:
     for i in range(28):
      a=i*2.39996;r=(2+(i%5)*.5)*q;y=cy+2.7*q-1.8*q*q
      if y>=cy-.2:self.draw('rock',8,matrix([cx+r*np.cos(a),y,cz+r*np.sin(a)],.12+.06*(i%3)),tint=(1.3,.29,.045,1))
   if with_water and cfg['water_visible']:self.draw('water',2)
 def frame(self,cfg,t):
  c=self.c;eye=np.array(cfg['eye'],float);target=np.array(cfg['target'],float);vp=perspective(cfg['fov'],W/H)@look(eye,target)
  if cfg['water_visible'] and not cfg['orbital']:
   re=eye.copy();rt=target.copy();re[1]=2*cfg['sea']-re[1];rt[1]=2*cfg['sea']-rt[1];self.reflectvp=perspective(cfg['fov'],W/H)@look(re,rt);self.rf.use();c.viewport=(0,0,W//2,H//2);self.rf.clear(.1,.1,.1,1,depth=1);self.background(cfg,t,re,self.reflectvp);self.setcommon(cfg,t,re,self.reflectvp);self.world(cfg,t,False)
  else:self.reflectvp=vp
  self.main.use();c.viewport=(0,0,W,H);self.main.clear(0,0,0,1,depth=1);self.background(cfg,t,eye,vp);self.setcommon(cfg,t,eye,vp);self.world(cfg,t)
  self.out.use();c.viewport=(0,0,W,H);c.disable(moderngl.DEPTH_TEST|moderngl.BLEND);self.color.use(6);self.depth.use(7);self.n3.use(5)
  for name,val in [('picture',6),('depthmap',7),('noise3',5),('invvp',np.linalg.inv(vp)),('eye',eye),('sun',self.sun),('time',t),('eruption',cfg['eruption']),('sea',cfg['sea']),('orbital',int(cfg['orbital']))]:self.put(self.comp,name,val)
  self.compvao.render(moderngl.TRIANGLE_STRIP);im=Image.frombytes('RGB',(W,H),self.out.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM);self.frames+=1
  clearance=None if cfg['orbital'] else float(eye[1]-self.g.height(eye[0],eye[2]))
  return im,{'camera_terrain_clearance':clearance,'underwater':bool(not cfg['orbital'] and eye[1]<cfg['sea']),'terrain_triangles':self.meshes['land'][-1],'camera':eye.tolist(),'target':target.tolist(),'fov':cfg['fov'],'event':cfg['event'],'water_level':cfg['sea'],'eruption':cfg['eruption']}

def keytime(tl,idx,kana,default=0):
 c=tl['cues'][idx];want=kana.replace('ー','');text='';ledger=c.get('moras',[])
 for i,m in enumerate(ledger):
  text=''.join(x['kana'] for x in ledger[i:]).replace('ー','')
  if text.startswith(want):return c['audio_start']+m['start']
 return c['start']+default

def config(t,tl):
 s=min(9,max(0,int(np.searchsorted(tl['boundaries'],t,side='right')-1)));a,d=tl['boundaries'][s:s+2];u=float(np.clip((t-a)/(d-a),0,1));second=tl['cues'][s*2+1]['start'];p=ease(u)
 C={'scene':s,'u':u,'eye':[28,14,54],'target':[0,9,-18],'fov':43.,'sea':-5.,'wet':0.,'heat':1.,'eruption':.6,'water_visible':False,'orbital':False,'ocean':0.,'turn':.25+t*.027,'event':'volcanic_world','impact':-5.}
 if s==0:
  if t<second:
   C.update(eye=mix([9.5,19,-7.5],[7.2,18,-10.8],ramp(t,a,second)).tolist(),target=[0,13,-18],fov=49.,event='crater_rim_reveal',eruption=.8)
  else:C.update(orbital=True,eye=mix([1.3,.8,17.5],[2.6,1.1,20.3],ramp(t,second,d)).tolist(),target=[0,0,0],fov=35.,event='cut_to_planet')
 elif s==1:C.update(orbital=True,eye=mix([-4.5,1.3,20.4],[-2.8,1.0,19.4],p).tolist(),target=[0,0,0],fov=35.,wet=.26,event='name_and_age',heat=.8)
 elif s==2:C.update(orbital=True,eye=[-3.,.8,30.],target=[0,0,0],fov=40.,heat=.45,wet=.3,event='chronology_comparison')
 elif s==3:
  if t<second:C.update(eye=mix([35,10,35],[30,11,29],ramp(t,a,second)).tolist(),target=[12,6,-3],fov=47.,impact=t-keytime(tl,6,'インセキ',.8)-.4,event='impact_and_ejecta',eruption=.26)
  else:C.update(eye=mix([9,24,-8],[5,23,-9.5],ramp(t,second,d)).tolist(),target=[0,15,-18],fov=48.,eruption=.30+.70*ramp(t,second,d-.2),event='lava_fountain_closeup')
 elif s==4:
  if t<second:C.update(eye=mix([20,22,15],[18,29,11],ramp(t,a,second)).tolist(),target=[3,32,-16],fov=45.,eruption=.9,event='ascending_volumetric_plume')
  else:C.update(orbital=True,eye=[2,1.2,20.2],target=[0,0,0],fov=35.,wet=.3+.7*ramp(t,second,d),heat=.35,event='atmosphere_builds')
 elif s==5:C.update(orbital=True,eye=mix([2,1.2,20.2],[3.8,.9,19.7],p).tolist(),target=[0,0,0],fov=35.,wet=.8,ocean=.22+.56*ramp(t,a+.1,d-.15),heat=.45*(1-p),event='ocean_covers_same_relief')
 elif s==6:
  C.update(eye=mix([-15,7.0,35],[-10,7.8,29],p).tolist(),target=[0,12,-18],fov=43.,sea=5.2,wet=1.,heat=.18,water_visible=True,eruption=.22,event='same_volcano_from_coast')
 elif s==7:
  cuts=[keytime(tl,14,'ソラ'),keytime(tl,14,'ネツ',.8),keytime(tl,14,'ミズ',1.5)]
  C.update(sea=5.2,wet=1.,water_visible=True,heat=.45,eruption=.45)
  if t<cuts[1]:C.update(eye=[18,29,12],target=[3,34,-17],fov=44.,event='atmosphere_detail')
  elif t<cuts[2]:C.update(eye=[7,21,-8.5],target=[0,13,-18],fov=47.,event='heat_detail',eruption=.9,water_visible=False)
  elif t<second:C.update(eye=[-13,6.1,30],target=[-8,5.2,17],fov=48.,event='water_detail')
  else:C.update(eye=mix([26,25,38],[22,28,31],ramp(t,second,d)).tolist(),target=[0,8,-18],fov=46.,event='unified_landscape')
 elif s==8:C.update(eye=mix([-21,7.0,42],[-16,7.2,29],p).tolist(),target=[2,10,-23],fov=44.,sea=5.2,wet=1.,heat=.13,water_visible=True,eruption=.16,event='coastal_parallax_and_waves')
 else:
  q=ramp(t,a+.05,d-.3);C.update(eye=mix([-9,8.0,36],[-8,3.2,22],q).tolist(),target=mix([0,11,-18],[-7,2,5],q).tolist(),fov=46.,sea=5.2,wet=1.,heat=.06,water_visible=True,eruption=.10,event='continuous_waterline_dive')
 return C
