"""Build regression tests; no network, Blender, or TTS runtime required."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_build', ROOT / 'web' / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build.load_content()
        cls.views = {}
        for scene in ('haram', 'masa'):
            cls.views.update(json.loads((ROOT / 'renders4k' / f'{scene}_views.json').read_text()))

    def test_missing_translation_is_rejected(self):
        data = copy.deepcopy(self.data)
        del data['stations'][0]['steps'][0]['ar']
        with self.assertRaisesRegex(ValueError, 'translation'):
            build.validate_content(data, self.views)

    def test_unknown_dua_and_camera_are_rejected(self):
        for field, value, message in [('dua', 'unknown', 'Unknown dua'), ('look', 'unknown', 'camera target')]:
            data = copy.deepcopy(self.data)
            data['stations'][0]['steps'][0][field] = value
            with self.assertRaisesRegex(ValueError, message):
                build.validate_content(data, self.views)

    def test_approval_requires_reviewer_and_date(self):
        data = copy.deepcopy(self.data)
        data['review']['status'] = 'approved'
        with self.assertRaisesRegex(ValueError, 'reviewer and date'):
            build.validate_content(data, self.views)

    def test_modified_recording_is_rejected(self):
        original = Path.read_bytes
        def changed(path):
            return b'changed recording' if path.name == 'ihram_0.mp3' else original(path)
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'Recording changed'):
                build.validate_sources(self.data)

    def test_missing_practice_controls_translation_is_rejected(self):
        data = copy.deepcopy(self.data)
        del data['practice']['text']['ar']['how']
        with self.assertRaisesRegex(ValueError, 'practice translation: how'):
            build.validate_sources(data)

    def test_unknown_scripted_audio_cue_is_rejected(self):
        data = copy.deepcopy(self.data)
        data['practice']['missions'][0]['audio'].append('n:missing_1')
        with self.assertRaisesRegex(ValueError, 'Unknown 3D audio cue'):
            build.validate_sources(data)

    def test_clean_build_has_shared_content_night_assets_and_binary_models(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'site'
            assets = build.build(out)
            self.assertIn('start', assets['night'])
            self.assertTrue((out / 'pano4k' / 'start_night.jpg').is_file())
            self.assertTrue((out / 'fps' / 'masa.glb').is_file())
            self.assertFalse(list((out / 'fps').glob('*.json')))
            self.assertEqual((out / 'fps' / 'haram.glb').read_bytes(), (ROOT / 'fps' / 'haram.glb').read_bytes())
            for name in ('index.html', 'explore.html'):
                html = (out / name).read_text()
                self.assertIn('lib/content.js', html)
                self.assertNotIn('/*@', html)
            self.assertLess(assets['models']['haram']['bytes'] + assets['models']['pilgrims']['bytes'], 9_000_000)
            self.assertRegex(assets['models']['haram']['url'], r'^fps/haram\.glb\?v=[a-f0-9]{12}$')
            self.assertTrue((out / 'lib' / 'layout.js').is_file())
            self.assertFalse((out / 'visual-review').exists(), 'Developer review page must stay out of the public site')

    def test_artifact_build_embeds_models_as_json(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'site'
            assets = build.build(out, artifact=True)
            self.assertFalse(list((out / 'fps').glob('*.glb')))
            gltf = json.loads((out / 'fps' / 'pilgrims.json').read_text())
            self.assertTrue(gltf['buffers'][0]['uri'].startswith('data:application/octet-stream;base64,'))
            self.assertRegex(assets['models']['haram']['url'], r'^fps/haram\.json\?v=[a-f0-9]{12}$')

    def test_missing_render_metadata_fails_before_emitting_a_partial_site(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'site'
            with self.assertRaisesRegex(ValueError, 'render metadata'):
                build.build(out, temp)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
