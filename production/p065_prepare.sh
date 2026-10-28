#!/usr/bin/env bash
set -euo pipefail
bash production/p064_prepare.sh
python - <<'PY'
from pathlib import Path
p=Path('production/p065_film.py')
s=p.read_text()
s=s.replace('import p064_v2_film as f\n','import p064_v2_film as f\nf.ROOT=ROOT\n')
p.write_text(s)
print('P065 voice, rendering, and assembly share one explicit root.')
PY
