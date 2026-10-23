"""Headless browser play-through of both experiences.

Skipped when Playwright or its Chromium is not installed. CI installs both:
    python -m pip install playwright==1.47.0 && python -m playwright install --with-deps chromium
Runs on software WebGL (SwiftShader), so it checks behaviour, not frame rate.
"""
import functools
import http.server
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_build', ROOT / 'web' / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required']
STATE = '({mi: __game.game.mi, done: !document.getElementById("done").hidden, guide: __game.input.guide})'


@unittest.skipUnless(sync_playwright, 'playwright is not installed')
class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        site = Path(cls.temp.name) / 'site'
        build.build(site)
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        handler = functools.partial(Quiet, directory=str(site))
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(args=ARGS)
        except Exception as exc:  # pragma: no cover
            cls.pw.stop(); cls.server.shutdown()
            raise unittest.SkipTest(f'Chromium unavailable: {exc}')

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.temp.cleanup()

    def page(self, url, mobile=False):
        context = self.browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 900, 'height': 600},
                                           is_mobile=mobile, has_touch=mobile)
        context.add_init_script('localStorage.setItem("umrah:sound", "false")')
        self.addCleanup(context.close)   # software WebGL is CPU-heavy; never leave a page rendering
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(self.base + url, wait_until='domcontentloaded', timeout=120_000)
        return page, errors

    def test_explore_keyboard_works_after_start_and_all_missions_complete(self):
        page, errors = self.page('/explore.html?lowq')
        page.wait_for_function('!document.getElementById("bStart").disabled', timeout=180_000)
        page.click('#bStart')
        page.wait_for_function('window.__tourStarted === true', timeout=60_000)
        start = page.evaluate('[__game.player.x, __game.player.y]')
        page.keyboard.down('KeyW'); page.wait_for_timeout(1200); page.keyboard.up('KeyW')
        moved = page.evaluate(f'Math.hypot(__game.player.x - {start[0]}, __game.player.y - {start[1]})')
        self.assertGreater(moved, 0.05, 'W must move the player even though a HUD button has focus')
        for _ in range(80):
            state = page.evaluate(STATE)
            if state['done']:
                break
            page.evaluate('''() => {
              const g = __game, m = g.game.mi;
              if (g.M[m]?.id === 'safa') { document.getElementById('bAct').click(); return; }
              if (!g.input.guide) document.getElementById('bGuide').click();
              if ((g.M[m]?.id === 'tawaf' && g.game.tawaf.count >= 1) || (g.M[m]?.id === 'sai' && g.game.sai.count >= 1)) {
                const skip = document.getElementById('bSkip'); if (!skip.hidden) skip.click();
              }
              g.sim(30, () => g.game.mi !== m);
            }''')
            page.wait_for_timeout(150)  # the Mas'a loads asynchronously
        self.assertTrue(page.evaluate(STATE)['done'], f'tour did not finish: {page.evaluate(STATE)}')
        self.assertEqual(errors, [])

    def test_guided_tour_and_text_mode(self):
        page, errors = self.page('/index.html')
        page.wait_for_timeout(1500)
        page.click('#btnNext')
        self.assertEqual(errors, [])
        page, errors = self.page('/index.html?text', mobile=True)
        page.wait_for_timeout(1000)
        self.assertFalse(page.is_visible('#btn3d'), 'text mode must not offer the 3D tour')
        self.assertTrue(page.is_visible('#illus'), 'the first step drawing works without 3D')
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
