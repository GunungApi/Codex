"""P066: replication, inherited variation and differential amplification.
Original explanatory meshes and an explicitly schematic population model.
Rendering and speech infrastructure inherited from the approved P064 pipeline.
"""
from pathlib import Path
import os,sys,types,math,json,shutil,subprocess,zipfile,hashlib,re
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','3')
os.environ.setdefault('OMP_NUM_THREADS','3')
import numpy as np
from PIL import Image,ImageDraw
import soundfile as sf
from scipy.signal import butter,sosfilt
BASE=Path(__file__).with_name('p064_v2_film.py')
source=BASE.read_text().replace("Path('p064_v2')","Path('p066_v1')").replace('前史064','前史066').replace('脂肪酸膜の模式表現  ·  大きさと時間を圧縮','複製と継承の模式図  ·  配列と時間を簡略化').replace('多層の脂肪酸膜を使った模型実験の模式化','配列・個数・増え方は説明用の模型')
b=types.ModuleType('p066_infrastructure');b.__file__=str(BASE);sys.modules[b.__name__]=b
exec(compile(source,str(BASE),'exec'),b.__dict__)
R=b.ROOT;W,H,FPS,SR=1080,1920,24,48000;PREFIX='heionreki_p066_v1'
TITLE='コピーが変わると、歴史が枝分かれする'
PARTS=[
('コピーに違いが生まれたら、','When a copy changes,',0),
('その違いも、増えていく？','can that difference multiply too?',0),
('実験では、用意したRNAが、','In experiments, prepared RNA enzymes',1),
('相手を作る部品を、つなぎ合わせる。','join supplied fragments to form their partners.',1),
('できた相手が、今度はこちらを作る。','The partner, in turn, helps make this RNA.',2),
('材料を補うと、互いに増えていく。','With substrates replenished, both can amplify.',2),
('部品の組み合わせが変わると、','Recombining component sequences',3),
('新しい型が生まれることがある。','can produce new replicator variants.',3),
('その違いが、次のコピーにも残る。','The difference can be inherited by later copies.',4),
('同じ場所の、金色の印を追おう。','Follow the gold marker at the same position.',4),
('同じ材料の中でも、','Even in a shared pool of substrates,',5),
('型によって、増えやすさが違う。','variants can differ in how readily they amplify.',5),
('世代を重ねると、割合が変わる。','Their proportions can change over generations.',6),
('増えやすさは、周りの条件にもよる。','Which variants do well depends on the conditions.',6),
('材料。境界。反応。そして、継承。','Ingredients. Boundaries. Reactions. Inheritance.',7),
('どう生命につながるかを、探っている。','We are investigating how these connect to life.',7),
('複製と、受け継がれる違い。','Replication and heritable variation,',8),
('そこに、増え方の差が重なる。','combined with differences in amplification.',8),
('変化が、次の世代へ残っていく。','Changes persist into later generations.',9),
('小さな化学から、歴史が枝分かれする。','From tiny chemistry, histories branch out.',9)]
HEADINGS=['違いまで、増えていく？','部品がつながり、相手になる','今度は、相手がこちらを作る','組み合わせから、新しい型へ','同じ場所に、違いが残る','同じ材料でも、増え方が違う','世代を重ねると、割合が変わる','生命へつながる、四つの働き','複製 × 違い × 増え方','小さな化学が、歴史になる']
b.PARTS=PARTS;b.HEADINGS=HEADINGS;b.TITLE=TITLE
vsrc=source[source.index('def voice():'):source.index("VERT='''")]
vsrc=vsrc.replace("spoken=text.replace('尾は','おは').replace('二重に','にじゅうに')","spoken=text.replace('RNA','アールエヌエー').replace('複製','ふくせい').replace('継承','けいしょう').replace('世代','せだい').replace('割合','わりあい').replace('金色','きんいろ').replace('型','かた')")
exec(compile(vsrc,'p066_voice','exec'),b.__dict__)
CYAN=np.array([.12,.73,.94]);CORAL=np.array([1.,.32,.26]);GOLD=np.array([1.,.66,.10]);PALE=np.array([.79,.93,1.]);GREEN=np.array([.20,.90,.65])
SOURCES=[
{'id':'S1','title':'Lincoln & Joyce (2009), Self-sustained Replication of an RNA Enzyme','doi':'10.1126/science.1167856','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC2652413/','use':'Two RNA enzymes catalyse formation of each other from four supplied oligonucleotide substrates; continued replenishment, recombinants and selection in serial transfer.'},
{'id':'S2','title':'Joyce (2009), Evolution in an RNA World','doi':'10.1101/sqb.2009.74.004','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC2891321/','use':'Primary author account of heritable recombination, amplification and condition-dependent relative fitness in the experimental system.'},
{'id':'S3','title':'Sczepanski & Joyce (2012), Synthetic Evolving Systems that Implement a User-specified Genetic Code of Arbitrary Design','doi':'10.1016/j.chembiol.2012.08.015','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC3483592/','use':'Engineered cross-replicators connect heritable sequence information to molecular function; not reconstruction of the first life.'}]
CAPTIONS={
PARTS[0][0]:['コピーに違いが','生まれたら、'],PARTS[2][0]:['実験では、','用意したRNAが、'],PARTS[3][0]:['相手を作る部品を、','つなぎ合わせる。'],PARTS[4][0]:['できた相手が、','今度はこちらを作る。'],PARTS[5][0]:['材料を補うと、','互いに増えていく。'],PARTS[6][0]:['部品の組み合わせが','変わると、'],PARTS[7][0]:['新しい型が','生まれることがある。'],PARTS[8][0]:['その違いが、','次のコピーにも残る。'],PARTS[9][0]:['同じ場所の、','金色の印を追おう。'],PARTS[11][0]:['型によって、','増えやすさが違う。'],PARTS[12][0]:['世代を重ねると、','割合が変わる。'],PARTS[13][0]:['増えやすさは、','周りの条件にもよる。'],PARTS[14][0]:['材料。境界。反応。','そして、継承。'],PARTS[15][0]:['どう生命につながるかを、','探っている。'],PARTS[16][0]:['複製と、','受け継がれる違い。'],PARTS[17][0]:['そこに、','増え方の差が重なる。'],PARTS[18][0]:['変化が、','次の世代へ残っていく。'],PARTS[19][0]:['小さな化学から、','歴史が枝分かれする。']}
oldwrap=b.Renderer.wrap
def wrap(self,text,size,maxw):
 lines=CAPTIONS.get(text)
 if lines:
  assert all(self.fontobj(size).getlength(x)<=maxw for x in lines)
  return lines
 return oldwrap(self,text,size,maxw)
b.Renderer.wrap=wrap
# Preserve surface relief, with a more directional crystalline glint on RNA beads.
b.FRAG=b.FRAG.replace('float a=C.a;', 'c += C.rgb*pow(max(0.,dot(n,normalize(vec3(.7,.6,-.5)))),5.)*.22;\nfloat a=C.a;')

def poly_mesh(kind):
 if kind=='cube':
  pts=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)/np.sqrt(3)
  faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(3,7,6),(3,6,2),(0,4,7),(0,7,3),(1,2,6),(1,6,5)]
 else:
  pts=np.array([[1,1,1],[-1,-1,1],[-1,1,-1],[1,-1,-1]],float)/np.sqrt(3);faces=[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
 vv=[];ii=[]
 for f in faces:
  a,c,d=pts[list(f)];n=b.unit(np.cross(c-a,d-a));j=len(vv);vv.extend([[*a,*n],[*c,*n],[*d,*n]]);ii.extend([j,j+1,j+2])
 return np.array(vv,'f4'),np.array(ii,'i4')

class Scene(b.Renderer):
 def __init__(self):
  super().__init__();self.mesh('cube',*poly_mesh('cube'));self.mesh('tetra',*poly_mesh('tetra'))
 def reset(self):
  super().reset();self.atoms=[];self.whole=[];self.semantic={};self.eye=np.array([0.,1.25,20.5]);self.target=np.array([0.,.45,0.])
 def ring(self,c,rad,col=CYAN,alpha=.5,progress=1.,width=.018):
  if progress<=0:return
  c=np.asarray(c);pts=[c+np.array([rad*np.cos(a),rad*np.sin(a),0]) for a in np.linspace(-np.pi/2,-np.pi/2+2*np.pi*progress,max(3,int(50*progress)))]
  for x,y in zip(pts,pts[1:]):self.bar(x,y,width,col,alpha=alpha,emit=.35)
 def link(self,a,c,q=1.,col=PALE,t=0.,bend=.0,alpha=.65):
  if q<=.001:return
  a=np.array(a,float);c=np.array(c,float);v=c-a;side=np.array([-v[1],v[0],0]);side=b.unit(side)
  pts=[b.lerp(a,c,z)+side*bend*np.sin(np.pi*z) for z in np.linspace(0,min(1,q),25)]
  for x,y in zip(pts,pts[1:]):self.bar(x,y,.018,col,alpha=alpha,emit=.25)
  phase=(t*.9)%1
  if phase<q:
   p=b.lerp(a,c,phase)+side*bend*np.sin(np.pi*phase);self.ball(p,.06,col,emit=1.)
 def rna(self,c,kind=0,variant=False,sc=1.,progress=1.,alpha=1.,tag='rna',indices=None,offset=0.,phase=0.,glow=0.):
  if alpha<.02:return
  c=np.array(c,float);col=CYAN if kind==0 else CORAL;indices=list(range(6)) if indices is None else list(indices);points=[]
  for j in indices:
   show=b.smooth(progress,j/6,(j+.58)/6) if len(indices)==6 else 1.
   if show<.01:continue
   local=np.array([-.98+j*.392,.13*np.sin(j*1.2+kind*.8),.10*np.sin(j*1.3)])
   local[1]+=.018*np.sin(phase*1.5+j*.7)
   local[0]+=(-offset if j<3 else offset)
   p=c+local*sc;head=p+np.array([0,.28,.02])*sc
   color=GOLD if variant and j==3 else col
   rad=.115*sc*show;self.ball(p,.085*sc*show,PALE,alpha=alpha,rough=.22)
   self.bar(p,head,.025*sc,color,alpha=alpha)
   if variant and j==3:self.add('tetra',head,rad*1.42,GOLD,rotation=b.rot(.4,.6,.1),alpha=alpha,rough=.15,emit=.25+glow*.6)
   elif (j+kind)%2:self.add('cube',head,rad*1.28,color,rotation=b.rot(.3,.5,.1),alpha=alpha,rough=.18,emit=.10)
   else:self.ball(head,rad,color,alpha=alpha,rough=.16,emit=.10)
   if points and j==points[-1][0]+1:self.bar(points[-1][1],p,.038*sc,col,alpha=alpha,emit=.05)
   points.append((j,p))
   if alpha>.18:
    self.atoms.extend([(tag,p,.086*sc),(tag,head,.167*sc if variant and j==3 else .150*sc)])
  if len(indices)==6:self.whole.append({'tag':tag,'type':kind,'variant':variant,'center':c.tolist(),'scale':sc,'progress':progress})
  return c+np.array([.196,.28+.13*np.sin(3*1.2+kind*.8),.02+.10*np.sin(3*1.3)])*sc
 def glow_join(self,c,q):
  if q<=0:return
  p=np.array(c);self.ring(p,.12+.40*q,GOLD,alpha=.8*(1-q),width=.025);self.ball(p,.04+.04*np.sin(q*np.pi),PALE,alpha=.7*(1-q),emit=1.6)

def background(r,t):
 # Background is excluded from the semantic-event audit and never substitutes for main actions.
 for i in range(15):
  x=4.8*np.sin(i*2.1+t*.025);y=5.3*np.cos(i*1.5+t*.02);r.ball([x,y,-5-(i%3)],.026,[.10,.23,.30],rough=.8)

def pair_build(r,u,t,reverse=False):
 q=b.smooth(u,.12,.53);away=b.smooth(u,.60,.97);k=int(reverse);c=np.array([0,2.1,0.])
 r.rna(c,k,False,1.45,phase=t,tag='catalyst')
 target=np.array([0,-.30-1.20*away,0.]);r.rna(target,1-k,False,1.5,indices=range(3),offset=1.03*(1-q),phase=t,tag='product');r.rna(target,1-k,False,1.5,indices=range(3,6),offset=1.03*(1-q),phase=t,tag='product')
 r.link([-2.3,1.65,.1],[-2.3,-.3,.1],b.smooth(u,0,.24),col=CORAL if k else CYAN,t=t,bend=.30)
 r.glow_join(target+[0,.12,.15],b.smooth(u,.50,.72))
 r.text('型B' if reverse else '型A',540,543,36,(249,181,169) if k else (139,223,248))
 if q<.95:r.text('外から与えた二つの部品',540,1185,36,(206,224,234))
 else:r.text('型Aができる' if reverse else '型Bができる',540,1230,43,(139,223,248) if k else (249,181,169))
 r.semantic.update(substrate_approach=q,product_release=away,catalyst_type=k,product_type=1-k)

def tree(r,u,t,full=False):
 levels=[[(0,2.95,0)], [(-1.75,1.50,0),(1.75,1.50,0)], [(-2.55,.08,0),(-.85,.08,0),(.85,.08,0),(2.55,.08,0)], [(-2.8,-1.50,0),(-1.65,-1.50,0),(-.55,-1.50,0),(.55,-1.50,0),(1.65,-1.50,0),(2.8,-1.50,0)]]
 scales=[.76,.64,.49,.34];births=[]
 for lev,points in enumerate(levels):
  for j,point in enumerate(points):
   onset=lev*.22+j*.028;appear=b.smooth(u,onset,min(.97,onset+.17));p=np.array(point,float)
   if full:p[2]=.38*np.sin(t*.45+j+lev)
   if appear<=0:continue
   if lev:
    parent=levels[lev-1][min(len(levels[lev-1])-1,int(j*len(levels[lev-1])/len(points)))];r.link(np.array(parent)+[0,-.15,-.12],p+[0,.30,-.12],appear,col=GOLD if j%3==1 else CYAN,t=t+.22*j)
   v=(j%3==1) or (lev==1 and j==1);r.rna(p,j%2,v,scales[lev],progress=appear,tag=f'tree-{lev}-{j}',phase=t,glow=.2)
   births.append((lev,j,round(appear,3)))
 r.semantic.update(lineage_births=births,tree_growth=u)

def arrange(r,s,u,t,tl):
 r.reset();background(r,t);r.semantic={'scene':s,'progress':round(u,5)}
 c=next(x for x in tl['cues'] if x['scene']==s);seconds=(tl['boundaries'][s+1]-tl['boundaries'][s]);split=(tl['cues'][2*s+1]['start']-tl['boundaries'][s])/seconds
 if s==0:
  q=b.smooth(u,0,.23);r.rna([0,2.45,0],0,False,1.55,progress=q,tag='original',phase=t)
  for j,x in enumerate([-1.70,1.70]):
   p=b.smooth(u,.20+j*.13,.60+j*.13);r.link([0,2.10,-.05],[x,.54,-.05],p,col=GOLD if j else CYAN,t=t);r.rna([x,.05,0],0,bool(j),1.03,progress=p,tag=f'child-{j}',phase=t,glow=.3)
  q2=b.smooth(u,.55,.98);r.link([1.70,-.32,-.05],[1.70,-1.6,-.05],q2,col=GOLD,t=t);r.rna([1.70,-2.0,0],0,True,.91,progress=q2,tag='grandchild',phase=t,glow=.6)
  r.text('次へ残る「違い」',350,1255,38,(255,211,128));r.semantic.update(first_copy=q,second_copy=q2)
 elif s in [1,2]:pair_build(r,u,t,s==2)
 elif s==3:
  r.rna([-1.70,2.18,0],0,False,.98,tag='parent-left',phase=t)
  r.rna([1.70,2.18,0],0,True,.98,tag='parent-right',phase=t)
  q=b.smooth(u,.08,.66);target=np.array([0,-.85,0.]);off=1.03*(1-q)
  r.rna(target,0,True,1.65,indices=range(3),offset=off,tag='recombined',phase=t)
  mark=r.rna(target,0,True,1.65,indices=range(3,6),offset=off,tag='recombined',phase=t)
  r.link([-1.70,1.72,-.10],[-1.50,-.36,-.10],q,CYAN,t,bend=.3)
  r.link([1.70,1.72,-.10],[1.50,-.36,-.10],q,GOLD,t,bend=-.3)
  r.glow_join(target+[0,.1,.2],b.smooth(u,.60,.85))
  if q>.85:r.ring(mark+[0,0,.12],.36+.04*np.sin(t*4),GOLD,alpha=.8,width=.026)
  r.text('組み合わせが、次へ残る',540,1270,42,(255,210,129));r.semantic.update(recombination_assembly=q)
 elif s==4:
  for j,y in enumerate([2.55,.48,-1.59]):
   q=b.smooth(u,j*.23,min(1,j*.23+.20));p=np.array([0,y,0.]);mark=r.rna(p,0,True,1.60,progress=q,tag=f'generation-{j}',phase=t,glow=.15)
   if j:r.link([.31,y+1.70,.2],[.31,y+.70,.2],q,GOLD,t)
   if q>.90:
    pulse=(u*2.5-j*.7)%1;r.ring(mark+[0,0,.16],.30+.14*pulse,GOLD,.8*(1-pulse),width=.022)
   r.text(['親','次のコピー','さらに次'][j],870,615+j*291,32,(211,231,239))
  r.semantic.update(inherited_marker_index=3,generations=3,reveal=u)
 elif s==5:
  q=b.smooth(u,.05,.94)
  for side in [0,1]:
   x=-1.70 if side==0 else 1.70;r.text('型A' if side==0 else '型Aの別型',290 if side==0 else 790,490,36,(139,223,248) if side==0 else (255,211,128))
   n=4 if side else 2
   for j in range(n):
    on=j/(n+1);progress=b.smooth(q,on,on+.20);y=2.22-j*1.20
    r.rna([x,y,0],0,bool(side),.98,progress=progress,tag=f'population-{side}-{j}',phase=t)
    if j:r.link([x,y+.89,-.1],[x,y+.46,-.1],progress,GOLD if side else CYAN,t)
  r.text('供給する材料は、共通',540,1300,38,(222,234,242));r.semantic.update(type_A_copies=2,type_variant_copies=4,relative_rates_are_schematic=True,amplification_progress=q)
 elif s==6:
  # Three successive cohorts; no existing molecule is recoloured into another genotype.
  fractions=[2,3,3]
  for row,y in enumerate([2.46,.53,-1.40]):
   p=b.smooth(u,row*.25,min(.96,row*.25+.22));count=fractions[row]
   for j,x in enumerate([-2.45,-.82,.82,2.45]):
    variant=j>=4-count;r.rna([x,y,0],0,variant,.67,progress=p,tag=f'cohort-{row}-{j}',phase=t)
   if row:r.link([-3.15,y+1.64,-.1],[-3.15,y+.45,-.1],p,PALE,t)
   r.text(['出発点','次の世代','その次'][row],540,727+row*275,31,(188,213,224))
  if u>split:r.text('どの型が増えるかは、条件しだい',540,1310,34,(117,215,238))
  r.semantic.update(cohort_variant_counts=fractions,cohort_size=4,visible_generations=u)
 elif s==7:
  # Four separated panels recap distinct functions, rather than claiming assembled life.
  centers=[[-1.70,1.90,0],[1.70,1.90,0],[-1.70,-.70,0],[1.70,-.70,0]]
  for j,c0 in enumerate(centers):
   q=b.smooth(u,j*.13,j*.13+.16);c0=np.array(c0,float)
   if q<=0:continue
   if j==0:
    for k in range(5):
     a=k*2*np.pi/5+t*.35;p=c0+np.array([.55*np.cos(a),.45*np.sin(a),.10*np.sin(a)])
     r.ball(p,.13,GOLD,alpha=q,rough=.20)
   elif j==1:
    r.mesh('recap_membrane',*b.sphere_mesh(32,20,.65*(1-q),(.76,.76,.76)));r.add('recap_membrane',c0,1,CYAN,alpha=.72*q,kind=2)
    for k in range(3):r.ball(c0+[-.28+k*.28,.12*np.sin(t+k),.04],.10,GOLD,alpha=q)
   elif j==2:
    r.add('cube',c0,[.29,.72,.28],[.25,.38,.44],alpha=q,rough=.65)
    for k in range(3):
     f=(t*.8+k/3)%1;r.ball(c0+[-.78+1.56*f,.32*(k-1),.36],.07,PALE,alpha=q,emit=.8)
    r.ring(c0,.90,GREEN,alpha=.35*q,progress=q)
   else:
    r.rna(c0+[0,.34,0],0,True,.64,progress=q,tag='recap-copy-a',phase=t)
    r.rna(c0+[0,-.47,0],0,True,.64,progress=q,tag='recap-copy-b',phase=t)
   r.text(['材料','境界','反応','継承'][j],290 if j%2==0 else 790,815 if j<2 else 1195,39,(230,239,244),int(255*q))
  r.semantic.update(recap_functions_revealed=min(4,int(u/.13)+1),functions_not_integrated=True)
 elif s==8:
  tree(r,u,t);r.semantic.update(inheritance_selection_link=True)
 else:
  tree(r,.15+.85*u,t,True)
  # Subtle pull-back exposes additional branches; object growth remains the main action.
  r.eye=np.array([.15+.25*u,1.25,20.2+1.3*u]);r.text('違いが残る。歴史が育つ。',540,1320,40,(255,214,143));r.semantic.update(final_branch_reveal=.15+.85*u)


def project_checks(r):
 # Separate molecules may have intentional internal bonds; only inter-group atoms are compared.
 minimum=1e9;projected=1e9;violations=[];offscreen=[];pts=[]
 for tag,p,rad in r.atoms:
  v=r.vp@np.r_[p,1.];ndc=v[:3]/v[3];screen=np.array([(ndc[0]+1)*W/2,(1-ndc[1])*H/2]);radius=H*.5/(np.tan(np.radians(37)/2)*v[3])*rad
  pts.append((tag,p,rad,screen,radius))
  if screen[0]-radius<44 or screen[0]+radius>1036 or screen[1]-radius<405 or screen[1]+radius>1435:offscreen.append(tag)
 for i,(tag,p,rad,screen,rpx) in enumerate(pts):
  for tag2,p2,rad2,screen2,rpx2 in pts[i+1:]:
   if tag==tag2:continue
   d=float(np.linalg.norm(p-p2)-rad-rad2);dp=float(np.linalg.norm(screen-screen2)-rpx-rpx2)
   minimum=min(minimum,d);projected=min(projected,dp)
   if d<-.003 or dp<-.5:violations.append((tag,tag2,round(d,3),round(dp,2)))
 return {'world_clearance':None if minimum==1e9 else minimum,'projected_atom_clearance_px':None if projected==1e9 else projected,'overlap_pairs':violations[:10],'offscreen_tags':sorted(set(offscreen))}


def do_voice():
 tl,narr=b.voice();b.dump(R/'docs/sources.json',SOURCES)
 checks=[]
 expected={'RNA':'アールエヌエー','複製':'フクセイ','継承':'ケイショオ','世代':'セダイ','割合':'ワリアイ','金色':'キンイロ','型':'カタ'}
 for word,reading in expected.items():
  rows=[c for c in tl['cues'] if word in c['text']];clean=lambda x:re.sub(r"[^ァ-ヺー]",'',x)
  got=[clean(c['kana']) for c in rows];ok=any(reading in x for x in got)
  checks.append({'word':word,'expected':reading,'readings':got,'query_reading_checked':ok})
 b.dump(R/'review/key_readings.json',checks)
 print('READING_CHECK',json.dumps(checks,ensure_ascii=False),flush=True)
 music(tl,narr);print('TIMELINE',tl['duration'],tl['max_query_speech_gap'],flush=True)

def music(tl,narr):
 T=tl['duration'];n=len(narr);tt=np.arange(n)/SR;bg=np.zeros((n,2),np.float32);rng=np.random.default_rng(6601)
 chords=[[146.832,220,293.665,440],[130.813,195.998,261.626,391.995],[174.614,261.626,349.228,523.251],[164.814,246.942,329.628,493.883]]
 for ci,notes in enumerate(chords):
  a=ci*T/4;d=(ci+1)*T/4;env=np.clip((tt-a)/.6,0,1)*np.clip((d+.5-tt)/.8,0,1)
  for j,f in enumerate(notes):
   tone=(np.sin(2*np.pi*f*tt)+.18*np.sin(2*np.pi*f*2.002*tt))*env*.006
   bg[:,j%2]+=tone;bg[:,1-j%2]+=tone*.65
 for beat,st in enumerate(np.arange(.18,T,.43)):
  a=round(st*SR);ln=min(round(.26*SR),n-a);x=np.arange(ln)/SR;ci=min(3,int(st/(T/4)));f=chords[ci][beat%4]*2
  env=np.exp(-x*16)*(1-np.exp(-x*120));tone=np.sin(2*np.pi*f*x)*env*.018;bg[a:a+ln,beat%2]+=tone;bg[a:a+ln,1-beat%2]+=tone*.48
 events=[]
 for s in range(10):
  a,d=tl['boundaries'][s:s+2];st=tl['cues'][s*2+1]['start']+.1;at=round(st*SR);ln=min(round(.48*SR),n-at);x=np.arange(ln)/SR
  noise=sosfilt(butter(2,[600,4200],btype='bandpass',fs=SR,output='sos'),rng.normal(0,1,ln));env=np.exp(-x*12)*(1-np.exp(-x*180))
  sound=np.sin(2*np.pi*(70*x+32*x*x))*np.exp(-x*12)*.075+noise*env*.025
  sound+=np.sin(2*np.pi*([880,1320,1760][s%3])*x)*np.exp(-x*35)*.022
  bg[at:at+ln]+=sound[:,None];events.append({'scene':s,'time':st,'event':'word-linked assembly, marker or branching emphasis'})
 gain=np.ones(n,np.float32)
 for c in tl['cues']:gain[max(0,round((c['start']-.10)*SR)):min(n,round((c['end']+.12)*SR))]=.38
 coarse=np.convolve(gain[::480],np.ones(7)/7,mode='same');gain=np.interp(np.arange(n),np.arange(len(coarse))*480,coarse).astype('f4');bg*=gain[:,None]
 bg*= (np.clip(tt/.18,0,1)*np.clip((T-tt)/.30,0,1))[:,None]
 sf.write(R/'audio/music_and_effects.wav',bg,SR,subtype='PCM_24');sf.write(R/'audio/mix_premaster.wav',bg+narr[:,None],SR,subtype='PCM_24');b.dump(R/'audio/sound_events.json',events)
 out=subprocess.run(['ffmpeg','-v','info','-i',str(R/'audio/mix_premaster.wav'),'-af','loudnorm=I=-16:TP=-2:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);m=json.loads(out.stderr[out.stderr.rfind('{'):out.stderr.rfind('}')+1]);b.dump(R/'audio/loudness_first_pass.json',m)
 filt='loudnorm=I=-16:TP=-2:LRA=9:linear=true:measured_I={input_i}:measured_LRA={input_lra}:measured_TP={input_tp}:measured_thresh={input_thresh}:offset={target_offset}'.format(**m)
 b.run(['ffmpeg','-y','-v','error','-i',str(R/'audio/mix_premaster.wav'),'-af',filt,'-ar',str(SR),'-c:a','pcm_s24le',str(R/'audio/master.wav')])

def shot(s,preview=False):
 tl=json.loads((R/'timeline.json').read_text());r=Scene();start=round(tl['boundaries'][s]*FPS);end=round(tl['boundaries'][s+1]*FPS);states=[];old=None
 selected=[start+round((end-start-1)*f) for f in [.08,.32,.60,.91]]
 if preview:indices=sorted(set(selected))
 else:indices=range(start,end)
 log=(R/'review'/f'ffmpeg_{s:02}.log').open('w');pipe=None
 if not preview:pipe=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','3',str(R/'render'/f'shot_{s:02}.mp4')],stdin=subprocess.PIPE,stderr=log)
 try:
  for f in indices:
   t=f/FPS;u=np.clip((t-tl['boundaries'][s])/(tl['boundaries'][s+1]-tl['boundaries'][s]),0,1);cue=next((c for c in tl['cues'] if c['start']-.07<=t<=c['end']+.16),None)
   arrange(r,s,float(u),t,tl);im,raw=r.frame(t,s,cue);qa=project_checks(r)
   tiny=np.asarray(raw.crop((45,405,1035,1435)).resize((198,206)),dtype=np.int16);diff=float(np.mean(np.abs(tiny-old))) if old is not None else 0.;old=tiny
   states.append({'frame':f,'scene':s,'raw_subject_delta':diff,**qa,'semantic':r.semantic,'whole_symbols':r.whole})
   if pipe:pipe.stdin.write(im.tobytes())
   if f in selected:im.save(R/'review'/f'p066_scene_{s:02}_{f:04}.jpg',quality=94)
   if not preview and (f-start)%48==0:print('SHOT',s,'FRAME',f-start,'OF',end-start,'GAP',qa['projected_atom_clearance_px'],'VIOLATIONS',len(qa['overlap_pairs']),flush=True)
  if pipe:pipe.stdin.close();assert pipe.wait()==0
 finally:log.close()
 b.dump(R/'review'/f'{"preview" if preview else "states"}_{s:02}.json',states)
 if preview:print('PREVIEW',s,'overlap_frames',sum(bool(x['overlap_pairs']) for x in states),'offscreen_frames',sum(bool(x['offscreen_tags']) for x in states),flush=True)

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
  vs=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(vs['nb_frames'])==round(tl['duration']*FPS)
  audio=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','adts','-']);hashes.append(hashlib.sha256(audio).hexdigest())
 assert hashes[0]==hashes[1]
 out=subprocess.run(['ffmpeg','-v','info','-i',str(high),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);lm=json.loads(out.stderr[out.stderr.rfind('{'):out.stderr.rfind('}')+1])
 states=[]
 for i in range(10):states+=json.loads((R/'review'/f'states_{i:02}.json').read_text())
 assert len(states)==round(tl['duration']*FPS)
 vals=np.array([s['raw_subject_delta'] for s in states]);win=np.convolve(vals,np.ones(48)/48,mode='valid');gaps=[x['projected_atom_clearance_px'] for x in states if x['projected_atom_clearance_px'] is not None]
 qa={'duration':tl['duration'],'frames':len(states),'native_resolution':[1080,1920],'fps':24,'audio_sample_rate':48000,'max_query_speech_gap':tl['max_query_speech_gap'],'minimum_projected_inter_molecule_atom_gap_px':min(gaps),'overlap_frames':[x['frame'] for x in states if x['overlap_pairs']],'offscreen_frames':[x['frame'] for x in states if x['offscreen_tags']],'minimum_two_second_mean_raw_picture_difference':float(win.min()),'weak_windows':[int(i) for i,v in enumerate(win) if v<.015],'loudness':lm,'audio_payload_identical':True,'caption_count':len(tl['cues']),'human_continuous_viewing':False,'auditory_listening':False,'visual_inspection':False,'limitations':'Checks compare constituent atom bounds of independent RNA symbols in world and projected coordinates. Bonds within a symbol, reaction contacts, mapping lines and decorative emphasis rings are intentional. Pixel activity is a screening metric, not a perceptual quality score.'}
 b.dump(R/'review/verification.json',qa);b.dump(R/'review/media.json',probes);b.dump(R/'review/loudness.json',lm)
 images=sorted((R/'review').glob('p066_scene_*.jpg'));sheet=Image.new('RGB',(1080,1920),(3,13,21))
 for i,p in enumerate(images[:40]):sheet.paste(Image.open(p).resize((135,240)),((i%8)*135,(i//8)*240))
 sheet.save(R/'review/contact_sheet.jpg',quality=94)
 # Frames taken from the encoded deliverable make compression and subtitle checks reproducible.
 for k,c in enumerate(tl['cues']):
  at=(c['start']+c['end'])/2;b.run(['ffmpeg','-y','-v','error','-ss',str(at),'-i',str(high),'-frames:v','1','-q:v','2',str(R/'review'/f'final_caption_{k+1:02}.jpg')])
 notes='平穏暦全史・前史066 第1版\n'+TITLE+'\n制作日・資料確認日：2026-10-28\n\n'
 notes+=f"仕様：{tl['duration']:.3f}秒、1080×1920の直接描画、24fps、{len(states)}コマ。日本語音声・音楽・効果音・字幕。軽量版720×1280。\n\n台本：\n"+'\n'.join(x[0] for x in PARTS)
 notes+='\n\n科学と演出の対応：\n冒頭は継承の問いを提示する概念映像。続く相互複製は、用意した二種類のRNA酵素が四種類の供給済み断片から互いの形成を触媒する研究が出発点。万能な一本の分子が原料なしに増える説明にはしない。\n青と珊瑚色は相互複製する二者の識別。六つの記号は配列を追うための略図であり、六塩基のRNAが実験と同じ機能をもつという意味ではない。折り畳み構造・結合角・分子形状の精密再現ではない。\n金色の四面体は受け継がれる配列上の違いの記号。研究で観測された組換えに対応する説明で、特定の有利な一点変異を観測した図ではない。\n増え方の比較と三世代の割合は、内容の理解のために設定した模式例。論文の個数、速度、世代ごとの比率や実測曲線の再現ではない。同一分子を途中で別の型へ塗り替えず、次世代の別個体を順に示す。増えやすさは基質と環境等に依存する。\n材料・境界・反応・継承の四画面は別の機能の振り返り。これらを一つの実験で統合して生命の起源を解決したという主張は含めない。最後の樹形図は継承の説明で、特定の生物系統樹や人類へ向かう進歩の階段を表さない。\n\n出典：\n'+'\n\n'.join(x['id']+' '+x['title']+'\n'+x['url']+'\nDOI '+x['doi']+'\n'+x['use'] for x in SOURCES)
 notes+='\n\n音声：VOICEVOX 四国めたん・ノーマル。エンジン0.25.2、コア0.16.1、速度1.03。RNA＝アールエヌエー、複製＝ふくせい、継承＝けいしょう、世代＝せだい、割合＝わりあい、型＝かた。合成クエリの読みと実際の音声長・発声時刻を照合。耳の試聴は未実施。\n音楽と効果音は独自の数式合成。外部楽曲・画像不使用。書体Noto Sans CJK JP。フォントと音声エンジン・モデルのファイルは配布物に含めない。\n\n確認結果：\n'+json.dumps(qa,ensure_ascii=False,indent=2)
 notes+='\n\n原音20区間、拍の時刻、編集時間軸、声の読み、撮影コード、各場面素材、完成動画からの字幕確認画像、検査記録を同梱。自動検査・静止画作成と、人が見る通し試写・耳の試聴は区別する。未実施の視聴検査を合格と記さない。\n'
 (d/(PREFIX+'_script_and_sources.txt')).write_text(notes,encoding='utf-8')
 shutil.copy(__file__,R/'source/p066_film.py');shutil.copy(BASE,R/'source/p064_v2_film.py');b.dump(R/'docs/sources.json',SOURCES)
 (R/'source/README.txt').write_text('作業ディレクトリにp066_v1を展開。原音は取得済み。python source/p066_film.py shot 0..9、最後にassemble。音声再生成のみ別途公式VOICEVOXを必要とする。ffmpeg、numpy、Pillow、scipy、soundfile、moderngl==5.12.0、glcontext==3.0.0、EGL、Noto Sans CJK JPが必要。\n',encoding='utf-8')
 manifest=[]
 for p in sorted(R.rglob('*')):
  if p.is_file() and 'voice_data' not in p.parts and p.suffix not in ['.ttf','.otf','.ttc','.zip']:manifest.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 b.dump(R/'review/manifest.json',manifest)
 archive=d/(PREFIX+'_production.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in R.rglob('*'):
   if p.is_file() and p!=archive and 'voice_data' not in p.parts and p.suffix not in ['.ttf','.otf','.ttc']:z.write(p,str(p.relative_to(R)))
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
