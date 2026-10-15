"""Execute a bounded production stage and publish only a diagnostic JSON record."""
from pathlib import Path
import os,sys,json,subprocess,traceback,base64
import requests
phase=sys.argv[1];report={'phase':phase,'run_id':os.environ.get('GITHUB_RUN_ID'),'status':'running'}
try:
    if phase=='preflight':
        # Move the common-clock scene upward to reserve the subtitle-safe region.
        p=Path('p041_20261015/render.py');s=p.read_text();s=s.replace('[0,37,7.0],[0,0,0],39','[0,37,7.0],[0,0,1.1],39').replace('[0,37,7],[0,0,0],39','[0,37,7],[0,0,1.1],39');s=s.replace("'-g','48','-video_track_timescale'","'-g','48','-bf','0','-video_track_timescale'");p.write_text(s)
        commands=[['python','p041_20261015/prepare.py'],['python','p041_20261015/render.py','proof'],['python','p041_20261015/render.py','shot','7']]
    elif phase.startswith('shot_'):
        commands=[['python','p041/code/render.py','shot',phase.split('_')[1]]]
    elif phase=='finish':commands=[['python','p041_20261015/finish.py']]
    else:raise ValueError(phase)
    for cmd in commands:
        r=subprocess.run(cmd,text=True,capture_output=True)
        print(r.stdout,flush=True);print(r.stderr,flush=True)
        if r.returncode:
            report['command']=cmd;report['stdout_tail']=r.stdout[-5000:];report['stderr_tail']=r.stderr[-12000:];raise RuntimeError(f'Stage command failed: {cmd}')
    report['status']='success'
    if phase=='preflight':
        p=json.loads(Path('p041/timeline.json').read_text());report.update(duration=p['duration'],frames=p['frames'],shots=p['shots'],captions=p['captions'],narration=p['narration'])
        report['orbit_visibility']=json.loads(Path('p041/validation/orbit_visibility.json').read_text());report['audio_checks']=json.loads(Path('p041/validation/original_audio_integrity.json').read_text())
    elif phase=='finish':report.update(json.loads(Path('status.json').read_text()))
except Exception as e:
    report['status']='failed';report['error']=str(e);report['traceback']=traceback.format_exc()
finally:
    path=f'p041_20261015/status_{phase}.json';text=json.dumps(report,ensure_ascii=False,indent=2);Path('stage_status.json').write_text(text)
    # Only status, times, verification measurements, and safe error text are written.
    # Finished video, audio, and images remain in authenticated workflow artifacts.
    token=os.environ.get('GH_STATUS_TOKEN')
    if token:
        url=f'https://api.github.com/repos/GunungApi/Codex/contents/{path}';headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
        existing=requests.get(url,headers=headers,timeout=30)
        payload={'message':f'P041 {phase} execution record','content':base64.b64encode(text.encode()).decode()}
        if existing.ok:payload['sha']=existing.json()['sha']
        elif existing.status_code!=404:existing.raise_for_status()
        result=requests.put(url,headers=headers,json=payload,timeout=30);result.raise_for_status();print('DIAGNOSTIC_SAVED',path,flush=True)
if report['status']=='failed':sys.exit(1)
