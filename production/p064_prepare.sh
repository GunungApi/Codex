#!/usr/bin/env bash
set -euo pipefail
sudo timeout 150 apt-get install -y -qq ffmpeg libegl1 libegl-mesa0 libgl1-mesa-dri >/tmp/p064-system-install.log 2>&1 || { cat /tmp/p064-system-install.log; exit 1; }
python -m pip install --quiet --progress-bar off numpy scipy Pillow moderngl==5.12.0 glcontext==3.0.0 soundfile
curl -fsSL --retry 2 --max-time 90 https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf -o "$RUNNER_TEMP/NotoSansCJKjp-Bold.otf"
echo "P064_FONT=$RUNNER_TEMP/NotoSansCJKjp-Bold.otf" >> "$GITHUB_ENV"
mkdir -p p064_v2/source
python -m pip freeze > p064_v2/source/requirements-lock.txt
python -c "import moderngl; c=moderngl.create_standalone_context(backend='egl'); print('Native renderer:',c.info['GL_RENDERER'])"
python production/p064_v2_refine.py
python production/p064_v2_visual_review.py
