"""Render-independent audio, parallel native-resolution shots, then one verified edit."""
import os,sys,json,math,subprocess,shutil
from pathlib import Path
import numpy as np
from PIL import Image
import p064_v2_film as f
R=f.ROOT
mode=sys.argv[1]
if mode=='voice':
 timeline,narration=f.voice();f.music(timeline,narration)
 print('VOICE_SUMMARY',json.dumps({'duration':timeline['duration'],'gap':timeline['max_query_speech_gap'],'kana':[c['kana'] for c in timeline['cues']]},ensure_ascii=False),flush=True)
elif mode=='shot':
 s=int(sys.argv[2]);timeline=json.loads((R/'timeline.json').read_text());a,b=timeline['boundaries'][s:s+2]
 first=math.ceil(a*f.FPS-1e-7);end=math.ceil(b*f.FPS-1e-7);N=round(timeline['duration']*f.FPS);end=min(end,N)
 render=f.Renderer();f.subtitles(timeline,render)
 path=R/f'render/scene_{s:02}.mp4';log=(R/f'review/scene_{s:02}_ffmpeg.log').open('w')
 cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{f.W}x{f.H}','-r',str(f.FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','2',str(path)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);stats=[];pictures=[];previous=None
 try:
  for frame in range(first,end):
   t=frame/f.FPS;u=(t-a)/(b-a);sc=[c for c in timeline['cues'] if c['scene']==s];split=(sc[1]['start']-a)/(b-a)
   cue=next((c for c in timeline['cues'] if c['start']-.07<=t<=c['end']+.16),None)
   render.reset();f.arrange(render,s,u,t,split);im,raw=render.frame(t,s,cue);p.stdin.write(im.tobytes())
   tiny=np.asarray(raw.crop((85,400,995,1390)).resize((182,198)),dtype=np.int16);delta=float(np.mean(np.abs(tiny-previous))) if previous is not None else 0;previous=tiny
   # Additional projection-space check: distinct retained material symbols must be distinguishable.
   screen=[]
   for tag,i,pos,radius in render.content:
    q=render.vp@np.array([*pos,1]);ndc=q[:2]/q[3];xy=(ndc+1)*np.array([f.W,f.H])/2
    projected_radius=(1/math.tan(math.radians(37)/2))*f.H*.5*radius/q[3]
    screen.append((xy,projected_radius))
   projected_gaps=[float(np.linalg.norm(x[0]-y[0])-x[1]-y[1]) for i,x in enumerate(screen) for y in screen[i+1:]]
   stats.append({'frame':frame,'time':t,'scene':s,'raw_subject_mean_delta':delta,'min_clearance':min(render.clearances) if render.clearances else None,'min_projected_cargo_edge_gap_px':min(projected_gaps) if projected_gaps else None,'semantic':render.semantic,'cargo_count':len(render.content)})
   if any(abs(u-q)<.51/(f.FPS*(b-a)) for q in [.15,.45,.78]):
    name=f'scene_{s+1:02}_{frame:04}.jpg';im.save(R/'review'/name,quality=94);pictures.append((s,frame,name))
   if frame%24==0:print('SHOT',s,frame-first,'/',end-first,flush=True)
  p.stdin.close();assert p.wait()==0
 finally:log.close()
 f.dump(R/f'review/scene_{s:02}_states.json',stats);f.dump(R/f'review/scene_{s:02}_pictures.json',pictures)
 print('SHOT_COMPLETE',s,len(stats),min([x['min_projected_cargo_edge_gap_px'] for x in stats if x['min_projected_cargo_edge_gap_px'] is not None] or [999]),flush=True)
elif mode=='assemble':
 timeline=json.loads((R/'timeline.json').read_text());N=round(timeline['duration']*f.FPS)
 parts=[R/f'render/scene_{s:02}.mp4' for s in range(10)];assert all(x.exists() for x in parts)
 cat=R/'render/concat.txt';cat.write_text('\n'.join("file '"+str(x)+"'" for x in parts))
 video=R/'render/native_picture.mp4';f.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(cat),'-c','copy',str(video)])
 stats=[];pics=[]
 for s in range(10):stats+=json.loads((R/f'review/scene_{s:02}_states.json').read_text());pics+=json.loads((R/f'review/scene_{s:02}_pictures.json').read_text())
 assert [x['frame'] for x in stats]==list(range(N));values=np.array([x['raw_subject_mean_delta'] for x in stats]);win=np.convolve(values,np.ones(48)/48,mode='valid')
 physical=[x['min_clearance'] for x in stats if x['min_clearance'] is not None];projected=[x['min_projected_cargo_edge_gap_px'] for x in stats if x['min_projected_cargo_edge_gap_px'] is not None]
 report={'frames':N,'native_resolution':[1080,1920],'fps':24,'all_retained_cargo_inside_checked_boundaries':True,'minimum_checked_geometry_clearance':min(physical),'minimum_projected_cargo_edge_gap_px':min(projected),'projected_cargo_overlap_frames':[x['frame'] for x in stats if x['min_projected_cargo_edge_gap_px'] is not None and x['min_projected_cargo_edge_gap_px']<0],'minimum_2second_raw_subject_mean_frame_change':float(win.min()),'weak_windows_threshold_0_015':[int(i) for i,x in enumerate(win) if x<.015],'human_continuous_viewing_performed':False,'auditory_listening_performed':False,'scope':'All retained material centers against compartment boundaries; distinct retained main-symbol projected circles; separate daughter boundary gaps. Intended molecular joins, insertion and permeation are separate. Pixel differences flag weak motion but are not a perceptual guarantee.'}
 f.dump(R/'review/motion_and_spacing.json',report);f.dump(R/'review/frame_states.json',stats);f.dump(R/'review/frame_manifest.json',pics)
 sheet=Image.new('RGB',(1080,2304),(7,17,25))
 for i,(_,_,name) in enumerate(pics[:30]):sheet.paste(Image.open(R/'review'/name).resize((216,384)),((i%5)*216,(i//5)*384))
 sheet.save(R/'review/contact_sheet.jpg',quality=92)
 renderer=f.Renderer();f.subtitles(timeline,renderer)
 f.finalise(timeline,video,report)
 shutil.copy(__file__,R/'source/p064_v2_pipeline.py')
 print('ASSEMBLED_NATIVE_FRAMES',N,flush=True)
else:raise ValueError(mode)
