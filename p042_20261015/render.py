"""HEION-P042: native 1080x1920 mesh rendering, not image-pan animation."""
import os
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
from pathlib import Path
import json, math, sys, time, hashlib, subprocess
import numpy as np
from PIL import Image,ImageDraw
import moderngl
import base
ROOT=Path('p042'); W,H=1080,1920; FPS=24
PLAN=json.loads((ROOT/'timeline.json').read_text())
smooth=base.smooth;norm=base.norm;font=base.font
WHITE=base.WHITE;CYAN=base.CYAN;GOLD=base.GOLD;MUTED=base.MUTED
# Same underlying sphere and continent field for both members of each comparison.
base.FS=base.FS.replace('if(mode==1){', '''if(mode==6){float c=fb(local*8.+vec3(time*.024,0.,time*.007));float a=smoothstep(.53,.67,c)*.75;float lit=.28+.72*max(0.,dot(N,L));frag=vec4(vec3(.85,.89,.91)*lit,a);return;}
if(mode==7){float rim=pow(1.-max(0.,dot(N,V)),2.8);frag=vec4(.24,.61,.75,rim*.26);return;}
if(mode==1){''').replace('if(mode==2){', '''if(mode==4||mode==5){float land=fb(local*3.7+vec3(2.4,5.2,1.7));float coast=smoothstep(.468,.492,land);float rockgrain=fb(local*52.);vec3 rock=mix(vec3(.25,.19,.13),vec3(.58,.48,.32),rockgrain);vec3 ocean=mix(vec3(.025,.10,.18),vec3(.04,.37,.42),smoothstep(.40,.49,land));float shine=pow(max(0.,dot(N,halfv)),90.)*.65;vec3 wet=mix(ocean,rock,coast);vec3 dry=mix(vec3(.46,.28,.14),rock,.35+.5*coast);col=(mode==5?wet:dry)*(fill+diffuse*1.15);if(mode==5){col+=shine*(1.-coast)*vec3(.95,.87,.7);float ice=smoothstep(.78,.95,abs(local.y));col=mix(col,vec3(.6,.74,.77)*(fill+diffuse),ice);}}
if(mode==2){''')
TVS='''#version 330
in vec3 in_pos;in vec3 in_normal;in vec3 in_local;
uniform mat4 vp;uniform mat4 lightvp;uniform float time;uniform int mode;
out vec3 pos;out vec3 normal;out vec3 local;out vec4 shadowpos;
void main(){vec3 p=in_pos;if(mode==1)p.y+=.018*sin(p.x*2.1+time*1.3)+.011*sin(p.z*3.4-time*.8);if(mode==2)p.y+=.024*sin(p.x*1.7)*sin(p.z*2.);pos=p;normal=in_normal;local=in_local;shadowpos=lightvp*vec4(p,1.);gl_Position=vp*vec4(p,1.);}
'''
TFS='''#version 330
in vec3 pos;in vec3 normal;in vec3 local;in vec4 shadowpos;
uniform vec3 eye;uniform sampler3D noise_tex;uniform sampler2D shadowtex;uniform float time;uniform int mode;uniform int phase;
out vec4 frag;
float n(vec3 p){return texture(noise_tex,p*.061).r;}
float fb(vec3 p){return .53*n(p)+.27*n(p*2.03+3.)+.13*n(p*4.08)+.07*n(p*8.3);}
vec3 sky(vec3 r){float y=clamp(r.y,0.,1.);vec3 a=mix(vec3(.29,.39,.43),vec3(.07,.19,.30),pow(y,.65));vec3 sun=normalize(vec3(-.5,.65,.3));a+=vec3(.45,.32,.18)*pow(max(0.,dot(r,sun)),64.);return a;}
float visibility(){vec3 p=shadowpos.xyz/shadowpos.w*.5+.5;if(p.x<0.||p.x>1.||p.y<0.||p.y>1.)return 1.;float s=0.;for(int i=0;i<2;i++)for(int j=0;j<2;j++){float z=texture(shadowtex,p.xy+(vec2(i,j)-.5)/2048.).r;s+=p.z-.002>z?.28:1.;}return s*.25;}
void main(){vec3 V=normalize(eye-pos);vec3 L=normalize(vec3(-.5,.65,.3));vec3 N=normalize(normal);float grain=fb(pos*6.);float diffuse=max(0.,dot(N,L));float sh=visibility();vec3 col;
if(mode==0){float slope=1.-abs(N.y);vec3 albedo=mix(vec3(.23,.16,.11),vec3(.43,.36,.27),grain);albedo=mix(albedo,vec3(.40,.35,.29),smoothstep(.16,.62,slope));float snow=smoothstep(4.1,6.6,pos.y+grain*.65)*(1.-smoothstep(.5,.8,slope));if(phase==0)snow=max(snow,smoothstep(1.2,3.1,pos.y)*.6);albedo=mix(albedo,vec3(.73,.81,.84),snow);float shore=1.-smoothstep(.10,.48,abs(pos.y-.075));albedo=mix(albedo,vec3(.49,.41,.28),shore*.6);col=albedo*(.20+diffuse*sh*1.3);}
else if(mode==1){float dx=.046*cos(pos.x*2.1+time*1.3)+.036*cos(pos.x*8.1-pos.z*3.3+time*2.);float dz=.038*cos(pos.z*3.4-time*.8)-.026*cos(pos.x*8.1-pos.z*3.3+time*2.);N=normalize(vec3(-dx,1.,-dz));float fres=.025+.975*pow(1.-max(0.,dot(N,V)),5.);float depth=max(.0,.075-local.y);vec3 water=mix(vec3(.08,.35,.35),vec3(.012,.095,.16),1.-exp(-depth*.9));vec3 refl=sky(reflect(-V,N));float spec=pow(max(0.,dot(N,normalize(V+L))),160.);col=mix(water*(.48+.48*sh),refl,min(.88,fres));col+=vec3(1.,.9,.7)*spec*.6*sh;float foam=(1.-smoothstep(.015,.10,depth))*(.35+.65*sin(pos.x*8.+pos.z*5.+time));col=mix(col,vec3(.53,.69,.65),clamp(foam,0.,1.)*.32);}
else{float crack=pow(abs(sin(pos.x*1.31+fb(pos*3.)*2.)*sin(pos.z*.84+pos.x*.43)),.13);vec3 ice=mix(vec3(.08,.22,.32),vec3(.55,.72,.78),crack);float spec=pow(max(0.,dot(N,normalize(V+L))),45.)*.25;col=ice*(.27+max(0.,dot(N,L))*sh*.85)+spec;}
float dist=length(eye-pos);vec3 haze=sky(normalize(pos-eye));float f=1.-exp(-dist*.005);col=mix(col,haze,f);col=col/(1.+col*.42);col=pow(max(col,vec3(0.)),vec3(1./2.2));frag=vec4(col,1.);}
'''
BVS='''#version 330
in vec2 in_pos;out vec2 uv;void main(){uv=in_pos;gl_Position=vec4(in_pos,1.,1.);}
'''
BFS='''#version 330
in vec2 uv;out vec4 frag;uniform mat4 invvp;uniform vec3 eye;uniform sampler3D noise_tex;uniform float time;uniform int ground;uniform int phase;
float n(vec3 p){return texture(noise_tex,p*.047).r;}
float fb(vec3 p){return .56*n(p)+.28*n(p*2.07+3.)+.16*n(p*4.13+8.);}
void main(){vec4 far=invvp*vec4(uv,1.,1.);vec3 r=normalize(far.xyz/far.w-eye);vec3 c;
if(ground==0){float f=fb(r*17.);float band=exp(-pow((r.x*.3+r.z*.7+r.y)*4.,2.));c=vec3(.009,.017,.029)+vec3(.01,.025,.033)*band*f;}
else{float y=clamp(r.y,0.,1.);c=mix(vec3(.27,.37,.42),vec3(.035,.14,.27),pow(y,.6));vec3 L=normalize(vec3(-.5,.65,.3));c+=vec3(.8,.60,.34)*pow(max(0.,dot(r,L)),1100.);
if(r.y>.045){float a=max(0.,(10.-eye.y)/r.y),dt=4./r.y/16.;float trans=1.;vec3 add=vec3(0.);for(int i=0;i<16;i++){vec3 p=eye+r*(a+(float(i)+.5)*dt);float shape=clamp(1.-abs(p.y-12.)/2.,0.,1.);float dens=smoothstep(.54,.72,fb(p*.19+vec3(time*.025,0.,0.)))*shape;float light=clamp(1.-smoothstep(.5,.74,fb((p+L*1.8)*.19+vec3(time*.025,0.,0.))),.23,1.);float alpha=1.-exp(-dens*dt*.33);add+=trans*alpha*mix(vec3(.23,.32,.38),vec3(.80,.84,.81),light);trans*=1.-alpha;}c=c*trans+add;}
if(phase==0)c=mix(c,vec3(.22,.32,.42),.12);if(phase==2)c=mix(c,vec3(.39,.29,.20),.16);}
c=pow(max(c,vec3(0.)),vec3(1./2.2));frag=vec4(c,1.);}
'''
DVS='''#version 330
in vec3 in_pos;uniform mat4 lightvp;void main(){gl_Position=lightvp*vec4(in_pos,1.);}
'''
DFS='''#version 330
void main(){}
'''
def height(x,z):
    x=np.asarray(x);z=np.asarray(z)
    sides=2.6*(1.-np.exp(-(x/5.5)**2))
    mountains=5.1*np.exp(-((x+9.)**2/20+(z+10.)**2/82))+5.8*np.exp(-((x-9.)**2/28+(z+17.)**2/94))
    distant=2.6/(1+np.exp((z+25.)*.45))*(.62+.38*np.sin(x*.47+z*.11)**2)
    rip=.28*np.sin(x*.74+z*.27)*np.sin(z*.68)+.16*np.sin(x*1.7-z*.31)*np.cos(z*1.4)+.075*np.sin(x*3.8+z*2.1)
    return -.86+sides+mountains+distant+rip

def ortho(l,r,b,t,n,f):
    m=np.eye(4);m[0,0]=2/(r-l);m[1,1]=2/(t-b);m[2,2]=-2/(f-n);m[0,3]=-(r+l)/(r-l);m[1,3]=-(t+b)/(t-b);m[2,3]=-(f+n)/(f-n);return m

class Renderer(base.Renderer):
    def __init__(self):
        super().__init__(); self.camera_audit=[]
        self.bg=self.ctx.program(vertex_shader=BVS,fragment_shader=BFS);buf=self.ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());self.bgv=self.ctx.vertex_array(self.bg,[(buf,'2f','in_pos')]);self.bg['noise_tex']=0
        self.tp=self.ctx.program(vertex_shader=TVS,fragment_shader=TFS);self.tp['noise_tex']=0;self.tp['shadowtex']=1
        xs=np.linspace(-29,29,265);zs=np.linspace(-46,18,281);x,z=np.meshgrid(xs,zs);y=height(x,z);eps=.03
        nx=(height(x-eps,z)-height(x+eps,z))/(2*eps);nz=(height(x,z-eps)-height(x,z+eps))/(2*eps);nn=np.stack([nx,np.ones_like(x),nz],-1);nn/=np.linalg.norm(nn,axis=-1,keepdims=True)
        pos=np.stack([x,y,z],-1).reshape(-1,3);loc=pos.copy();normal=nn.reshape(-1,3)
        i=np.arange(len(zs)-1)[:,None];j=np.arange(len(xs)-1)[None,:];a=i*len(xs)+j;b=a+1;c=a+len(xs);d=c+1
        faces=np.stack([np.stack([a,c,b],-1),np.stack([b,c,d],-1)],-2).reshape(-1,3).astype('i4')
        self.tibo=self.ctx.buffer(faces.tobytes());self.tvbo=self.ctx.buffer(np.hstack([pos,normal,loc]).astype('f4').tobytes());self.terrain=self.ctx.vertex_array(self.tp,[(self.tvbo,'3f 3f 3f','in_pos','in_normal','in_local')],index_buffer=self.tibo)
        water=pos.copy();water[:,1]=.075;wn=np.zeros_like(pos);wn[:,1]=1
        self.wvbo=self.ctx.buffer(np.hstack([water,wn,loc]).astype('f4').tobytes());self.water=self.ctx.vertex_array(self.tp,[(self.wvbo,'3f 3f 3f','in_pos','in_normal','in_local')],index_buffer=self.tibo)
        np.savez_compressed(ROOT/'assets/landscape.npz',vertices=pos.astype('f4'),normals=normal.astype('f4'),triangles=faces,water=water.astype('f4'),water_bed=loc.astype('f4'))
        self.lightvp=ortho(-40,40,-40,40,.1,140)@base.look(np.array([-36.,55.,21.]),[0,0,-12])
        self.depth=self.ctx.depth_texture((2048,2048));self.depth.compare_func='';self.shadowfb=self.ctx.framebuffer(depth_attachment=self.depth)
        dp=self.ctx.program(vertex_shader=DVS,fragment_shader=DFS);dp['lightvp'].write(self.lightvp.T.astype('f4').tobytes());dv=self.ctx.vertex_array(dp,[(self.tvbo,'3f 24x','in_pos')],index_buffer=self.tibo)
        self.shadowfb.use();self.shadowfb.clear(depth=1.);self.ctx.enable(moderngl.DEPTH_TEST);dv.render();self.depth.use(1)
        self.tp['lightvp'].write(self.lightvp.T.astype('f4').tobytes())
        rng=np.random.default_rng(420042);self.molecules=np.column_stack([rng.uniform(-3,3,30),rng.uniform(.5,4,30),rng.uniform(-9,-1,30)])
        np.savez_compressed(ROOT/'assets/molecule_markers.npz',points=self.molecules)
        # Mesh annulus for the conditional distance band, not a calibrated stellar model.
        th=np.linspace(0,2*np.pi,241);vs=[];fs=[]
        for angle in th:
            for radius in [2.4,3.5]:vs.append([radius*np.cos(angle),0,radius*np.sin(angle)])
        for i in range(240):a=2*i;fs.extend([[a,a+1,a+2],[a+1,a+3,a+2]])
        self.bandb=self.ctx.buffer(np.array(vs,'f4').tobytes());self.bandi=self.ctx.buffer(np.array(fs,'i4').tobytes());self.bandv=self.ctx.vertex_array(self.lp,[(self.bandb,'3f','in_pos')],index_buffer=self.bandi)
        (ROOT/'validation/p042_renderer.json').write_text(json.dumps(dict(resolution=[W,H],samples=4,land_vertices=len(pos),land_triangles=len(faces),shadow_map=[2048,2048],volumetric_cloud_steps=16,terrain_seed=420042,geometry_reused_for_water_states=True,renderer=self.ctx.info['GL_RENDERER']),indent=2))
    def background(self,t,ground=0,phase=1):
        self.ctx.disable(moderngl.DEPTH_TEST);self.bg['invvp'].write(np.linalg.inv(self.vp).T.astype('f4').tobytes());self.bg['eye'].value=tuple(self.eye);self.bg['time']=t;self.bg['ground']=ground;self.bg['phase']=phase;self.bgv.render(mode=moderngl.TRIANGLE_STRIP);self.ctx.enable(moderngl.DEPTH_TEST)
        if not ground:self.stars()
    def world(self,p,r,state,t,rotation=.3):
        self.sphere(p,r,4,(.5,.4,.3),5 if state=='wet' else 4,rotation)
        if state=='wet':
            self.ctx.depth_mask=False;self.sphere(p,r*1.013,6,(.8,.85,.9),6,rotation+t*.0005);self.sphere(p,r*1.037,6,(.2,.5,.7),7,rotation);self.ctx.depth_mask=True
    def terrain_scene(self,t,phase,eye=None,target=None):
        eye=[3.2,5.2,12.5] if eye is None else eye;target=[0,.45,-9] if target is None else target
        self.camera(eye,target,43);self.background(t,1,phase);self.tp['vp'].write(self.vp.T.astype('f4').tobytes());self.tp['eye'].value=tuple(self.eye);self.tp['time']=t;self.tp['phase']=phase;self.tp['mode']=0;self.terrain.render()
        if phase in [0,1]:self.tp['mode']=2 if phase==0 else 1;self.water.render()
        margin=float(self.eye[1]-height(self.eye[0],self.eye[2]));assert margin>.4
        self.camera_audit.append(dict(t=t,phase=phase,height_margin=margin))
    def packet(self,a,b,t,col=(.97,.65,.25,.9),wave=False):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        for k in range(2):
            u=(t*.45+k*.5)%1;start=max(0,u-.22);s=np.linspace(start,u,32);p=a+s[:,None]*v
            if wave:p[:,0]+=.045*np.sin(s*43.-t*7.)
            self.line(p,col)
    def frame(self,f,shot):
        t=f/FPS;u=float(np.clip((t-shot['start'])/(shot['end']-shot['start']),0,1));k=shot['kind'];s=smooth(u)
        self.ms.use();self.ctx.viewport=(0,0,W,H);self.ms.clear(.009,.014,.023,1);self.ctx.enable(moderngl.DEPTH_TEST|moderngl.BLEND);self.ctx.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA);self.prog['time']=t
        annotations=[];ratio=None
        if k in ['opening','twins']:
            eye=[2.2-.5*s,1.1,12.0+.55*s] if k=='opening' else [1.7+.65*s,1.25,12.55]
            self.camera(eye,[0,-.12,0],42);self.background(t);self.prog['light'].value=(-6,6,7)
            # Both are at equal camera depth, equal radius, and share the same underlying mesh.
            for x,state in [(-1.40,'dry'),(1.40,'wet')]:
                self.world([x,.08,0],1.12,state,t,.32+t*.018);q,_=self.project([x,-1.22,0]);annotations.append(('同じ半径',q[0],q[1]+30,32,MUTED))
        elif k=='flux':
            self.camera([3.2,.9,18.], [0,.55,0],40);self.background(t);star=np.array([0,3.25,0]);near=2.2;scale=1.+smooth(np.clip((u-.22)/.45,0,1));p=star+np.array([0,-near*scale,0]);self.prog['light'].value=tuple(star)
            self.sphere(star,.56,6,(1.,.72,.35),1,t*.02);self.world(p,.58,'dry',t,.4)
            # A single receiver moves outward; star output and receiver radius do not change.
            for j in [-.32,0,.32]:self.packet(star+[j,0,0],p+[j,.63,0],t+j)
            self.line([[.95,star[1],0],[.95,p[1],0]],(.46,.70,.75,.85));self.line([[.82,p[1],0],[1.08,p[1],0]],(.46,.70,.75,.85))
            ratio=scale;self.audit.append(dict(frame=f,distance_ratio=scale,flux_ratio=1/scale**2,star_luminosity=1.,receiver_radius=.58))
        elif k in ['reflect','heat']:
            self.camera([3.0,2.1,10.8],[0,.2,0],42);self.background(t);self.prog['light'].value=(-6,7,6);self.world([0,-.45,0],1.5,'wet',t,.4+t*.009)
            ang=np.linspace(.15,np.pi-.15,100);arc=np.stack([1.96*np.cos(ang),1.96*np.sin(ang)-.45,np.ones(len(ang))*.2],-1);self.line(arc,(.40,.72,.79,.5))
            if k=='reflect':
                self.packet([-3.1,3.7,1.1],[-.75,1.35,.65],t)
                self.packet([-.75,1.35,.65],[-2.7,3.35,1.7],t+.8,(.5,.82,.91,.9))
            else:
                self.packet([.0,1.02,.85],[.28,1.77,.73],t,(1.,.44,.19,.98),True)
                # Absorption is a local handoff; outgoing packets are newly emitted both ways.
                self.sphere([.28,1.77,.73],.070,6,(.95,.58,.24),1,t)
                self.packet([.28,1.77,.73],[1.75,3.3,.8],t-.4,(1.,.54,.22,.9),True)
                self.packet([.28,1.77,.73],[.95,.84,1.0],t+.3,(1.,.54,.22,.9),True)
        elif k in ['ice','liquid','vapor']:
            phase={'ice':0,'liquid':1,'vapor':2}[k];self.terrain_scene(t,phase)
            if phase==2:
                self.prog['light'].value=(-20,35,12)
                for i,p in enumerate(self.molecules):
                    q=p.copy();q[1]+=.18*np.sin(t*.9+i);q[0]+=.14*np.sin(t*.4+i*2)
                    self.sphere(q,.035+(i%3)*.01,6,(.50,.80,.9),1,t)
        elif k=='zone':
            self.camera([4.5,9,12],[0,-.2,0],42);self.background(t);self.prog['light'].value=(0,0,0);self.sphere([0,0,0],.55,6,(1.,.72,.36),1,t*.02)
            self.ctx.depth_mask=False;self.lp['color'].value=(.15,.51,.58,.23);self.bandv.render();self.ctx.depth_mask=True
            for r in [2.4,3.5]:
                th=np.linspace(0,2*np.pi,320,endpoint=False);self.line(np.stack([r*np.cos(th),np.zeros(len(th)),r*np.sin(th)],-1),(.22,.52,.57,.7),True)
            ang=.7+u*.55;p=[2.9*np.cos(ang),0,2.9*np.sin(ang)];self.world(p,.36,'wet',t,.2)
        elif k=='evidence':
            self.camera([2.5,1.1,8.7],[0,-.35,0],42);self.background(t);self.prog['light'].value=(-6,6,7);self.world([0,.3,0],1.30,'wet',t,.4+t*.012)
        else:
            if k=='shore':eye=[2.6-1.2*s,3.8+.7*s,11.+2*s]
            else:eye=[1.4-.6*s,4.5+.7*s,13.+2*s]
            self.terrain_scene(t,1,eye,[0,.4,-11])
        self.ctx.copy_framebuffer(self.fbo,self.ms);im=Image.frombytes('RGB',(W,H),self.fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGBA')
        over=Image.new('RGBA',(W,H));d=ImageDraw.Draw(over)
        def text(v,x,y,n=40,col=WHITE,anchor='mm'):d.text((int(x),int(y)),v,font=font(n),fill=col,anchor=anchor,stroke_width=1,stroke_fill=(0,0,0,140))
        # Subtle upper scrim protects small chapter text over bright sky.
        d.rectangle((0,0,W,170),fill=(4,10,18,135))
        text('平穏暦全史 ／ 前史042',65,112,30,MUTED,'lm');text('第2巻・第6章',1015,112,28,MUTED,'rm')
        titles={'opening':'惑星がある。海もある？','twins':'同じ大きさ、違う環境','flux':'変えるのは、星からの距離','reflect':'大気は、光にも働く','heat':'大気は、熱にも働く','ice':'温度と気圧で、水の姿が変わる','liquid':'同じ地形、別の条件','vapor':'同じ地形、別の条件','zone':'地表に液体の水がありうる帯','evidence':'生命の証拠を、さらに探す','shore':'惑星を見つけた、その先へ','ending':'環境を知る旅は、続く'}
        text(titles[k],540,277,43,CYAN)
        for a in annotations:text(*a)
        if k in ['opening','twins']:text('環境の比較模型',540,350,31,MUTED)
        if k=='flux':
            text(f'距離  {ratio:.1f} 倍',540,1225,51,CYAN)
            result='4分の1' if ratio>1.99 else f'{1/ratio**2:.2f} 倍'
            text('届く光  '+result,540,1310,58,GOLD)
            text('同じ星・同じ受光面積',540,350,31,MUTED)
        if k=='reflect':text('光の一部は、宇宙へ',540,350,32,MUTED)
        if k=='heat':text('吸収した熱を、外向きにも地面にも放つ',540,350,30,MUTED)
        if k in ['ice','liquid','vapor']:
            label={'ice':'氷','liquid':'液体の水','vapor':'水蒸気'}[k]
            d.rounded_rectangle((380,376,700,470),radius=18,fill=(5,16,25,165));text(label,540,423,55,WHITE)
        if k=='zone':
            seg=PLAN['narration'][4];start=seg['start']+seg['groups'][2]['start']
            text('大気などの条件と合わせて考える',540,352,31,MUTED)
            if t>=start:text('ハビタブルゾーン',540,1265,58,CYAN)
        if k=='evidence':
            text('環境の条件',540,1180,45,CYAN);text('生命の検出は、次の問い',540,1282,44,WHITE)
        note='環境の比較模型／地表の液体の水を考える'
        if k in ['ice','liquid']:note='同じ地形・別条件／実在惑星の海の復元ではない'
        if k=='vapor':note='水蒸気は透明／光る点は分子の目印'
        if k=='zone':note='帯の幅は模式化／大気などの条件で変わる'
        if k in ['shore','ending']:note='説明用の景観／生物や植物は描いていない'
        text(note,540,1760,28,MUTED)
        return Image.alpha_composite(im,over).convert('RGB')

def burn_proof(path,out,t):
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(path),'-vf',f'setpts=PTS+{t}/TB,ass=p042/captions/heionreki_p042_v1_ja.ass','-frames:v','1',str(out)],check=True)

def render_shot(ren,sid):
    shot=PLAN['shots'][sid];out=ROOT/f'clips/shot_{sid:02d}.mp4';out.parent.mkdir(parents=True,exist_ok=True)
    filt=f'setpts=PTS+{shot["start"]}/TB,ass=p042/captions/heionreki_p042_v1_ja.ass,setpts=PTS-STARTPTS'
    cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','24','-i','-','-vf',filt,'-an','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-r','24','-g','48','-video_track_timescale','24000','-movflags','+faststart',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE);start=time.time()
    try:
        for f in range(shot['start_frame'],shot['end_frame']):
            proc.stdin.write(ren.frame(f,shot).tobytes())
            if (f-shot['start_frame'])%48==0:print('FRAME',sid,f,'ELAPSED',round(time.time()-start,1),flush=True)
    finally:proc.stdin.close()
    assert proc.wait()==0
    report=dict(id=sid,frames=shot['end_frame']-shot['start_frame'],elapsed=time.time()-start,bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),camera_checks=ren.camera_audit,model_checks=ren.audit)
    (ROOT/f'validation/shot_{sid:02d}.json').write_text(json.dumps(report,indent=2));print('SHOT_DONE',sid,report['frames'],flush=True)

def main():
    ren=Renderer();mode=sys.argv[1] if len(sys.argv)>1 else 'proof'
    if mode=='shot':render_shot(ren,int(sys.argv[2]));return
    folder=ROOT/'validation/previews';folder.mkdir(parents=True,exist_ok=True);thumbs=[]
    for shot in PLAN['shots']:
        f=(shot['start_frame']+shot['end_frame'])//2;raw=folder/f'raw_{shot["id"]:02d}.png';out=folder/f'caption_{shot["id"]:02d}.png'
        ren.frame(f,shot).save(raw);burn_proof(raw,out,f/FPS);im=Image.open(out).convert('RGB');thumb=im.resize((270,480));d=ImageDraw.Draw(thumb);d.rectangle((0,0,200,27),fill='black');d.text((5,3),f'{shot["id"]:02d}  {f/FPS:.2f}s',fill='white');thumbs.append(thumb)
    sheet=Image.new('RGB',(1080,math.ceil(len(thumbs)/4)*480))
    for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*270,(i//4)*480))
    sheet.save(ROOT/'validation/contact_sheet.jpg',quality=94)
    # Full difficult shots are retained, avoiding a low-resolution stand-in.
    for sid in [5,6,7]:render_shot(ren,sid)
    print('NATIVE_PROOF_DONE',flush=True)
if __name__=='__main__':main()
