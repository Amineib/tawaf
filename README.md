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
| `web/app.html`, `web/explore.html` | Guided and 3D player source |
| `web/tour.json` | Canonical bilingual lessons, duas, references, and content review metadata |
| `web/runtime.js` | Shared persistence, cancellation, and bounded GPU texture cache helpers |
| `web/media/`, `web/vendor/` | Source recordings/transcripts and vendored three.js runtime |
| `web/build.py` | Validates sources and rebuilds `dist/` from `renders4k/`, with the newer `v2/` images overlaid |
| `blender/` | Procedural scene generator (Haram + Mas'a), see `blender/README.md` |
| `gpu/` | Hyperstack H100 startup script, job runner and the render job used |
| `renders4k/` | 4K panoramas (first batch); `renders4k/v2/` = new architecture + night |
| `voice/` | Voice scripts (run them from `aiprojects/tts`, which has the Python environments), narration texts and the two reference voices |

## Build and verify

Python 3.9+ and Node.js 24 are sufficient for the web build and regression checks.
Blender and the TTS models are needed only when producing new source assets.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python web/build.py
node --test tests/*.test.cjs
python -m unittest discover -s tests -p 'test_*.py'
python web/build.py --check
./serve.sh
```

The build starts in an isolated temporary directory, validates bilingual content,
camera targets, narration, recording hashes, and 3D audio cues, then replaces
`web/dist/`. It removes obsolete generated assets. `--check` rebuilds in isolation
and fails when committed output differs. `--output /tmp/umrah-build` creates a
separate build; an optional positional argument selects a different renders folder.

Edit `web/tour.json` for lessons and duas. Both experiences read the same generated
content, including the full Safa dhikr. `python voice/export_text.py` exports the
English and Arabic TTS input files; `--check` detects drift. TTS generators also
read the canonical source. The recording manifest at `web/media/recordings.json`
records transcript and MP3 SHA-256 hashes so changing a transcript alone cannot
silently publish stale narration. After regenerating and listening to an affected
clip, update that entry's `textSha256` and `audioSha256` to match the new files.
This recording manifest does not represent scholarly or recitation approval.

Review fields (`status`, `reviewer`, `reviewedAt`) remain `pending` until a qualified
reviewer completes the work. Approved entries require a reviewer and ISO date.
Linked references identify supporting texts; exact wording, composite duas, and
translations still need review. In particular, the niyyah wording and the full
Bismillah/takbir attribution still await precise reference verification.

## Sessions, accessibility, and recovery

- On phones, the panorama occupies about half the screen, with the current step
  and playback controls below. Settings, duas, translations, sources and tour
  notes expand on request. The 3D tour uses a compact mission card, a menu for
  secondary controls, and expandable captions/recitation cards. Full warning
  messages remain visible. English and Arabic share the same responsive layout.
- Both players save progress locally in this browser; no account is required.
  Switching back from 3D restores the guided lesson and its counters. 3D resume
  restores position, partial circuit/length progress, cue history, and elapsed time.
  Original mission-only saves migrate automatically. Saves do not start audio or
  movement until the user chooses to resume.
- Quality is shared across modes: **Auto**, **Low data**, and **High**. Auto avoids
  4K panoramas and lowers rendering resolution on touch/save-data devices. Low data
  uses 2K panoramas and reduced 3D crowd density at startup. The Mas'a model downloads
  only when entering or resuming that part of the rehearsal.
- Scene failures expose retry controls. `index.html?text` provides the same lessons,
  duas, narration and manual counters without WebGL. The 3D entry screen always links
  to these lessons, including when its renderer or module cannot initialize.
- Station buttons have 44px-high touch targets. The station dialog contains keyboard
  focus and restores it when closed. Mobile zoom remains available. Reduced motion
  disables panorama/camera tweens, 3D head bobbing, automatic guide turns, marker
  pulsing and crowd animation.
- 3D has a pause/resume button and pauses when hidden or unfocused; input is cleared
  to prevent stuck movement. Muted mission narration still displays captions.

## Audio sources
| Audio | Source |
|---|---|
| Quran verses (2:125, 2:158, 2:201) | Mishary Rashid Alafasy, via AlQuran Cloud / Islamic Network; cut to the phrase with Quran.com word timings |
| Talbiyah, entering the mosque, Safa/Marwah dhikr, "أبدأ بما بدأ الله به", "بسم الله والله أكبر" | Hisn al-Muslim recordings, hisnmuslim.com (no license stated: ask before public release) |
| Umrah intention, condition (ishtirat) | Synthetic (voice 4): no free recording exists, record them |
| English + Arabic narration | Synthetic: Qwen3-TTS VoiceDesign + Chatterbox Multilingual (`voice/`) |

## Re-render the scenes

Heavy renders run on a rented Hyperstack H100. The current reproducible batch is
`gpu/render_visuals.sh`: CUDA contact bake → binary model export → five fixed
day/night comparison views and crowd close-ups → all Haram day/night and Mas'a 4K panoramas → asset validation
and checksums. It requires Python 3.11, `bpy==5.0.1`, `Pillow==11.3.0`, and
`numpy==1.26.4`. `gpu/create_blender_vm.py <your-public-IPv4>` creates one isolated
worker with SSH restricted to that IP, using the existing credential at
`~/.config/hyperstack/api_key`; credentials are never uploaded. Pin the worker's
SSH host key from its authenticated provider console before sending the batch.
Retrieve and verify outputs, then delete the worker and confirm its removal.
Run-specific state is ignored under `gpu/runs/`. Shutdown is a backstop, not VM
deletion or a guarantee that all storage billing has stopped.

After retrieving raw exports, run the inexpensive CPU postprocess
`bash blender/optimize_models.sh <raw-fps-folder> fps`. It pins glTF Transform
4.2.1 and uses 16-bit positions/UVs and 12-bit normals. The bundled loader
supports `KHR_mesh_quantization`, so delivery needs no additional decoder.
This keeps the richer landmark assets within the existing download budgets.

The shared geometry and collision frame is `blender/layout.json`. Landmark masters
are in `blender/landmarks.py`; review cameras are in `blender/visual-cameras.json`.
The [reference ledger](docs/visual-reference-ledger.md) records sources, CC0
texture provenance, the curtain's 2016 date, and remaining approximations.
The curtain uses photographed Arabic artwork; the remaining kiswa embroidery is
reserved pending accurate artwork and review.

The eight crowd variants in `blender/pilgrims.py` share the same body/clothing
masters between panoramas and the live tour. `web/crowd.js` animates tagged limbs
inside instanced vertex shaders, including matching shadow poses. Quality modes
limit crowd density, and reduced motion freezes the correctly placed crowd.

For geometry generation or a deliberately small developer experiment:
```bash
pip install bpy pillow
python3 blender/fetch_assets.py 2k assets          # or 4k for finals
UMRAH_ASSETS=assets python3 blender/build_scene.py haram out 2048 64
UMRAH_ASSETS=assets UMRAH_TIME=night python3 blender/build_scene.py haram out 2048 64
UMRAH_ASSETS=assets python3 blender/build_scene.py masa out 2048 64
```
Add `none` as the last argument to only write the `.blend` files and open them in Blender.
On the H100: `UMRAH_DEVICE=CUDA`. A requested unavailable GPU fails explicitly
instead of silently starting a CPU render.

## Before any public release
- Scholar review of every step and dua.
- Tajweed and wording review of all recitation clips (the shipped Quran excerpts use a human reciter).
- Complete and review kiswa calligraphy and placement (only the sourced door
  curtain artwork is included in the first visual milestone).

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
  - `blender/export_fps.py` exports `fps/*.glb` with GPU instancing and 1K textures: `python3 blender/export_fps.py fps assets`.
  - `web/build.py` copies binary GLBs into `web/dist/fps/`; the player loads the Mas'a only when needed. Use a static host that serves `.glb` files (GitHub Pages and the local server do).
- **Test mode:** `explore.html?lowq` lowers resolution for software-GL test runs; `window.__game.sim(seconds)` runs the game logic headless.
- **Visual diagnostics:** `explore.html?stats` displays rolling frame rate, 95th
  percentile frame time, draw calls, triangles, texture/geometry counts and DPR.
  Measurements stay on the device. Test actual mobile hardware before accepting
  a performance target; desktop preview results are not phone benchmarks.
- **Asset checks:** `python3 blender/check_assets.py fps --strict --delivery` checks texture
  UVs, normals, material roles, cloth/roughness channels, instancing and budgets.

## Publishing (GitHub Pages)

`.github/workflows/pages.yml` tests and builds on pull requests, then rebuilds and publishes on every push to `main`. In the repository settings, under **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions** (one time only). The site is then served at https://amineib.github.io/tawaf/.
