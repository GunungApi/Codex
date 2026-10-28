#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
if ! sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a timeout 240 apt-get install -y -qq --no-install-recommends -o Dpkg::Use-Pty=0 ffmpeg libegl1 libegl-mesa0 libgl1-mesa-dri > /tmp/p067v4-system.log 2>&1; then
  sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a timeout 80 dpkg --configure -a >> /tmp/p067v4-system.log 2>&1 || true
  command -v ffmpeg >/dev/null || { tail -60 /tmp/p067v4-system.log; exit 1; }
fi
ffmpeg -version | head -1
python -m pip install --quiet --timeout 40 numpy scipy Pillow moderngl==5.12.0 glcontext==3.0.0 python-docx
curl -fsSL --retry 2 --max-time 80 https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf -o "$RUNNER_TEMP/NotoSansCJKjp-Bold.otf"
echo "P067_FONT=$RUNNER_TEMP/NotoSansCJKjp-Bold.otf" >> "$GITHUB_ENV"
python -m py_compile production/p067v4_kinetic.py production/p067v4_polish.py
