#!/bin/bash
# Job: improved-architecture Haram, day + night, 4K.
set -x
W=/opt/umrah; T=197a7cf9035120fd78d4b4d1; OUT=$W/www/$T/v2; ST=$W/www/$T/status.txt
mkdir -p $OUT
cp common.py build_scene.py fetch_assets.py $W/code/
cd $W/code && python3 fetch_assets.py 4k $W/assets
export UMRAH_ASSETS=$W/assets UMRAH_DEVICE=OPTIX UMRAH_RESUME=1
for TIME in day night; do
  UMRAH_TIME=$TIME $W/blender/blender -b -P build_scene.py -- haram $OUT 4096 256 2>&1 \
    | grep --line-buffered -E "rendered|Error|Traceback" | sed -u "s/^/$TIME: /" >> $ST
done
echo "$(date -u +%H:%M:%S) v2 DONE" >> $ST
