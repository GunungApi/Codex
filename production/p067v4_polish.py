"""Visual-review corrections for the event-driven fourth cut.
The v3 review revealed foreground occlusion of the crater, overly yellow lava,
and ignored text alpha. Correct those causes rather than adding camera shake.
"""
from pathlib import Path
import sys,math,json,shutil,zipfile,hashlib
import numpy as np
from PIL import Image,ImageDraw
import p067v4_kinetic as K
S=K.S;F=K.F;ROOT=K.ROOT;V=K.V;P=K.P

# Retain photographed relief but give volcanic rock a dark, legible albedo.
a='vec3 base=mix(vec3(grey),rgb,.14)*vec3(.78,.84,.90);base*=.78+.32*q.r;'
b='vec3 base=mix(vec3(grey),rgb,.20)*vec3(.37,.39,.42);base*=.65+.48*q.r;'
assert a in S.FRAG;S.FRAG=S.FRAG.replace(a,b)
start=S.FRAG.index('else if(kind==1){');end=S.FRAG.index('else if(kind==2){',start)
S.FRAG=S.FRAG[:start]+r'''else if(kind==1){
 vec2 flowing=vec2(UV.x*.85,UV.y*.21-time*.13);
 float broad=texture(detailtex,flowing).r;
 float grain=texture(detailtex,flowing*2.3+vec2(time*.016,0)).r;
 float crust=smoothstep(.455,.565,broad*.67+grain*.33);
 vec3 hot=mix(vec3(1.8,.080,.002),vec3(3.5,.48,.016),grain);
 float edge=1.-smoothstep(.015,.055,abs(broad-.50));
 col=mix(hot,vec3(.023,.018,.015)*(.35+sunlit*.65),crust*.985);
 col+=vec3(.50,.040,.001)*edge*(1.-crust);
 col*=.66+.34*clamp(heat,0.,1.7);
}
'''+S.FRAG[end:]
OLD_CONFIG=K.config

def config(t,tl):
 c=OLD_CONFIG(t,tl);s=c['scene'];a,d=tl['boundaries'][s:s+2];sec=tl['cues'][s*2+1]['start']
 if s==0 and not c['orbital']:
  q=S.ramp(t,a,sec);c['eye']=S.mix([13.,32.,-3.],[8.,30.,-7.],q).tolist();c['target']=[0,12.5,-18];c['fov']=46.;c['event']='visible_caldera_and_eruption'
 elif s==3 and t>=sec:
  q=S.ramp(t,sec,d);c['eye']=S.mix([10.,32.,-6.5],[6.5,30.5,-9.],q).tolist();c['target']=[0,13.,-18];c['fov']=47.;c['event']='clear_lava_fountain_above_rim'
 elif s==7 and c['event']=='heat_detail':
  c['eye']=[7.,31.,-8.5];c['target']=[0,13.,-18];c['fov']=47.
 return c

class Cinema(K.Cinema):
 def jets(self,cfg,t):
  strength=float(cfg['eruption'])
  if strength<.08:return
  base=float(self.g.height(0,-18))+.55;phase=float(cfg.get('jetphase',t))
  for j in range(42):
   birth=math.floor((phase+j*.071)/1.55)*1.55-j*.071;age=phase-birth
   if not 0<=age<=1.55:continue
   ang=j*2.39996;speed=1.7+.30*(j%7);vz=12.+1.25*(j%5)
   p=np.array([speed*math.cos(ang)*age,base+vz*age-4.1*age*age,-18+speed*math.sin(ang)*age])
   if p[1]<float(self.g.height(p[0],p[2]))+.13:continue
   if j>18 and strength<.65:continue
   rad=.105+.025*(j%4)
   self.draw('rock',12,S.matrix(p,[rad,rad*1.6,rad],t*.8+j),tint=(3.1,.33,.012,1))
   vel=np.array([speed*math.cos(ang),vz-8.2*age,speed*math.sin(ang)])
   tail=p-S.unit(vel)*(.32+.30*min(strength,1.7));self.draw('kineticbeam',8,K.align_beam(tail,p,.020+.006*(j%3)),tint=(1.8,.14,.004,1))

class Typography(K.BASETYPO):
 def overlay(self,im,t,cfg,tl):
  # Draw translucent text on a separate layer, then composite it onto the scene.
  out=im.convert('RGBA');out.alpha_composite(self.shade);layer=Image.new('RGBA',out.size,(0,0,0,0));d=ImageDraw.Draw(layer)
  s=cfg['scene'];a,b=tl['boundaries'][s:s+2];sec=tl['cues'][s*2+1]['start']
  self.text(d,'平穏暦全史  ／  前史067',68,128,29,(217,230,236,240),'lm')
  if s==1:
   self.text(d,'オーウェル',540,281,72,(244,236,221,255));op=round(255*S.ramp(t,sec-.06,sec+.35))
   if op:self.text(d,'約80億年前',540,1250,61,(255,218,152,op))
  elif s==2:
   self.text(d,'同じ宇宙、違う始まり',540,255,42,(215,232,240,255))
   eye=np.array(cfg['eye']);vp=S.perspective(cfg['fov'],S.W/S.H)@S.look(eye,cfg['target']);boxes=[]
   for p,title,age,col in [(V.A+[0,.85,0],'オーウェルの形成','約80億年前',(255,206,133,255)),(V.B+[0,.85,0],'太陽の形成','約46億年前',(181,227,248,255))]:
    h=vp@np.r_[p,1.];v=h[:3]/h[3];x=float(np.clip((v[0]+1)*S.W/2,225,855));y=float(np.clip((1-v[1])*S.H/2+110,690,1275))
    self.text(d,title,x,y,31,col);self.text(d,age,x,y+58,46,col);boxes.append([x-180,y-24,x+180,y+90])
   assert not(max(boxes[0][0],boxes[1][0])<min(boxes[0][2],boxes[1][2]) and max(boxes[0][1],boxes[1][1])<min(boxes[0][3],boxes[1][3])),('Chronology labels overlap',t,boxes)
   q=S.ramp(t,sec-.04,sec+.36);op=round(255*q)
   if op:
    self.text(d,'約34億年',540,455+18*(1-q),88,(255,224,165,op));self.text(d,'先に始まった世界',540,548+18*(1-q),39,(231,240,245,op))
  elif s in [3,4,6,8]:
   title={3:'若い火山世界',4:'大気が育つ',6:'同じ大地、変わった景色',8:'この海にも、時間がある'}[s];self.text(d,title,68,215,34,(220,232,237,245),'lm')
  elif s==5:self.text(d,'海が、世界を包む',540,280,49,(228,244,247,255))
  elif s==7 and t<sec:
   word={'atmosphere_detail':'空','heat_detail':'熱','water_detail':'水'}.get(cfg['event'],'')
   if word:self.text(d,word,540,276,76,(241,236,221,255))
  elif s==9:self.text(d,'次は、この海の中へ',540,275,45,(218,240,245,255))
  cue=next((c for c in tl['cues'] if c['start']-.07<=t<=c['end']+.16),None)
  if cue:
   op=min(S.ramp(t,cue['start']-.07,cue['start']+.08),1-S.ramp(t,cue['end']+.04,cue['end']+.16));rise=16*(1-S.ramp(t,cue['start']-.07,cue['start']+.11));lines=self.lines(cue['text']);cy=1550+rise;hh=87*len(lines)+32
   if op>.001:
    d.rounded_rectangle((60,cy-hh/2,1020,cy+hh/2),radius=17,fill=(3,12,20,round(145*op)))
    for j,line in enumerate(lines):self.text(d,line,540,cy+(j-(len(lines)-1)/2)*87,64,(242,247,248,round(255*op)))
  label='年代の比較  ·  光の道と奥行きは時間を表す演出' if s==2 else 'オリオン腕の世界設定  ·  地形・景観は再構成'
  self.text(d,label,540,1788,24,(187,205,214,235))
  out.alpha_composite(layer);return out.convert('RGB')

F.Cinema=Cinema;F.config=config;F.Typography=Typography

def assemble():
 K.assemble()
 qa=json.loads((ROOT/'review/verification.json').read_text());qa.update(previous_v3_frames_visually_inspected=True,crater_visibility_reframed=True,lava_crust_contrast_revised=True,caption_alpha_compositing_corrected=True)
 F.dump(ROOT/'review/verification.json',qa)
 note=ROOT/'deliverables'/f'{F.PREFIX}_script_and_sources.txt';text=note.read_text();text+='\n追加の目視に基づく修正：前版の火口・海岸・年代比較の実画像を確認し、火口が手前の岩に隠れる構図、一様に黄く発光する溶岩、文字の透過が適用されない合成を修正。火口内が見える上方の撮影位置へ変更し、暗い冷却殻と赤橙色の流体を分けた。最終版の連続動画再生・耳の試聴と、静止画目視を区別する。\n'
 note.write_text(text,encoding='utf-8');shutil.copy(__file__,ROOT/'source'/Path(__file__).name)
 (ROOT/'source/REEDIT.txt').write_text('第4版の実行入口はp067v4_polish.py。sourceのp067v2_scene.py、p067v2_finish.py、p067v3_rocktime.py、p067v3_phototexture.py、p067v4_kinetic.pyを同じフォルダに置く。p067_v4を作業ディレクトリにしてpython source/p067v4_polish.py shot N（0..9）。完成MP4をoriginal_previewに置きassembleでAACをコピー。原音、材質、timeline.jsonを保持。P067_FONTで日本語書体を指定。',encoding='utf-8')
 archive=ROOT/'deliverables'/f'{F.PREFIX}_production.zip';archive.unlink()
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in ROOT.rglob('*'):
   if p.is_file() and p!=archive and p.suffix.lower() not in ['.ttf','.otf','.ttc','.zip'] and 'review_ooxml' not in p.parts and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(ROOT)))
 print('POLISHED_FINAL',json.dumps(qa,ensure_ascii=False),flush=True)
 print('POLISHED_FILES',json.dumps([{'name':p.name,'bytes':p.stat().st_size} for p in (ROOT/'deliverables').iterdir()],ensure_ascii=False),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':P.acquire_assets();F.prepare()
 elif mode=='preview':
  for s in [0,2,3,5,6,8,9]:F.shot(s,True)
  K.review_package()
 elif mode=='testclip':F.shot(2);F.shot(3)
 elif mode=='shot':F.shot(int(sys.argv[2]))
 elif mode=='assemble':assemble()
 else:raise ValueError(mode)
