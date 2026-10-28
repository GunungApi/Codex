#!/usr/bin/env bash
set -euo pipefail
sudo timeout 100 apt-get install -y -qq ffmpeg libegl1 libegl-mesa0 libgl1-mesa-dri >/tmp/p067-apt.log 2>&1 || { sudo timeout 100 apt-get update -qq; sudo timeout 100 apt-get install -y -qq ffmpeg libegl1 libegl-mesa0 libgl1-mesa-dri; }
python -m pip install --quiet --timeout 30 numpy scipy Pillow moderngl==5.12.0 glcontext==3.0.0 soundfile
curl -fsSL --retry 2 --max-time 90 https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf -o "$RUNNER_TEMP/NotoSansCJKjp-Bold.otf"
echo "P067_FONT=$RUNNER_TEMP/NotoSansCJKjp-Bold.otf" >> "$GITHUB_ENV"
python - <<'PY'
from pathlib import Path
p=Path('production/p064_v2_film.py');s=p.read_text();a="self.font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';";assert a in s;s=s.replace(a,"self.font=os.environ.get('P067_FONT','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc');");p.write_text(s)
PY
python production/polish_orwell_067.py
python -m py_compile production/p067_film.py
mkdir -p p067_v1/source
python -m pip freeze > p067_v1/source/requirements-lock.txt
