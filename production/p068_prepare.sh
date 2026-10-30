#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
sudo timeout 240 apt-get install -y --no-install-recommends ffmpeg libegl1 libegl-mesa0 libgl1-mesa-dri >/tmp/p068-render-apt.log 2>&1 || { sudo timeout 120 apt-get update -qq; sudo timeout 240 apt-get install -y --no-install-recommends ffmpeg libegl1 libegl-mesa0 libgl1-mesa-dri; }
python -m pip install --quiet --timeout 45 numpy scipy Pillow moderngl==5.12.0 glcontext==3.0.0 python-docx soundfile
curl -fsSL --retry 2 --max-time 80 https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf -o "$RUNNER_TEMP/NotoSansCJKjp-Bold.otf"
echo "P068_FONT=$RUNNER_TEMP/NotoSansCJKjp-Bold.otf" >> "$GITHUB_ENV"
python production/p068_refine.py
python -m py_compile production/p068_scene.py production/p068_finish.py
mkdir -p p068_v1/source
python -m pip freeze > p068_v1/source/requirements-lock.txt
