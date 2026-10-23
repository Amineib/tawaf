#!/usr/bin/env bash
# Runs only on the isolated rented H100; invoked after the source archive arrives.
set -euo pipefail
cd /opt/umrah/project
export UMRAH_DEVICE=CUDA
export UMRAH_ASSETS="$PWD/assets"
export UMRAH_RESUME=1
PY=/opt/umrah/render-env/bin/python
mkdir -p output/contact output/fps output/review output/panos
nvidia-smi --query-gpu=name,uuid,memory.total --format=csv > output/gpu.csv
if [ -n "${UMRAH_CONTACT_SOURCE:-}" ]; then
  cp "$UMRAH_CONTACT_SOURCE" output/contact/contact.png
else
  "$PY" blender/bake_contact.py output/contact
fi
export UMRAH_CONTACT="$PWD/output/contact/contact.png"
"$PY" blender/export_fps.py output/fps assets
"$PY" blender/render_people.py output/review
"$PY" blender/render_comparisons.py output/review
"$PY" blender/build_scene.py haram output/panos 4096 64
UMRAH_TIME=night "$PY" blender/build_scene.py haram output/panos 4096 64
"$PY" blender/build_scene.py masa output/panos 4096 64
find output -name '*.blend' -delete
"$PY" blender/check_assets.py output/fps --strict --output output/asset-report.json
"$PY" - <<'PY'
import hashlib,json
from pathlib import Path
root=Path('output')
records={p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in root.rglob('*') if p.is_file()}
(root/'checksums.json').write_text(json.dumps(records,indent=2))
PY
touch output/DONE
echo UMRAH_RENDER_COMPLETE
