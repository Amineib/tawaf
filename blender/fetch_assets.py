"""Download the CC0 textures and HDRI used by the scenes (Poly Haven + ambientCG).

    python fetch_assets.py 2k  [out_dir]      # quick tests
    python fetch_assets.py 4k  [out_dir]      # final renders

Writes <out_dir>/tex/<key>/{color,normal,rough}.jpg and <out_dir>/sky.hdr
(out_dir defaults to ../assets next to this script). Uses curl (a browser-like
client is needed: some CDNs refuse Python's default user agent).
"""
import json, os, subprocess, sys, zipfile, glob, shutil

RES = sys.argv[1] if len(sys.argv) > 1 else '2k'
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

POLYHAVEN = {            # key -> Poly Haven asset id
    'granite': 'granite_tile',
    'stucco': 'white_stucco',
    'satin': 'crepe_satin',
    'rock': 'sandstone_cracks',
}
AMBIENTCG = {            # key -> ambientCG asset id
    'marble_white': 'Marble021',   # Mataf / Mas'a floors
    'marble_warm': 'Marble001',    # arcades, columns, walls
}
HDRI = 'syferfontein_18d_clear_puresky'


def curl(url, out=None):
    cmd = ['curl', '-sSL', '--retry', '5', '--retry-all-errors', '--retry-delay', '2', '-A', 'Mozilla/5.0 (umrah-tour)']
    if out:
        cmd += ['-o', out]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=out is None, check=True)
    return r.stdout


def main():
    os.makedirs(os.path.join(OUT, 'tex'), exist_ok=True)
    for key, asset in POLYHAVEN.items():
        d = json.loads(curl(f'https://api.polyhaven.com/files/{asset}'))
        folder = os.path.join(OUT, 'tex', key)
        os.makedirs(folder, exist_ok=True)
        for src, dst in [('Diffuse', 'color'), ('nor_gl', 'normal'), ('Rough', 'rough')]:
            path = os.path.join(folder, dst + '.jpg')
            if not os.path.exists(path):
                curl(d[src][RES]['jpg']['url'], path)
        print('ok', key)
    for key, asset in AMBIENTCG.items():
        folder = os.path.join(OUT, 'tex', key)
        if os.path.exists(os.path.join(folder, 'rough.jpg')):
            print('ok', key); continue
        os.makedirs(folder, exist_ok=True)
        z = os.path.join(folder, 'a.zip')
        curl(f'https://ambientcg.com/get?file={asset}_{RES.upper()}-JPG.zip', z)
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                for suffix, dst in [('_Color.jpg', 'color'), ('_NormalGL.jpg', 'normal'), ('_Roughness.jpg', 'rough')]:
                    if n.endswith(suffix):
                        with zf.open(n) as fi, open(os.path.join(folder, dst + '.jpg'), 'wb') as fo:
                            shutil.copyfileobj(fi, fo)
        os.remove(z)
        print('ok', key)
    night = os.path.join(OUT, 'sky_night.hdr')
    if not os.path.exists(night):
        d = json.loads(curl('https://api.polyhaven.com/files/rogland_clear_night'))
        curl(d['hdri'][RES]['hdr']['url'], night)
    print('ok night sky')
    sky = os.path.join(OUT, 'sky.hdr')
    if not os.path.exists(sky):
        d = json.loads(curl(f'https://api.polyhaven.com/files/{HDRI}'))
        curl(d['hdri'][RES]['hdr']['url'], sky)
    print('ok sky')


if __name__ == '__main__':
    main()
