"""Assemble dist/index.html from app.html + content.js + view angles, and copy panoramas."""
import json, os, shutil, sys
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
renders = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'renders')
dist = os.path.join(here, 'dist'); os.makedirs(os.path.join(dist, 'pano'), exist_ok=True)
views = {}
for f in ('haram_views.json', 'masa_views.json'):
    p = os.path.join(renders, f)
    if not os.path.exists(p):
        p = os.path.join(here, '..', 'test', f)
    views.update(json.load(open(p)))
html = open(os.path.join(here, 'app.html')).read()
html = html.replace('/*@CONTENT@*/', open(os.path.join(here, 'content.js')).read())
html = html.replace('/*@VIEWS@*/', json.dumps(views))
audio_dir = os.path.join(dist, 'audio')
keys = sorted(f[:-4] for f in os.listdir(audio_dir) if f.endswith('.mp3')) if os.path.isdir(audio_dir) else []
html = html.replace('/*@AUDIO@*/', json.dumps(keys))
narr_dir = os.path.join(dist, 'voice', 'en')
nkeys = sorted(f[:-4] for f in os.listdir(narr_dir) if f.endswith('.mp3')) if os.path.isdir(narr_dir) else []
html = html.replace('/*@NARR@*/', json.dumps(nkeys))
ar_dir = os.path.join(dist, 'voice', 'ar')
akeys = sorted(f[:-4] for f in os.listdir(ar_dir) if f.endswith('.mp3')) if os.path.isdir(ar_dir) else []
html = html.replace('/*@NARR_AR@*/', json.dumps(akeys))
hisn_keys = []
hp = os.path.join(here, 'hisn_keys.json')
if os.path.exists(hp):
    hisn_keys = json.load(open(hp))
html = html.replace('/*@HISN@*/', json.dumps({k: 'hisn' for k in hisn_keys}))
hd_out = os.path.join(dist, 'pano4k'); os.makedirs(hd_out, exist_ok=True)
for f in sorted(os.listdir(renders)):
    if not f.endswith('.jpg'):
        continue
    name = f[:-4]
    if name.split('_night')[0] not in views:
        continue
    im = Image.open(os.path.join(renders, f)).convert('RGB')
    if im.width >= 4096:
        im.save(os.path.join(hd_out, f), quality=84, optimize=True, progressive=True)
        im = im.resize((2048, 1024), Image.LANCZOS)
    im.save(os.path.join(dist, 'pano', f), quality=84, optimize=True, progressive=True)
night = sorted(f[:-10] for f in os.listdir(os.path.join(dist, 'pano')) if f.endswith('_night.jpg'))
html = html.replace('/*@NIGHT@*/', json.dumps(night))
hd_dir = os.path.join(dist, 'pano4k')
hd = sorted(f[:-4] for f in os.listdir(hd_dir) if f.endswith('.jpg')) if os.path.isdir(hd_dir) else []
html = html.replace('/*@HD@*/', json.dumps(hd))
open(os.path.join(dist, 'index.html'), 'w').write(html)
shutil.copy(os.path.join(here, 'explore.html'), os.path.join(dist, 'explore.html'))
print('ok', sorted(os.listdir(os.path.join(dist, 'pano'))))

# 3D Explore assets: GLB -> self-contained glTF JSON (artifact hosting serves .json, not .glb)
import base64, struct
fps_src = os.path.join(here, '..', 'fps'); fps_out = os.path.join(dist, 'fps')
if os.path.isdir(fps_src):
    os.makedirs(fps_out, exist_ok=True)
    for f in os.listdir(fps_src):
        if f.endswith('.glb'):
            d = open(os.path.join(fps_src, f), 'rb').read()
            jl = struct.unpack('<I', d[12:16])[0]; j = json.loads(d[20:20 + jl])
            o = 20 + jl; bl = struct.unpack('<I', d[o:o + 4])[0]
            j['buffers'][0]['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(d[o + 8:o + 8 + bl]).decode()
            open(os.path.join(fps_out, f[:-4] + '.json'), 'w').write(json.dumps(j, separators=(',', ':')))
        elif f.endswith('.jpg'):
            shutil.copy(os.path.join(fps_src, f), fps_out)
    print('fps', sorted(os.listdir(fps_out)))
