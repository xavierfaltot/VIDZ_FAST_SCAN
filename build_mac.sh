#!/bin/bash
set -e

cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller   --noconfirm   --windowed   --name "VIDZ SCAN FAST"   --collect-all scenedetect   app.py

echo ""
echo "DONE → dist/VIDZ SCAN FAST.app"
