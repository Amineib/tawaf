# Umrah tour — Blender scene generator

Two procedural scenes, generated 100% from Python (no downloaded models or textures):

- **haram** — Kaaba (kiswa, gold band, door curtain, Black Stone in its silver frame, waterspout), Hijr Ismail, Maqam Ibrahim, 4-level arcades with domes, minarets, the clock tower complex, Zamzam coolers, ~2,000 faceless pilgrims walking counter-clockwise.
- **masa** — the Mas'a gallery: Safa and Marwah rocks under domes, lanes and dividers, the green-light section, pilgrims walking both directions.

Each camera is a 360° equirectangular camera placed at a tour station.

## Render

```bash
pip install bpy            # Blender as a Python module (5.x), or use Blender's own Python
python build_scene.py haram out 2048 32          # all Haram cameras, 2048x1024, 32 samples
python build_scene.py masa  out 2048 32
python build_scene.py haram out 8192 128 start   # one camera in 8K
```

Outputs `out/<scene>.blend` (open it in Blender to edit by hand), `out/<camera>.jpg`, and
`out/<scene>_views.json` (yaw/pitch of every point of interest, used by the web player to aim the camera and place labels).

On a Mac with Apple Silicon, open the `.blend` in Blender and switch Cycles to **GPU (Metal)** for much faster 4K/8K renders.

## Where to take it next

- Replace the abstract gold pattern on the kiswa with properly sourced calligraphy artwork.
- Swap primitive meshes for hero models (Kaaba, Maqam, arcade columns) as they are made.
- Pilgrims are deliberately faceless and simple; keep it that way, but add cloth folds and walking poses.
- Coordinates: Kaaba at origin; Black Stone corner at (+x, +y). Everything is in metres.
