from pathlib import Path
p=Path(__file__).with_name('p065_film.py')
s=p.read_text()
old="""  # Separated lattices become a mixed lattice without interpenetration.
  for j in range(12):
   y=-1.6+(j//4)*1.35;col=j%4;x=-2.7+col*1.8
   kind=0 if col<2 else 1;target_kind=(j+j//4)%2
   p=np.array([x,y,.65]);r.molecule(p,kind,1.2,alpha=1-mix,tag='oldstate')
   # Alternate identity represents blending of composition, not chemical conversion.
   if mix>.02:
    colr=(AMBER if target_kind==0 else CYAN);r.ball(p,.20, colr,alpha=mix,rough=.25)
"""
new="""  # Preserve every molecule's identity. The middle columns exchange on two
  # distinct curved paths; outer columns stay as fixed spatial reference points.
  for row in range(3):
   y=-1.45+row*1.45
   for col in range(4):
    kind=0 if col<2 else 1;x=-2.7+col*1.8;yy=y
    if col==1:x=-.9+1.8*mix;yy=y+.40*np.sin(np.pi*mix)
    if col==2:x=.9-1.8*mix;yy=y-.40*np.sin(np.pi*mix)
    r.molecule([x,yy,.65],kind,1.05,tag='mixing')
"""
assert old in s;s=s.replace(old,new)
s=s.replace("cell(r,t*(1-.45*cutoff),strength=strength,continuous=False)","flow_time=r.scene_start+(t-r.scene_start)*(1-.30*cutoff)\n  cell(r,flow_time,strength=strength,continuous=False)")
s=s.replace("r.arrow_flow(x,.2,t*(1-.75*cutoff),col,1,1 if x<0 else -1,strength)","r.arrow_flow(x,.2,flow_time,col,1,1 if x<0 else -1,strength)")
s=s.replace("t=f/FPS;u=(t-a)/(z-a);r.reset();arrange", "t=f/FPS;u=(t-a)/(z-a);r.reset();r.scene_start=a;arrange")
p.write_text(s)
print('P065 identity-preserving mixing and continuous timings applied')
