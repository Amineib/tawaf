# 7aj.ai — Umrah virtual tour (proof of concept)

A guided 360° tour of Umrah for older and first-time pilgrims: 10 stations, English
narration and Arabic (designed voices), Arabic duas recited, Tawaf/Sa'i
counters, Day/Night switch, 4K panoramas rendered in Blender.

## Open it
```bash
./serve.sh          # then http://localhost:8000 (Firefox, Chrome, Safari)
```
On a phone on the same Wi-Fi: http://<your-mac-ip>:8000

## Folders
| Folder | What it is |
|---|---|
| `web/dist/` | The built site, ready to serve or upload to any static host |
| `web/app.html`, `web/content.js` | Player source and the tour script (steps, camera targets, duas, English + Arabic) |
| `web/build.py` | Rebuilds `dist/` from a folder holding all 4K renders + `*_views.json` (needs Pillow) |
| `blender/` | Procedural scene generator (Haram + Mas'a), see `blender/README.md` |
| `gpu/` | Hyperstack H100 startup script, job runner and the render job used |
| `renders4k/` | 4K panoramas (first batch); `renders4k/v2/` = new architecture + night |
| `voice/` | Voice scripts (run them from `aiprojects/tts`, which has the Python environments), narration texts and the two reference voices |

## Audio sources
| Audio | Source |
|---|---|
| Quran verses (2:125, 2:158, 2:201) | Mishary Rashid Alafasy, via AlQuran Cloud / Islamic Network; cut to the phrase with Quran.com word timings |
| Talbiyah, entering the mosque, Safa/Marwah dhikr, "أبدأ بما بدأ الله به", "بسم الله والله أكبر" | Hisn al-Muslim recordings, hisnmuslim.com (no license stated: ask before public release) |
| Umrah intention, condition (ishtirat) | Synthetic (voice 4): no free recording exists, record them |
| English + Arabic narration | Synthetic: Qwen3-TTS VoiceDesign + Chatterbox Multilingual (`voice/`) |

## Re-render the scenes
```bash
pip install bpy pillow
python3 blender/fetch_assets.py 2k assets          # or 4k for finals
UMRAH_ASSETS=assets python3 blender/build_scene.py haram out 2048 64
UMRAH_ASSETS=assets UMRAH_TIME=night python3 blender/build_scene.py haram out 2048 64
UMRAH_ASSETS=assets python3 blender/build_scene.py masa out 2048 64
```
Add `none` as the last argument to only write the `.blend` files and open them in Blender.
On GPU: `UMRAH_DEVICE=OPTIX` (NVIDIA) — on a Mac, open the .blend in Blender and use Metal.

## Before any public release
- Scholar review of every step and dua.
- Tajweed check of the 3 Quranic verses (synthetic voice), ideally a human reciter.
- Real kiswa calligraphy artwork (the current gold pattern is a placeholder).

## Explore in 3D (free-roam mode)

`web/explore.html` is a first-person, real-time version of the Umrah, built with three.js (bundled in `web/dist/lib/`). It opens from the "Explore in 3D" button in the guided tour.

- **Missions:** each step of the Umrah is a mission, in order: enter the Haram, reach the Black Stone line, 7 tawaf circuits (counted automatically, with wrong-way and Hijr warnings), pray behind Maqam Ibrahim, drink Zamzam, walk to the Mas'a, the dhikr at Safa, then 7 Sa'i lengths.
- **Minimap:** a rotating minimap shows the objective and a route to it.
- **Guide me:** walks you to the next goal; fast-forward is offered after the first circuit or length.
- **Controls:**
  - Desktop: WASD or the arrow keys, drag to look, Shift to run.
  - Phone: drag on the left half to walk and on the right half to look.
- **Day and night:** follow the guided tour's setting.
- **Assets:**
  - `blender/export_fps.py` exports `fps/*.glb` with GPU instancing and 1K textures: `python3 export_fps.py ../fps ../assets`.
  - `web/build.py` converts the GLBs to self-contained glTF `.json` files in `web/dist/fps/`, because the artifact host doesn't serve `.glb`.
- **Test mode:** `explore.html?lowq` lowers resolution for software-GL test runs; `window.__game.sim(seconds)` runs the game logic headless.

## Publishing (GitHub Pages)

`.github/workflows/pages.yml` publishes `web/dist` on every push to `main`. In the repository settings, under **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions** (one time only). The site is then served at https://amineib.github.io/tawaf/.
