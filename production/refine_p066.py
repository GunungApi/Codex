"""Apply reviewed refinements to the P066 working copy before rendering.
No credentials, fonts, voice-engine files or public media are written to Git.
"""
from pathlib import Path
import json
p=Path(__file__).with_name('p066_film.py');s=p.read_text()
def patch(a,c):
 global s
 if a in s:s=s.replace(a,c)
 elif c not in s:raise RuntimeError('Expected patch anchor missing: '+a[:100])
patch("'doi':'10.1016/j.chembiol.2012.08.015'","'doi':'10.1016/j.chembiol.2012.08.017'")
patch("'RNA':'アールエヌエー'","'RNA':'アアルエヌエエ'")
patch('def pair_build(r,u,t,reverse=False):\n q=b.smooth(u,.12,.53);away=b.smooth(u,.60,.97);k=int(reverse);c=np.array([0,2.1,0.])', '''def keyword_start(tl,scene,index,needle):
 cue=tl['cues'][scene*2+index];text=''.join(m['kana'] for m in cue['moras']);at=text.find(needle)
 if at<0:return cue['start']
 total=0
 for m in cue['moras']:
  if total+len(m['kana'])>at:return cue['audio_start']+m['start']
  total+=len(m['kana'])
 return cue['start']

def join_bridge(r,center,kind,scale,progress,phase=0.):
 if progress<.985:return
 pts=[]
 for j in [2,3]:
  v=np.array([-.98+j*.392,.13*np.sin(j*1.2+kind*.8)+.018*np.sin(phase*1.5+j*.7),.10*np.sin(j*1.3)])
  pts.append(np.array(center)+v*scale)
 r.bar(pts[0],pts[1],.038*scale,CYAN if kind==0 else CORAL,emit=.30)

def pair_build(r,u,t,reverse=False,tl=None):
 scene=2 if reverse else 1;a,d=tl['boundaries'][scene:scene+2]
 trigger=keyword_start(tl,scene,0 if reverse else 1,'ツク' if reverse else 'ツナギ')
 join=np.clip((trigger-a)/(d-a),.30,.84)
 pre=b.smooth(u,.01,max(.15,join-.15));q=b.smooth(u,max(.13,join-.15),min(.94,join+.08));away=b.smooth(u,min(.94,join+.11),.998);offset=(1.03-.48*pre)*(1-q);k=int(reverse);c=np.array([0,2.1,0.])''')
patch("r.rna(c,k,False,1.45,phase=t,tag='catalyst')","r.rna(c,k,False,1.45,progress=b.smooth(u,0,.16),phase=t,tag='catalyst')")
patch("offset=1.03*(1-q)","offset=offset")
patch("r.glow_join(target+[0,.12,.15],b.smooth(u,.50,.72))","join_bridge(r,target,1-k,1.5,q,t)\n r.glow_join(target+[0,.12,.15],b.smooth(u,join+.035,min(.999,join+.24)))")
patch("r.semantic.update(substrate_approach=q,product_release=away,catalyst_type=k,product_type=1-k)","r.semantic.update(substrate_approach=q,product_release=away,catalyst_type=k,product_type=1-k,spoken_trigger_time=trigger)")
patch("elif s in [1,2]:pair_build(r,u,t,s==2)","elif s in [1,2]:pair_build(r,u,t,s==2,tl)")
patch("off=1.03*(1-q)","off=.72*(1-q)")
patch("r.glow_join(target+[0,.1,.2],b.smooth(u,.60,.85))","join_bridge(r,target,0,1.65,q,t)\n  r.glow_join(target+[0,.1,.2],b.smooth(u,.60,.85))")
patch("v=(j%3==1) or (lev==1 and j==1)","v=bool(lev>0 and j>=len(points)//2)")
patch("col=GOLD if j%3==1 else CYAN","col=GOLD if j>=len(points)//2 else CYAN")
patch("r.rna(c0+[0,-.47,0],0,True,.64,progress=q,tag='recap-copy-b',phase=t)","r.rna(c0+[0,-.47,0],0,True,.64,progress=b.smooth(u,.55,.99),tag='recap-copy-b',phase=t)\n    r.link(c0+[.125,.47,.15],c0+[.125,-.11,.15],b.smooth(u,.55,.99),GOLD,t)")
patch("else '型Bができる',540,1230,43", "else '型Bができる',540,1340,43")
patch("815 if j<2 else 1195,39", "900 if j<2 else 1330,39")
patch("minimum=1e9;projected=1e9;violations=[];offscreen=[];pts=[]", "minimum=1e9;projected=1e9;violations=[];offscreen=[];pts=[];label_hits=[]")
patch(" return {'world_clearance':None if minimum==1e9 else minimum", ''' for text,x,y,size,col,alpha in r.labels:
  if alpha<48:continue
  half=r.fontobj(size).getlength(text)/2+3
  rect=np.array([x-half,y-size*.60-3,x+half,y+size*.60+3])
  for tag,p,rad,screen,rpx in pts:
   nearest=np.clip(screen,rect[:2],rect[2:])
   if np.linalg.norm(screen-nearest)<rpx+1:label_hits.append((text,tag))
 return {'text_model_overlap':label_hits[:10],'world_clearance':None if minimum==1e9 else minimum''')
patch("def assemble():", '''def all_frame_layout_audit(tl):
 r=Scene();issues=[];inherited=[];minimum=1e9
 for fnum in range(round(tl['duration']*FPS)):
  t=fnum/FPS;scene=min(9,int(np.searchsorted(tl['boundaries'],t,side='right')-1));a,d=tl['boundaries'][scene:scene+2];u=float(np.clip((t-a)/(d-a),0,1));arrange(r,scene,u,t,tl)
  eye=r.eye;forward=b.unit(r.target-eye);right=b.unit(np.cross(forward,[0,1,0]));up=np.cross(right,forward);v=np.eye(4);v[:3,:3]=[right,up,-forward];v[:3,3]=-v[:3,:3]@eye
  k=1/np.tan(np.radians(37)/2);near=.1;far=100.;proj=np.zeros((4,4));proj[0,0]=k/(W/H);proj[1,1]=k;proj[2,2]=(far+near)/(near-far);proj[2,3]=2*far*near/(near-far);proj[3,2]=-1;r.vp=proj@v
  check=project_checks(r)
  if check['text_model_overlap']:issues.append({'frame':fnum,'scene':scene,'pairs':check['text_model_overlap']})
  if scene in [8,9]:
   for item in r.whole:
    _,level,index=item['tag'].split('-');level=int(level);index=int(index)
    if level>=2:
     expected=index>=([1,2,4,6][level]//2)
     if item['variant']!=expected:inherited.append({'frame':fnum,'tag':item['tag']})
 report={'frames':round(tl['duration']*FPS),'label_model_overlap_frames':issues,'inherited_marker_errors':inherited,'method':'Analytic projection matches the exact 37 degree perspective camera and font-metric label bounds. RNA atom bounding spheres only; manually spaced recap symbols are outside the RNA check.'}
 b.dump(R/'review/all_frame_label_and_inheritance_audit.json',report)
 print('LAYOUT_AUDIT',json.dumps(report,ensure_ascii=False),flush=True)
 assert not issues,('Label clearance',issues[:5])
 assert not inherited,('Inherited marker mismatch',inherited[:5])
 return report

def assemble():''')
patch("b.dump(R/'review/verification.json',qa);", "qa['polish_revision']=3\n assert not qa['overlap_frames'],('Independent model overlap',qa['overlap_frames'][:12])\n assert not qa['offscreen_frames'],('Model outside safe frame',qa['offscreen_frames'][:12])\n layout=all_frame_layout_audit(tl);qa['all_frame_label_checks']=layout['frames'];qa['label_model_overlap_frames']=[];qa['inherited_marker_errors']=[]\n b.dump(R/'review/verification.json',qa);")
patch("notes+='\\n\\n科学と演出の対応：", "notes+='\\n\\n磨き込み：部品結合を実音声の「つなぎ」「作る」に対応させ、二断片の中央結合を追加。組換え場面の左右余白、系統図の金色の印の継承、四機能の振り返りの終盤の組立動作を調整。説明ラベルは模型から分離し、全コマの文字とRNA模型の間隔および系統の印を検査。\\n\\n科学と演出の対応：")
patch('音声：VOICEVOX 四国めたん・ノーマル。', '音声：VOICEVOX:四国めたん（ノーマル）。')
p.write_text(s)
review=Path('p066_v1/review/key_readings.json')
if review.exists():
 rows=json.loads(review.read_text())
 for x in rows:
  if x['word']=='RNA':x['expected']='アアルエヌエエ';x['query_reading_checked']=any('アアルエヌエエ' in y for y in x['readings']);x['note']='Long vowels are represented as アア/エエ in the decoder kana, equivalent to アー/エー.'
 assert all(x['query_reading_checked'] for x in rows),rows
 review.write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print('P066 refined: speech-linked ligation, inherited markers, safe frame and label margins, primary DOI and phonetic ledger',flush=True)
