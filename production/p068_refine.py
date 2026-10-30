from pathlib import Path
p=Path(__file__).with_name('p068_scene.py');s=p.read_text()
fixes={
"self.post['time']=t;self.postvao.render()":"self.uniform(self.post,'time',t);self.postvao.render()",
"self.backfb=self.c.framebuffer([self.back])":"self.backfb=self.c.framebuffer([self.back],self.c.depth_renderbuffer((W,H)))",
"[.3,1.9,12.6]":"[.3,1.9,15.0]",
"[.2,1.8,10.5]":"[.2,1.8,13.5]",
"生息環境の再現例  ·  生命の起源の場所を示すものではない":"生息環境の再現例  ·  起源の場所は未特定"
}
for a,b in fixes.items():
 if a in s:s=s.replace(a,b)
 elif b not in s:raise RuntimeError('Expected renderer line not found: '+a)
p.write_text(s,encoding='utf-8')
print('PORTABILITY_AND_SILHOUETTE_REFINEMENTS_APPLIED')
