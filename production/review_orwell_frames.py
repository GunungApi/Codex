"""Wrap actual rendered frames in an OOXML document for private visual review.
The artifact archive is the OOXML package itself. No media are committed to Git.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import shutil,json
root=Path('review_document');(root/'_rels').mkdir(parents=True,exist_ok=True);(root/'word/_rels').mkdir(parents=True,exist_ok=True);(root/'word/media').mkdir(parents=True,exist_ok=True)
selected=[]
for version,base in [('v2',Path('old_review')),('v3',Path('new_review'))]:
 for scene,index in [(0,0),(3,-1),(6,1)]:
  files=sorted(base.rglob(f'p067v2_s{scene:02}_*.jpg'))
  if files:selected.append((version+f' scene {scene:02} '+files[index].name,files[index]))
for p in sorted(Path('new_review').rglob('p067v2_s02_*.jpg')):selected.append(('v3 chronology '+p.name,p))
assert selected,'No rendered frames retrieved'
NS='http://schemas.openxmlformats.org/wordprocessingml/2006/main';RN='http://schemas.openxmlformats.org/officeDocument/2006/relationships';DN='http://schemas.openxmlformats.org/drawingml/2006/main';WN='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing';PN='http://schemas.openxmlformats.org/drawingml/2006/picture'
paras=[];rels=[]
for i,(title,p) in enumerate(selected,1):
 target=f'frame_{i:02}.jpg';shutil.copy(p,root/'word/media'/target);rels.append(f'<Relationship Id="rId{i}" Type="{RN}/image" Target="media/{target}"/>')
 if i>1:paras.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
 paras.append('<w:p><w:pPr><w:spacing w:after="40"/></w:pPr><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>'+escape(title)+'</w:t></w:r></w:p>')
 cx,cy=4800600,8534400
 paras.append(f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{i}" name="Rendered frame {i}"/><a:graphic><a:graphicData uri="{PN}"><pic:pic><pic:nvPicPr><pic:cNvPr id="{i}" name="{target}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId{i}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
sect='<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="520" w:right="520" w:bottom="520" w:left="520" w:header="120" w:footer="120" w:gutter="0"/></w:sectPr>'
doc=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{NS}" xmlns:r="{RN}" xmlns:wp="{WN}" xmlns:a="{DN}" xmlns:pic="{PN}"><w:body>'+''.join(paras)+sect+'</w:body></w:document>'
(root/'word/document.xml').write_text(doc,encoding='utf-8')
(root/'word/_rels/document.xml.rels').write_text('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(rels)+'</Relationships>',encoding='utf-8')
(root/'_rels/.rels').write_text('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',encoding='utf-8')
(root/'[Content_Types].xml').write_text('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="jpg" ContentType="image/jpeg"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',encoding='utf-8')
print('VISUAL_PAGES',json.dumps([x[0] for x in selected]),flush=True)
