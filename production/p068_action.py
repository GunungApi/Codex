"""P068 visual refinements after inspecting the first 20 native test pictures.
The fixed-camera explanatory shots gain visible fluid motion and staged exchanges.
Warm currents and membrane light pulses are explicitly explanatory representations.
"""
import sys,math,json
import numpy as np
import p068_scene as S
S.CAPTIONS['水に漂い、周囲とやり取りする。']=['水に漂い、','周囲とやり取りする。']
S.CAPTIONS['小さな命の営みが続いていた。']=['小さな命の営みが','続いていた。']
S.FRAG=S.FRAG.replace('mix(behind,wall,.46+.27*rim)','mix(behind,wall,.62+.20*rim)').replace('vec3(.22,.56,.51)*rim','vec3(.13,.34,.29)*rim').replace('*sp*.56','*sp*.40')
S.FRAG=S.FRAG.replace('vec3(.20,.062,.008)*warm','vec3(.75,.20,.018)*warm')
BASE=S.arrange

def arrange(t,tl,s):
 c=BASE(t,tl,s);a,b=tl['boundaries'][s:s+2];tt=t-a;second=c['second'];span=b-a
 # Scale changes are intentional close/wide shot changes, not biological growth.
 if s==0:
  q=S.ramp(tt,0,1.05);c['eye']=S.mix([.8,2.2,19.0],[.1,1.5,10.4],q).tolist();c['target']=[0,.45,0]
 elif s==1:
  c['eye']=S.mix([-.8,2.0,14.5],[.7,2.0,14.5],S.ramp(tt,.1,span-.15)).tolist()
 elif s==2:c['eye']=[.3,1.65,12.0];c['target']=[0,.45,0]
 elif s==3:
  c['eye']=[1.4,2.1,10.1];c['target']=[0,.45,0]
 elif s==4:
  c['eye']=[.8,1.4,10.2];c['target']=[0,.45,0]
 elif s==5:c['eye']=[-.7,1.8,13.3]
 elif s==6:
  q=S.ramp(t,second-.18,second+.65);c['eye']=S.mix([4.3,4.4,17.],[.5,1.7,11.7],q).tolist();c['heat']=1.4
 elif s==7:c['eye']=[0,2.4,17.5]
 elif s==8:
  c['eye']=S.mix([-2.2,3.7,16.],[1.8,2.4,16.],S.ramp(tt,.1,span-.1)).tolist();c['target']=[0,.35,0]
 elif s==9:
  q=S.ramp(tt,.1,span-.2);c['eye']=S.mix([.2,1.8,13.7],[2.0,5.2,24.],q).tolist()
 # Fluid-driven displacement and tumbling are coherent, not camera shake.
 for j,h in enumerate(c['cells']):
  group=s in [1,2,5,7,8,9];amp=.23 if group else .43
  h['p'][0]+=amp*np.sin(tt*1.6+.6*j)
  h['p'][1]+=.15*np.sin(tt*1.65+j*.4)
  h['angles'][2]+=.38*np.sin(tt*1.15+j*.7)
  h['angles'][1]+=.25*np.sin(tt*.9+j)
  if j>0:h['scale'][1]*=.82+.13*(j%2)
  if s==4:
   h['p'][0]=-.35+.13*np.sin(tt*1.2);h['angles'][2]=.10+.12*np.sin(tt*1.3);h['angles'][1]=.08
   h['cut']=.90*S.ramp(tt,.20,.85)
   h['energy']=.16+.84*S.ramp(t,second-.10,second+.35)
  if s==3 and t>second:h['energy']=.20+.65*S.ramp(t,second,second+.6)
  h['p'][1]=max(h['p'][1],float(S.floor(h['p'][0],h['p'][2]))+1.5*max(h['scale'])+.18)
 c['food']=[]
 if s in [0,2,3,4,5,6,8,9]:
  cp=np.array(c['cells'][0]['p']);sc=c['cells'][0]['scale'][0]
  for j in range(6):
   phase=(tt*.65+j*.171)%1.;x=2.8-3.1*phase;y=(j-2.5)*.28;z=sc*.70+.09*np.sin(phase*np.pi)
   if s!=4 and x<sc*.66:continue
   if s==4 and x<-.18:continue
   c['food'].append({'p':(cp+[x,y,z]).tolist(),'r':.087})
 c['event']+='; fluid_current_and_exchange';return c
S.arrange=arrange
BASEC=S.Cinema
class Cinema(BASEC):
 def __init__(self):
  self._scene=-1;self._t=0.;self._a=0.;self._second=0.;super().__init__()
  for j,x in enumerate([-3.1,-2.6,2.9]):
   ps=[[x+.22*np.sin(u*7+j),-3.2+7.5*u,-6.+.45*np.sin(u*5+j)] for u in np.linspace(0,1,130)]
   self.mesh('warmflow'+str(j),*S.tube(ps,.045,8))
 def frame(self,t,tl,s):
  self._scene=s;self._t=t;self._a=tl['boundaries'][s];self._second=next(x for x in tl['cues'] if x['scene']==s and x['id']%2==0)['start']
  return super().frame(t,tl,s)
 def draw(self,name,kind,model=None,tint=(.12,.41,.34),cut=0,energy=0,reveal=1):
  if name=='timepath':model=S.matrix([0,2.25,-1.5]);tint=(.10,.38,.50)
  if kind==2 and tint==(.25,.48,.35):
   p=model[:3,3];q=.5+.5*np.sin(self._t*2.8+p[1]*5.);v=S.ramp(self._t,self._second-.05,self._second+.5)
   tint=tuple(S.mix([.16,.29,.24],[.64,.68,.20],q*v))
  super().draw(name,kind,model,tint,cut,energy,reveal)
  if name=='terrain' and self._scene==6:
   tt=self._t-self._a
   for j in range(3):
    r=S.ramp(tt,.16+j*.23,1.15+j*.23)
    super().draw('warmflow'+str(j),3,tint=(.50,.22,.045),energy=.1,reveal=r)
S.Cinema=Cinema
BASEOVER=S.Typography.overlay

def overlay(self,im,t,cfg,tl):
 # Footer remains short; it clarifies only the scenes that use explicit diagram light.
 out=BASEOVER(self,im,t,cfg,tl)
 if cfg['scene']==6:
  from PIL import Image,ImageDraw
  q=out.convert('RGBA');d=ImageDraw.Draw(q);d.rectangle((90,1748,990,1810),fill=(3,24,30,255));self.text(d,'暖かな水の流れを強調  ·  生息環境の再現例',540,1782,23,(171,205,214,235));return q.convert('RGB')
 return out
S.Typography.overlay=overlay
if __name__=='__main__':
 if sys.argv[1]=='preview':
  for s in range(10):S.shot(s,True)
 elif sys.argv[1]=='shot':S.shot(int(sys.argv[2]))
 elif sys.argv[1]=='assemble':
  import p068_finish as F
  F.finish()
 else:raise ValueError(sys.argv[1])
