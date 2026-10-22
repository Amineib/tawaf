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
