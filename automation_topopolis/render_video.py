import cv2
import json
import math
import os
import random
import subprocess
from pathlib import Path

import numpy as np

W, H, FPS = 1080, 1920, 24
ROOT = Path(__file__).resolve().parent
VOICE = ROOT / "voice"
OUT = ROOT / "output"
OUT.mkdir(parents=True, exist_ok=True)

TEXTS = [
    "もし、恒星を何周もする一本の巨大なチューブの内側に、街も海も森も入っていたら？",
    "オリオン腕でいうトポポリスは、星や惑星の周囲を少なくとも一周する、細長い回転式の宇宙居住地。",
    "チューブそのものを長い軸のまわりに回転させ、内壁へ遠心力をつくる。そこが、この世界の地面になる。",
    "普通の物質で一Ｇほどの重力を作る場合、材料強度のため、チューブの半径はおよそ千キロメートルが目安になる。",
    "でも長さは別だ。代表例のケーブルヴィルでは、スパゲッティという構造が恒星を五十周する。",
    "内部の面積は、地球の表面積の八万四千三百倍以上。一本の建物なのに、ほとんど惑星系そのものだ。",
    "近距離なら外壁を走る真空列車。でも遠くの区画へ行くなら、都市間移動ではなく宇宙船が必要になる。",
    "住む場所を惑星から解放すると、世界は丸い星である必要さえなくなる。これが、トポポリス。",
]

CAPTIONS = [
    "もし、恒星を何周もする\N巨大なチューブの内側に住んだら？",
    "トポポリスは、星の周囲を一周以上する\N細長い回転式の宇宙居住地",
    "チューブ自体が回転し、内壁へ遠心力をつくる\Nそこが、この世界の地面になる",
    "一Ｇほどの重力では、材料強度のため\N半径はおよそ千キロメートルが目安",
    "でも長さは別だ\Nケーブルヴィルのスパゲッティは恒星を五十周",
    "内部面積は、地球の表面積の\N八万四千三百倍以上",
    "近距離は真空列車\N遠くへ行くなら、もう宇宙船が必要になる",
    "世界は、丸い星である必要さえなくなる\Nこれが、トポポリス",
]

HIGHLIGHTS = ["巨大なチューブ", "トポポリス", "遠心力", "千キロメートル", "五十周", "八万四千三百倍", "宇宙船", "トポポリス"]
CHAPTERS = [
    (0.0, 6.0, "01｜星を巻く世界"),
    (6.0, 15.0, "02｜地面はチューブの内側"),
    (15.0, 25.0, "03｜回転が重力をつくる"),
    (25.0, 37.0, "04｜長さの桁が変わる"),
    (37.0, 47.0, "05｜建物が惑星系になる"),
    (47.0, 60.0, "06｜惑星から自由になる"),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def probe_duration(path):
    p = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], check=True, capture_output=True, text=True)
    return float(p.stdout.strip())


def srt_ts(sec):
    sec = max(0.0, sec)
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_ts(sec):
    sec = max(0.0, sec)
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ass_escape(text):
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def highlight(text, word):
    if word not in text:
        return ass_escape(text)
    a, b = text.split(word, 1)
    return ass_escape(a) + "{\\c&H00EED775&}" + ass_escape(word) + "{\\c&H00F8F7F2&}" + ass_escape(b)


def build_audio_and_captions():
    files = [VOICE / f"{i:02d}.mp3" for i in range(1, 9)]
    for f in files:
        if not f.exists() or f.stat().st_size < 1000:
            raise RuntimeError(f"missing voice segment: {f.name}")
    durs = [probe_duration(f) for f in files]
    # Actual segment lengths determine the edit timeline.
    start = 0.55
    gap = 0.25
    starts = []
    t = start
    for d in durs:
        starts.append(t)
        t += d + gap
    audio_end = starts[-1] + durs[-1]
    duration = max(48.0, audio_end + 1.6)
    if duration > 59.8:
        raise RuntimeError(f"narration too long for short: {duration:.2f}s")

    cmd = ["ffmpeg", "-y"]
    for f in files:
        cmd += ["-i", str(f)]
    filters = []
    labels = []
    for i, st in enumerate(starts):
        delay = int(round(st * 1000))
        filters.append(
            f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,adelay={delay}|{delay}[a{i}]"
        )
        labels.append(f"[a{i}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs=8:duration=longest:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=9[voice]"
    )
    cmd += ["-filter_complex", ";".join(filters), "-map", "[voice]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(OUT / "voice_mix.wav")]
    run(cmd)

    srt_lines = []
    for i, (st, d, txt) in enumerate(zip(starts, durs, TEXTS), 1):
        en = st + d + 0.10
        srt_lines += [str(i), f"{srt_ts(st)} --> {srt_ts(en)}", txt, ""]
    (OUT / "captions.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Caption,Noto Sans CJK JP,64,&H00F8F7F2,&H00F8F7F2,&H80070B12,&H6A170E08,-1,0,0,0,100,100,1,0,3,1.3,0,5,70,70,0,1
Style: Title,Noto Sans CJK JP,34,&H00F8F7F2,&H00F8F7F2,&H90070B12,&H00000000,-1,0,0,0,100,100,4,0,1,1,0,7,64,64,72,1
Style: Chapter,Noto Sans CJK JP,28,&H00EED775,&H00EED775,&H90070B12,&H00000000,-1,0,0,0,100,100,3,0,1,1,0,7,64,64,126,1
Style: Note,Noto Sans CJK JP,24,&H99F8F7F2,&H99F8F7F2,&H90070B12,&H00000000,0,0,0,0,100,100,1,0,1,1,0,9,50,58,78,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    events.append(f"Dialogue: 0,{ass_ts(0)},{ass_ts(min(duration,5.8))},Title,,0,0,0,,オリオン腕さんぽ｜トポポリス")
    events.append(f"Dialogue: 0,{ass_ts(0)},{ass_ts(duration)},Note,,0,0,0,,概念映像・縮尺圧縮")
    for st, en, label in CHAPTERS:
        if st < duration:
            events.append(f"Dialogue: 0,{ass_ts(st)},{ass_ts(min(en,duration))},Chapter,,0,0,0,,{label}")
    for st, d, txt, word in zip(starts, durs, CAPTIONS, HIGHLIGHTS):
        en = min(duration, st + d + 0.10)
        body = highlight(txt, word)
        body = "{\\move(540,1476,540,1460,0,180)\\fscx98\\fscy98\\t(0,180,\\fscx100\\fscy100)\\fad(140,120)}" + body
        events.append(f"Dialogue: 2,{ass_ts(st)},{ass_ts(en)},Caption,,0,0,0,,{body}")
    (OUT / "captions.ass").write_text(ass + "\n".join(events) + "\n", encoding="utf-8")

    timeline = {
        "episode": "topopolis_schedule_test_v1",
        "fps": FPS,
        "width": W,
        "height": H,
        "duration_seconds": duration,
        "audio_target": {"sample_rate": 48000, "integrated_lufs_target": -16, "true_peak_db_target": -1.5},
        "segments": [
            {"index": i+1, "start": starts[i], "duration": durs[i], "text": TEXTS[i]}
            for i in range(8)
        ],
        "note": "Caption times are derived from the decoded duration of each final narration segment; no character-count timing is used."
    }
    (OUT / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    return duration, starts, durs


# --- Original procedural 3D / cinematic renderer ---
rng = np.random.default_rng(20260917)
STARFIELD = np.zeros((H, W, 3), np.uint8)
for _ in range(720):
    x = int(rng.integers(0, W)); y = int(rng.integers(0, H))
    b = int(rng.integers(80, 235)); r = 1 if rng.random() < 0.88 else 2
    cv2.circle(STARFIELD, (x, y), r, (b, b, min(255, b + 12)), -1, cv2.LINE_AA)

Y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
BG_TOP = np.array([18, 10, 7], np.float32)   # BGR
BG_BOT = np.array([4, 3, 7], np.float32)
GRAD = ((1-Y)[...,None] * BG_TOP + Y[...,None] * BG_BOT).astype(np.uint8)
GRAD = np.repeat(GRAD, W, axis=1)
BASE_BG = cv2.add(GRAD, STARFIELD)


def ease(x):
    x = np.clip(x, 0.0, 1.0)
    return x*x*(3-2*x)


def rot_x(a):
    c,s=math.cos(a),math.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]],np.float32)


def rot_y(a):
    c,s=math.cos(a),math.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]],np.float32)


def rot_z(a):
    c,s=math.cos(a),math.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]],np.float32)


def project(pts, yaw=0, pitch=0, roll=0, camdist=11.0, focal=820.0, cx=540, cy=900, tx=0, ty=0):
    R = rot_z(roll) @ rot_x(pitch) @ rot_y(yaw)
    q = pts @ R.T
    q[:,0] += tx; q[:,1] += ty; q[:,2] += camdist
    z = np.maximum(q[:,2], 0.3)
    x = cx + focal * q[:,0] / z
    y = cy - focal * q[:,1] / z
    return np.stack([x,y,z], axis=1)


def alpha_circle(img, center, radius, color, alpha):
    overlay = img.copy()
    cv2.circle(overlay, center, int(radius), color, -1, cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)


def draw_sun(img, center, radius):
    for k, a in [(3.4,0.035),(2.5,0.05),(1.8,0.08),(1.35,0.13)]:
        alpha_circle(img, center, radius*k, (70,145,255), a)
    alpha_circle(img, center, radius, (165,225,255), 0.98)
    alpha_circle(img, (center[0]-int(radius*0.16), center[1]-int(radius*0.18)), radius*0.72, (210,245,255), 0.42)


def coil_points(turns=6, samples=700, R=5.0):
    th = np.linspace(-turns*math.pi, turns*math.pi, samples, dtype=np.float32)
    # A gently braided orbit: conceptual scale compression for visual readability.
    x = R*np.cos(th)
    y = R*np.sin(th)
    z = 0.45*np.sin(th*0.46) + 0.18*np.sin(th*1.7)
    return np.stack([x,y,z], axis=1)

COIL = coil_points()


def draw_coil(img, t, camdist, yaw, pitch, focal, offset=(0,0), thick=13):
    pp = project(COIL, yaw=yaw, pitch=pitch, roll=0.04*math.sin(t*0.35), camdist=camdist, focal=focal, cx=540+offset[0], cy=890+offset[1])
    segs=[]
    for i in range(len(pp)-1):
        if pp[i,2] < 0.45 or pp[i+1,2] < 0.45: continue
        p1=(int(pp[i,0]),int(pp[i,1])); p2=(int(pp[i+1,0]),int(pp[i+1,1]))
        z=(pp[i,2]+pp[i+1,2])*0.5
        segs.append((z,p1,p2))
    segs.sort(reverse=True)  # far first, near last under this camera convention
    for z,p1,p2 in segs:
        if p1[0] < -3000 or p1[0] > 4000 or p1[1] < -3000 or p1[1] > 5000: continue
        depth = np.clip((camdist+5-z)/10,0,1)
        core=(int(125+65*depth),int(165+55*depth),int(190+50*depth))
        w=max(3,int(thick*(camdist/max(z,2))))
        cv2.line(img,p1,p2,(24,60,78),w+12,cv2.LINE_AA)
        cv2.line(img,p1,p2,(56,115,142),w+6,cv2.LINE_AA)
        cv2.line(img,p1,p2,core,w,cv2.LINE_AA)
        # slim moving utility light on the tube
        if (int(t*18)+int(z*5))%53==0:
            cv2.circle(img,p1,max(2,w//3),(210,245,255),-1,cv2.LINE_AA)


def draw_exterior(img, local, mode):
    if mode == 0:
        e=ease(local)
        cam=16.0-5.6*e; yaw=-0.32+0.42*e; pitch=-0.22+0.16*e; focal=760+120*e
        draw_sun(img,(540,865),112+15*e)
        draw_coil(img,local*8,cam,yaw,pitch,focal,thick=15)
    elif mode == 1:
        e=ease(local)
        cam=10.4-1.8*e; yaw=0.10+1.15*e; pitch=-0.08+0.34*math.sin(local*math.pi); focal=910+150*e
        draw_sun(img,(470-int(90*e),840),98)
        draw_coil(img,local*8,cam,yaw,pitch,focal,offset=(int(100*e),0),thick=18)
        # foreground pass of the habitat, enhancing parallax
        y0=int(1180-420*e)
        cv2.line(img,(-100,y0),(1180,y0-280),(32,70,90),120,cv2.LINE_AA)
        cv2.line(img,(-100,y0-5),(1180,y0-285),(110,178,198),82,cv2.LINE_AA)
        cv2.line(img,(-100,y0-18),(1180,y0-298),(205,230,228),10,cv2.LINE_AA)
    else:
        e=ease(local)
        cam=13.8+3.2*e; yaw=1.25+0.8*e; pitch=0.16-0.2*e; focal=840-80*e
        draw_sun(img,(540,860),104)
        draw_coil(img,local*8,cam,yaw,pitch,focal,thick=14)
        # small craft departing from a nearby segment
        sx=int(660+280*e); sy=int(1110-520*e)
        cv2.line(img,(sx-90,sy+120),(sx,sy),(110,185,230),3,cv2.LINE_AA)
        cv2.circle(img,(sx,sy),8,(230,245,250),-1,cv2.LINE_AA)
        alpha_circle(img,(sx,sy),24,(90,180,255),0.10)


def draw_inside(img, local):
    # Cylindrical tunnel viewed along its long axis; ring rotation and camera advance create parallax.
    e=ease(local)
    cx=int(540+80*math.sin(local*2.5))
    cy=int(900+35*math.cos(local*2.1))
    maxr=1180
    phase=local*1.8
    # atmospheric glow on the axis
    alpha_circle(img,(cx,cy),260,(85,160,210),0.08)
    # distant light aperture
    draw_sun(img,(cx,cy),42+15*e)
    # perspective rings
    for k in range(34,0,-1):
        z=(k + (local*6)%1)/34
        r=int(70 + (1-z)**1.45*maxr)
        col=(26+int(38*(1-z)),46+int(50*(1-z)),58+int(50*(1-z)))
        cv2.ellipse(img,(cx,cy),(r,int(r*0.63)),0,0,360,col,2,cv2.LINE_AA)
    # inner-world sectors: water, forest, rock. These are original concept visuals.
    for band, base_col in [(0,(70,110,55)),(1,(95,125,65)),(2,(105,85,55))]:
        pts=[]
        for a in np.linspace(math.pi*0.16+band*0.72, math.pi*0.78+band*0.72, 140):
            rr=maxr*(0.88 + 0.035*math.sin(a*9+phase*3+band))
            x=cx+rr*math.cos(a); y=cy+0.63*rr*math.sin(a)
            pts.append((int(x),int(y)))
        for j in range(len(pts)-1):
            cv2.line(img,pts[j],pts[j+1],base_col,24,cv2.LINE_AA)
    # ocean band
    pts=[]
    for a in np.linspace(math.pi*0.95, math.pi*1.55, 180):
        rr=maxr*(0.90+0.014*math.sin(a*13+phase*4))
        pts.append((int(cx+rr*math.cos(a)),int(cy+0.63*rr*math.sin(a))))
    for j in range(len(pts)-1):
        cv2.line(img,pts[j],pts[j+1],(150,105,55),36,cv2.LINE_AA)
        if j%8==0: cv2.circle(img,pts[j],3,(220,180,110),-1,cv2.LINE_AA)
    # volumetric-looking clouds as translucent layered blobs
    for i in range(18):
        a=0.35*i+phase*0.7
        rr=380+34*i
        x=int(cx+rr*math.cos(a)); y=int(cy+0.63*rr*math.sin(a))
        if -120<x<W+120 and -120<y<H+120:
            alpha_circle(img,(x,y),34+(i%4)*8,(210,220,225),0.035)
    # city lights in lower arc
    for i in range(34):
        a=math.pi*0.20+i*0.055+phase*0.06
        rr=maxr*0.86
        x=int(cx+rr*math.cos(a)); y=int(cy+0.63*rr*math.sin(a))
        if 0<x<W and 0<y<H:
            cv2.circle(img,(x,y),2+(i%3==0),(190,225,240),-1,cv2.LINE_AA)


def draw_cross_section(img, local):
    e=ease(local)
    cx,cy=540,930
    R=int(455+25*math.sin(local*math.pi))
    # outer hull
    for w,c in [(88,(32,62,76)),(64,(88,133,146)),(34,(165,190,191))]:
        cv2.circle(img,(cx,cy),R,c,w,cv2.LINE_AA)
    # interior sky and landscape patches following the inside wall
    overlay=img.copy()
    cv2.circle(overlay,(cx,cy),R-52,(42,45,52),-1,cv2.LINE_AA)
    cv2.addWeighted(overlay,0.45,img,0.55,0,img)
    phase=local*2*math.pi
    for i in range(100):
        a=2*math.pi*i/100+phase
        rr=R-82
        p=(int(cx+rr*math.cos(a)),int(cy+rr*math.sin(a)))
        if math.sin(a*3.0)>0:
            cv2.circle(img,p,10,(65,112,55),-1,cv2.LINE_AA)
        else:
            cv2.circle(img,p,10,(125,92,55),-1,cv2.LINE_AA)
    # rotation markers
    for j in range(12):
        a=phase+j*2*math.pi/12
        rr=R+78
        p=(int(cx+rr*math.cos(a)),int(cy+rr*math.sin(a)))
        cv2.circle(img,p,7,(120,215,240),-1,cv2.LINE_AA)
    # vector from axis to surface, emphasizing effective down direction
    a=-0.35+0.2*math.sin(local*3)
    p1=(cx,cy); p2=(int(cx+(R-120)*math.cos(a)),int(cy+(R-120)*math.sin(a)))
    cv2.arrowedLine(img,p1,p2,(110,210,235),5,cv2.LINE_AA,tipLength=0.06)
    alpha_circle(img,(cx,cy),32,(180,220,245),0.35)


def draw_scale(img, local):
    e=ease(local)
    draw_sun(img,(540,860),82)
    draw_coil(img,local*6,15.5+2.5*e,0.8+0.35*e,-0.12,760-70*e,thick=10)
    # tiny Earth-like comparison globe, original schematic rendering
    ex,ey=830,1250
    er=42
    alpha_circle(img,(ex,ey),er,(135,95,45),0.95)
    cv2.ellipse(img,(ex-8,ey-4),(22,12),-20,0,360,(65,120,70),-1,cv2.LINE_AA)
    cv2.ellipse(img,(ex+12,ey+16),(17,9),25,0,360,(75,130,75),-1,cv2.LINE_AA)
    alpha_circle(img,(ex-12,ey-14),18,(220,210,175),0.11)
    # A chain of luminous dots along the tube hints at separated regions/cities.
    for i in range(24):
        a=i/24*2*math.pi+local*0.5
        x=int(540+330*math.cos(a)); y=int(860+120*math.sin(a))
        cv2.circle(img,(x,y),2,(200,230,240),-1,cv2.LINE_AA)


def render_visual(duration):
    visual = OUT / "visual.mp4"
    cmd=[
        "ffmpeg","-y","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","bgr24",
        "-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an",
        "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
        "-movflags","+faststart",str(visual)
    ]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    frames=int(round(duration*FPS))
    for n in range(frames):
        t=n/FPS
        frame=BASE_BG.copy()
        u=t/duration
        # subtle drifting nebular veil
        ov=frame.copy()
        bx=int(300+150*math.sin(t*0.09)); by=int(450+170*math.cos(t*0.07))
        cv2.ellipse(ov,(bx,by),(520,330),-20,0,360,(55,24,30),-1,cv2.LINE_AA)
        cv2.addWeighted(ov,0.045,frame,0.955,0,frame)

        if u < 0.12:
            draw_exterior(frame,u/0.12,0)
        elif u < 0.26:
            draw_exterior(frame,(u-0.12)/0.14,1)
        elif u < 0.45:
            draw_inside(frame,(u-0.26)/0.19)
        elif u < 0.61:
            draw_cross_section(frame,(u-0.45)/0.16)
        elif u < 0.79:
            draw_scale(frame,(u-0.61)/0.18)
        else:
            draw_exterior(frame,(u-0.79)/0.21,2)

        # cinematic letter-free guide marks and progress line, safe from platform controls
        prog=int(1000*u)
        cv2.line(frame,(40,1780),(40+prog,1780),(110,215,238),3,cv2.LINE_AA)
        cv2.line(frame,(40+prog,1780),(1040,1780),(40,52,65),2,cv2.LINE_AA)
        # vignette
        overlay=np.zeros_like(frame)
        cv2.rectangle(overlay,(0,0),(W,H),(0,0,0),-1)
        mask=np.zeros((H,W),np.uint8)
        cv2.ellipse(mask,(W//2,H//2),(int(W*0.62),int(H*0.57)),0,0,360,255,-1,cv2.LINE_AA)
        mask=cv2.GaussianBlur(mask,(0,0),120)
        inv=(255-mask).astype(np.float32)/255.0*0.30
        frame=(frame.astype(np.float32)*(1-inv[...,None])).astype(np.uint8)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    rc=proc.wait()
    if rc!=0: raise RuntimeError(f"ffmpeg visual encoder failed: {rc}")
    return visual


def finalize(duration, visual):
    # Quiet procedural ambient bed; voice remains dominant. Ducking is handled by sidechain compression.
    ambient=OUT/"ambient.wav"
    run([
        "ffmpeg","-y","-f","lavfi","-i",f"anoisesrc=color=pink:amplitude=0.14:d={duration}:r=48000",
        "-f","lavfi","-i",f"sine=frequency=72:sample_rate=48000:duration={duration}",
        "-filter_complex","[0:a]lowpass=f=1000,highpass=f=70,volume=0.08[n];[1:a]volume=0.025[s];[n][s]amix=inputs=2:duration=longest,afade=t=in:st=0:d=1.4,afade=t=out:st="+f"{max(0,duration-2.4):.3f}"+":d=2.4[a]",
        "-map","[a]","-ar","48000","-ac","2","-c:a","pcm_s16le",str(ambient)
    ])
    mixed=OUT/"mix.wav"
    run([
        "ffmpeg","-y","-i",str(ambient),"-i",str(OUT/"voice_mix.wav"),
        "-filter_complex","[0:a][1:a]sidechaincompress=threshold=0.018:ratio=8:attack=12:release=260[duck];[duck][1:a]amix=inputs=2:weights='0.30 1.0':duration=longest,loudnorm=I=-16:TP=-1.5:LRA=9[a]",
        "-map","[a]","-ar","48000","-ac","2","-c:a","pcm_s16le",str(mixed)
    ])

    high=OUT/"topopolis_schedule_test_v1_high.mp4"
    run([
        "ffmpeg","-y","-i",str(visual),"-i",str(mixed),
        "-vf",f"ass={OUT/'captions.ass'}",
        "-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","medium","-crf","17","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-r",str(FPS),"-t",f"{duration:.3f}","-movflags","+faststart",str(high)
    ])
    light=OUT/"topopolis_schedule_test_v1_light.mp4"
    run([
        "ffmpeg","-y","-i",str(high),"-vf","scale=720:1280:flags=lanczos","-c:v","libx264","-preset","veryfast","-crf","25","-c:a","aac","-b:a","128k","-movflags","+faststart",str(light)
    ])
    return high,light


def verify(duration, high, light):
    report={"expected":{"width":W,"height":H,"fps":FPS,"duration_seconds":duration,"audio_sample_rate":48000}}
    for label,path in [("high",high),("light",light)]:
        p=subprocess.run([
            "ffprobe","-v","error","-show_entries","stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels:format=duration,size",
            "-of","json",str(path)
        ],check=True,capture_output=True,text=True)
        report[label]=json.loads(p.stdout)
        # Full decode, catches truncation/corruption.
        subprocess.run(["ffmpeg","-v","error","-i",str(path),"-f","null","-"],check=True)
    # Black-frame detection and loudness measurement are logged as machine checks.
    black=subprocess.run([
        "ffmpeg","-hide_banner","-i",str(high),"-vf","blackdetect=d=0.25:pix_th=0.02","-an","-f","null","-"
    ],capture_output=True,text=True)
    report["blackdetect_stderr_tail"]=black.stderr[-4000:]
    loud=subprocess.run([
        "ffmpeg","-hide_banner","-i",str(high),"-map","0:a:0","-af","ebur128=peak=true","-f","null","-"
    ],capture_output=True,text=True)
    report["ebur128_stderr_tail"]=loud.stderr[-5000:]
    (OUT/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    # representative frames
    for t in [1.0,7.5,16.5,26.5,36.5,max(1.0,duration-2.0)]:
        run(["ffmpeg","-y","-ss",f"{t:.2f}","-i",str(high),"-frames:v","1","-q:v","2",str(OUT/f"frame_{t:05.2f}.jpg")])
    return report


def main():
    duration, starts, durs = build_audio_and_captions()
    visual=render_visual(duration)
    high,light=finalize(duration,visual)
    report=verify(duration,high,light)
    production={
        "id":"topopolis_schedule_test_v1",
        "created_jst":"2026-09-17 19:36",
        "source_article":"https://orionsarm.com/eg-article/4cea908020d1e",
        "supporting_article":"https://www.orionsarm.com/eg-article/48ac37b0e82ba",
        "central_question":"恒星を何周もする一本のチューブの内側に住む世界は、どんな構造になる？",
        "visuals":"Original procedural 3D/concept rendering; no Orion's Arm site imagery reused.",
        "canon":"Topopolis definition, ~1000 km conventional-material minor-radius guidance, vac-train/spacecraft travel, and Cableville Spaghetti 50 turns / >84,300 Earth surface areas are based on the cited OA pages.",
        "creative_note":"Landscape, cities, clouds, craft, and camera staging are illustrative non-canon imagery; conceptual scale is compressed for readability."
    }
    (OUT/"production_record.json").write_text(json.dumps(production,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/"transcript.txt").write_text("\n".join(TEXTS)+"\n",encoding="utf-8")
    print(json.dumps({"duration":duration,"voice_durations":durs,"outputs":[high.name,light.name]},ensure_ascii=False))

if __name__=="__main__":
    main()
