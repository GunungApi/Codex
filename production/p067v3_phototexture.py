"""P067 v3 finishing layer using Poly Haven CC0 rock surface maps.
The donated material is recolored as volcanic scenic art, not identified as sampled basalt.
Original geographical geometry, time ribbon, lighting and approved audio are retained.
"""
from pathlib import Path
import sys, json, hashlib, urllib.request, time, shutil, zipfile
import numpy as np
from PIL import Image
import moderngl
import p067v3_rocktime as V
S=V.S;F=V.F;ROOT=V.ROOT
ASSET='rock_boulder_dry'
URLBASE='https://dl.polyhaven.org/file/ph-assets/Textures/jpg/4k/rock_boulder_dry/'
MAPPINGS={'diff':'diff','normal':'nor_gl','arm':'arm'}

def acquire_assets():
 folder=ROOT/'assets/polyhaven';folder.mkdir(parents=True,exist_ok=True);rows=[]
 for role,suffix in MAPPINGS.items():
  name=f'{ASSET}_{suffix}_4k.jpg';dest=folder/name;url=URLBASE+name
  if not dest.exists():
   last=None
   for attempt in range(2):
    try:
     req=urllib.request.Request(url,headers={'User-Agent':'OrionArmVideoProduction/1.0'})
     with urllib.request.urlopen(req,timeout=75) as response:payload=response.read()
     assert len(payload)>100000,('Incomplete texture',role,len(payload))
     temp=dest.with_suffix('.download');temp.write_bytes(payload)
     with Image.open(temp) as image:image.verify()
     temp.replace(dest);last=None;break
    except Exception as exc:last=exc;time.sleep(1+attempt)
   if last is not None:raise RuntimeError('Could not retrieve licensed rock texture '+role) from last
  with Image.open(dest) as im:sz=im.size
  rows.append({'role':role,'file':str(dest.relative_to(ROOT)),'url':url,'dimensions':sz,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
 credit={'asset':'Rock Boulder Dry','source':'https://polyhaven.com/a/rock_boulder_dry','license':'CC0-1.0','license_source':'https://polyhaven.com/license','photography':'Dimitrios Savva','processing':'Rico Cilliers','verified_date':'2026-10-28','adaptation':'Albedo recolored to cool dark volcanic rock; triplanar normals, occlusion and roughness combined with original layered and fractured terrain. The source rock is not asserted to be basalt.','files':rows}
 F.dump(ROOT/'docs/rock_material_credit.json',credit)
 print('ROCK_MATERIAL_READY',json.dumps(rows,ensure_ascii=False),flush=True)
 return folder

S.FRAG=S.FRAG.replace('uniform sampler2D rocktex;','uniform sampler2D rocktex;uniform sampler2D photocolor;uniform sampler2D photonormal;uniform sampler2D photoarm;')
old='n=normalize(gn+perturb*.86+micro*.22);'
new=r'''vec3 px=texture(photonormal,P.zy*.145).rgb*2.-1.;
 vec3 py=texture(photonormal,P.xz*.145).rgb*2.-1.;
 vec3 pz=texture(photonormal,P.xy*.145).rgb*2.-1.;
 vec3 pn=vec3(0.,px.y,px.x)*weights.x+vec3(py.x,0.,py.y)*weights.y+vec3(pz.x,pz.y,0.)*weights.z;
 n=normalize(gn+pn*.73+perturb*.27+micro*.10);
 vec3 rgb=texture(photocolor,P.zy*.145).rgb*weights.x+texture(photocolor,P.xz*.145).rgb*weights.y+texture(photocolor,P.xy*.145).rgb*weights.z;
 rgb=pow(max(rgb,vec3(.001)),vec3(2.2));float grey=dot(rgb,vec3(.2126,.7152,.0722));
 vec3 arm=texture(photoarm,P.zy*.145).rgb*weights.x+texture(photoarm,P.xz*.145).rgb*weights.y+texture(photoarm,P.xy*.145).rgb*weights.z;
 float pao=clamp(arm.r,.12,1.);float roughness=clamp(arm.g,.35,.97);'''
assert old in S.FRAG;S.FRAG=S.FRAG.replace(old,new)
old='vec3 base=mix(vec3(.065,.074,.081),vec3(.23,.225,.207),clamp(q.r*1.35-.10,0.,1.));'
new='vec3 base=mix(vec3(grey),rgb,.14)*vec3(.78,.84,.90);base*=.78+.32*q.r;'
assert old in S.FRAG;S.FRAG=S.FRAG.replace(old,new)
S.FRAG=S.FRAG.replace('joint*.81','joint*.38').replace('float ao=clamp(1.-joint*.54-layer*.10,.30,1.);','float ao=clamp((1.-joint*.30-layer*.08)*pao,.18,1.);')
S.FRAG=S.FRAG.replace('mix(17.,72.,damp)','mix(mix(64.,12.,roughness),72.,damp)')

BaseCinema=V.Cinema
class PhotoCinema(BaseCinema):
 def __init__(self):
  folder=acquire_assets();super().__init__();self.photomaps={}
  for role,suffix in MAPPINGS.items():
   with Image.open(folder/f'{ASSET}_{suffix}_4k.jpg') as src:im=src.convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS)
   tex=self.c.texture(im.size,3,im.tobytes());tex.build_mipmaps();tex.filter=(moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR);self.photomaps[role]=tex
 def setcommon(self,cfg,t,eye,vp):
  super().setcommon(cfg,t,eye,vp)
  for role,slot,name in [('diff',9,'photocolor'),('normal',10,'photonormal'),('arm',11,'photoarm')]:self.photomaps[role].use(slot);self.put(self.prog,name,slot)
 def frame(self,cfg,t):
  image,qa=super().frame(cfg,t);qa['photographic_rock_detail']=True
  if cfg.get('time_scene',False):
   eye=np.array(cfg['eye']);vp=S.perspective(cfg['fov'],S.W/S.H)@S.look(eye,cfg['target']);bounds=[]
   for center,radius in [(V.A+[0,.85,0],1.),(V.B+[0,.85,0],.98)]:
    pts=[]
    for axis in np.eye(3):
     for sign in [-1,1]:
      p=center+axis*radius*sign;h=vp@np.r_[p,1.];q=h[:3]/h[3];pts.append([(q[0]+1)*S.W/2,(1-q[1])*S.H/2])
    p=np.array(pts);box=[float(p[:,0].min()),float(p[:,1].min()),float(p[:,0].max()),float(p[:,1].max())];bounds.append(box)
    assert box[0]>25 and box[2]<1055 and box[1]>330 and box[3]<1435,('Time landmark outside safe frame',box)
   assert bounds[0][2]<bounds[1][0] or bounds[0][3]<bounds[1][1],('Time landmarks intersect',bounds)
   qa['chronology_landmark_bounds']=bounds
  return image,qa

oldconfig=V.config
def config(t,tl):
 c=oldconfig(t,tl)
 if c['scene']==2:
  a,d=tl['boundaries'][2:4];second=tl['cues'][5]['start'];q=S.ramp(t,second-.15,d-.20)
  c['eye']=S.mix([8.,4.,25.],[9.,6.,29.5],q).tolist();c['target']=S.mix([1.8,.5,2.5],[0.,.55,0.],q).tolist()
 return c
F.Cinema=PhotoCinema;F.config=config

def assemble():
 acquire_assets();V.finish()
 note=ROOT/'deliverables'/f'{F.PREFIX}_script_and_sources.txt';text=note.read_text()
 text=text.replace('外部写真・楽曲なし。','岩肌にはPoly HavenのCC0写真由来素材を使用。外部楽曲なし。')
 text+='\n\n岩肌の追加素材：Rock Boulder Dry — Poly Haven\n撮影：Dimitrios Savva／処理：Rico Cilliers\nhttps://polyhaven.com/a/rock_boulder_dry\nライセンス：CC0-1.0。https://polyhaven.com/license\n2026-10-28確認。原寸4Kの色・法線・環境遮蔽／粗さ画像を取得し、描画には2048角の材質として使用。画面そのものは1080×1920の3D描画。色を黒い火山岩向けに調整した芸術表現で、原素材の岩種の同定を行ったものではない。映像の背景を写真に置き換えていない。\n'
 note.write_text(text,encoding='utf-8');shutil.copy(__file__,ROOT/'source'/Path(__file__).name)
 qa=json.loads((ROOT/'review/verification.json').read_text());qa.update(photographic_rock_source='Poly Haven: Rock Boulder Dry (CC0)',source_maps_resolution='4K',render_material_resolution=[2048,2048],chronology_endpoint_clearance_checked=True)
 F.dump(ROOT/'review/verification.json',qa)
 (ROOT/'source/REEDIT.txt').write_text('第3版の再編集入口はp067v3_phototexture.py。元のp067v3_rocktime.py、p067v2_scene.py、p067v2_finish.pyも同じフォルダへ置く。p067_v3として作業フォルダへ展開。python source/p067v3_phototexture.py shot N（0..9）、続けてassemble。原音は再生成せず、同梱の完成MP4をoriginal_previewへ置く。P067_FONTにNoto Sans CJK JPのパスを指定。材料画像はassets/polyhavenに保存済み。原寸素材はCC0で再配布可能。フォント・音声エンジン・モデルは同梱しない。\n',encoding='utf-8')
 archive=ROOT/'deliverables'/f'{F.PREFIX}_production.zip';archive.unlink()
 entries=[]
 for p in ROOT.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.ttf','.otf','.ttc','.zip']:entries.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
 F.dump(ROOT/'review/manifest.json',entries)
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,3) as z:
  for p in ROOT.rglob('*'):
   if p.is_file() and p!=archive and p.suffix.lower() not in ['.ttf','.otf','.ttc'] and 'voice_data' not in p.parts:z.write(p,str(p.relative_to(ROOT)))
 print('PHOTO_FINAL_QA',json.dumps(qa,ensure_ascii=False),flush=True)
 print('PHOTO_DELIVERY',json.dumps([{'name':p.name,'bytes':p.stat().st_size} for p in (ROOT/'deliverables').iterdir()],ensure_ascii=False),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':acquire_assets();F.prepare()
 elif mode=='preview':
  for s in [0,2,3,4,6,9]:F.shot(s,True)
 elif mode=='testclip':F.shot(2);F.shot(3)
 elif mode=='shot':F.shot(int(sys.argv[2]))
 elif mode=='assemble':assemble()
 else:raise ValueError(mode)
