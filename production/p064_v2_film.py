"""P064 v2: a native 3-D membrane short. Run only in the authorized production job.
Fonts and voice-engine/model binaries are dependencies, never delivery contents.
Scientific images are original explanatory meshes, not microscopy or simulations.
"""
from pathlib import Path
import os, sys, json, math, time, stat, zipfile, shutil, wave, subprocess, urllib.request, urllib.parse, hashlib, re
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','3')
os.environ.setdefault('OMP_NUM_THREADS','3')
import numpy as np
import moderngl
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import butter, sosfilt
import soundfile as sf
ROOT=Path('p064_v2').resolve()
for sub in ['audio/raw','source','render','review','docs','deliverables']: (ROOT/sub).mkdir(parents=True,exist_ok=True)
W,H,FPS,SR=1080,1920,24,48000
TITLE='膜が作る、内側と外側'
PARTS=[
('膜が閉じると、','When a membrane closes,',0),
('ばらばらの材料に、内側が生まれる。','scattered ingredients gain an inside.',0),
('その膜を作るのは、','The membrane is built from',1),
('脂肪酸などの小さな分子。','small molecules, such as fatty acids.',1),
('水になじむ頭は、水のほうへ。','Water-friendly heads face the water.',2),
('水を避ける尾は、膜の奥へ。','Water-avoiding tails face into the membrane.',2),
('こうして二重に並んだ膜が、','Arranged in two layers, the membrane',3),
('くるりと閉じる。','curves into a closed compartment.',3),
('外から膜の材料を加えると、','In some experiments, adding membrane material',4),
('袋が伸びる実験もある。','makes the compartments elongate.',4),
('そこへ穏やかな水の動きが加わると、','Gentle movement of the water can then',5),
('いくつかの袋に分かれる。','divide them into smaller compartments.',5),
('中に入れた材料も、','The enclosed material is also',6),
('分かれた袋へ受け渡される。','passed on to the new compartments.',6),
('さらに膜は、一部の分子を通し、','The membrane lets some molecules through',7),
('別の材料を中に保つ。','while retaining other material.',7),
('大事なのは、閉じ込めることと、','Both containment',8),
('外とやり取りすること。','and exchange with the surroundings matter.',8),
('袋ができた。','A compartment has formed.',9),
('その中で、どうすれば反応が続くのだろう。','How can reactions keep going inside?',9)]
HEADINGS=['境界が、生まれる。','膜を作る、小さな分子','水に触れる側・隠れる側','二重の膜が、閉じる','外から材料を加える','水の動きで、分かれる','中身も、次の袋へ','通すもの・保つもの','守りながら、交換する','中では、何が続く？']
SOURCES=[{'id':'S1','title':'Zhu & Szostak (2009), Coupled Growth and Division of Model Protocell Membranes','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC2669828/','doi':'10.1021/ja900919c','use':'Growth by external fatty-acid supply, filamentous shapes, division under mild fluid shear, retention and distribution of contents.'},{'id':'S2','title':'Mansy et al. (2008), Template-directed synthesis of a genetic polymer in a model protocell','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC2743009/','doi':'10.1038/nature07018','use':'Permeability to selected externally supplied small substrates while larger encapsulated material is retained. No claim that all small solutes cross.'},{'id':'S3','title':'Mansy & Szostak (2008), Thermostability of model protocell membranes','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC2528865/','doi':'10.1073/pnas.0805086105','use':'Single-chain amphiphiles and retention of encapsulated oligonucleotides in experimental model membranes.'}]
def dump(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def run(c,**kw): return subprocess.run(c,check=True,**kw)
def ease(x): x=float(np.clip(x,0,1));return x*x*(3-2*x)
def smooth(t,a,b): return ease((t-a)/max(.0001,b-a))
def unit(x): x=np.asarray(x,float);return x/max(np.linalg.norm(x),1e-10)
def lerp(a,b,q): return np.asarray(a)*(1-q)+np.asarray(b)*q
def rot(x=0,y=0,z=0):
 cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def restore_voice():
 engine=Path('voice_engine').resolve();engine.mkdir(exist_ok=True)
 cache=Path('runtime'); sparse=Path('voice_engine_sparse.vvpp')
 ranges=[(0,129169125,'engine_range_0.bin','4da9d1e2dbb883d7a9732d3232e50f7a1e726d744d24b278f5dedeacbfd89141'),(1689641293,1911613160,'engine_range_1.bin','839b6f1b1846157fee6d680b083741ece4e31045a31e9952bb1441773b0cbd2e')]
 with sparse.open('wb') as f:
  f.truncate(1911613161)
  for a,b,n,d in ranges:
   data=(cache/n).read_bytes();assert len(data)==b-a+1 and hashlib.sha256(data).hexdigest()==d
   f.seek(a);f.write(data)
 count=0
 with zipfile.ZipFile(sparse) as z:
  for inf in z.infolist():
   n=inf.filename
   if n.endswith('/'):continue
   if not any(a<=inf.header_offset and inf.header_offset+30+len(n.encode())+inf.compress_size<=b+1 for a,b,_,_ in ranges):continue
   p=engine/n;assert p.resolve().is_relative_to(engine)
   data=z.read(inf);p.parent.mkdir(parents=True,exist_ok=True);mode=inf.external_attr>>16
   if stat.S_ISLNK(mode):
    if p.exists() or p.is_symlink():p.unlink()
    p.symlink_to(data.decode())
   else:p.write_bytes(data);p.chmod((mode&0o777) or 0o644)
   count+=1
 with zipfile.ZipFile(cache/'voicevox_core_0.16.1.zip') as z:
  data=z.read('voicevox_core-linux-x64-0.16.1/lib/libvoicevox_core.so')
  assert hashlib.sha256(data).hexdigest()=='d5e1f20a7ff9deb2e6c6ae9dd0d9afada1caec1e2ae6f4fab672afb018274635'
  (engine/'libvoicevox_core.so').write_bytes(data)
 (engine/'run').chmod(0o755)
 print('RESTORED_OFFICIAL_VOICE_MEMBERS',count,flush=True)
 return engine

def voice():
 engine=restore_voice();env=os.environ.copy();env['XDG_DATA_HOME']=str(ROOT/'voice_data')
 base='http://127.0.0.1:50764'
 def req(path,params=None,body=None):
  url=base+path+('?' + urllib.parse.urlencode(params) if params else '')
  r=urllib.request.Request(url,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST' if params or body is not None else 'GET')
  with urllib.request.urlopen(r,timeout=180) as f:
   data=f.read();return data if path=='/synthesis' else json.loads(data)
 log=(ROOT/'audio/engine.log').open('w');p=subprocess.Popen([str(engine/'run'),'--host','127.0.0.1','--port','50764','--cpu_num_threads','3'],cwd=engine,env=env,stdout=log,stderr=subprocess.STDOUT)
 try:
  for _ in range(180):
   if p.poll() is not None:raise RuntimeError((ROOT/'audio/engine.log').read_text()[-6000:])
   try:version=req('/version');break
   except Exception:time.sleep(.3)
  else:raise RuntimeError('VOICEVOX startup timeout')
  assert version=='0.25.2'
  cursor=.18;pieces=[];cues=[];pron=[]
  for i,(text,en,scene) in enumerate(PARTS):
   spoken=text.replace('尾は','おは').replace('二重に','にじゅうに')
   q=req('/audio_query',{'text':spoken,'speaker':2},body={})
   q.update(speedScale=1.03,pitchScale=-.015,intonationScale=1.08,volumeScale=1.,prePhonemeLength=.08,postPhonemeLength=.12,pauseLengthScale=1.,outputSamplingRate=SR,outputStereo=False)
   data=req('/synthesis',{'speaker':2},q);path=ROOT/f'audio/raw/{i+1:02}.wav';path.write_bytes(data)
   wav,sr=sf.read(path,dtype='float32');assert sr==SR and wav.ndim==1
   # Read the query's real decoder-frame schedule, never allocate by character count.
   frame=round(q['prePhonemeLength']/q['speedScale']*93.75);first=frame
   ledger=[]
   for a in q['accent_phrases']:
    for m in a['moras']:
     st=frame
     if m.get('consonant'):frame+=round(m['consonant_length']/q['speedScale']*93.75)
     frame+=round(m['vowel_length']/q['speedScale']*93.75)
     ledger.append({'kana':m['text'],'start':st/93.75,'end':frame/93.75})
    if a.get('is_interrogative') and a['moras'][-1]['pitch']>0:frame+=round(.15/q['speedScale']*93.75)
    if a.get('pause_mora'):frame+=round(a['pause_mora']['vowel_length']/q['speedScale']*93.75)
   last=max(m['end'] for m in ledger)
   predicted=(frame+round(q['postPhonemeLength']/q['speedScale']*93.75))*512
   assert abs(predicted-len(wav))<=512,(i,predicted,len(wav))
   dur=len(wav)/SR
   cue={'id':i+1,'text':text,'en':en,'scene':scene,'audio_start':cursor,'start':cursor+first/93.75,'end':cursor+last,'audio_end':cursor+dur,'kana':q['kana'],'moras':ledger}
   cues.append(cue);pieces.append((cursor,wav));cursor+=dur+.10
   dump(ROOT/f'audio/raw/{i+1:02}_query.json',q)
   pron.append({'id':i+1,'text':text,'synthesis_text':spoken,'kana':q['kana'],'decoder_samples':predicted,'actual_samples':len(wav),'auditory_listening':False})
   print('VOICE',i+1,round(dur,3),q['kana'],flush=True)
  T=math.ceil((cursor+.28)*FPS)/FPS;n=round(T*SR);out=np.zeros(n,np.float32)
  for st,w in pieces:a=round(st*SR);out[a:a+len(w)]+=w
  sf.write(ROOT/'audio/narration.wav',out,SR,subtype='PCM_24')
  intervals=[]
  for c in cues:
   for m in c['moras']: intervals.append((c['audio_start']+m['start'],c['audio_start']+m['end']))
  intervals.sort();gaps=[intervals[0][0],T-intervals[-1][1]]+[max(0,b[0]-a[1]) for a,b in zip(intervals,intervals[1:])]
  boundaries=[0.]
  for s in range(1,10):
   c=next(c for c in cues if c['scene']==s);boundaries.append(c['audio_start']-.035)
  boundaries.append(T)
  dump(ROOT/'audio/pronunciation_review.json',{'voice':'VOICEVOX:四国めたん','style':2,'engine':'0.25.2','records':pron,'method':'Synthesis reading and decoder-frame inspection; no claim of human listening.'})
  timeline={'duration':T,'fps':FPS,'sample_rate':SR,'boundaries':boundaries,'cues':cues,'max_query_speech_gap':max(gaps),'source':'Actual generated audio and exact synthesis decoder times'}
  dump(ROOT/'timeline.json',timeline)
  return timeline,out
 finally:p.terminate();p.wait(timeout=20);log.close()

VERT='''#version 330
in vec3 pos;in vec3 normal;in vec4 m0;in vec4 m1;in vec4 m2;in vec4 m3;in vec4 color;in vec4 mat;
uniform mat4 vp;out vec3 P;out vec3 N;out vec4 C;out vec4 M;
void main(){mat4 m=mat4(m0,m1,m2,m3);vec4 p=m*vec4(pos,1);P=p.xyz;N=normalize(transpose(inverse(mat3(m)))*normal);C=color;M=mat;gl_Position=vp*p;}
'''
FRAG='''#version 330
in vec3 P;in vec3 N;in vec4 C;in vec4 M;uniform vec3 eye;uniform float t;out vec4 frag;
void main(){vec3 n=normalize(N),v=normalize(eye-P);float ndv=abs(dot(n,v));float rim=pow(1.-ndv,3.);vec3 l=normalize(vec3(-.6,.85,1.4));
float diffuse=max(0.,dot(n,l));float s=pow(max(0.,dot(reflect(-l,n),v)),mix(110.,12.,M.y));float fill=max(0.,dot(n,normalize(vec3(1.,-.1,.4))));
vec3 c=C.rgb*(.18+1.15*diffuse)+C.rgb*vec3(.08,.23,.45)*fill+vec3(.85,1.,1.05)*s*(1.-M.y)*.8+C.rgb*M.z;
float a=C.a;
if(M.x>1.5){float ripple=sin(P.x*12.+t*.8)*sin(P.y*9.-P.z*7.+t*.6);vec3 ir=mix(vec3(.12,.62,.75),vec3(.46,.24,.68),.5+.5*sin(ndv*10.+P.y*.3));c=ir*(.25+1.8*rim)+vec3(.45,.8,.92)*s*.45;c+=vec3(.08,.17,.22)*ripple*.16;a=C.a*(.10+.82*rim);}
frag=vec4(c,a);}
'''
QVERT='''#version 330
in vec2 p;out vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0,1);}
'''
BG='''#version 330
in vec2 uv;out vec4 frag;uniform float t;
float h(float x){return fract(sin(x*127.1)*43758.5453);}
void main(){vec2 q=uv-vec2(.5,.57);vec3 c=mix(vec3(.002,.007,.014),vec3(.014,.073,.095),exp(-dot(q*vec2(.7,1.),q*vec2(.7,1.))*7.));
float rays=pow(max(0.,sin(uv.x*13.+uv.y*3.+t*.13)),18.)*pow(uv.y,3.);c+=vec3(.012,.038,.043)*rays;
for(int i=0;i<24;i++){float k=float(i);vec2 a=vec2(h(k+1.),fract(h(k+42.)+t*.007*(.3+h(k+4.))));float r=.004+.019*h(k+7.);float b=exp(-dot(uv-a,uv-a)/(r*r));c+=vec3(.012,.033,.039)*b*(.1+.3*h(k+9.));}
frag=vec4(c,1);}
'''
POST='''#version 330
in vec2 uv;out vec4 frag;uniform sampler2D tex;
void main(){vec3 c=texture(tex,uv).rgb;vec3 b=vec3(0);vec2 d=1./vec2(textureSize(tex,0));for(int i=-2;i<=2;i++){b+=max(vec3(0),texture(tex,uv+vec2(float(i)*2.5*d.x,0)).rgb-.9);b+=max(vec3(0),texture(tex,uv+vec2(0,float(i)*2.5*d.y)).rgb-.9);}c+=b*.012;c*=1.-.12*smoothstep(.25,.8,length(uv-.5));c=clamp((c*(2.51*c+.03))/(c*(2.43*c+.59)+.14),0,1);frag=vec4(pow(c,vec3(1./2.2)),1);}
'''
def sphere_mesh(nx=24,ny=16,gap=0.,scale=(1,1,1)):
 th=np.linspace(gap,np.pi,ny+1);ph=np.linspace(0,2*np.pi,nx+1)
 a,b=np.meshgrid(th,ph,indexing='ij');n=np.stack([np.sin(a)*np.cos(b),np.cos(a),np.sin(a)*np.sin(b)],axis=-1).reshape(-1,3);sc=np.array(scale);v=n*sc;norm=n/sc;norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-8)
 vv=np.concatenate([v,norm],axis=1).astype('f4');ff=[]
 for j in range(ny):
  for i in range(nx):k=j*(nx+1)+i;l=k+nx+1;ff.extend([k,k+1,l,k+1,l+1,l])
 return vv,np.array(ff,'i4')
def cylinder_mesh():
 vv=[];ff=[]
 for z in [-.5,.5]:
  for i in range(17):a=2*np.pi*i/16;vv.append([np.cos(a),np.sin(a),z,np.cos(a),np.sin(a),0])
 for i in range(16):ff.extend([i,i+1,i+17,i+1,i+18,i+17])
 return np.array(vv,'f4'),np.array(ff,'i4')
def profile_mesh(q):
 x=np.linspace(-3.12,3.12,193);centers=np.array([-2.08,0,2.08]);lobes=np.max(1.04**2-(x[:,None]-centers[None,:])**2,axis=1)
 capsule=1.02**2-np.maximum(np.abs(x)-2.08,0)**2
 r=np.sqrt(np.maximum(0,(1-q)*capsule+q*lobes))
 volume=np.pi*np.trapezoid(r*r,x);r*=math.sqrt((3*4*np.pi/3*1.04**3)/max(volume,1e-8))
 ph=np.linspace(0,2*np.pi,49);dx=np.gradient(r,x);vv=[]
 for k,xx in enumerate(x):
  for a in ph:
   n=unit([-dx[k],np.cos(a),np.sin(a)]);vv.append([xx,r[k]*np.cos(a),r[k]*np.sin(a),*n])
 ff=[]
 for j in range(len(x)-1):
  for i in range(48):k=j*49+i;l=k+49;ff.extend([k,l,k+1,k+1,l,l+1])
 return np.array(vv,'f4'),np.array(ff,'i4'),x,r

CYAN=np.array([.10,.67,.79]);GOLD=np.array([.94,.51,.12]);WHITE=np.array([.73,.88,.91]);BLUE=np.array([.14,.39,.93]);TAIL=np.array([.49,.62,.68])
class Renderer:
 def __init__(self):
  self.c=moderngl.create_standalone_context(backend='egl',require=330);print('GL',self.c.info['GL_RENDERER'],flush=True)
  self.color=self.c.texture((W,H),4,dtype='f2');self.depth=self.c.depth_renderbuffer((W,H));self.f=self.c.framebuffer([self.color],self.depth);self.out=self.c.simple_framebuffer((W,H),3)
  self.p=self.c.program(vertex_shader=VERT,fragment_shader=FRAG);self.ib=self.c.buffer(reserve=4096*24*4);self.meshes={};self.dynamic=[]
  self.mesh('sphere',*sphere_mesh());self.mesh('large',*sphere_mesh(64,40));self.mesh('bar',*cylinder_mesh())
  qb=self.c.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes())
  self.bg=self.c.program(vertex_shader=QVERT,fragment_shader=BG);self.bgv=self.c.vertex_array(self.bg,[(qb,'2f','p')]);self.post=self.c.program(vertex_shader=QVERT,fragment_shader=POST);self.pv=self.c.vertex_array(self.post,[(qb,'2f','p')]);self.post['tex']=0
  self.font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';assert Path(self.font).exists();self.fonts={};self.label_cache={};self.reset()
 def mesh(self,name,v,idx,dynamic=False):
  if name in self.meshes:
   vao,vb,eb=self.meshes[name];vao.release();vb.release();eb.release()
  vb=self.c.buffer(v.tobytes());eb=self.c.buffer(idx.tobytes());va=self.c.vertex_array(self.p,[(vb,'3f 3f','pos','normal'),(self.ib,'4f 4f 4f 4f 4f 4f /i','m0','m1','m2','m3','color','mat')],eb);self.meshes[name]=(va,vb,eb)
 def reset(self):self.items=[];self.labels=[];self.content=[];self.clearances=[];self.eye=np.array([.6,2.2,20.]);self.target=np.array([0,.3,0]);self.semantic={}
 def add(self,name,center,scale,color=CYAN,alpha=1.,rotation=None,kind=0,rough=.25,emit=0):
  if alpha<.005:return
  m=np.eye(4);m[:3,:3]=(np.eye(3) if rotation is None else rotation)@np.diag(np.broadcast_to(scale,(3,)));m[:3,3]=center;self.items.append((name,m,np.array(color),alpha,[kind,rough,emit,0]))
 def ball(self,p,r,col=CYAN,**kw):self.add('sphere' if r<.6 else 'large',p,r,col,**kw)
 def bar(self,a,b,r=.04,col=TAIL,**kw):
  a=np.array(a);b=np.array(b);z=unit(b-a);x=unit(np.cross([0,1,0],z))
  if np.linalg.norm(x)<.1:x=unit(np.cross([1,0,0],z))
  y=np.cross(z,x);self.add('bar',(a+b)/2,[r,r,np.linalg.norm(b-a)],col,rotation=np.column_stack([x,y,z]),**kw)
 def lipid(self,head,direction,scale=1.,col=CYAN,phase=0.,tail_len=.58):
  head=np.asarray(head);d=unit(direction);side=unit(np.cross(d,[0,0,1]));self.ball(head,.15*scale,col,rough=.16)
  pts=[head+d*(.10*scale)]
  for j in range(1,5):pts.append(head+d*(.10+tail_len*j/4)*scale+side*.033*scale*np.sin(j*1.7+phase))
  for a,b in zip(pts,pts[1:]):self.bar(a,b,.044*scale,TAIL,rough=.34)
 def cargo(self,points,t,tag='cargo',emphasis=0):
  for i,p in enumerate(points):
   p=np.asarray(p,float);self.ball(p,.19,GOLD,rough=.13,emit=emphasis*.25);self.content.append((tag,i,p.tolist(),.19))
   # Paired bead detail is part of a single material symbol, not new material.
   self.ball(p+np.array([.12,.13,.03]),.075,[1.,.77,.30],rough=.2)
 def vesicle(self,center=(0,.6,0),r=2.,gap=0.,stretch=(1,1,1),double=False,heads=120,alpha=.78,phase=0.):
  # Surface and lipids share the exact same geometry and coordinates.
  sc=np.array(stretch)*r;self.mesh('shell',*sphere_mesh(64,40,gap,sc));self.add('shell',center,1,CYAN,alpha=alpha,kind=2)
  for i in range(heads):
   f=(i+.5)/heads;cy=-1+f*(1+np.cos(gap));ang=i*2.399963229728653;v=np.array([np.sqrt(max(0,1-cy*cy))*np.cos(ang),cy,np.sqrt(max(0,1-cy*cy))*np.sin(ang)])
   p=np.array(center)+sc*v;self.ball(p,.039,CYAN,rough=.2,emit=.08)
  if gap>.025:
   pts=[np.array(center)+sc*np.array([np.sin(gap)*np.cos(a),np.cos(gap),np.sin(gap)*np.sin(a)]) for a in np.linspace(0,2*np.pi,65)]
   for a,b in zip(pts,pts[1:]):self.bar(a,b,.032,WHITE,emit=.18)
  if double:
   self.mesh('inner',*sphere_mesh(64,40,gap,sc-.16));self.add('inner',center,1,[.1,.45,.63],alpha=.5,kind=2)
 def text(self,text,x,y,size=42,color=(237,247,249),alpha=255):self.labels.append((text,x,y,size,color,alpha))
 def frame(self,t,scene,cue):
  c=self.c;self.f.use();c.viewport=(0,0,W,H);self.f.clear(0,0,0,1,depth=1);c.disable(moderngl.DEPTH_TEST|moderngl.BLEND|moderngl.CULL_FACE);self.bg['t']=t;self.bgv.render(moderngl.TRIANGLE_STRIP)
  eye=self.eye;f=unit(self.target-eye);right=unit(np.cross(f,[0,1,0]));up=np.cross(right,f);v=np.eye(4);v[:3,:3]=[right,up,-f];v[:3,3]=-v[:3,:3]@eye
  k=1/np.tan(np.radians(37)/2);near=.1;far=100;p=np.zeros((4,4));p[0,0]=k/(W/H);p[1,1]=k;p[2,2]=(far+near)/(near-far);p[2,3]=2*far*near/(near-far);p[3,2]=-1
  self.vp=p@v;self.p['vp'].write(self.vp.T.astype('f4').tobytes());self.p['eye']=tuple(eye);self.p['t']=t
  c.enable(moderngl.DEPTH_TEST)
  for translucent in [False,True]:
   if translucent:c.enable(moderngl.BLEND);c.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA);self.f.depth_mask=False
   for name,(vao,_,_) in self.meshes.items():
    rows=[]
    for n,m,col,a,mat in self.items:
     if n==name and (a<.995)==translucent:rows.append([*m.T.reshape(-1),*col,a,*mat])
    if rows:self.ib.write(np.array(rows,'f4').tobytes());vao.render(instances=len(rows))
   if translucent:self.f.depth_mask=True;c.disable(moderngl.BLEND)
  c.disable(moderngl.DEPTH_TEST);self.out.use();self.color.use(0);self.pv.render(moderngl.TRIANGLE_STRIP)
  img=Image.frombytes('RGB',(W,H),self.out.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  raw=img.copy();d=ImageDraw.Draw(img,'RGBA')
  self.drawtext(d,'平穏暦全史  ／  前史064',540,142,29,(205,225,233,255))
  d.rounded_rectangle((474,192,606,196),radius=2,fill=(117,215,238,200))
  self.drawtext(d,HEADINGS[scene],540,308,49,(238,248,250,255))
  for text,x,y,size,col,a in self.labels:self.drawtext(d,text,x,y,size,(*col,a))
  footer='脂肪酸膜の模式表現  ·  大きさと時間を圧縮'
  if scene in [4,5,6]:footer='多層の脂肪酸膜を使った模型実験の模式化'
  self.drawtext(d,footer,540,1790,25,(157,187,199,235))
  if cue:
   st=cue['start'];en=cue['end'];op=min(smooth(t,st-.07,st+.08),1-smooth(t,en+.04,en+.16));rise=16*(1-smooth(t,st-.07,st+.11));lines=self.wrap(cue['text'],64,880)
   assert len(lines)<=2,lines
   cy=1548+rise;boxh=len(lines)*85+38
   d.rounded_rectangle((74,cy-boxh/2,1006,cy+boxh/2),radius=18,fill=(3,14,24,int(210*op)))
   d.rounded_rectangle((100,cy-boxh/2+18,105,cy+boxh/2-18),radius=2,fill=(117,215,238,int(210*op)))
   for j,line in enumerate(lines):self.drawtext(d,line,552,cy+(j-(len(lines)-1)/2)*85,64,(242,247,248,int(255*op)))
  return img,raw
 def fontobj(self,n):
  if n not in self.fonts:self.fonts[n]=ImageFont.truetype(self.font,n,index=0)
  return self.fonts[n]
 def drawtext(self,d,text,x,y,size,col):d.text((x,y),text,font=self.fontobj(size),fill=col,anchor='mm',stroke_width=1,stroke_fill=(1,7,11,col[3]))
 def wrap(self,text,size,maxw):
  font=self.fontobj(size)
  if font.getlength(text)<=maxw:return [text]
  candidates=[i for i in range(1,len(text)) if font.getlength(text[:i])<=maxw and font.getlength(text[i:])<=maxw and text[i] not in '、。！？ー']
  if not candidates:raise RuntimeError('Caption too long: '+text)
  i=min(candidates,key=lambda x:abs(font.getlength(text[:x])-font.getlength(text[x:]))-(60 if text[x-1] in '、' else 0));return [text[:i],text[i:]]

BASE_CARGO=np.array([[-.65,.05,.20],[-.48,-.55,-.12],[.25,-.52,.18],[.64,.05,-.12],[.12,.59,.0],[-.45,.56,-.10]])
def safe_cargo(r,pts,center,axes,t,tag,emphasis=0):
 pts=np.asarray(pts);center=np.asarray(center);axes=np.asarray(axes)
 for p in pts:
  relative=np.linalg.norm((p-center)/(axes-.27));assert relative<1.,(tag,relative,p,center,axes)
  r.clearances.append(float(1-relative))
 r.cargo(pts,t,tag,emphasis)
def arrange(r,s,u,t,split):
 center=np.array([0,.65,0]);r.semantic={'scene':s,'u':round(u,5)}
 # World particles are kept behind the main subject; they are never pacing evidence.
 for i in range(20):
  x=4.6*np.sin(i*2.3+t*.06);y=5.8*np.cos(i*1.8+t*.04);z=-5.5-(i%4)*.8;r.ball([x,y,z],.025+(i%3)*.012,[.12,.27,.31],rough=.65)
 if s==0:
  q=smooth(u,.03,.43);gap=1.35*(1-q);rad=2.*np.sqrt(2/(1+np.cos(gap)))
  r.eye=np.array([.4+.7*q,2.8,19.]);r.vesicle(center,rad,gap,heads=150)
  pts=center+BASE_CARGO*(1+.05*np.sin(t*1.8));safe_cargo(r,pts,center,[2,2,2],t,'enclosed')
  if q>.8:r.text('外側',230,590,38,(149,211,229));r.text('内側',550,1190,42,(255,207,116))
  r.semantic.update(opening=gap,retained_materials=6)
 elif s==1:
  r.eye=np.array([2.7,2.3,18.5]);q=smooth(u,.1,.85)
  for i in range(7):
   x=(i-3)*.77;offset=(1-smooth(u,i*.045,.30+i*.045))*(2.1 if i%2 else -2.1)
   head=np.array([x,1.6+offset,.32*np.sin(i)])
   r.lipid(head,[.10*np.sin(t+i),-1,.04],1.3,phase=t*.8+i)
  r.text('脂肪酸',540,1230,48,(117,215,238));r.semantic.update(assembly=q)
 elif s==2:
  r.eye=np.array([3.,3.3,20.]);phase=0 if u<split else 1
  for layer in [-1,1]:
   for j in range(4):
    for i in range(8):
     x=(i-3.5)*.62;z=(j-1.5)*.53;head=np.array([x,center[1]+layer*1.03,z]);direction=np.array([.08*np.sin(t+i+j),-layer,.03*np.cos(t+j)])
     r.lipid(head,direction,1.,CYAN if phase==0 else CYAN*.64,phase=t*.4,tail_len=.69)
  for i in range(12):
   p=[-3.1+(i%6)*1.07+.22*np.sin(t+i),center[1]+(2.02 if i<6 else -2.02),.35*np.cos(t+i)]
   r.ball(p,.12,BLUE,emit=.16)
  r.text('水',210,610,39,(117,215,238));r.text('水',850,1260,39,(117,215,238))
  r.text('水になじむ頭' if phase==0 else '水を避ける尾',540,1370,42,(117,215,238) if phase==0 else (235,220,175))
  r.semantic.update(active_part='heads' if phase==0 else 'tails')
 elif s==3:
  q=smooth(u,.12,.9);gap=1.5*(1-q);rad=1.95*np.sqrt(2/(1+np.cos(gap)))
  r.eye=np.array([3.1*(1-q)+.9,3.5,19.7]);r.vesicle(center,rad,gap,double=True,heads=160)
  safe_cargo(r,center+BASE_CARGO,center,[1.95]*3,t,'enclosed')
  r.text('頭は、袋の外側にも内側にも',540,1330,35,(173,222,233))
  r.semantic.update(opening=gap)
 elif s==4:
  q=smooth(u,.10,.95);sx=1+q*.85;rad=1.57;sc=np.array([sx,1/np.sqrt(sx),1/np.sqrt(sx)])
  r.eye=np.array([.4,2.,21.5]);r.vesicle(center,rad,stretch=sc,double=True,heads=100+int(q*70))
  for i in range(11):
   f=((u*1.65+i/11)%1);a=np.array([-4.8,2.5-.36*i,.3]);b=center+np.array([-rad*sx*.83,.48*np.sin(i),.46*np.cos(i)])
   p=lerp(a,b,ease(f));r.lipid(p,unit(center-p),.5,phase=t+i)
  pts=center+BASE_CARGO*np.array([sx,.68,.68]);safe_cargo(r,pts,center,rad*sc,t,'elongating')
  r.text('膜の材料を追加',540,1280,42,(117,215,238));r.semantic.update(surface_feed=q,stretch=sx)
 elif s==5:
  r.eye=np.array([.25,2.1,22.]);q=smooth(u,max(.12,split-.08),.94)
  vv,idx,x,radius=profile_mesh(q);r.mesh('division',vv,idx);r.add('division',center,1,CYAN,alpha=.86,kind=2)
  for i in range(130):
   xx=-3.0+6*((i+.5)/130);rr=float(np.interp(xx,x,radius));a=i*2.39996
   if rr>.06:r.ball(center+[xx,rr*np.cos(a),rr*np.sin(a)],.04,CYAN,emit=.08)
  pts=[]
  for ci in [-2.08,0,2.08]:
   for yy in [-.32,.32]:pts.append(center+[ci+.10*np.sin(t),yy,.09*np.cos(t+ci)])
  for p in pts:
   local=p-center;rr=float(np.interp(local[0],x,radius));clear=rr-np.linalg.norm(local[1:])-.27;assert clear>.05; r.clearances.append(clear)
  r.cargo(pts,t,'division_contents')
  # Opposite fluid lanes: movement is a gentle shear, not a pair of solid cutting blades.
  for lane in [-1,1]:
   for i in range(5):
    xx=(((t*.6+i*.85)*lane+4)%8)-4;y=center[1]+lane*1.9;r.bar([xx-.27*lane,y,-.3],[xx+.27*lane,y,-.3],.027,BLUE,emit=.25)
  r.text('穏やかな水の動き',540,1280,41,(117,215,238));r.semantic.update(neck_closing=q,retained_materials=6)
 elif s==6:
  r.eye=np.array([.25,2.0,22.]);sep=2.16+.30*smooth(u,0,.9)
  for j in range(3):
   c=center+np.array([(j-1)*sep,.15*np.sin(t*.6+j),0]);rr=.98;r.vesicle(c,rr,heads=55,alpha=.75)
   pts=c+np.array([[.08,-.31,.12],[-.09,.31,-.10]])+np.array([.05*np.sin(t*1.6+j),0,0]);safe_cargo(r,pts,c,[rr]*3,t,'daughter'+str(j),.5+.5*np.sin(t*2+j))
  assert sep-1.96>=.19;r.clearances.append(sep-1.96)
  r.text('同じ材料が、分かれて残る',540,1320,41,(255,207,116));r.semantic.update(daughter_distance=sep,retained_materials=6)
 elif s==7:
  r.eye=np.array([1.6,2.4,19.]);r.vesicle(center,2.08,heads=130)
  pts=center+BASE_CARGO*(.95+.06*np.sin(t*1.4));safe_cargo(r,pts,center,[2.08]*3,t,'retained')
  for i in range(5):
   f=(u*1.5+i*.21)%1.;xx=-3.5+7*f;y=center[1]+(-.9+i*.46);p=np.array([xx,y,.35]);r.ball(p,.105,BLUE,rough=.12,emit=.2)
   for j in range(1,4):r.ball(p+[-j*.13,0,0],.035,BLUE,emit=.2)
  r.text('通りやすさは、分子と膜で変わる',540,1310,35,(176,217,229));r.semantic.update(exchange_progress=u,retained_materials=6,allowed_membrane_crossings='blue permeation symbols only')
 elif s==8:
  r.eye=np.array([.4,2.1,21.]);r.bar([0,-1.8,-.1],[0,3.2,-.1],.016,[.12,.25,.30])
  for j,xx in enumerate([-1.85,1.85]):
   c=center+[xx,0,0];r.vesicle(c,1.35,heads=75)
   pts=c+BASE_CARGO[:3]*.70+np.array([.07*np.sin(t*2),0,0]);safe_cargo(r,pts,c,[1.35]*3,t,'function'+str(j))
   if j==1:
    for i in range(3):
     f=(u*1.7+i*.3)%1;p=c+[-2.3+4.6*f,-.55+i*.55,.35];r.ball(p,.10,BLUE,emit=.25)
  r.text('保つ',280,1270,45,(255,207,116));r.text('交換する',800,1270,45,(117,215,238));r.clearances.append(.9);r.semantic.update(exchange_progress=u)
 else:
  r.eye=np.array([.8+u*.5,2.2,19.8]);r.vesicle(center,2.15,heads=150)
  pts=center+BASE_CARGO*(.9+.1*np.sin(t*1.25));safe_cargo(r,pts,center,[2.15]*3,t,'future_reactions')
  for i in range(4):
   a=t*.8+i*1.57;p=center+np.array([1.28*np.cos(a),.98*np.sin(a),.20*np.sin(t+i)]);r.ball(p,.10,BLUE,emit=.2)
  r.text('境界の次は、続く反応へ',540,1320,40,(117,215,238));r.semantic.update(internal_motion=float(np.sin(t*1.25)))


def music(timeline,narration):
 T=timeline['duration'];n=len(narration);tt=np.arange(n,dtype=np.float64)/SR;rng=np.random.default_rng(6402);bg=np.zeros((n,2),np.float32)
 # Original synthesized score. No samples or third-party music are used.
 chords=[[146.832,220.,293.665,349.228],[130.813,195.998,261.626,329.628],[174.614,261.626,349.228,440.],[164.814,246.942,329.628,391.995]]
 for ci in range(4):
  start=ci*T/4;end=(ci+1)*T/4;env=np.clip((tt-start)/1.2,0,1)*np.clip((end+1-tt)/1.6,0,1)
  for j,f in enumerate(chords[ci]):
   tone=(np.sin(2*np.pi*f*tt)+.23*np.sin(2*np.pi*f*2.003*tt)+.10*np.sin(2*np.pi*f*3*tt))*env*.006
   bg[:,0]+=tone*(.9+.1*np.sin(j));bg[:,1]+=tone*(.9+.1*np.cos(j))
 for beat,st in enumerate(np.arange(.20,T,.55)):
  a=round(st*SR);ln=min(round(.34*SR),n-a);x=np.arange(ln)/SR;f=chords[min(3,int(st/(T/4)))][beat%4]*2
  env=np.exp(-x*13)*(1-np.exp(-x*95));tone=np.sin(2*np.pi*f*x)*env*.017
  bg[a:a+ln,beat%2]+=tone;bg[a:a+ln,1-beat%2]+=tone*.55
 events=[]
 for s in range(10):
  a,b=timeline['boundaries'][s:s+2];st=a+(b-a)*(.38 if s in [0,3] else .65);at=round(st*SR);ln=min(round(.65*SR),n-at);x=np.arange(ln)/SR
  noise=rng.normal(0,1,ln);noise=sosfilt(butter(2,[280,3600],btype='bandpass',fs=SR,output='sos'),noise);env=np.sin(np.pi*np.minimum(1,x/.65))**2
  effect=noise*env*.025+np.sin(2*np.pi*(85*x+20*x*x))*np.exp(-x*9)*.06
  bg[at:at+ln]+=effect[:,None];events.append({'scene':s,'time':st,'kind':'soft material impact and airless design sweep'})
 # Voice-keyed ducking is built from actual synthesis timings.
 gain=np.ones(n,np.float32)
 for c in timeline['cues']:
  a=max(0,round((c['start']-.10)*SR));b=min(n,round((c['end']+.12)*SR));gain[a:b]=.35
 gain=np.convolve(gain[::480],np.ones(9)/9,mode='same');gain=np.interp(np.arange(n),np.arange(len(gain))*480,gain).astype('f4')
 bg*=gain[:,None];fade=np.clip(tt/.25,0,1)*np.clip((T-tt)/.4,0,1);bg*=fade[:,None]
 sf.write(ROOT/'audio/music_and_effects.wav',bg,SR,subtype='PCM_24');sf.write(ROOT/'audio/mix_premaster.wav',bg+narration[:,None],SR,subtype='PCM_24');dump(ROOT/'audio/sound_events.json',events)
 first=subprocess.run(['ffmpeg','-v','info','-i',str(ROOT/'audio/mix_premaster.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 measurement=json.loads(first.stderr[first.stderr.rfind('{'):first.stderr.rfind('}')+1]);dump(ROOT/'audio/loudness_first_pass.json',measurement)
 filt='loudnorm=I=-16:TP=-1.5:LRA=9:linear=true:measured_I={input_i}:measured_LRA={input_lra}:measured_TP={input_tp}:measured_thresh={input_thresh}:offset={target_offset}'.format(**measurement)
 run(['ffmpeg','-y','-v','error','-i',str(ROOT/'audio/mix_premaster.wav'),'-af',filt,'-ar',str(SR),'-c:a','pcm_s24le',str(ROOT/'audio/master.wav')])

def ts(x,ass=False):
 if ass:
  h=int(x//3600);m=int(x//60)%60;s=int(x)%60;return f'{h}:{m:02}:{s:02}.{int(x%1*100):02}'
 ms=round(x*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def subtitles(timeline,r):
 out=ROOT/'deliverables';ja=[];en=[];ass=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','WrapStyle: 2','ScaledBorderAndShadow: yes','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding','Style: Default,Noto Sans CJK JP,64,&H00F8F7F2,&H00EED775,&HBB180E03,&HBB180E03,1,0,0,0,100,100,0,0,3,14,0,5,70,70,200,1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 for c in timeline['cues']:
  a=max(0,c['start']-.07);b=c['end']+.16;lines=r.wrap(c['text'],64,880);j='\n'.join(lines);ja.append(f"{c['id']}\n{ts(a)} --> {ts(b)}\n{j}\n");en.append(f"{c['id']}\n{ts(a)} --> {ts(b)}\n{c['en']}\n")
  at='{\\move(552,1564,552,1548,0,180)\\fad(140,120)}'+r'\N'.join(lines);ass.append(f'Dialogue: 0,{ts(a,True)},{ts(b,True)},Default,,0,0,0,,{at}')
 (out/'heionreki_p064_v2_ja.srt').write_text('\n'.join(ja),encoding='utf-8');(out/'heionreki_p064_v2_en.srt').write_text('\n'.join(en),encoding='utf-8');(out/'heionreki_p064_v2_ja.ass').write_text('\n'.join(ass),encoding='utf-8')

def render(timeline):
 r=Renderer();subtitles(timeline,r);T=timeline['duration'];N=round(T*FPS);path=ROOT/'render/native_picture.mp4';log=(ROOT/'review/render_ffmpeg.log').open('w')
 p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','3',str(path)],stdin=subprocess.PIPE,stderr=log)
 stats=[];prev=None;prevtiny=None;frames=[];minclear=1e9;positions=[]
 try:
  for f in range(N):
   t=f/FPS;s=min(9,int(np.searchsorted(timeline['boundaries'],t,side='right')-1));a,b=timeline['boundaries'][s:s+2];u=(t-a)/(b-a)
   scene_cues=[c for c in timeline['cues'] if c['scene']==s];split=(scene_cues[1]['start']-a)/(b-a)
   cue=next((c for c in timeline['cues'] if c['start']-.07<=t<=c['end']+.16),None)
   r.reset();arrange(r,s,u,t,split);im,raw=r.frame(t,s,cue);p.stdin.write(im.tobytes())
   tiny=np.asarray(raw.crop((85,400,995,1390)).resize((182,198)),dtype=np.int16)
   delta=float(np.mean(np.abs(tiny-prevtiny))) if prevtiny is not None else 0.;prevtiny=tiny
   if r.clearances:minclear=min(minclear,min(r.clearances))
   stats.append({'frame':f,'scene':s,'time':t,'raw_subject_mean_delta':delta,'min_clearance':min(r.clearances) if r.clearances else None,'semantic':r.semantic,'cargo_count':len(r.content)})
   if f%24==0:print('RENDER',f,'/',N,'scene',s,'delta',round(delta,4),flush=True)
   fractions=[.15,.45,.78]
   if any(abs(u-q)<.51/(FPS*(b-a)) for q in fractions):
    name=f'scene_{s+1:02}_{f:04}.jpg';im.save(ROOT/'review'/name,quality=94);frames.append((s,f,name))
  p.stdin.close();rc=p.wait();assert rc==0
 finally:log.close()
 assert N>0
 # Pixel evidence is a flagging aid, not a claim to have watched the film.
 vals=np.array([x['raw_subject_mean_delta'] for x in stats]);windows=np.convolve(vals,np.ones(48),mode='valid')/48 if len(vals)>=48 else vals
 report={'frames':N,'native_resolution':[W,H],'fps':FPS,'actual_3d_mesh_renderer':r.c.info['GL_RENDERER'],'all_retained_cargo_inside_checked_boundaries':True,'minimum_normalized_or_world_clearance':minclear,'separate_daughters_positive_gap':True,'same_daughter_material_count':6,'intended_intersections':['Bond joins within one molecule','Blue permeation symbols cross the membrane','Supplied amphiphiles join a growing membrane','Connected membrane necks before fission'],'minimum_2second_raw_subject_mean_frame_change':float(windows.min()),'weak_windows_threshold_0_015':[int(i) for i,v in enumerate(windows) if v<.015],'not_counted_as_motion':'Subtitle changes and background are excluded by cropping, but camera contributions cannot be perfectly separated from pixel differences. Semantic scene parameters are also recorded.','human_continuous_viewing_performed':False,'frames_written_for_visual_review':len(frames)}
 dump(ROOT/'review/motion_and_spacing.json',report);dump(ROOT/'review/frame_states.json',stats);dump(ROOT/'review/frame_manifest.json',frames)
 # A contact sheet is shipped for transparent visual review.
 sheet=Image.new('RGB',(5*216,6*384),(7,17,25))
 for i,(_,_,name) in enumerate(frames[:30]):sheet.paste(Image.open(ROOT/'review'/name).resize((216,384)),((i%5)*216,(i//5)*384))
 sheet.save(ROOT/'review/contact_sheet.jpg',quality=92)
 return path,report

def finalise(timeline,video,report):
 d=ROOT/'deliverables';high=d/'heionreki_p064_v2_high_1080x1920.mp4';light=d/'heionreki_p064_v2_light_720x1280.mp4'
 run(['ffmpeg','-y','-v','error','-i',str(video),'-i',str(ROOT/'audio/master.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar',str(SR),'-movflags','+faststart','-t',str(timeline['duration']),str(high)])
 run(['ffmpeg','-y','-v','error','-i',str(high),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','fast','-crf','24','-threads','3','-c:a','copy','-movflags','+faststart',str(light)])
 media={}
 for path in [high,light]:
  run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'])
  probe=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-show_format','-of','json',str(path)]));media[path.name]=probe
  vs=next(s for s in probe['streams'] if s['codec_type']=='video');assert int(vs['nb_frames'])==round(timeline['duration']*FPS);assert any(s['codec_type']=='audio' for s in probe['streams'])
 loud=subprocess.run(['ffmpeg','-v','info','-i',str(high),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);lm=json.loads(loud.stderr[loud.stderr.rfind('{'):loud.stderr.rfind('}')+1]);dump(ROOT/'review/export_loudness.json',lm);dump(ROOT/'review/final_media.json',media)
 notes=f'''平穏暦全史・前史064 第2版\n{TITLE}\n\n制作日：2026-10-27\n再制作の範囲：旧064のファイルは回収できず、新しい台本・原音・立体模型・編集で再構成。063の声の条件、2秒以上の停滞を避ける方針、模型の間隔確認を継承。\n\n仕様：{timeline['duration']:.3f}秒、1080×1920を直接描画、24fps、{round(timeline['duration']*FPS)}コマ。軽量版720×1280。日本語焼き込み字幕、原音、音楽・効果音、日英字幕。\n\n問い：膜の境界ができると、何が変わる？\n持ち帰る発見：内側に材料を保ちながら、外との交換も行える。境界を作る機能から、次回の反応の継続へ。\n\n台本：\n'''
 for text,en,s in PARTS:notes+=text+'\n'
 notes+='\n科学と演出の区別：\n・閉じる膜は、両親媒性分子の配置を示す説明模型。特定の古代細胞の復元ではない。\n・脂肪酸の模型は一つの頭と一本の尾。現代の二本鎖リン脂質と混同しない。頭は袋の外の水と内の水の双方を向く。\n・成長・分裂場面は、外から膜材料を与え、多層の脂肪酸膜の袋を穏やかな水のせん断で分けた実験を模式化。膜の層数・寸法・速度・娘袋の個数は説明用に簡略化。\n・黄色は内部に保持する材料の記号。6個を3個の袋へ2個ずつ割り振るのは、同じ材料を追うための演出。実験の分配比を測った図ではない。\n・青は膜を通過する一部の分子の記号。透過性は膜の組成と分子の性質に依存し、全ての小分子が通るという意味ではない。\n・成長・分裂と透過性の説明は、同一実験で生命の全機能が完成したという主張ではない。\n・膜の閉鎖・尾の内向き配向・外部供給・伸長・水の動き・くびれ・分離・受け渡し・交換を主な視覚変化として設計。\n\n出典（2026-10-27確認）：\n'
 for src in SOURCES:notes+=src['id']+' '+src['title']+'\n'+src['url']+'\nDOI: '+src['doi']+'\n'+src['use']+'\n\n'
 notes+=f"音声：VOICEVOX 四国めたん・ノーマル。エンジン0.25.2、コア0.16.1。速度1.03。尾＝お、二重＝にじゅうを生成用文字で指定。全区間の読みをquery記録へ保存。生成結果の復号、発話時刻、合成クエリと音声長を照合。耳による聴感検査は未実施。\n最長の発話空白（合成クエリ時刻基準）：{timeline['max_query_speech_gap']:.3f}秒。\n書出し後測定：{lm['input_i']} LUFS、{lm['input_tp']} dBTP。\n\n検証：完成2本を全編復号。コマ数・寸法・音声有無・字幕区間を確認。全コマの保持材料と境界の座標、分離後の袋の間隔を確認。透過粒子・結合点など意図した交差は別扱い。画面差分は字幕を除いた主役領域から集計。代表30画面と一覧画像を同梱。自動検査は、目視・通し試写・耳の試聴の代わりにはならず、今回はそれらを実施済みとは記載しない。\n\n音楽・効果音：本作専用の数式合成。外部楽曲不使用。\n書体：環境のNoto Sans CJK JP。フォントファイルは配布物に含めない。\n再生成：source/p064_v2_film.py と制作実行条件を参照。声のエンジン・モデル・フォントは外部依存として別途取得。\n"
 (d/'heionreki_p064_v2_script_and_sources.txt').write_text(notes,encoding='utf-8');dump(ROOT/'docs/sources.json',SOURCES)
 shutil.copy(__file__,ROOT/'source/p064_v2_film.py')
 (ROOT/'source/requirements.txt').write_text('numpy\nscipy\nPillow\nmoderngl==5.12.0\nglcontext==3.0.0\nsoundfile\n')
 manifest=[]
 for p in sorted(ROOT.rglob('*')):
  if p.is_file() and 'voice_data' not in p.parts and p.suffix not in ['.ttf','.otf','.ttc']:
   manifest.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 dump(ROOT/'review/manifest.json',manifest)
 archive=d/'heionreki_p064_v2_production.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
  for p in sorted(ROOT.rglob('*')):
   if p.is_file() and p!=archive and 'voice_data' not in p.parts and p.suffix not in ['.ttf','.otf','.ttc'] and p.name not in ['native_picture.mp4','mix_premaster.wav']:z.write(p,'HEION-P064-v2/'+str(p.relative_to(ROOT)))
 dump(ROOT/'review/delivery_summary.json',{'duration':timeline['duration'],'frames':round(timeline['duration']*FPS),'speech_gap':timeline['max_query_speech_gap'],'loudness':lm,'files':[{'name':p.name,'bytes':p.stat().st_size} for p in d.iterdir()],'motion_report':report})
 print('DELIVERY_SUMMARY', (ROOT/'review/delivery_summary.json').read_text(),flush=True)
if __name__=='__main__':
 timeline,narration=voice();music(timeline,narration);video,report=render(timeline);finalise(timeline,video,report)
