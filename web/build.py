"""Build and validate the static site from canonical content and source assets.

    python web/build.py                 # writes web/dist
    python web/build.py --check         # validates sources and the committed build
    python web/build.py --output /tmp/tour-build
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
sys.path.insert(0, str(ROOT / 'voice'))
from content import load_content, narration_text


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_content(data, views):
    require(data.get('schemaVersion') == 1, 'Unsupported content schema version')
    require(data.get('stations'), 'No tour stations')
    ids = [s['id'] for s in data['stations']]
    require(len(ids) == len(set(ids)), 'Duplicate station IDs')
    for item in [data, *data['stations'], *data['duas'].values()]:
        review = item.get('review', {})
        require(review.get('status') in ('pending', 'approved'), 'Missing review status')
        if review['status'] == 'approved':
            require(review.get('reviewer') and re.fullmatch(r'\d{4}-\d{2}-\d{2}', review.get('reviewedAt') or ''), 'Approved content needs a reviewer and date')
    for key, dua in data['duas'].items():
        require(all(isinstance(dua.get(k), str) and dua[k].strip() for k in ('ar', 'en', 'tr')), f'Incomplete dua: {key}')
        for ref in dua.get('references', []):
            require(ref.get('url', '').startswith('https://') and ref.get('label'), f'Invalid reference: {key}')
    for station in data['stations']:
        require(station.get('steps'), f'Empty station: {station["id"]}')
        require(all(station.get(k, {}).get(lang) for k in ('title', 'place') for lang in ('en', 'ar')), f'Missing station translation: {station["id"]}')
        require(station['pano'] in views, f'Unknown panorama: {station["pano"]}')
        for label in station['labels']:
            require(label in data['labels'], f'Unknown landmark label: {label}')
            require(label in views[station['pano']], f'Missing landmark target: {label}')
        for step in station['steps']:
            require(all(step.get(lang) for lang in ('en', 'ar')), f'Missing step translation: {station["id"]}')
            require(step['look'] in views[station['pano']], f'Missing camera target: {step["look"]}')
            require(not step.get('dua') or step['dua'] in data['duas'], f'Unknown dua: {step.get("dua")}')
    return data


def validate_sources(data):
    recordings = json.loads((WEB / 'media' / 'recordings.json').read_text(encoding='utf-8'))['narration']
    for lang in ('en', 'ar'):
        lines = narration_text(lang, data)
        transcript = ROOT / 'voice' / f'narration_{lang}.json'
        require(json.loads(transcript.read_text(encoding='utf-8')) == lines, f'{transcript.name} is stale; run python voice/export_text.py')
        for key in lines:
            audio = WEB / 'media' / 'voice' / lang / f'{key}.mp3'
            require(audio.is_file(), f'Missing {lang} narration: {key}')
            record = recordings.get(f'{lang}:{key}', {})
            require(record.get('textSha256') == hashlib.sha256(lines[key].encode()).hexdigest(), f'Recording transcript changed: {lang}:{key}; regenerate/review the clip and update its recording manifest')
            require(record.get('audioSha256') == hashlib.sha256(audio.read_bytes()).hexdigest(), f'Recording changed: {lang}:{key}; review the new clip and update its recording manifest')
    for key in data['duas']:
        require((WEB / 'media' / 'audio' / f'{key}.mp3').is_file(), f'Missing dua audio: {key}')
    # Every scripted 3D cue must resolve to a canonical transcript or dua.
    explore = (WEB / 'explore.html').read_text(encoding='utf-8')
    en = narration_text('en', data)
    cues = [f'{kind}:{key}' for kind, key in re.findall(r"['\"]([nd]):([a-z_]+\d*)['\"]", explore)]
    practice = data['practice']
    dynamic_text = {'circuit', 'length', 'stats', 'resume', 'missionDone'}
    for key in set(re.findall(r'\bT\.(\w+)', explore)) - dynamic_text:
        require(all(practice['text'][lang].get(key) for lang in ('en', 'ar')), f'Missing practice translation: {key}')
    require(all(isinstance(practice['text'][lang]['how'], list) for lang in ('en', 'ar')), 'Practice controls must be a list')
    cues += [cue for mission in practice['missions'] for cue in mission['audio']]
    cues += [cue for script in practice['tawafScript'].values() for _, cue in script]
    cues += [cue for _, _, cue in practice['saiScript']]
    for cue in cues:
        kind, key = cue.split(':', 1)
        if kind == 'dhikr':
            require(key.isdigit() and int(key) < len(practice['dhikr']), f'Unknown dhikr cue: {cue}')
            continue
        require(key in (data['duas'] if kind == 'd' else en), f'Unknown 3D audio cue: {kind}:{key}')


def js_json(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def build(output, renders=None):
    from PIL import Image
    renders = Path(renders or ROOT / 'renders4k').resolve()
    views = {}
    for filename in ('haram_views.json', 'masa_views.json'):
        path = renders / filename
        require(path.is_file(), f'Missing render metadata: {path}')
        for version in ('v2', 'v3'):
            if (renders / version / filename).is_file():
                path = renders / version / filename
        views.update(json.loads(path.read_text(encoding='utf-8')))
    data = validate_content(load_content(), views)
    validate_sources(data)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for folder in ('pano', 'pano4k', 'fps'):
        (output / folder).mkdir(exist_ok=True)
    shutil.copytree(WEB / 'vendor', output / 'lib', dirs_exist_ok=True)
    for folder in ('audio', 'voice'):
        shutil.copytree(WEB / 'media' / folder, output / folder, dirs_exist_ok=True)
    for filename in ('runtime.js', 'illus.js', 'crowd.js'):
        shutil.copy2(WEB / filename, output / 'lib' / filename)
    layout = json.loads((ROOT / 'blender' / 'layout.json').read_text())
    require(layout.get('schemaVersion') == 1 and layout.get('units') == 'metres', 'Invalid scene layout')
    (output / 'lib' / 'layout.js').write_text('/* Shared Blender/browser coordinates. */\nwindow.TourLayout=' + js_json(layout) + ';\n')
    # Versioned render batches supersede earlier Haram and Mas'a derivatives.
    panoramas = {source.name: source for source in sorted(renders.glob('*.jpg'))}
    for version in ('v2', 'v3'):
        panoramas.update({source.name: source for source in sorted((renders / version).glob('*.jpg'))})
    for source in panoramas.values():
        if source.stem.removesuffix('_night') not in views:
            continue
        with Image.open(source) as image:
            image = image.convert('RGB')
            if image.width >= 4096:
                image.save(output / 'pano4k' / source.name, quality=84, optimize=True, progressive=True)
                image = image.resize((2048, 1024), Image.Resampling.LANCZOS)
            image.save(output / 'pano' / source.name, quality=84, optimize=True, progressive=True)
    for station in data['stations']:
        require((output / 'pano' / (station['pano'] + '.jpg')).is_file(), f'Missing panorama image: {station["pano"]}')
    models = {}
    for name in ('haram', 'masa', 'pilgrims'):
        source = ROOT / 'fps' / f'{name}.glb'
        require(source.is_file() and source.read_bytes()[:4] == b'glTF', f'Missing or invalid GLB: {source}')
        shutil.copy2(source, output / 'fps' / source.name)
        version = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        models[name] = {'url': f'fps/{source.name}?v={version}', 'bytes': source.stat().st_size}
    shutil.copy2(ROOT / 'fps' / 'sky_1k.jpg', output / 'fps' / 'sky_1k.jpg')
    lines = {lang: narration_text(lang, data) for lang in ('en', 'ar')}
    data['narration'] = {key: {lang: values[key] for lang, values in lines.items() if key in values} for key in lines['en']}
    data['views'] = views
    (output / 'lib' / 'content.js').write_text('/* Generated from web/tour.json. */\nwindow.TourContent=' + js_json(data) + ';\n', encoding='utf-8')
    assets = {'audio': sorted(data['duas']), 'narration': {lang: sorted(lines[lang]) for lang in lines},
              'night': sorted(p.name[:-10] for p in (output / 'pano').glob('*_night.jpg')),
              'hd': sorted(p.stem for p in (output / 'pano4k').glob('*.jpg')), 'models': models}
    (output / 'lib' / 'assets.js').write_text('/* Generated asset manifest. */\nwindow.TourAssets=' + js_json(assets) + ';\n', encoding='utf-8')
    for source, target in (('app.html', 'index.html'), ('explore.html', 'explore.html')):
        html = (WEB / source).read_text(encoding='utf-8')
        require('/*@' not in html, f'Unresolved build placeholder in {source}')
        (output / target).write_text(html, encoding='utf-8')
    review = ROOT / 'docs' / 'visual-review'
    if review.is_dir():
        shutil.copytree(review, output / 'visual-review')
        shutil.copy2(WEB / 'visual-review.html', output / 'visual-review' / 'index.html')
    return assets


def file_hashes(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(folder).rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('renders', nargs='?', help='Optional panorama source folder (default: renders4k)')
    parser.add_argument('--output', type=Path, default=WEB / 'dist')
    parser.add_argument('--check', action='store_true', help='Fail if the committed output is stale or contains obsolete files')
    args = parser.parse_args()
    # Build in isolation; validation or encoding failures never leave a partial published site.
    with tempfile.TemporaryDirectory(prefix='umrah-build-') as temp:
        staging = Path(temp) / 'site'
        build(staging, args.renders)
        if args.check:
            expected, actual = file_hashes(staging), file_hashes(args.output)
            changed = sorted(k for k in set(expected) | set(actual) if expected.get(k) != actual.get(k))
            require(not changed, 'Stale build files: ' + ', '.join(changed))
            print('Build, content, audio, landmarks, and committed output verified.')
        else:
            target = args.output.resolve()
            require(target not in (ROOT.resolve(), WEB.resolve(), Path('/')) and target not in ROOT.resolve().parents, 'Refusing to replace source directory')
            if target.exists() and any(target.iterdir()):
                require(target == (WEB / 'dist').resolve() or (target / 'lib' / 'assets.js').is_file(), 'Output is not an existing tour build or empty folder')
            if args.output.exists():
                shutil.rmtree(args.output)
            shutil.copytree(staging, args.output)
            print(f'Built {args.output}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, ImportError) as exc:
        raise SystemExit(f'Build failed: {exc}')
