#!/usr/bin/env bash
set -euo pipefail
bash production/p064_prepare.sh
python - <<'PY'
from pathlib import Path
p=Path('production/p065_film.py')
s=p.read_text()
s=s.replace('import p064_v2_film as f\n','import p064_v2_film as f\nf.ROOT=ROOT\n')
s=s.replace('scale=1.,comparison=False):','scale=1.,comparison=False,reveal=1.):')
s=s.replace('sy=1.95*sc,sz=.35*sc)','sy=1.95*sc*reveal,sz=.35*sc)')
s=s.replace('for j in range(3):\n   phase=(t*.32*max(.15,flow)+j/3)%1.', 'for j in range(4):\n   phase=(t*.32*max(.15,flow)+j/4)%1.')
s=s.replace('if mixed>.1 and j==1:kind=1-kind','if (mixed>.2 and j==1) or (mixed>.6 and j==3):kind=1-kind')
s=s.replace('kind,.65*sc,track=True','kind,1.0*sc,track=True')
s=s.replace('p(x,y,.48),.080*sc','p(x,y,.72),.115*sc')
s=s.replace('np.array([x,y,.68])*sc','np.array([x,y,1.12])*sc')
s=s.replace('np.array([-.58+q*1.16,y*.55,.43])*sc','np.array([-.58+q*1.16,y*.55,.72])*sc')
s=s.replace('progress=cueq,electrons=True)','progress=cueq,electrons=True,reveal=.32+.68*smooth(u,.03,max(.1,split)))')
s=s.replace(',.6+.75*math.sin(q*math.pi),1.0]',',.6+.75*math.sin(q*math.pi),1.2]')
p.write_text(s)
print('P065 explicit root, matching mixed compositions, larger tracers, keyword-driven mineral reveal, and protected reaction plane applied.')
PY
