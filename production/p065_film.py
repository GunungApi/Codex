"""P065: original explanatory 3-D animation, not an experiment or molecular dynamics.
Reuses only the verified narration, text and mesh-rendering infrastructure from P064.
"""
from pathlib import Path
import os,sys,types,math,json,shutil,subprocess,zipfile,hashlib
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','3')
os.environ.setdefault('OMP_NUM_THREADS','3')
import numpy as np
from PIL import Image,ImageDraw
import soundfile as sf
BASE=Path(__file__).with_name('p064_v2_film.py')
source=BASE.read_text().replace("Path('p064_v2')","Path('p065_v1')").replace('前史064','前史065').replace('脂肪酸膜の模式表現  ·  大きさと時間を圧縮','熱水と鉱物の模式図  ·  時間と縮尺を圧縮').replace('多層の脂肪酸膜を使った模型実験の模式化','分子・電子は説明用の記号')
b=types.ModuleType('p065_infrastructure');sys.modules[b.__name__]=b
exec(compile(source,str(BASE),'exec'),b.__dict__)
R=b.ROOT;FPS=24;SR=48000;W=1080;H=1920
PREFIX='heionreki_p065_v1'
PARTS=[
('熱い水があるだけで、','Is hot water alone enough',0),
('反応は、ずっと続く？','to keep a reaction going?',0),
('見よう。熱水と、周りの海水。','Look at the vent fluid and the surrounding seawater.',1),
('中にある材料が違う。','They contain different chemical ingredients.',1),
('電子を渡す側と、受け取る側。','An electron-donating side and an accepting side.',2),
('この化学的な差が、反応を動かす。','Chemical disequilibrium can drive reactions.',2),
('間にあるのは、電気を通す鉱物。','Between them is electrically conducting mineral.',3),
('電子が、その中を移動する。','Electrons move through it.',3),
('鉱物の表面で、材料が変わる。','Reactions change ingredients at mineral surfaces.',4),
('こうした働きが、実験で調べられている。','Such processes are being investigated in experiments.',4),
('では、新しい水の供給を止めよう。','Now stop the supply of fresh fluid.',5),
('残った材料は、少しずつ使われる。','The remaining reactants are gradually consumed.',5),
('混ざって、差も小さくなる。','Mixing also reduces the chemical difference.',6),
('それを使う反応は、弱まっていく。','The reactions driven by that difference weaken.',6),
('一方、流れが続く場所では、','Where flow continues, however,',7),
('新しい材料が入り、できたものが出る。','fresh ingredients enter and products leave.',7),
('供給を止めると、弱まる。','Without replenishment, the driving force weakens.',8),
('供給が続くと、差を保てる。','Continued replenishment can maintain it.',8),
('生命につながる化学を、支えるのは、','Chemistry relevant to life can be sustained by',9),
('反応を動かし続ける、つながった流れ。','connected flows that keep reactions going.',9)]
HEADINGS=['熱いだけで、続く？','同じ水でも、中身が違う','反応を動かす「化学的な差」','鉱物を通って、電子が動く','境界で、材料が変わる','新しい供給を、止めると？','混ざる。差が、小さくなる','流れが、差を作り直す','止める世界・続く世界','反応を支える、つながった流れ']
b.PARTS=PARTS;b.HEADINGS=HEADINGS;b.TITLE='反応を続けるには、「差」がいる'
# Explicit phonetic spellings only in the TTS input; subtitles retain proper kanji.
spoken_replace={"spoken=text.replace('尾は','おは').replace('二重に','にじゅうに')":"spoken=text.replace('熱水','ねっすい').replace('鉱物','こうぶつ').replace('供給','きょうきゅう').replace('海水','かいすい')"}
# Recompile just the voice function to keep its verified decoder timing calculation.
vsrc=source[source.index('def voice():'):source.index("VERT='''")]
for old,new in spoken_replace.items():vsrc=vsrc.replace(old,new)
exec(compile(vsrc,'p065_voice','exec'),b.__dict__)
CYAN=np.array([.16,.70,.91]);AMBER=np.array([1.,.48,.09]);GREEN=np.array([.20,.91,.63]);PALE=np.array([.90,.95,1.]);ROCK=np.array([.19,.25,.28])
SOURCES=[
{'id':'S1','title':'Kitadai et al. (2019), Metals likely promoted protometabolism in early ocean alkaline hydrothermal systems','doi':'10.1126/sciadv.aav7848','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6584212/','use':'Laboratory evidence for electrochemical mineral conversion and promotion of organic reactions; proposed early hydrothermal setting.'},
{'id':'S2','title':'Kitadai et al. (2018), Geoelectrochemical CO production: Implications for the autotrophic origin of life','doi':'10.1126/sciadv.aao7265','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC5884689/','use':'Laboratory electroreduction of carbon dioxide on selected sulfides under specified electrochemical conditions.'},
{'id':'S3','title':'JAMSTEC / Tokyo Institute of Technology, 2019-06-21 research announcement','url':'https://www.jamstec.go.jp/j/about/press_release/20190621/','use':'Primary institutional description distinguishing experiments from a proposed origin-of-life environment.'}]
CAPTIONS={
PARTS[2][0]:['見よう。熱水と、','周りの海水。'],PARTS[4][0]:['電子を渡す側と、','受け取る側。'],PARTS[5][0]:['この化学的な差が、','反応を動かす。'],PARTS[6][0]:['間にあるのは、','電気を通す鉱物。'],PARTS[9][0]:['こうした働きが、','実験で調べられている。'],PARTS[10][0]:['では、新しい水の','供給を止めよう。'],PARTS[11][0]:['残った材料は、','少しずつ使われる。'],PARTS[13][0]:['それを使う反応は、','弱まっていく。'],PARTS[15][0]:['新しい材料が入り、','できたものが出る。'],PARTS[18][0]:['生命につながる化学を、','支えるのは、'],PARTS[19][0]:['反応を動かし続ける、','つながった流れ。']}
original_wrap=b.Renderer.wrap
def wrap(self,text,size,maxw):
 if text in CAPTIONS:return CAPTIONS[text]
 return original_wrap(self,text,size,maxw)
b.Renderer.wrap=wrap
# Mineral texture varies in three dimensions and remains fixed to each mesh.
b.FRAG=b.FRAG.replace('float a=C.a;', '''if(M.x>.5 && M.x<1.5){float grain=sin(P.x*31.+sin(P.z*23.))*sin(P.y*27.+P.z*17.);float strata=.5+.5*sin(P.y*14.+sin(P.x*4.)+P.z*3.);c*=.70+.20*strata+.10*grain;c+=vec3(.12,.075,.02)*pow(max(0.,grain),12.);}\nfloat a=C.a;''')

def boxmesh():
 v=[];ind=[]
 faces=[([1,0,0],[(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5),(.5,-.5,.5)]),([-1,0,0],[(-.5,-.5,.5),(-.5,.5,.5),(-.5,.5,-.5),(-.5,-.5,-.5)]),([0,1,0],[(-.5,.5,-.5),(-.5,.5,.5),(.5,.5,.5),(.5,.5,-.5)]),([0,-1,0],[(-.5,-.5,.5),(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5)]),([0,0,1],[(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]),([0,0,-1],[(.5,-.5,-.5),(-.5,-.5,-.5),(-.5,.5,-.5),(.5,.5,-.5)])]
 for n,pts in faces:
  j=len(v);v += [[*p,*n] for p in pts];ind += [j,j+1,j+2,j,j+2,j+3]
 return np.array(v,'f4'),np.array(ind,'i4')
def chimney_mesh():
 vv=[];ff=[];N=56;J=32
 for j in range(J+1):
  y=-2.5+5*j/J;rad=.53+.12*np.sin(j*.6)+.36*(1-j/J)**2
  for i in range(N+1):
   a=2*np.pi*i/N;rr=rad*(1+.09*np.sin(a*7+j*.65)+.045*np.sin(a*17-j*.7));vv.append([rr*np.cos(a),y,rr*np.sin(a),np.cos(a),.10,np.sin(a)])
 for j in range(J):
  for i in range(N):k=j*(N+1)+i;z=k+N+1;ff.extend([k,z,k+1,k+1,z,z+1])
 return np.array(vv,'f4'),np.array(ff,'i4')
class Scene(b.Renderer):
 def __init__(self):
  super().__init__();self.mesh('slab',*boxmesh());self.mesh('chimney',*chimney_mesh());v,idx=b.sphere_mesh(18,12);p=v[:,:3];noise=1+.16*np.sin(p[:,0]*13+p[:,1]*9)*np.sin(p[:,2]*11-p[:,1]*7);v[:,:3]*=noise[:,None];self.mesh('rock',v,idx)
 def reset(self):
  super().reset();self.glyphs=[];self.exempt=[]
 def molecule(self,pos,kind,scale=1.,alpha=1.,tag='solution'):
  if alpha<.02:return
  p=np.asarray(pos,float);col=[AMBER,CYAN,GREEN][kind]
  if kind==0:
   off=[[-.105,0,0],[.105,0,0]];rad=.105
  else:
   off=[[-.125,-.07,0],[.125,-.07,0],[0,.15,0]];rad=.093
  for o in off:self.ball(p+np.array(o)*scale,rad*scale,col,alpha=alpha,rough=.20,emit=.12)
  for k in range(len(off)-1):self.bar(p+np.array(off[k])*scale,p+np.array(off[k+1])*scale,.025*scale,col,alpha=alpha)
  if kind==2:self.bar(p+np.array(off[-1])*scale,p+np.array(off[0])*scale,.025*scale,col,alpha=alpha,emit=.3)
  self.glyphs.append((p,.245*scale,tag))
 def arrow(self,a,c,col,scale=1.,alpha=1.):
  a=np.array(a);c=np.array(c);d=b.unit(c-a);side=b.unit(np.cross(d,[0,0,1]));self.bar(a,c,.035*scale,col,alpha=alpha,emit=.13)
  self.bar(c,c-d*.27*scale+side*.14*scale,.04*scale,col,alpha=alpha);self.bar(c,c-d*.27*scale-side*.14*scale,.04*scale,col,alpha=alpha)
 def mineral(self,center=(0,.25,0),scale=1.,open_amount=0):
  c=np.array(center)
  for ix in [-1,1]:
   self.add('slab',c+[ix*(.19+open_amount),0,0],[.36*scale,3.8*scale,.58*scale],ROCK,kind=1,rough=.58)
  for j in range(10):
   y=-1.6+j*.36;self.add('rock',c+[.03*np.sin(j*2),y*scale,-.36*scale],[.35*scale,.21*scale,.25*scale],ROCK*.8,kind=1,rough=.7)
 def arrow_flow(self,x,y,t,col,scale=1.,direction=1.,strength=1.):
  for j in range(4):
   yy=y+((t*.8+j*.74)%3.0-1.5)*scale
   self.arrow([x,yy-.18*scale*direction,.28],[x,yy+.18*scale*direction,.28],col,scale*.7,alpha=.25+.6*strength)

def cell(r,t,center=(0,0,0),sc=1.,strength=1.,continuous=True,phase=0):
 c=np.array(center,float);r.mineral(c+[0,.25*sc,0],sc)
 for lane,y in enumerate([-1.05,.20,1.45]):
  f=(t*.31+lane*.31+phase)%1
  x=-3.05+2.0*f
  r.molecule(c+np.array([x,y,.72])*sc,0,sc,alpha=max(.12,strength),tag='donor')
  x2=2.98-2.02*f
  r.molecule(c+np.array([x2,y,.72])*sc,1,sc,alpha=max(.12,strength),tag='acceptor')
  # Electron icons travel inside the conducting mineral. This intersection is intentional.
  if strength>.08:
   e=(t*1.2+lane*.32)%1;r.ball(c+np.array([-.43+.86*e,y,.32])*sc,.075*sc,PALE,emit=1.25,alpha=strength)
  # Products leave by a distinct lane and do not pass through reactant symbols.
  g=(t*.27+lane*.31+phase)%1
  r.molecule(c+np.array([.98+1.90*g,y+.52,.72])*sc,2,.73*sc,alpha=max(.08,strength),tag='product')
  rr=.10+.13*(.5+.5*np.sin(t*5+lane))
  r.ball(c+np.array([.48,y,.48])*sc,rr*sc,[.50,.96,.72],emit=1.25*strength,alpha=max(.1,strength))
 if continuous:
  r.arrow_flow(c[0]-3.42*sc,c[1]+.2*sc,t,AMBER,sc,1,strength)
  r.arrow_flow(c[0]+3.42*sc,c[1]+.2*sc,t,CYAN,sc,-1,strength)

def landscape(r,t,u,closing=False):
 r.eye=np.array([4.3-1.1*u,3.7,23.5-1.8*u]);r.target=np.array([0,.7,0])
 # Three-dimensional seabed, low foreground outcrops, and independent chimney clusters.
 r.add('slab',[0,-2.85,-.6],[15,.5,10],[.055,.12,.15],rough=.8,kind=1)
 for i in range(25):
  x=-6+(i%7)*1.8;z=-4+(i//7)*1.8;sz=.25+.20*(.5+.5*np.sin(i*3.7))
  r.add('rock',[x,-2.48,z],[sz*1.8,sz,sz*1.4],ROCK*(.55+.13*(i%3)),rotation=b.rot(.2*i,.5*i,.1*i),kind=1,rough=.75)
 r.add('chimney',[0,0,0],1,ROCK,kind=1,rough=.64)
 r.add('chimney',[-2.7,-1.0,-2.8],[.65,.60,.65],ROCK*.65,kind=1,rough=.65)
 r.add('chimney',[2.8,-1.5,-3.0],[.7,.40,.7],ROCK*.7,kind=1,rough=.7)
 for j in range(34):
  f=(t*.17+j/34)%1;ang=j*2.4+t*.2;rad=.1+f*.7
  r.ball([rad*np.cos(ang),2.15+3.2*f,rad*np.sin(ang)],.10+.15*f,[.15,.31,.34],alpha=(1-f)*.48,rough=.9)
 for lane in range(3):
  f=(t*.24+lane*.33)%1
  r.molecule([-.95-.35*np.sin(f*3),-1.9+4*f,.72],0,.74,tag='environment')
  r.molecule([2.9-2.15*f,.25+lane*.90,.72],1,.72,tag='environment')
  r.molecule([.85+1.8*f,-.5-lane*.55,.72],2,.62,tag='environment')
 if closing:
  r.text('新しい材料 → 反応 → 外へ',540,1310,42,(178,231,224))
 else:
  q=b.smooth(u,.05,.35);r.text('海底の、化学が動く場所',540,1320,38,(178,213,223),int(255*q))
 r.semantic={'vent_supply':t*.24,'plume':t*.17,'steady_conditions':True}

def arrange(r,s,u,t,split):
 r.eye=np.array([1.6,2.0,22.3]);r.target=np.array([0,.3,0]);q=b.smooth(u,split-.07,split+.20)
 if s in [0,9]:landscape(r,t,u,s==9);return
 if s==1:
  opening=b.smooth(u,.04,.32);r.mineral(scale=1.,open_amount=.35*opening)
  for j in range(5):
   y=-1.6+j*.82;drift=.12*np.sin(t*1.6+j)
   r.molecule([-2.35+drift,y,.65],0,1.1,tag='leftwater');r.molecule([2.35-drift,y,.65],1,1.1,tag='rightwater')
  r.arrow_flow(-3.1,.2,t,AMBER,1,1);r.arrow_flow(3.1,.2,t,CYAN,1,-1)
  r.text('熱水',275,570,45,(255,190,106));r.text('海水',810,570,45,(128,214,249))
  r.text('二つの水。異なる材料。',540,1330,40,(212,238,243));r.semantic={'mineral_opens':opening,'different_ingredients':t}
 elif s==2:
  for i in range(3):
   y=-1.15+i*1.4
   r.molecule([-2.2+.12*np.sin(t*2+i),y,.45],0,1.8,tag='donor_compare');r.molecule([2.2+.12*np.cos(t*2+i),y,.45],1,1.8,tag='acceptor_compare')
   r.arrow([-1.2,y,.35],[1.2,y,.35],PALE,1,alpha=.4+.5*q)
   f=(t*.75+i*.27)%1;r.ball([-1.1+2.2*f,y,.40],.075+.025*q,PALE,emit=.8)
  r.text('渡す側',260,570,43,(255,190,106));r.text('受け取る側',810,570,43,(128,214,249))
  r.text('電子',540,1285,40,(235,246,249));r.semantic={'electron_transfer':t*.75,'drive_emphasis':q}
 elif s in [3,4]:
  cell(r,t,strength=.50+.50*q)
  r.text('鉱物',540,520,42,(221,226,226));r.text('電子を通す',540,1310,40,(229,240,243))
  if s==4:
   r.text('材料',280,590,38,(255,190,106));r.text('生成物',820,1240,38,(117,236,188))
   r.text('反応の仕組みを示す模型',540,1390,29,(158,189,199))
  r.semantic={'electron_motion':t*1.2,'reaction_progress':t*.27,'catalyst_light':q}
 elif s==5:
  cutoff=b.smooth(u,.08,.40);strength=1-.68*b.smooth(u,.22,.96)
  cell(r,t*(1-.45*cutoff),strength=strength,continuous=False)
  for x,col in [(-3.42,AMBER),(3.42,CYAN)]:
   r.arrow_flow(x,.2,t*(1-.75*cutoff),col,1,1 if x<0 else -1,strength)
   # A decreasing supply indicator, not a physical valve in a natural vent.
   r.bar([x-.20,-2.10,.5],[x-.20+(.4*(1-cutoff)+.002),-2.10,.5],.065,col)
  r.text('供給を停止',540,545,44,(246,210,146));r.text('残った材料を、使っていく',540,1330,39,(213,230,235));r.semantic={'supply':1-cutoff,'reaction_strength':strength}
 elif s==6:
  mix=b.smooth(u,.03,.94)
  # Separated lattices become a mixed lattice without interpenetration.
  for j in range(12):
   y=-1.6+(j//4)*1.35;col=j%4;x=-2.7+col*1.8
   kind=0 if col<2 else 1;target_kind=(j+j//4)%2
   p=np.array([x,y,.65]);r.molecule(p,kind,1.2,alpha=1-mix,tag='oldstate')
   # Alternate identity represents blending of composition, not chemical conversion.
   if mix>.02:
    colr=(AMBER if target_kind==0 else CYAN);r.ball(p,.20, colr,alpha=mix,rough=.25)
  r.text('混ざると、差が縮む',540,555,43,(229,234,237))
  for side,xx in enumerate([-1.65,1.65]):
   ht=(1-mix)*1.3+.22;r.bar([xx,-2.1,.5],[xx,-2.1+ht,.5],.13,[AMBER,CYAN][side])
  r.text('反応を動かす力 ↓',540,1350,42,(170,216,224));r.semantic={'composition_difference':1-mix,'reaction_strength':(1-mix)**2}
 elif s==7:
  cell(r,t,strength=1,continuous=True)
  r.text('新しい材料',260,540,39,(255,190,106));r.text('できたもの',815,1280,39,(117,236,188))
  r.text('入り続ける。出ていく。',540,1380,39,(214,237,241));r.semantic={'supply':1,'outflow':t*.27,'reaction_strength':1}
 elif s==8:
  r.eye=np.array([.3,1.0,23.0]);r.target=np.array([0,.2,0])
  decline=1-.9*b.smooth(u,.02,.67)
  cell(r,t*.65,center=[0,1.9,0],sc=.52,strength=decline,continuous=False)
  cell(r,t,center=[0,-1.6,0],sc=.52,strength=1,continuous=True)
  r.text('供給を止める',540,550,42,(232,203,164));r.text('供給を続ける',540,1045,42,(117,231,203))
  r.bar([-3.25,.2,-.1],[3.25,.2,-.1],.015,[.18,.33,.39])
  r.semantic={'stopped_strength':decline,'ongoing_strength':1,'ongoing_reaction_phase':t*.27}

def check_spacing(r):
 # Only independent material symbols: intentional bonds, surfaces and electrons excluded.
 minimum=999.;pairs=0
 for i,(p,rad,tag) in enumerate(r.glyphs):
  for q,rad2,tag2 in r.glyphs[i+1:]:
   if tag=='environment' or tag2=='environment':continue
   d=float(np.linalg.norm(p-q)-rad-rad2);minimum=min(minimum,d);pairs+=1
 return {'minimum_symbol_sphere_clearance':None if minimum==999 else minimum,'pairs':pairs}

def do_voice():
 tl,narr=b.voice();b.music(tl,narr)
 # Readings are documented and checked against the synthesis kana, never called listening.
 readings={};keys={'鉱物':'コーブツ','電子':'デンシ','供給':'キョーキュー','熱水':'ネッスイ','海水':'カイスイ'}
 for word,kana in keys.items():
  hits=[c for c in tl['cues'] if word in c['text']]
  readings[word]={'expected':kana,'records':[c['kana'] for c in hits],'checked':all(kana in re_kana(c['kana']) for c in hits)}
 b.dump(R/'review/readings.json',readings)
 print('READING_CHECK',json.dumps(readings,ensure_ascii=False),flush=True)
 print('TIMELINE',tl['duration'],tl['max_query_speech_gap'],flush=True)
 b.dump(R/'docs/sources.json',SOURCES)

def re_kana(x):
 import re
 return re.sub(r"[\'_/？?、。]",'',x)

def shot(s,preview=False):
 tl=json.loads((R/'timeline.json').read_text());r=Scene();a,z=tl['boundaries'][s:s+2];start=round(a*FPS);end=round(z*FPS);second=[c for c in tl['cues'] if c['scene']==s][1]['start'];split=(second-a)/(z-a)
 target=R/'render'/f'shot_{s:02}.mp4';target.parent.mkdir(exist_ok=True)
 if not preview:
  log=(R/'review'/f'ffmpeg_{s:02}.log').open('w');proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','3',str(target)],stdin=subprocess.PIPE,stderr=log)
 samples={start+round((end-start-1)*f) for f in [.08,.32,.58,.85]};states=[];last=None
 frames=sorted(samples) if preview else range(start,end)
 for f in frames:
  t=f/FPS;u=(t-a)/(z-a);r.reset();arrange(r,s,u,t,split)
  cue=next((c for c in tl['cues'] if c['start']-.07<=t<c['end']+.16),None)
  im,raw=r.frame(t,s,cue)
  if not preview:proc.stdin.write(im.tobytes())
  tiny=np.array(raw.crop((85,420,995,1420)).resize((182,200)),dtype=np.int16);delta=float(np.abs(tiny-last).mean()) if last is not None else 0;last=tiny
  check=check_spacing(r);states.append({'frame':f,'time':t,'semantic':r.semantic,'raw_subject_delta':delta,**check})
  if f in samples:im.save(R/'review'/f'p065_scene_{s:02}_{f:04}.jpg',quality=92)
 if not preview:
  proc.stdin.close();rc=proc.wait();log.close();assert rc==0
  b.dump(R/'review'/f'states_{s:02}.json',states)
  vals=[st['minimum_symbol_sphere_clearance'] for st in states if st['minimum_symbol_sphere_clearance'] is not None]
  print('SHOT_COMPLETE',s,'FRAMES',end-start,'CLEARANCE',min(vals) if vals else None,flush=True)

def assemble():
 tl=json.loads((R/'timeline.json').read_text());d=R/'deliverables';d.mkdir(exist_ok=True)
 rr=Scene();b.subtitles(tl,rr)
 for suffix in ['ja.srt','ja.ass','en.srt']:
  old=d/('heionreki_p064_v2_'+suffix)
  if old.exists():old.rename(d/(PREFIX+'_'+suffix))
 listing=R/'render/concat.txt';listing.write_text(''.join("file '"+str((R/'render'/f'shot_{i:02}.mp4').resolve())+"'\n" for i in range(10)))
 picture=R/'render/full_picture.mp4';b.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(picture)])
 high=d/(PREFIX+'_high_1080x1920.mp4');light=d/(PREFIX+'_light_720x1280.mp4')
 b.run(['ffmpeg','-y','-v','error','-i',str(picture),'-i',str(R/'audio/master.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(tl['duration']),'-movflags','+faststart',str(high)])
 b.run(['ffmpeg','-y','-v','error','-i',str(high),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','fast','-crf','24','-threads','3','-c:a','copy','-movflags','+faststart',str(light)])
 probes={};hashes=[]
 for p in [high,light]:
  b.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'])
  probe=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-show_format','-of','json',str(p)]));probes[p.name]=probe
  vs=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(vs['nb_frames'])==round(tl['duration']*FPS)
  audio=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','adts','-']);hashes.append(hashlib.sha256(audio).hexdigest())
 assert hashes[0]==hashes[1]
 loud=subprocess.run(['ffmpeg','-v','info','-i',str(high),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);lm=json.loads(loud.stderr[loud.stderr.rfind('{'):loud.stderr.rfind('}')+1]);b.dump(R/'review/loudness.json',lm)
 states=[]
 for i in range(10):states+=json.loads((R/'review'/f'states_{i:02}.json').read_text())
 assert len(states)==round(tl['duration']*FPS)
 positive=[s['minimum_symbol_sphere_clearance'] for s in states if s['minimum_symbol_sphere_clearance'] is not None]
 vals=np.array([s['raw_subject_delta'] for s in states]);win=np.convolve(vals,np.ones(48)/48,mode='valid')
 qa={'duration':tl['duration'],'frames':len(states),'native_resolution':[1080,1920],'fps':FPS,'audio_sample_rate':SR,'max_query_speech_gap':tl['max_query_speech_gap'],'minimum_independent_symbol_clearance':min(positive),'negative_clearance_frames':[s['frame'] for s in states if s['minimum_symbol_sphere_clearance'] is not None and s['minimum_symbol_sphere_clearance']<-.001],'minimum_two_second_mean_raw_picture_difference':float(win.min()),'weak_windows':[int(i) for i,x in enumerate(win) if x<.015],'loudness':lm,'audio_payload_identical':True,'caption_count':len(tl['cues']),'human_continuous_viewing':False,'auditory_listening':False,'limitations':'Collision bounds concern independent material symbols in explanation scenes, not rocks or intentional surface contacts. Projection and perceived clarity still need visual review. Pixel changes do not by themselves prove interesting pacing.'}
 b.dump(R/'review/verification.json',qa);b.dump(R/'review/media.json',probes)
 images=sorted((R/'review').glob('p065_scene_*.jpg'));sheet=Image.new('RGB',(1080,1920),(3,13,21))
 for i,p in enumerate(images):sheet.paste(Image.open(p).resize((135,240)),((i%8)*135,(i//8)*240))
 sheet.save(R/'review/contact_sheet.jpg',quality=93)
 notes='平穏暦全史・前史065 第1版\n反応を続けるには、「差」がいる\n制作日・出典確認日：2026-10-28\n\n'
 notes+=f"仕様：{tl['duration']:.3f}秒、1080×1920を直接描画、24fps、{len(states)}コマ。軽量版720×1280。声・音楽・効果音・日本語字幕入り。\n\n"
 notes+='台本：\n'+'\n'.join(x[0] for x in PARTS)+'\n\n'
 notes+='科学と演出：\n熱水と海水の酸化還元の不均衡、導電性の鉱物と電気化学反応を説明する。生体分子の合成につながる反応を実験で検討していることと、自然界で生命が生じた場所の確定を分ける。\n橙の二粒、青の三粒、緑の閉じた三角は材料の役割を区別する記号であり、具体的な元素・分子や完全な化学反応式ではない。白い点は電子移動の説明用。生成物が分子の色替えだけで作られる主張ではない。\n鉱物の開閉は内部を見せる断面の演出。熱水に実物の配線や弁を埋め込まない。温度差による濃縮は063の題材であり、本作の中心は化学的な差の維持。\n供給停止・混合・反応の弱化と継続供給は説明用の時間圧縮。自然現象の測定曲線・反応速度・実験結果の定量再現ではない。供給だけで全反応の持続が保証されるとはせず、対象反応を駆動する条件が保たれる比較とする。\n\n'
 notes+='出典：\n'+'\n\n'.join(x['id']+' '+x['title']+'\n'+x['url']+'\n'+x.get('doi','')+'\n'+x['use'] for x in SOURCES)
 notes+='\n\n声：VOICEVOX 四国めたん（ノーマル）、エンジン0.25.2、コア0.16.1。速度1.03。熱水＝ねっすい／鉱物＝こうぶつ／供給＝きょうきゅう／海水＝かいすいを生成入力で指定。電子なども合成読みを確認。原音、合成クエリと拍の時刻を保存。耳による試聴は未実施。\n音楽・効果音：数式合成のオリジナル。外部音源不使用。書体は環境のNoto Sans CJK JP。フォントファイル・音声モデルの再配布なし。\n'
 notes+='\n検証：\n'+json.dumps(qa,ensure_ascii=False,indent=2)+'\n\n再編集：source/p065_film.py を参照。voice、shot 0..9、assembleの順に実行。原音と時間軸を同梱しており、映像の再描画に音声エンジンの再取得は不要。音声の再生成には別途公式VOICEVOXを要する。\n'
 (d/(PREFIX+'_script_and_sources.txt')).write_text(notes,encoding='utf-8')
 shutil.copy(__file__,R/'source/p065_film.py');shutil.copy(BASE,R/'source/p064_v2_film.py');b.dump(R/'docs/sources.json',SOURCES)
 (R/'source/README.txt').write_text('python p065_film.py shot 0\n各場面0..9の描画後 python p065_film.py assemble\n作業フォルダp065_v1へ展開。ffmpeg、numpy、Pillow、scipy、soundfile、moderngl==5.12.0、glcontext==3.0.0、Noto Sans CJK JPとEGLが必要。\n',encoding='utf-8')
 manifest=[]
 for p in sorted(R.rglob('*')):
  if p.is_file() and p.suffix not in ['.ttf','.otf','.ttc'] and 'voice_data' not in p.parts:manifest.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 b.dump(R/'review/manifest.json',manifest)
 archive=d/(PREFIX+'_production.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in R.rglob('*'):
   if p.is_file() and p!=archive and p.suffix not in ['.ttf','.otf','.ttc'] and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(R)))
 print('FINAL_VERIFICATION',json.dumps(qa,ensure_ascii=False),flush=True)
 print('DELIVERABLES',json.dumps([{'name':p.name,'bytes':p.stat().st_size} for p in d.iterdir()],ensure_ascii=False),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='voice':do_voice()
 elif mode=='shot':shot(int(sys.argv[2]))
 elif mode=='preview':
  for i in range(10):shot(i,True)
 elif mode=='assemble':assemble()
 else:raise ValueError(mode)
