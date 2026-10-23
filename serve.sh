#!/bin/bash
# Build the site, then open it locally on http://localhost:8000 (browsers block
# WebGL textures from file://, so a tiny local server is needed).
# web/dist is generated and not committed; this always serves a fresh build.
cd "$(dirname "$0")" || exit 1
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
if ! "$PY" web/build.py --review; then
  echo "Build failed. First time? Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi
(sleep 1; open "http://localhost:8000" 2>/dev/null || xdg-open "http://localhost:8000" 2>/dev/null) &
cd web/dist && "$PY" -m http.server 8000
