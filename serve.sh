#!/bin/bash
# Open the tour locally: serves web/dist on http://localhost:8000 (browsers block
# WebGL textures from file://, so a tiny local server is needed).
cd "$(dirname "$0")/web/dist" && (sleep 1; open "http://localhost:8000" 2>/dev/null || xdg-open "http://localhost:8000") &
cd "$(dirname "$0")/web/dist" && python3 -m http.server 8000
