# Umrah tour scene pipeline

`build_scene.py` produces the Haram and Mas'a; `export_fps.py` derives instanced
glTF models from the same masters. These remain instructional reconstructions.

The first visual milestone rebuilds the Kaaba area. `landmarks.py` contains draped
cloth, the sloping shadharwan, a separate gold door and traced open curtain,
recessed Black Stone/silver surround, Hijr coping and open Maqam enclosure.
`layout.json` supplies the browser and Blender with the same coordinate frame.

The curtain's photographed Arabic comes from a documented CC0 source in
`artwork/`; the remaining kiswa embroidery is reserved, pending accurate artwork
and review. Read [the reference ledger](../docs/visual-reference-ledger.md).
Other architecture remains schematic. `pilgrims.py` supplies eight lightweight
adult silhouettes with profiled clothing, hands, footwear and varied builds.
Tagged arm/calf/foot vertices drive instanced walking in `web/crowd.js`; the same
poses are baked into panorama crowds. Faces remain deliberately simple.

## Heavy rendering: rented H100

Use `gpu/render_visuals.sh` on the isolated Hyperstack worker. It runs a static
contact bake (no pilgrims), glTF export, two crowd studio views, ten fixed
day/night landmark views, ten 4K Haram panoramas and three 4K Mas'a panoramas.
The worker uses Python 3.11, `bpy==5.0.1`,
`Pillow==11.3.0`, `numpy==1.26.4`, `UMRAH_DEVICE=CUDA`. A missing requested GPU
is an error; there is no silent CPU fallback.

Creation, restricted SSH, credential handling, output retrieval and deletion are
documented in the root README. No VM credentials belong in source archives.

## Source assets and derivatives

```bash
python3 blender/fetch_assets.py 2k assets
```

Downloads CC0 material scans and skies. The actual locations are recorded in the
reference ledger. `assets/` is a reproducible local cache, excluded from Git.

```bash
UMRAH_ASSETS=assets python3 blender/export_fps.py fps assets
python3 blender/check_assets.py fps --strict
```

`fps/contact.png` is the saved GPU bake used by default. Override its location
with `UMRAH_CONTACT`, or set that variable to an empty string while rebaking.
Texture colour, normal and packed metallic/roughness channels survive export;
material-role extras tell the browser which meshes represent cloth, glass and
contact shading. Dedicated landmark UVs are preserved. Small metal profiles are
batched, while repeated architecture uses `EXT_mesh_gpu_instancing`.

Export to a separate raw folder when producing delivery assets, then run
`bash blender/optimize_models.sh <raw-folder> fps`. The pinned glTF Transform
postprocess quantizes vertex storage while preserving instancing and artwork UVs.
`python3 blender/check_assets.py fps --strict --delivery` enforces the final
8.6 MB Haram, 3.3 MB Mas'a and 900 KB crowd payload limits. It also checks curtain
orientation and the custom gait attributes. This postprocess is small CPU work;
all baking and image rendering runs on the rented H100.

For building `.blend` source files without rendering:

```bash
UMRAH_ASSETS=assets python3 blender/build_scene.py haram out 2048 64 none
```

`visual-cameras.json` fixes review framing. `render_comparisons.py` renders those
views on the GPU. Normal tour camera metadata is emitted with the panoramas.
