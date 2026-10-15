"""Native 3-D rendering for P041. No source image zooms or frame interpolation."""
import os
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
from pathlib import Path
import json,math,sys,time,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import moderngl
ROOT=Path('p041');W,H=1080,1920;FPS=24
PLAN=json.loads((ROOT/'timeline.json').read_text());DATA=json.loads((ROOT/'assets/system.json').read_text())
FONTS={}
WHITE=(242,247,248,255);CYAN=(117,215,238,255);GOLD=(242,195,125,255);MUTED=(174,190,199,255)
def font(n):
    if n not in FONTS:FONTS[n]=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',n,index=0)
    return FONTS[n]
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def norm(v):v=np.asarray(v,dtype=float);return v/(np.linalg.norm(v)+1e-15)
def look(eye,target):
    f=norm(np.asarray(target)-eye);r=norm(np.cross(f,[0,1,0]));u=np.cross(r,f)
    m=np.eye(4);m[:3,:3]=np.array([r,u,-f]);m[:3,3]=-m[:3,:3]@eye;return m

def perspective(fov):
    q=1/math.tan(math.radians(fov)/2);near=.03;far=6000.;p=np.zeros((4,4));p[0,0]=q/(W/H);p[1,1]=q;p[2,2]=(far+near)/(near-far);p[2,3]=2*far*near/(near-far);p[3,2]=-1;return p

def globe(seed=0,nu=257,nv=129,craters=True):
    rng=np.random.default_rng(410041+seed);th=np.linspace(0,np.pi,nv);ph=np.linspace(0,2*np.pi,nu)
    tt,pp=np.meshgrid(th,ph,indexing='ij');dirs=np.stack([np.sin(tt)*np.cos(pp),np.cos(tt),np.sin(tt)*np.sin(pp)],-1)
    flat=dirs.reshape(-1,3);height=np.zeros(len(flat));centers=[]
    if craters:
        height=.005*np.sin(flat[:,0]*11+seed)*np.sin(flat[:,1]*13-.5)*np.sin(flat[:,2]*9)+.002*np.sin(flat[:,0]*41+flat[:,2]*27)*np.cos(flat[:,1]*33)
        for j in range(76):
            c=norm(rng.normal(size=3));r=float(rng.uniform(.035,.22));d=np.sqrt(np.maximum(0,2*(1-flat@c)))/r
            height+=r*(-.055*np.exp(-d**4)+.024*np.exp(-((d-1)/.16)**2));centers.append([*c,r])
    pos=(flat*(1+height)[:,None]).reshape(nv,nu,3)
    dx=np.gradient(pos,axis=1);dy=np.gradient(pos,axis=0);nn=np.cross(dx,dy);nn/=np.maximum(np.linalg.norm(nn,axis=-1,keepdims=True),1e-12)
    nn[0]=dirs[0];nn[-1]=dirs[-1];nn[:,0]=normals_seam=(nn[:,0]+nn[:,-1])/2;nn[:,-1]=normals_seam
    nn/=np.maximum(np.linalg.norm(nn,axis=-1,keepdims=True),1e-12)
    i=np.arange(nv-1)[:,None];j=np.arange(nu-1)[None,:];a=i*nu+j;b=a+1;c=a+nu;d=c+1
    faces=np.stack([np.stack([a,b,c],-1),np.stack([b,d,c],-1)],-2).reshape(-1,3).astype('i4')
    return pos.reshape(-1,3).astype('f4'),nn.reshape(-1,3).astype('f4'),flat.astype('f4'),faces,np.array(centers)
VS='''#version 330
in vec3 in_pos; in vec3 in_normal; in vec3 in_local;
uniform mat4 mvp; uniform mat4 model;
out vec3 pos; out vec3 normal; out vec3 local;
void main(){vec4 p=model*vec4(in_pos,1.);pos=p.xyz;normal=normalize(mat3(model)*in_normal);local=in_local;gl_Position=mvp*vec4(in_pos,1.);}
'''
FS='''#version 330
in vec3 pos; in vec3 normal; in vec3 local;
uniform vec3 eye; uniform vec3 light; uniform vec3 basecolor; uniform int mode; uniform float time; uniform sampler3D noise_tex;
out vec4 frag;
float n(vec3 p){return texture(noise_tex,p*.047).r;}
float fb(vec3 p){return .54*n(p)+.27*n(p*2.03+4.2)+.13*n(p*4.1+7.5)+.06*n(p*8.4);}
void main(){vec3 N=normalize(normal);vec3 V=normalize(eye-pos);vec3 L=normalize(light-pos);float grain=fb(local*15.);vec3 col;
if(mode==1){float conv=fb(local*24.+vec3(time*.043,0.,time*.029));float gran=n(local*290.+time*.09);float limb=.47+.53*pow(max(0.,dot(N,V)),.48);col=basecolor*(.68+.53*conv+.13*gran)*limb*1.78;}
else{float fine=n(local*410.);vec3 albedo=basecolor*(.54+.57*grain+.065*fine);float diffuse=max(0.,dot(N,L));vec3 halfv=normalize(V+L);float spec=pow(max(0.,dot(N,halfv)),23.)*.065;float fill=.065+.105*max(0.,dot(N,normalize(vec3(1.,.3,1.))));col=albedo*(fill+diffuse*1.28)+vec3(.89,.75,.6)*spec;
if(mode==2){float band=fb(local*8.+vec3(local.y*12.,time*.005,0.));col=mix(vec3(.51,.34,.15),vec3(.82,.69,.43),band)*(fill+diffuse*1.05);}
if(mode==3){col=vec3(.20,.38,.49)*(.75+.20*grain)*(fill+diffuse*1.3);}
}
col=col/(1.+col*.52);col=pow(max(col,vec3(0.)),vec3(1./2.2));frag=vec4(col,1.);}
'''
LVS='''#version 330
in vec3 in_pos; uniform mat4 vp; void main(){gl_Position=vp*vec4(in_pos,1.);}
'''
LFS='''#version 330
uniform vec4 color;out vec4 frag;void main(){frag=color;}
'''
SVS='''#version 330
in vec3 in_pos; in float magnitude;uniform mat4 vp;out float lum;void main(){gl_Position=vp*vec4(in_pos,1.);gl_PointSize=1.1+2.6*magnitude;lum=magnitude;}
'''
SFS='''#version 330
in float lum;out vec4 frag;void main(){float d=length(gl_PointCoord-.5)*2.;if(d>1.)discard;float a=exp(-d*d*3.5);frag=vec4(vec3(.73,.82,.90)*(.3+.6*lum),a);}
'''
class Renderer:
    def __init__(self):
        self.ctx=moderngl.create_standalone_context(backend='egl',require=330)
        self.ms=self.ctx.framebuffer(color_attachments=[self.ctx.renderbuffer((W,H),components=4,samples=4)],depth_attachment=self.ctx.depth_renderbuffer((W,H),samples=4))
        self.fbo=self.ctx.simple_framebuffer((W,H),components=3)
        self.prog=self.ctx.program(vertex_shader=VS,fragment_shader=FS);self.lp=self.ctx.program(vertex_shader=LVS,fragment_shader=LFS);self.sp=self.ctx.program(vertex_shader=SVS,fragment_shader=SFS)
        rng=np.random.default_rng(410041);vol=rng.random((64,64,64));tex=self.ctx.texture3d((64,64,64),1,(vol*255).astype('u1').tobytes());tex.filter=(moderngl.LINEAR,moderngl.LINEAR);tex.repeat_x=tex.repeat_y=tex.repeat_z=True;tex.use(0);self.noise=tex;self.prog['noise_tex']=0
        np.savez_compressed(ROOT/'assets/noise.npz',volume=(vol*255).astype('u1'))
        self.meshes=[]
        for s in range(7):
            pos,nn,loc,idx,craters=globe(s,craters=(s!=6));vbo=self.ctx.buffer(np.hstack([pos,nn,loc]).astype('f4').tobytes());ibo=self.ctx.buffer(idx.tobytes())
            vao=self.ctx.vertex_array(self.prog,[(vbo,'3f 3f 3f','in_pos','in_normal','in_local')],index_buffer=ibo);self.meshes.append((vao,vbo,ibo))
            np.savez_compressed(ROOT/f'assets/globe_{s}.npz',vertices=pos,normals=nn,local=loc,triangles=idx,craters=craters)
        pts=rng.normal(size=(6200,3));pts/=np.linalg.norm(pts,axis=1,keepdims=True);pts*=3000;mag=rng.random((len(pts),1))**3
        self.starb=self.ctx.buffer(np.hstack([pts,mag]).astype('f4').tobytes());self.starvao=self.ctx.vertex_array(self.sp,[(self.starb,'3f 1f','in_pos','magnitude')])
        self.lineb=self.ctx.buffer(reserve=4096*3*4);self.linevao=self.ctx.vertex_array(self.lp,[(self.lineb,'3f','in_pos')]);self.ctx.line_width=1.65
        self.audit=[]
        (ROOT/'validation/render_runtime.json').write_text(json.dumps(dict(renderer=self.ctx.info['GL_RENDERER'],version=self.ctx.info['GL_VERSION'],resolution=[W,H],samples=4,mesh_vertices=len(pos),mesh_triangles=len(idx)),indent=2))
    def camera(self,eye,target,fov):
        self.eye=np.asarray(eye,float);self.vp=perspective(fov)@look(self.eye,np.asarray(target));self.prog['eye'].value=tuple(self.eye);self.sp['vp'].write(self.vp.T.astype('f4').tobytes());self.lp['vp'].write(self.vp.T.astype('f4').tobytes())
    def sphere(self,center,radius,seed=0,color=(.48,.39,.3),mode=0,rotation=0):
        c,s=math.cos(rotation),math.sin(rotation);model=np.eye(4);model[:3,:3]=np.array([[c,0,s],[0,1,0],[-s,0,c]])*radius;model[:3,3]=center
        self.prog['model'].write(model.T.astype('f4').tobytes());self.prog['mvp'].write((self.vp@model).T.astype('f4').tobytes());self.prog['basecolor'].value=tuple(color);self.prog['mode']=mode;self.meshes[seed%7][0].render()
    def line(self,points,color=(.21,.4,.46,.8),loop=False):
        a=np.asarray(points,'f4');assert len(a)<=4096;self.lineb.write(a.tobytes());self.lp['color'].value=color;self.ctx.enable(moderngl.BLEND);self.linevao.render(mode=moderngl.LINE_LOOP if loop else moderngl.LINE_STRIP,vertices=len(a))
    def project(self,p):
        q=self.vp@np.r_[p,1.];nd=q[:3]/q[3];return np.array([(nd[0]*.5+.5)*W,(.5-nd[1]*.5)*H]),q[3]>0
    def stars(self):
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE|moderngl.BLEND);self.starvao.render(mode=moderngl.POINTS)
    def orbit_scene(self,t,kind,u):
        if kind=='revolution':
            self.camera([0,37,7.0],[0,0,0],39);day=min(u/.93,1)*10
        elif kind=='young':
            ang=.28+.18*u;self.camera([12*math.sin(ang),28,32],[0,-.35,0],40);day=48+t*.55
        elif kind=='ending':
            self.camera([7.0-1.8*smooth(u),31+4*smooth(u),29+3*smooth(u)],[0,-.2,0],39);day=48+t*.55
        else:
            self.camera([8-2*smooth(u),27.5+3*smooth(u),30],[0,-.2,0],39);day=t*.55
        self.prog['light'].value=(0,0,0)
        self.sphere([0,0,0],.65,6,(1.,.65,.28),1,t*.02)
        xy=[];colors=[(.44,.40,.34),(.47,.35,.26),(.44,.38,.32),(.53,.42,.31),(.46,.39,.34)]
        for i,(a,p,rad) in enumerate(zip(DATA['semimajor_au'],DATA['period_days'],DATA['radius_earth'])):
            r=a*80;theta=2*np.pi*day/p+[-.7,.7,2.2,-1.8,1.65][i]
            ang=np.linspace(0,2*np.pi,800,endpoint=False);ring=np.stack([r*np.cos(ang),np.zeros(len(ang)),r*np.sin(ang)],-1)
            self.line(ring,(.18,.31,.35,.78),True)
            pos=np.array([r*math.cos(theta),0,r*math.sin(theta)])
            tr=np.linspace(theta-.31,theta,70);trail=np.stack([r*np.cos(tr),np.zeros(len(tr)),r*np.sin(tr)],-1);trail[-1]=pos
            self.line(trail,(.38,.70,.75,.93));self.sphere(pos,rad*.46,seed=i,color=colors[i],rotation=t*.02)
            point,vis=self.project(pos);xy.append((point,i+1));assert vis
            # The complete orbit frame must contain every planet center, above captions.
            self.audit.append(dict(t=t,kind=kind,planet=i,x=float(point[0]),y=float(point[1]),in_frame=bool(25<point[0]<W-25 and 190<point[1]<1400),trail_error=float(np.max(np.abs(trail[-1]-pos)))))
        return xy,day
    def frame(self,frame,shot):
        t=frame/FPS;u=(t-shot['start'])/(shot['end']-shot['start']);k=shot['kind'];self.ms.use();self.ms.clear(.008,.012,.020,1.);self.ctx.enable(moderngl.DEPTH_TEST|moderngl.BLEND);self.ctx.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA);self.prog['time']=t
        labels=[];xy=[];day=None
        if k in ['opening','hero']:
            if k=='opening':eye=[3.-.7*smooth(u),1.15+.3*smooth(u),6.6+1.5*smooth(u)];fov=40
            else:eye=[2.6+.7*smooth(u),1.7,7.6+.6*smooth(u)];fov=39
            self.camera(eye,[0,-.3,0],fov);self.prog['light'].value=(-5,4,4)
            self.stars();self.sphere([0,0,0],1.35,4,(.48,.39,.30),0,.27+t*.012)
            self.sphere([-5,3.8,-8],.9,6,(1.,.65,.28),1,t*.02)
            for i,p in enumerate([[3.8,1.3,-6],[1.7,2.4,-10],[-1.5,2.1,-14],[-3.1,.5,-17]]):self.sphere(p,.14+i*.02,i,(.39,.34,.30),0,t*.012)
        elif k in ['orbits','revolution','young','ending']:
            # Set the exact same camera for stars and geometry.
            if k=='revolution':self.camera([0,37,7],[0,0,0],39)
            elif k=='young':self.camera([12*math.sin(.28+.18*u),28,32],[0,-.35,0],40)
            elif k=='ending':self.camera([7-1.8*smooth(u),31+4*smooth(u),29+3*smooth(u)],[0,-.2,0],39)
            else:self.camera([8-2*smooth(u),27.5+3*smooth(u),30],[0,-.2,0],39)
            self.stars();xy,day=self.orbit_scene(t,k,u)
        elif k in ['ages','early']:
            self.camera([0,0,22],[0,0,0],40);self.stars();self.prog['light'].value=(-5,4,7)
            # Stars appear beside the age chart, not as an angular-size comparison.
            self.sphere([-1.72,3.38,0],.48,6,(1.,.65,.28),1,t*.008)
            self.sphere([1.72,-.6,0],.48,6,(1.,.84,.57),1,t*.008)
        elif k=='five':
            self.camera([0,.4,23],[0,.4,0],39);self.stars();self.prog['light'].value=(-5,6,9)
            for i,r in enumerate(DATA['radius_earth']):
                p=[(i-2)*1.65,1.22,0];self.sphere(p,r*.83,i,(.46,.40,.33),0,t*.017);labels.append((p,.83*r,str(i+1),32))
            p=[0,-1.28,0];self.sphere(p,.83,5,(.3,.5,.6),3,t*.014);labels.append((p,.83,'地球',43))
        elif k in ['mercury','venus']:
            self.camera([0,.28,18 if k=='mercury' else 21],[0,.28,0],40);self.stars();self.prog['light'].value=(-5,6,9)
            if k=='mercury':objects=[([-1.7,0,0],.383*2.15,5,(.44,.42,.37),0,'水星'),([1.7,0,0],.403*2.15,0,(.46,.40,.33),0,'内側の惑星')]
            else:objects=[([-1.7,0,0],.741*1.38,4,(.46,.40,.33),0,'外側の惑星'),([1.7,0,0],.949*1.38,5,(.75,.59,.38),2,'金星')]
            for p,r,seed,col,mode,name in objects:self.sphere(p,r,seed,col,mode,t*.017);labels.append((p,r,name,42))
        self.ctx.copy_framebuffer(self.fbo,self.ms);im=Image.frombytes('RGB',(W,H),self.fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGBA')
        over=Image.new('RGBA',(W,H));d=ImageDraw.Draw(over)
        def text(s,x,y,n=40,color=WHITE,anchor='mm'):
            d.text((x,y),s,font=font(n),fill=color,anchor=anchor,stroke_width=1,stroke_fill=(0,0,0,120))
        text('平穏暦全史 ／ 前史041',65,112,30,MUTED,'lm');text('第2巻・第6章',1015,112,28,MUTED,'rm')
        titles={'opening':'太陽より古い、惑星の世界','orbits':'ケプラー444','ages':'年齢を、同じ目盛りで比べる','early':'太陽が生まれた、その時には','five':'五つとも、地球より小さい','mercury':'大きさを、同じ縮尺で比較','venus':'大きさを、同じ縮尺で比較','revolution':'五つの軌道を、同じ時計で','young':'若い宇宙に、すでにあった世界','hero':'太陽系へと続く、長い歴史','ending':'ケプラー444'}
        text(titles[k],540,278,43 if k!='ending' else 52,CYAN)
        if k in ['orbits','young','ending']:
            for pt,i in xy:text(str(i),float(pt[0])+20,float(pt[1])-24,29,CYAN)
            if k=='orbits':text('主星Aと、その近くの五惑星',540,354,31,MUTED)
        if k=='revolution':
            for pt,i in xy:text(str(i),float(pt[0])+20,float(pt[1])-24,29,CYAN)
            text(f'経過  {day:4.1f} 日',540,1240,66,WHITE)
            text('最も外側でも、およそ9.7日で一周',540,354,34,MUTED)
            if day>=9.74:text('五つとも、一周以上',540,1330,36,CYAN)
        for p,r,name,n in labels:
            q,_=self.project(p);bottom,_=self.project([p[0],p[1]-r,p[2]]);text(name,float(q[0]),min(float(bottom[1])+66,1340),n,WHITE)
        if k in ['ages','early']:
            base=1310;scale=75.;left=base-11.2*scale;right=base-4.6*scale
            for x,top,col in [(325,left,CYAN),(755,right,GOLD)]:
                d.rounded_rectangle((x-14,top,x+14,base),radius=12,fill=(*col[:3],190))
                for j in range(12):
                    yy=base-j*scale
                    if yy>=top:d.line((x-24,yy,x+24,yy),fill=(*col[:3],130),width=2)
                d.ellipse((x-23,top-23,x+23,top+23),fill=col)
            d.line((210,base,870,base),fill=(190,208,215,180),width=2);text('現在',540,1358,31,MUTED)
            text('ケプラー444',325,374,38,CYAN);text('約112億年',325,420,48,WHITE)
            text('太陽系',755,right-113,38,GOLD);text('約46億年',755,right-64,48,WHITE)
            if k=='ages':
                text('2015年の恒星年齢推定：112 ± 10億年',540,1760,29,MUTED)
                # Explicit uncertainty band around the old formation date.
                d.rounded_rectangle((274,left-75,376,left+75),radius=8,outline=(117,215,238,90),width=2)
            else:
                d.line((480,left,480,right),fill=CYAN,width=5);d.line((455,left,505,left),fill=CYAN,width=4);d.line((455,right,505,right),fill=CYAN,width=4)
                text('すでに',730,630,43,MUTED);text('約66億歳',730,720,82,CYAN)
                text('112億年 − 46億年',730,800,30,MUTED)
                text('2015年の推定から計算／差の幅は約±10億年',540,1760,28,MUTED)
        else:
            note='星と惑星の大きさを拡大／外観は想像'
            if k in ['five','mercury','venus']:note='大きさの比較模型／並びと間隔は説明用'
            elif k=='revolution':note='時間を圧縮／軌道は円で模式化'
            text(note,540,1760,29,MUTED)
        im=Image.alpha_composite(im,over).convert('RGB');return im

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'proof';ren=Renderer()
    if mode=='proof':
        folder=ROOT/'validation/previews';folder.mkdir(parents=True,exist_ok=True);thumbs=[]
        for shot in PLAN['shots']:
            f=round((shot['start_frame']+shot['end_frame'])/2);im=ren.frame(f,shot);p=folder/f'shot_{shot["id"]:02d}.png';im.save(p)
            thumb=im.resize((270,480));dd=ImageDraw.Draw(thumb);dd.rectangle((0,0,200,25),fill=(0,0,0));dd.text((6,3),f'{shot["id"]:02d} {f/FPS:.2f}s',font=ImageFont.load_default(),fill=(255,255,255));thumbs.append(thumb)
        sheet=Image.new('RGB',(1080,math.ceil(len(thumbs)/4)*480))
        for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*270,(i//4)*480))
        sheet.save(ROOT/'validation/contact_sheet.jpg',quality=94)
        audit_orbits(ren)
        print('PROOF_READY',json.dumps({'shots':len(thumbs),'native_resolution':[W,H],'renderer':ren.ctx.info['GL_RENDERER']}),flush=True)
    elif mode=='shot':
        sid=int(sys.argv[2]);shot=PLAN['shots'][sid];out=ROOT/f'clips/shot_{sid:02d}.mp4';out.parent.mkdir(exist_ok=True,parents=True)
        filt=f'setpts=PTS+{shot["start"]}/TB,ass=p041/captions/heionreki_p041_v1_ja.ass,setpts=PTS-STARTPTS'
        args=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf',filt,'-an','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-r',str(FPS),'-g','48','-video_track_timescale','24000','-movflags','+faststart',str(out)]
        proc=subprocess.Popen(args,stdin=subprocess.PIPE);st=time.time()
        try:
            for f in range(shot['start_frame'],shot['end_frame']):
                proc.stdin.write(ren.frame(f,shot).tobytes())
                if (f-shot['start_frame'])%48==0:print('RENDER',sid,f,'seconds',round(time.time()-st,1),flush=True)
        finally:proc.stdin.close()
        assert proc.wait()==0
        report={'id':sid,'frames':shot['end_frame']-shot['start_frame'],'elapsed':time.time()-st,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'camera_and_orbit_checks':ren.audit}
        (ROOT/f'validation/shot_{sid:02d}.json').write_text(json.dumps(report,indent=2));print('SHOT_DONE',sid,report['frames'],report['bytes'],flush=True)

def audit_orbits(ren):
    checks=[]
    for shot in PLAN['shots']:
        if shot['kind'] not in ['orbits','revolution','young','ending']:continue
        for f in range(shot['start_frame'],shot['end_frame']):
            t=f/FPS;u=(t-shot['start'])/(shot['end']-shot['start']);k=shot['kind']
            if k=='revolution':ren.camera([0,37,7],[0,0,0],39);day=min(u/.93,1)*10
            elif k=='young':ren.camera([12*math.sin(.28+.18*u),28,32],[0,-.35,0],40);day=48+t*.55
            elif k=='ending':ren.camera([7-1.8*smooth(u),31+4*smooth(u),29+3*smooth(u)],[0,-.2,0],39);day=48+t*.55
            else:ren.camera([8-2*smooth(u),27.5+3*smooth(u),30],[0,-.2,0],39);day=t*.55
            for i,(a,p) in enumerate(zip(DATA['semimajor_au'],DATA['period_days'])):
                r=a*80;ang=2*np.pi*day/p+[-.7,.7,2.2,-1.8,1.65][i];pos=[r*np.cos(ang),0,r*np.sin(ang)];q,vis=ren.project(pos)
                checks.append(dict(frame=f,planet=i,x=float(q[0]),y=float(q[1]),visible=bool(vis and 25<q[0]<W-25 and 190<q[1]<1400)))
    bad=[c for c in checks if not c['visible']]
    (ROOT/'validation/orbit_visibility.json').write_text(json.dumps(dict(checks=len(checks),failures=bad,all_visible=not bad),indent=2));assert not bad,bad[:3]

if __name__=='__main__':main()
