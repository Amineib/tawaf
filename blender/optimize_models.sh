#!/usr/bin/env bash
# CPU-only postprocessing. No render or decoder download is needed at runtime.
# The bundled r160 GLTFLoader supports KHR_mesh_quantization.
set -euo pipefail
SOURCE_DIR="${1:?Pass the raw Blender export folder}"
TARGET_DIR="${2:?Pass a different delivery folder}"
test "$(cd "$SOURCE_DIR" && pwd)" != "$(mkdir -p "$TARGET_DIR" && cd "$TARGET_DIR" && pwd)"
mkdir -p "$TARGET_DIR"
for MODEL in haram masa; do
  npm exec --yes --package=@gltf-transform/cli@4.2.1 -- gltf-transform quantize \
    "$SOURCE_DIR/$MODEL.glb" "$TARGET_DIR/$MODEL.glb" \
    --quantize-position 16 --quantize-normal 12 --quantize-texcoord 16
done
# Crowd prototypes are already tiny. Their local transforms are consumed by the
# crowd instancer; preserve them exactly rather than introducing dequant nodes.
cp "$SOURCE_DIR/pilgrims.glb" "$TARGET_DIR/pilgrims.glb"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECK_PYTHON="${UMRAH_PYTHON:-$PROJECT_ROOT/.venv/bin/python}"
if [ ! -x "$CHECK_PYTHON" ]; then CHECK_PYTHON=python3; fi
"$CHECK_PYTHON" "$PROJECT_ROOT/blender/check_assets.py" "$TARGET_DIR" --strict --delivery
