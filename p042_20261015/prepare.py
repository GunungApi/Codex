"""Build HEION-P042 from real original waveforms, with shared editorial timing."""
from pathlib import Path
import json, math, wave, hashlib, shutil, sys
HERE=Path(__file__).parent
old=(HERE/'inherited_prepare.py').read_text()
# Inherited, previously validated audio/clock helpers; source preserved in the package.
exec(old.split('# Each range')[0].replace("Path('p041')","Path('p042')"),globals())
(ROOT/'audio/edited').mkdir(parents=True,exist_ok=True)
SPEC=[
 [(0,1,'小さな惑星が見つかった。','A small planet has been found.'),(1,3,'そこに、\n海もあるだろうか。','Does it have an ocean?'),(3,5,'同じ大きさでも、\n環境で景色は変わる。','Same size, different conditions.\nDifferent worlds.')],
 [(0,2,'まず、星から届く光。','First, the light from its star.'),(2,4,'同じ星なら、\n距離が2倍になると、','For the same star,\nat twice the distance,'),(4,5,'受け取る光は、4分の1。','the incoming light is one quarter.')],
 [(0,2,'次は、大気。','Next, the atmosphere.'),(2,3,'光を反射し、','It reflects some light,'),(3,5,'地面から出る熱を吸収して、\nふたたび放つ。','absorbs heat from the surface,\nand radiates it again.'),(5,7,'その働きで、\n地表の温度が変わる。','This changes the\nsurface temperature.')],
 [(0,2,'水が液体でいられるかは、\n温度と気圧しだい。','Liquid water depends on\ntemperature and pressure.'),(2,4,'氷も、流れる水も、','Ice and flowing water,'),(4,6,'水蒸気も、\n同じ水の違う姿だ。','and water vapor: different\nstates of the same substance.')],
 [(0,1,'適切な大気のもとで、','With a suitable atmosphere,'),(1,2,'地表に液体の水が\nありうる距離の帯。','a range of distances could\nallow liquid surface water.'),(2,4,'これが、\nハビタブルゾーン。','This is the habitable zone.'),(4,6,'生命の証拠は、\nさらに別に探す。','Evidence of life\nis a further question.')],
 [(0,2,'惑星を見つけた先に、\n環境を知る旅がある。','Finding a planet begins\na journey into its environment.'),(2,4,'古い世界に、\n何が続いてきたのか。','What history has unfolded\non these ancient worlds?'),(4,6,'その中身を、\n確かめに行こう。','Let us investigate\nwhat lies beyond its outline.')]
]
records=json.loads((ROOT/'audio/raw/retrieval.json').read_text());segments=[];captions=[];checks=[];cursor=.35
for i,(rec,spec) in enumerate(zip(records,SPEC),1):
    path=ROOT/'audio/raw'/rec['file']; raw=readwav(path);q=json.loads((path.parent/f'{i:02d}_query.json').read_text())
    groups,moras,n=phrase_clock(q);assert n==len(raw),(i,n,len(raw));assert sha(path)==rec['sha256']
    print('GROUPS',i,[g['kana'] for g in groups],flush=True)
    assert len(groups)==max(x[1] for x in spec),(i,len(groups),spec)
    # Preserve all spoken samples. Add quiet observation beats between water states only.
    gaps=[(round(groups[g]['end']*SR),round(sec*SR)) for g,sec in ([(2,.70),(3,1.0)] if i==4 else [])]
    pieces=[];last=0
    for at,gap in gaps:
        pieces.extend([raw[last:at],np.zeros(gap,dtype='<i2')]);last=at
    pieces.append(raw[last:]);edited=np.concatenate(pieces)
    with wave.open(str(ROOT/'audio/edited'/rec['file']),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(edited.tobytes())
    def shifted(t,is_end=False):
        ns=round(t*SR);return (ns+sum(g for p,g in gaps if p<ns if is_end or p<=ns))/SR
    # Endpoint of the phrase preceding an inserted pause stays in place.
    for g in groups:
        s,e=round(g['start']*SR),round(g['end']*SR)
        g['start']=(s+sum(n for p,n in gaps if p<=s))/SR
        g['end']=(e+sum(n for p,n in gaps if p<e))/SR
    start=round(cursor*SR)/SR;end=start+len(edited)/SR
    segments.append(dict(id=i,file=rec['file'],start=start,end=end,duration=len(edited)/SR,original_duration=len(raw)/SR,text=rec['text'],groups=groups,kana=rec['kana'],inserted_silence_samples=gaps))
    for lo,hi,ja,en in spec:
        captions.append(dict(start=max(0,start+groups[lo]['start']-.065),end=start+groups[hi-1]['end']+.155,ja=ja,en=en,segment=i,groups=[lo,hi]))
    # Verify removing the inserted silence restores every original sample exactly.
    restored=[];p=0;offset=0
    for at,nz in gaps:
        cut=at+offset;restored.append(edited[p:cut]);p=cut+nz;offset+=nz
    restored.append(edited[p:]);assert np.array_equal(np.concatenate(restored),raw)
    checks.append(dict(id=i,raw_sha256=sha(path),original_samples=len(raw),phoneme_samples=n,original_samples_preserved=True,inserted_silence_samples=gaps,kana=rec['kana'],groups=groups))
    cursor=math.ceil((end+.52)*FPS)/FPS
end_voice=segments[-1]['end'];frames=math.ceil((end_voice+4.5)*FPS);duration=frames/FPS

def gs(s,g):return segments[s]['start']+segments[s]['groups'][g]['start']
# Transitions key off actual speech, not a fixed fifty-six-second script.
bounds=[0,gs(0,3),segments[1]['start'],segments[2]['start'],gs(2,3),segments[3]['start'],gs(3,3),gs(3,4),segments[4]['start'],gs(4,4),segments[5]['start'],end_voice,duration]
kinds=['opening','twins','flux','reflect','heat','ice','liquid','vapor','zone','evidence','shore','ending']
bf=[round(t*FPS) for t in bounds];bf[-1]=frames;assert all(b>a for a,b in zip(bf,bf[1:]))
shots=[dict(id=i,kind=k,start_frame=bf[i],end_frame=bf[i+1],start=bf[i]/FPS,end=bf[i+1]/FPS) for i,k in enumerate(kinds)]
plan=dict(id='HEION-P042',version=1,width=1080,height=1920,fps=FPS,frames=frames,duration=duration,narration=segments,captions=captions,shots=shots,seed=420042,model_note='環境の比較模型／実在惑星の表面を復元した映像ではない',data_scope='surface liquid water under suitable conditions; not a claim about all life or human breathing')
put(ROOT/'timeline.json',plan);put(ROOT/'assets/system.json',dict(radius_pair=[1.,1.],star_luminosity_fixed=1.,distance_ratio=[1.,2.],flux_ratio=[1.,.25],geometry_seed=420042,life_detected=False))
put(ROOT/'validation/original_audio_integrity.json',checks)
put(ROOT/'validation/model_assertions.json',dict(equal_planet_radii=True,stellar_power_held_fixed=True,inverse_square_ratio=(1/2)**2,no_claimed_surface_temperature=True,water_states='separate explanatory conditions; not a quantitative planetary climate calculation',water_vapor_is_transparent=True,habitable_zone_not_life_detection=True))
# Reuse only the established typography and audio finishing method.
sub=old.split('# Subtitle files')[1].split('# Keep the received PCM')[0]
exec(sub.replace('p041','p042'),globals())
tail=old.split('# Keep the received PCM')[1].split("for p in Path('p041_20261015')")[0]
tail='# Keep the received PCM'+tail
exec(tail.replace("ROOT/'audio/raw'/s['file']","ROOT/'audio/edited'/s['file']").replace('TP=-2','TP=-2.3'),globals())
for p in HERE.glob('*.py'):shutil.copy2(p,ROOT/'code'/p.name)
put(ROOT/'validation/edit_summary.json',dict(duration=duration,frames=frames,shots=shots,caption_count=len(captions),raw_segments=len(records),raw_total=sum(r['duration'] for r in records),voice_end=end_voice,observation_pause_added=1.7))
(ROOT/'reference/inheritance.md').write_text('前史041の描画支援、字幕意匠、音素時計、混音方法を継承。前史041の実際の比較画像と基準第5版の画像をFilesで確認した。P042の地形、同半径二惑星、水面・氷・大気の材質、放射経路は新規制作。原音6区間は今回生成。手元の実行環境のClientErrorを記録し、許可されたGitHub Actionsへ制作を切り替えた。実聴および投稿端末の試写は未実施。',encoding='utf-8')
print('EDIT_READY',json.dumps(dict(duration=duration,frames=frames,shots=shots,caption_count=len(captions)),ensure_ascii=False),flush=True)
