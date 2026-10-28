"""P067 v2 production entrypoint. Existing corrected voice is preserved exactly.
Run prepare, preview, shot N, assemble. Work products are private workflow artifacts.
Do not put generated frames, fonts, voice models, credentials or signed URLs in Git.
"""
from pathlib import Path
import os,sys,json,math,shutil,zipfile,subprocess,hashlib,re,time
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from p067v2_scene import Cinema,ROOT,W,H,FPS,config,ease,ramp
PREFIX='heionreki_p067_v2'
FONT=os.environ.get('P067_FONT','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
TITLE='八十億年前、別の世界が生まれた'
CAPTIONS={
'この惑星の歴史は、始まっていた。':['この惑星の歴史は、','始まっていた。'],
'オリオン腕の世界、オーウェル。':['オリオン腕の世界、','オーウェル。'],
'太陽が生まれるのは、約四十六億年前。':['太陽が生まれるのは、','約四十六億年前。'],
'およそ三十四億年も、先に始まった世界だ。':['およそ三十四億年も、','先に始まった世界だ。'],
'地下から出た気体が、空へ広がる。':['地下から出た気体が、','空へ広がる。'],
'厚い二酸化炭素の大気ができていく。':['厚い二酸化炭素の','大気ができていく。'],
'今度は、海の向こうに見える。':['今度は、','海の向こうに見える。'],
'別々に見てきた働きが、一つの歴史になる。':['別々に見てきた働きが、','一つの歴史になる。'],
'地球へ続く時間の、ずっと手前で、':['地球へ続く時間の、','ずっと手前で、'],
'この海には、この世界の時間が流れていた。':['この海には、この世界の','時間が流れていた。'],
'オーウェルの、生命の始まりを訪ねよう。':['オーウェルの、','生命の始まりを訪ねよう。']}

def dump(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def run(cmd,**kw):return subprocess.run(cmd,check=True,**kw)
def timeline():return json.loads((ROOT/'timeline.json').read_text())

def prepare():
 src=Path('recovered_audio')
 if (src/'p067_v1').exists():src=src/'p067_v1'
 assert (src/'timeline.json').exists()
 for sub in ['audio','docs','source']:
  if (src/sub).exists():shutil.copytree(src/sub,ROOT/sub,dirs_exist_ok=True)
 shutil.copy(src/'timeline.json',ROOT/'timeline.json')
 if (src/'review/key_readings.json').exists():shutil.copy(src/'review/key_readings.json',ROOT/'review/inherited_readings.json')
 tl=timeline();assert abs(tl['duration']-51.916666666666664)<.001
 assert 'オリオンワン' in re.sub(r"[^ァ-ヺー]",'',tl['cues'][2]['kana'])
 dump(ROOT/'review/audio_inheritance.json',{'source_run':40693127363,'source_artifact':'p067-v1-audio','master_sha256':hashlib.sha256((ROOT/'audio/master.wav').read_bytes()).hexdigest(),'narration_regenerated':False,'speech_times_preserved':True,'max_query_speech_gap':tl['max_query_speech_gap'],'auditory_listening':False})
 print('PREPARED_AUDIO',tl['duration'],tl['max_query_speech_gap'],flush=True)

class Typography:
 def __init__(self):
  assert Path(FONT).is_file(),FONT;self.fonts={}
  # Transparent gradient keeps the scene visible instead of a large solid label box.
  self.shade=Image.new('RGBA',(W,H),(0,0,0,0));a=np.zeros((H,W,4),np.uint8);a[:,:,0]=2;a[:,:,1]=8;a[:,:,2]=13
  yy=np.arange(H);alpha=np.maximum(np.clip((310-yy)/310,0,1)*160,np.clip((yy-1360)/430,0,1)*165);a[:,:,3]=alpha[:,None].astype('u1');self.shade=Image.fromarray(a)
 def font(self,n):
  if n not in self.fonts:self.fonts[n]=ImageFont.truetype(FONT,n)
  return self.fonts[n]
 def text(self,d,txt,x,y,size=42,col=(242,247,248,255),anchor='mm'):
  d.text((x,y),txt,font=self.font(size),fill=col,anchor=anchor,stroke_width=1,stroke_fill=(2,7,11,col[-1]))
 def lines(self,text):
  if text in CAPTIONS:return CAPTIONS[text]
  if self.font(64).getlength(text)<=920:return [text]
  can=[i for i in range(1,len(text)) if self.font(64).getlength(text[:i])<=920 and self.font(64).getlength(text[i:])<=920 and text[i] not in '、。ー！？']
  assert can,('long subtitle',text);q=min(can,key=lambda i:abs(self.font(64).getlength(text[:i])-self.font(64).getlength(text[i:]))-(50 if text[i-1]=='、' else 0));return [text[:q],text[q:]]
 def overlay(self,im,t,cfg,tl):
  out=im.convert('RGBA');out.alpha_composite(self.shade);d=ImageDraw.Draw(out,'RGBA');s=cfg['scene'];a,b=tl['boundaries'][s:s+2];u=cfg['u'];sec=tl['cues'][s*2+1]['start']
  self.text(d,'平穏暦全史  ／  前史067',68,128,29,(217,230,236,240),'lm')
  if s==1:
   self.text(d,'オーウェル',540,281,72,(244,236,221,255))
   op=int(255*ramp(t,sec-.06,sec+.35));self.text(d,'約80億年前',540,1250,61,(255,218,152,op))
  if s==2:
   d.rounded_rectangle((103,435,978,1355),radius=26,fill=(4,11,18,215))
   p=ramp(t,a+.08,sec+.22);y0,y1=600,1136
   d.line((218,y0,218,y0+(y1-y0)*p),fill=(181,201,214,225),width=7)
   d.ellipse((200,y0-18,236,y0+18),fill=(250,200,113,255));self.text(d,'オーウェルの形成',557,535,40,(241,225,199,255));self.text(d,'約80億年前',557,612,64,(255,218,152,255))
   op=int(255*ramp(t,a+.7,sec-.08));self.text(d,'太陽の形成',557,1060,40,(210,228,239,op));self.text(d,'約46億年前',557,1143,64,(174,220,241,op));d.ellipse((200,y0+(y1-y0)*p-18,236,y0+(y1-y0)*p+18),fill=(158,215,240,255))
   q=ramp(t,sec-.07,sec+1.1);op=int(255*q);self.text(d,'約34億年も前',575,868,67,(246,246,238,op));self.text(d,'同じ宇宙、違う始まり',540,1292,32,(191,211,220,255))
  if s in [3,4,6,8]:
   txt={3:'若い火山世界',4:'大気が育つ',6:'同じ大地、変わった景色',8:'この海にも、時間がある'}[s];self.text(d,txt,68,215,34,(220,232,237,245),'lm')
  if s==5:self.text(d,'海が、世界を包む',540,280,49,(228,244,247,255))
  if s==7:
   cue=tl['cues'][14]
   if t<sec:
    word={'atmosphere_detail':'空','heat_detail':'熱','water_detail':'水'}.get(cfg['event'],'')
    self.text(d,word,540,276,76,(241,236,221,255))
  if s==9:self.text(d,'次は、この海の中へ',540,275,45,(218,240,245,255))
  cue=next((c for c in tl['cues'] if c['start']-.07<=t<=c['end']+.16),None)
  if cue:
   op=min(ramp(t,cue['start']-.07,cue['start']+.08),1-ramp(t,cue['end']+.04,cue['end']+.16));rise=16*(1-ramp(t,cue['start']-.07,cue['start']+.11));lines=self.lines(cue['text']);assert len(lines)<=2
   cy=1550+rise;hh=87*len(lines)+32;d.rounded_rectangle((60,cy-hh/2,1020,cy+hh/2),radius=17,fill=(3,12,20,int(145*op)))
   for i,line in enumerate(lines):self.text(d,line,540,cy+(i-(len(lines)-1)/2)*87,64,(242,247,248,int(255*op)))
  self.text(d,'オリオン腕の世界設定  ·  地形・景観は再構成',540,1788,24,(187,205,214,235))
  return out.convert('RGB')

def shot(s,preview=False):
 tl=timeline();r=Cinema();typ=Typography();a=round(tl['boundaries'][s]*FPS);b=round(tl['boundaries'][s+1]*FPS);samples=sorted(set(a+round((b-a-1)*p) for p in [.10,.33,.60,.89]));indices=samples if preview else range(a,b);states=[];last=None
 log=(ROOT/'review'/f'encoder_{s:02}.log').open('w');proc=None
 if not preview:proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-threads','3',str(ROOT/'render'/f'shot_{s:02}.mp4')],stdin=subprocess.PIPE,stderr=log)
 try:
  for f in indices:
   t=f/FPS;cfg=config(t,tl);raw,check=r.frame(cfg,t);out=typ.overlay(raw,t,cfg,tl);tiny=np.asarray(raw.crop((35,350,1045,1440)).resize((202,218)),dtype=np.int16);delta=float(np.abs(tiny-last).mean()) if last is not None else 0;last=tiny
   issues=[]
   if check['camera_terrain_clearance'] is not None and check['camera_terrain_clearance']<.28:issues.append('camera_terrain_intersection')
   stat={'frame':f,'time':t,'scene':s,'raw_picture_change':delta,'mean_luma':float(tiny.mean()),'issues':issues,**check};states.append(stat)
   if proc:proc.stdin.write(out.tobytes())
   if f in samples:out.save(ROOT/'review'/f'p067v2_s{s:02}_f{f:04}.jpg',quality=95)
   if (f-a)%24==0 or preview:print('FRAME',s,f-a,'/',b-a,'clearance',check['camera_terrain_clearance'],'event',cfg['event'],'issues',issues,flush=True)
  if proc:proc.stdin.close();assert proc.wait()==0
 finally:log.close()
 dump(ROOT/'review'/f'{"preview" if preview else "states"}_{s:02}.json',states)
 if any(x['issues'] for x in states):raise RuntimeError([x for x in states if x['issues']][:3])
 print('SHOT_DONE',s,len(states),flush=True)

def ts(x,ass=False):
 if ass:return f'{int(x//3600)}:{int(x//60)%60:02}:{int(x)%60:02}.{int((x%1)*100):02}'
 z=round(x*1000);return f'{z//3600000:02}:{z//60000%60:02}:{z//1000%60:02},{z%1000:03}'

def subtitles(tl):
 typ=Typography();ja=[];en=[]
 ass=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','WrapStyle: 2','ScaledBorderAndShadow: yes','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding','Style: Default,Noto Sans CJK JP,64,&H00F8F7F2,&H00EED775,&HBB180E03,&HBB180E03,1,0,0,0,100,100,0,0,3,14,0,5,60,60,200,1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 for c in tl['cues']:
  a=max(0,c['start']-.07);b=min(tl['duration'],c['end']+.16);j='\n'.join(typ.lines(c['text']));ja.append(f"{c['id']}\n{ts(a)} --> {ts(b)}\n{j}\n");en.append(f"{c['id']}\n{ts(a)} --> {ts(b)}\n{c['en']}\n")
  txt=r'{\move(540,1566,540,1550,0,180)\fad(140,120)}'+r'\N'.join(typ.lines(c['text']));ass.append(f'Dialogue: 0,{ts(a,True)},{ts(b,True)},Default,,0,0,0,,{txt}')
 for su,ls in [('ja.srt',ja),('en.srt',en),('ja.ass',ass)]:(ROOT/'deliverables'/f'{PREFIX}_{su}').write_text('\n'.join(ls),encoding='utf-8')

def assemble():
 tl=timeline();subtitles(tl);d=ROOT/'deliverables';lst=ROOT/'render/concat.txt';lst.write_text(''.join("file '"+str((ROOT/'render'/f'shot_{i:02}.mp4').resolve())+"'\n" for i in range(10)))
 pic=ROOT/'render/picture_full.mp4';run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(pic)])
 original=next(Path('original_preview').rglob('*.mp4'));high=d/f'{PREFIX}_high_1080x1920.mp4';light=d/f'{PREFIX}_light_720x1280.mp4'
 run(['ffmpeg','-y','-v','error','-i',str(pic),'-i',str(original),'-map','0:v','-map','1:a:0','-c','copy','-t',str(tl['duration']),'-movflags','+faststart',str(high)])
 run(['ffmpeg','-y','-v','error','-i',str(high),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','fast','-crf','23','-threads','3','-c:a','copy','-movflags','+faststart',str(light)])
 probes={};ah=[]
 for p in [original,high,light]:
  run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'])
  pp=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]));probes[p.name]=pp
  v=next(x for x in pp['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==round(tl['duration']*FPS)
  by=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','adts','-']);ah.append(hashlib.sha256(by).hexdigest())
 assert len(set(ah))==1
 rows=[]
 for i in range(10):rows+=json.loads((ROOT/'review'/f'states_{i:02}.json').read_text())
 assert len(rows)==round(tl['duration']*FPS)
 vals=np.array([x['raw_picture_change'] for x in rows]);wins=np.convolve(vals,np.ones(48)/48,'valid')
 lm=subprocess.run(['ffmpeg','-v','info','-i',str(high),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);loud=json.loads(lm.stderr[lm.stderr.rfind('{'):lm.stderr.rfind('}')+1])
 qa={'native_resolution':[W,H],'fps':FPS,'duration':tl['duration'],'frames':len(rows),'caption_count':len(tl['cues']),'max_query_speech_gap':tl['max_query_speech_gap'],'aac_identical_to_previous_approved_cut':len(set(ah))==1,'loudness':loud,'camera_issues':[x['frame'] for x in rows if x['issues']],'minimum_camera_to_terrain_clearance':min(x['camera_terrain_clearance'] for x in rows if x['camera_terrain_clearance'] is not None),'terrain_triangles':rows[0]['terrain_triangles'],'minimum_2_second_mean_picture_change':float(wins.min()),'weak_motion_windows':[int(i) for i,x in enumerate(wins) if x<.025],'visual_inspection_performed':False,'continuous_preview_watched':False,'auditory_listening_performed':False,'limitations':'Pixel variation is an editing aid, not a perceptual quality score. World-space camera tests do not test every material or occlusion. Reflection is a half-resolution secondary pass; all final views and geometry are rendered directly at 1080x1920.'}
 assert not qa['camera_issues'],qa['camera_issues'][:5]
 dump(ROOT/'review/verification.json',qa);dump(ROOT/'review/media.json',probes)
 # Actual encoded frames and short continuous excerpts are retained for review.
 for i,c in enumerate(tl['cues']):
  run(['ffmpeg','-y','-v','error','-ss',str((c['start']+c['end'])/2),'-i',str(high),'-frames:v','1','-q:v','2',str(ROOT/'review'/f'encoded_{i:02}.jpg')])
 for i,s in enumerate([0,3,6,9]):
  a=tl['boundaries'][s];run(['ffmpeg','-y','-v','error','-ss',str(a),'-i',str(high),'-t','2.0','-vf','scale=540:960','-c:v','libx264','-preset','fast','-crf','22','-c:a','aac',str(ROOT/'review'/f'continuous_review_{s:02}.mp4')])
 shots=sorted((ROOT/'review').glob('encoded_*.jpg'));sheet=Image.new('RGB',(1080,1920),(3,9,15))
 for i,p in enumerate(shots):sheet.paste(Image.open(p).resize((216,384)),((i%5)*216,(i//5)*384))
 sheet.save(ROOT/'review/encoded_contact_sheet.jpg',quality=94)
 notes='平穏暦全史・前史067 第2版\n'+TITLE+'\n制作・資料確認：2026-10-28\n\n'
 notes+='改訂の中心：旧版の単純な火山形状・球体状の噴煙・反復した同一画角を、深い火口と放射状の谷、凹凸のある玄武岩、地面に沿う溶岩流、世界座標の密度場を使う噴煙、反射・浅瀬・岸の泡を持つ海へ変更。近接→惑星全景→年代比較→衝突→火口→空→全球海→同じ火山の海岸→潜水という撮影順。\n'
 notes+='映像は立体メッシュとGLSLによるオリジナルの再現。平面画像の拡大を主要場面に使用していない。地上地形は344064三角形。実際の岩体の接地、火口・尾根の座標は全地上場面で共通。薄い溶岩の帯は地形標高に追従。海は動く三次元メッシュ。噴煙はボリューム密度をレイマーチし、球体の積み上げを廃止。惑星と海岸の縮尺は別の再現模型。\n'
 notes+='維持したもの：全20区間の確認済み台本、原音、発声時刻、音楽・効果音。旧版の完成AAC音声を2本へ無再圧縮で引き継ぎ、3ファイルの音声ハッシュが一致。音声読みはオリオン腕＝オリオンわんを含む修正後の記録を継承。声の耳による再試聴は未実施。\n\n台本：\n'+'\n'.join(c['text'] for c in tl['cues'])
 notes+='\n\n公式設定と演出：\n約80億年前の形成、初期の衝突・火山活動、厚い二酸化炭素大気、世界規模の海が原典の軸。海岸線、火口、岩壁、雲、波、隕石の経路は独自の景観再構成。これを不穏暦の景観表現として添えるが、年代の軸は平穏暦と対応。二酸化炭素そのものの色を描いたものではなく、雲・噴煙・霞は視認できる凝結物・粒子等の表現。海の形成の時間圧縮は実測速度を表さない。原典にない気圧値や山脈名、生物は追加しない。\n'
 notes+='\n出典：\nTSSL, Orwell, Geological Periods, Orion\'s Arm Universe Project\nhttps://www.orionsarm.com/eg-article/546a05829e265\nTSSL, The Early Evolutionary History of Orwell\nhttps://www.orionsarm.com/eg-article/54749a15e55ef\nNASA Science, Sun Facts, Formation\nhttps://science.nasa.gov/sun/facts/\n約80億年と約46億年の差は概算で34億年。\n'
 notes+='\n音声：VOICEVOX 四国めたん（ノーマル）。音楽と効果音は前版の専用数式合成を継承。外部写真・楽曲なし。書体Noto Sans CJK JPは環境依存。フォントと音声モデルは配布物に含めない。\n'
 notes+='\n検証結果と未確認範囲：\n'+json.dumps(qa,ensure_ascii=False,indent=2)+'\n\n高画質・軽量とも全編復号。実書き出しから20枚、主要場面の連続2秒映像4本を保存。自動検査を目視・耳の試聴と同一視しない。\n'
 (d/f'{PREFIX}_script_and_sources.txt').write_text(notes,encoding='utf-8')
 for name in ['p067v2_scene.py','p067v2_finish.py']:shutil.copy(Path(__file__).with_name(name),ROOT/'source'/name)
 (ROOT/'source/REEDIT.txt').write_text('作業フォルダにp067_v2として展開。pip install numpy scipy Pillow moderngl==5.12.0 glcontext==3.0.0。ffmpegとEGL、Noto Sans CJK JPを用意。P067_FONTで書体を指定。sourceの2本を同じフォルダに配置し、python source/p067v2_finish.py shot 0（0..9）で場面再生成。assembleは旧版音声を含むMP4をoriginal_previewへ置いて実行。原音とmaster.wavも同梱。\n',encoding='utf-8')
 manifest=[]
 for p in ROOT.rglob('*'):
  if p.is_file() and p.suffix not in ['.ttf','.otf','.ttc','.zip'] and 'voice_data' not in p.parts:manifest.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 dump(ROOT/'review/manifest.json',manifest)
 arc=d/f'{PREFIX}_production.zip'
 with zipfile.ZipFile(arc,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in ROOT.rglob('*'):
   if p.is_file() and p!=arc and p.suffix not in ['.ttf','.otf','.ttc'] and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(ROOT)))
 print('FINAL_QA',json.dumps(qa,ensure_ascii=False),flush=True);print('FILES',[(p.name,p.stat().st_size) for p in d.iterdir()],flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':prepare()
 elif mode=='shot':shot(int(sys.argv[2]))
 elif mode=='preview':
  for s in [0,1,3,4,5,6,7,9]:shot(s,True)
 elif mode=='assemble':assemble()
 else:raise ValueError(mode)
