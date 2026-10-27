"""Final geometry-only refinements. This script is applied after p064_v2_refine.py."""
from pathlib import Path
p=Path(__file__).with_name('p064_v2_film.py')
s=p.read_text(encoding='utf-8')
replacements={
"r.eye=np.array([3.,3.3,20.]);phase=0 if u<split else 1":"r.eye=np.array([3.,10.,18.]);phase=0 if u<split else 1",
"z=(j-1.5)*.53;head=":"z=(j-1.5)*.80;head=",
"pts=center+BASE_CARGO*(1+.05*np.sin(t*1.8));safe_cargo(r,pts,center,[2,2,2],t,'enclosed')":"pts=center+BASE_CARGO*(1.55-.65*smooth(u,.44,.96));safe_cargo(r,pts,center,[2,2,2],t,'enclosed',smooth(u,.44,.85))",
"q=smooth(u,max(.12,split-.08),.94)":"q=smooth(u,.12,.94)",
"c=center+np.array([(j-1)*sep,.15*np.sin(t*.6+j),0]);rr=.98":"fan=smooth(u,.08,.94);c=center+np.array([(j-1)*(2.16-.30*fan),(.50 if j!=1 else -1.40)*fan,0]);rr=.98",
"assert sep-1.96>=.19;r.clearances.append(sep-1.96)":"fan=smooth(u,.08,.94);gap=((2.16-.30*fan)**2+(1.90*fan)**2)**.5-1.96;assert gap>.16;r.clearances.append(gap)",
"r.semantic.update(daughter_distance=sep,retained_materials=6)":"r.semantic.update(daughter_fan=fan,minimum_daughter_gap=gap,retained_materials=6)",
"with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4)":"with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4)"
}
for old,new in replacements.items():
 assert old in s,old
 s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('Final refinements: projection spacing, deliberate material convergence, continuous neck change and separated daughter fan.')
