from pathlib import Path
p=Path(__file__).with_name('p067_film.py');s=p.read_text()
def patch(a,c):
 global s
 assert a in s, a[:120]
 s=s.replace(a,c)
patch("READING={'八十億年前'", "READING={'オリオン腕':'オリオンわん','八十億年前'")
patch("expected={'八十億年前'", "expected={'オリオン腕':['オリオンワン'],'八十億年前'")
patch("q.y+=.075*sin(a)+.045*sin(b);nn=normalize(vec3(-.124*cos(a)-.0324*cos(b),1.,-.039*cos(a)+.063*cos(b)));", "q.y+=(.075*sin(a)+.045*sin(b))*(1.+mat.z);nn=normalize(vec3((-.124*cos(a)-.0324*cos(b))*(1.+mat.z),1.,(-.039*cos(a)+.063*cos(b))*(1.+mat.z)));")
patch("self.terrain_check=False;self.immersion=False;self.frame_notes=[]", "self.terrain_check=False;self.immersion=False;self.waveboost=0.;self.frame_notes=[]")
patch("self.add('watermesh',(0,sea,0),1,[.03,.18,.22],kind=6,rough=.05)", "self.add('watermesh',(0,sea,0),1,[.03,.18,.22],kind=6,rough=.05,emit=self.waveboost)")
patch("r.eye=np.array([6.8-2.4*b.ease(u),4.25+.4*np.sin(u*np.pi),12.6-2.0*b.ease(u)]);r.target=np.array([-1.2,1.9,-5.2]);r.terrain(t,sea=1.35,eruption=.12 if s!=7 else .55,vapor=.50,water_visible=True)", "r.eye=np.array([6.8-2.4*b.ease(u),4.25+.4*np.sin(u*np.pi),12.6-2.0*b.ease(u)]);r.target=np.array([-1.2,1.9,-5.2])\n  eruption=.12;vapor=.50\n  if s==7:\n   air=b.smooth(t,keytime(tl,14,'ソラ')-.06,keytime(tl,14,'ソラ')+.7);hot=b.smooth(t,keytime(tl,14,'ネツ')-.06,keytime(tl,14,'ネツ')+.7);wet=b.smooth(t,keytime(tl,14,'ミズ')-.06,keytime(tl,14,'ミズ')+.7)\n   r.eye=np.array([4.5-1.1*u,12.5,8.6-.9*u]);eruption=.15+.72*hot;vapor=.22+.66*air;r.waveboost=.90*wet;r.semantic.update(air_emphasis=air,heat_emphasis=hot,wave_emphasis=wet)\n  r.terrain(t,sea=1.35,eruption=eruption,vapor=vapor,water_visible=True)")
patch("music(tl,narr);print('TIMELINE'", "assert all(c['query_reading_checked'] for c in checks),checks\n # Independent waveform energy screening supplements the decoder schedule.\n hop=480;blocks=narr[:len(narr)//hop*hop].reshape(-1,hop);rms=np.sqrt(np.mean(blocks*blocks,axis=1));sil=rms<max(.0007,float(rms.max())*.008);runs=[];start=None\n for i,quiet in enumerate(np.r_[sil,False]):\n  if quiet and start is None:start=i\n  elif not quiet and start is not None:runs.append([start*.01,i*.01]);start=None\n b.dump(R/'review/waveform_silence.json',{'threshold_method':'10ms RMS, max(0.0007, peak block RMS * 0.008)','max_interval_seconds':max((y-x for x,y in runs),default=0),'intervals':runs,'auditory_listening':False})\n music(tl,narr);print('TIMELINE'")
patch("'caption_count':len(tl['cues']),'visual_inspection'", "'caption_count':len(tl['cues']),'waveform_silence_screen':json.loads((R/'review/waveform_silence.json').read_text()),'key_readings_checked':json.loads((R/'review/key_readings.json').read_text()),'visual_inspection'")
patch('八十億年前、四十六億年前、三十四億年、隕石、溶岩、二酸化炭素の読みを指定', 'オリオン腕＝オリオンわん、八十億年前、四十六億年前、三十四億年、隕石、溶岩、二酸化炭素の読みを指定')
p.write_text(s)
print('P067 spoken reading and three-process semantic animation refined.')
