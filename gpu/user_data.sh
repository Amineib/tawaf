#!/bin/bash
# Umrah tour 4K render job. Code is uploaded after boot (PUT /197a7cf9035120fd78d4b4d1/code.tgz).
exec > /var/log/umrah.log 2>&1
set -x
T=197a7cf9035120fd78d4b4d1
W=/opt/umrah; OUT=$W/www/$T
mkdir -p $W/code $OUT
status() { echo "$(date -u +%H:%M:%S) $*" >> $OUT/status.txt; }
cat > $W/srv.py <<'PY'
import http.server, os, sys
T = sys.argv[1]
class H(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(403); return None
    def do_PUT(self):
        if not self.path.startswith('/' + T + '/') or '..' in self.path:
            self.send_error(403); return
        n = int(self.headers['Content-Length']); p = '.' + self.path
        with open(p + '.part', 'wb') as f:
            f.write(self.rfile.read(n))
        os.replace(p + '.part', p)
        self.send_response(201); self.end_headers()
os.chdir('/opt/umrah/www')
http.server.ThreadingHTTPServer(('', 8080), H).serve_forever()
PY
cat > $W/gpucheck.py <<'PY'
import bpy
p = bpy.context.preferences.addons['cycles'].preferences
ok = False
for k in ('OPTIX', 'CUDA'):
    try:
        p.compute_device_type = k; p.get_devices()
        names = [d.name for d in p.devices if d.type == k]
        print('DEV', k, names); ok = ok or bool(names)
    except Exception as e:
        print('DEV', k, e)
open('/opt/umrah/gpu_ok', 'w').write('1' if ok else '0')
PY
nohup python3 $W/srv.py $T >/dev/null 2>&1 &
status "boot"
apt-get update -y && apt-get install -y libxrender1 libxxf86vm1 libxfixes3 libxi6 libxkbcommon0 libsm6 libgl1 libegl1 xz-utils curl
status "deps ok"
cd $W && curl -sSL --retry 5 -o blender.tar.xz https://download.blender.org/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz && tar -xf blender.tar.xz && mv blender-5.2.2-linux-x64 blender && status "blender ok"
nvidia-smi --query-gpu=name,driver_version --format=csv >> $OUT/status.txt
$W/blender/blender -b -P $W/gpucheck.py 2>&1 | grep DEV >> $OUT/status.txt
if [ "$(cat $W/gpu_ok)" != "1" ]; then status "NO_GPU - stopping"; exit 1; fi
status "gpu ok - waiting for code"
while [ ! -f $OUT/code.tgz ]; do sleep 5; done
tar -xzf $OUT/code.tgz -C $W/code && rm -f $OUT/code.tgz && status "code ok"
cd $W/code && python3 fetch_assets.py 4k $W/assets && status "assets ok" || status "ASSETS FAILED"
export UMRAH_ASSETS=$W/assets UMRAH_DEVICE=OPTIX UMRAH_RESUME=1
for SCENE in haram masa; do
  $W/blender/blender -b -P build_scene.py -- $SCENE $OUT 4096 256 >> $W/render_$SCENE.log 2>&1
  grep -E "rendered|Cycles device|HDRI|Error|Traceback" $W/render_$SCENE.log >> $OUT/status.txt
done
status "DONE"
