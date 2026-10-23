"""Guard the readable orientation of the sourced Arabic curtain artwork."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('asset_check', ROOT / 'blender' / 'check_assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class ArtworkTests(unittest.TestCase):
    def test_front_facing_curtain_reads_from_viewers_left_to_right(self):
        # Front faces +Y, so the viewer's screen-right is world -X.
        positions = [(2, 6.5, 4), (-2, 6.5, 4), (-2, 6.5, 8), (2, 6.5, 8)]
        assets.artwork_orientation(positions, [(0, 0), (1, 0), (1, 1), (0, 1)])
        with self.assertRaisesRegex(AssertionError, 'mirrored'):
            assets.artwork_orientation(positions, [(1, 0), (0, 0), (0, 1), (1, 1)])


if __name__ == '__main__':
    unittest.main()
