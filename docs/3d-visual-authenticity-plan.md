# 3D visual quality and authenticity plan

Prepared 22 October 2026 for the Umrah tour.

Implementation update, 23 October: the first Kaaba-area milestone is available in
the [visual review](visual-milestone-review.md). It includes shared landmark
masters, preserved PBR channels, baked contact shading, a sourced 2016 curtain,
day/night H100 renders and smaller real-time delivery models. The user-requested
crowd pass adds eight body/clothing variants and instanced limb animation. The
reference ledger records remaining artwork and geometric approximations. The later full
architecture, Mas'a and further crowd refinement remain pending, as do specialist
authenticity review and physical-device performance acceptance.

## Intended result

A recognizable, carefully referenced reconstruction of the contemporary Haram and
Mas'a, with convincing materials, lighting, human scale, and movement. Architecture
and landmarks receive the most detail; pilgrims retain the project's deliberately
simple faces. The existing guided lessons, counters, accessibility features, and
mobile quality modes remain part of the acceptance criteria.

Use a consistent, dated reference set for an everyday Umrah setting. Record the
specific year, floor, viewpoint, and kiswa configuration represented. Document
approximations where measurements or references are unavailable.

## What currently limits the visuals

These observations come from the scene generators, binary models, existing
panoramas, and the latest browser preview:

- The Haram is generated as repeated concentric arcade rings. Minaret positions
  and surrounding buildings are largely procedural rather than reference-matched.
- The Kaaba is a box with abstract gold lattice panels. Its door curtain, Black
  Stone frame, and Maqam enclosure use simple primitives or placeholder patterns.
- The exporter replaces procedural materials, uses generic box-projected UVs,
  and does not preserve all material channels. The browser then replaces the
  kiswa material again, discarding the exported normal map.
- The exporter removes Blender lights. The browser substitutes broad directional
  and hemisphere lighting; at night a directional light still supplies much of
  the illumination. This produces bright flat surfaces alongside very dark areas.
- Safa/Marwah use generic rock forms; the Mas'a uses a repeated gallery kit and
  approximate end halls. The learning portal and floor start line are artificial
  guidance graphics and can be mistaken for parts of the building.
- Pilgrims are four cone-and-sphere variants. Movement bobs and rotates entire
  meshes, without articulated walking. Mas'a crowds wrap abruptly between ends.

Current asset baseline:

| Asset | File size | Unique mesh triangles | Meshes | Materials | Embedded animation clips |
|---|---:|---:|---:|---:|---:|
| Haram | 8.60 MB | 110,482 | 158 | 24 | 0 |
| Mas'a | 3.15 MB | 32,856 | 48 | 11 | 0 |
| Pilgrims | 0.038 MB | 2,044 | 4 | 8 | 0 |

Triangle counts above describe unique meshes. Actual rendered triangles also depend
on instancing, crowd density, visibility, and shadow passes; measure those in-browser.

## 1. Establish the reference pack and visual baseline

**Work**

- Assemble dated frontal, corner, eye-level, and elevated reference views for the
  Kaaba, Black Stone, Hijr, Maqam, Mataf perimeter, Safa, Marwah, and Mas'a corridor.
- Prefer the Haram authority, Ministry/Nusuk, Saudi Press Agency, and Saudipedia.
  Record image usage rights separately from its usefulness as a reference.
- Keep historical expansion descriptions separate from the chosen modern scene.
  For example, sources describing different Mas'a expansions report different
  layouts; do not combine their dimensions into a single model.
- Establish landmark orientation and scale from corroborating sources. Published
  side lengths alone do not determine a complete footprint; do not invent corner
  angles or treat a perspective photograph as a surveyed plan.
- Create an accuracy ledger: feature, source/date, measurement or visual evidence,
  confidence, approximation, and reviewer. Include Arabic artwork and signage.
- Capture fixed comparison cameras: Kaaba front/corner, Black Stone close-up, Hijr,
  Maqam, Safa, central Mas'a/green section, and Marwah. Include day and night for
  the Haram, with landscape and portrait views.
- Record baseline frame times, draw calls, rendered triangles, texture allocation,
  and cold-load time on an agreed Android phone, iPhone, and desktop.

**Deliverable:** reference board, accuracy ledger, camera manifest, and performance
baseline. Resolve the target appearance before rebuilding architecture.

Useful starting references: [Haram authority](https://alharamain.gov.sa/public/?page=home_en),
[Nusuk Maps service](https://my.gov.sa/en/services/2173642),
[Saudipedia: Safa and Marwa](https://saudipedia.com/en/safa-and-marwa),
[Saudipedia: Kaaba dimensions](https://saudipedia.com/en/a-list-of-the-dimensions-of-the-four-sides-of-the-holy-kaaba).

## 2. Repair the material and lighting pipeline

**Primary files:** `blender/export_fps.py`, `blender/common.py`, `web/explore.html`.

- Preserve imported normal, roughness, metallic, and occlusion information. Replace
  broad name-based material overrides with explicit material roles and asset metadata.
- Give cloth, marble, gold embroidery, polished metal, glass, and rock separate
  material treatments. Preserve detail when tuning the kiswa's dark base color.
- Use dedicated UVs for landmarks and artwork. Keep tiled materials for appropriate
  architectural surfaces, with consistent real-world texture scale.
- Introduce baked contact shading and indirect-light information for static
  architecture, with dedicated bake UVs. Avoid baking crowds into those textures.
- Define separate daylight, floodlit night, and interior Mas'a lighting profiles.
  At night, use the placement and character of the actual floodlights as the reference.
- Use a limited number of real-time shadow sources, with baked fill and contact
  shading where useful. Check that selected mobile and desktop profiles both ground
  objects convincingly without crushed blacks or clipped white marble.
- Make desktop effects optional. Bloom, screen-space reflections, and full-screen
  ambient occlusion are not prerequisites for the mobile look.

**Deliverable:** the same small test scene looks materially consistent in Blender,
exported glTF, and the browser. Cloth detail survives export; gold reads as metal;
marble remains light without becoming a mirror or a featureless white surface.

This lighting approach follows the tradeoffs described in the
[three.js shadow guide](https://threejs.org/manual/pages/shadows.html): additional
shadow-casting lights introduce additional render work, while lightmaps and ambient
occlusion can move static shading work offline.

## 3. Build the first complete visual section around the Kaaba

**Primary files/assets:** `blender/build_scene.py`, new landmark master assets,
shared material library, and exporter.

- Rebuild the Kaaba's reference-supported proportions, base/shadharwan, roof edge,
  door and threshold, curtain, waterspout, and nearby details.
- Replace the abstract gold lattice with properly sourced, correctly positioned
  kiswa artwork. Separate black woven cloth detail, folds/seams, embroidered bands,
  and door-curtain artwork so each receives suitable texture resolution.
- Check Arabic lettering against the reference at every face: correct orientation,
  placement, cropping, and readable close-up detail. Require Arabic/artwork review.
- Model the Black Stone's inset and irregular oval silver surround from reference,
  instead of treating it as a regular torus and sphere.
- Rebuild the Hijr wall and Maqam enclosure, including their silhouette, materials,
  openings, base, and contact with the ground.
- Integrate only enough nearby architecture to make this section feel complete.
  Tune its materials, lighting, camera scale, and close-range detail together.

**Deliverable:** reference comparison images and an interactive Kaaba–Black Stone–
Maqam section in day and night, at both mobile and desktop quality.

**Review gate:** accept this section's geometry, artwork, lighting, and frame budget
before copying its approach throughout the site.

The [authority's Black Stone reference](https://alharamain.gov.sa/public/?page=The_Black_Stone-en)
and [Kaaba door reference](https://alharamain.gov.sa/public/?page=kaaba-door-en&site=ur)
provide useful landmark evidence. The
[SPA report on the 1448 AH kiswa](https://www.spa.gov.sa/en/N2613391) is a dated
starting point for the selected modern textile configuration; photographs remain
references unless their use as textures is authorized.

## 4. Rebuild the surrounding Haram as a coherent place

- Replace the uniform arcade rings with reference-matched building sections:
  distinctive bays, columns, capitals, floor levels, parapets, gates, and roof forms.
- Establish the correct visible silhouettes, directions, and relative scale of
  minarets and the clock-tower complex from the selected reference cameras.
- Spend geometry on silhouettes and nearby architectural profiles. Use simpler
  geometry or impostors for distant city blocks and small background details.
- Match marble tile direction and scale, floor roughness, expansion joints,
  railings, light fixtures, signs, and selected Zamzam facilities.
- Keep the courtyard legible for first-time users while making density and scale
  resemble the selected reference setting.

**Deliverable:** the fixed Mataf views are recognizable by their architecture and
landmarks, rather than depending on floating labels for identification.

## 5. Rebuild the Mas'a and its connection to the Haram

- Model Safa and Marwah as distinct reference-matched rock formations and end halls,
  including slopes, protective boundaries, nearby columns, and ceiling forms.
- Rebuild a representative corridor kit using the selected floor's column rhythm,
  ceiling panels, lighting, signs, rails, and circulation layout.
- Verify green-section placement and extent from dated references. Keep learning
  highlights visually distinct from permanent architectural lights.
- Replace the stylized glowing portal with a referenced approach toward Safa.
  Separate scene loading may remain, with the transition placed at a sensible,
  documented architectural boundary.
- Use shared layout data to generate model transforms, collision shapes, minimap
  geometry, mission targets, and tour camera targets. Update these together when
  geometry changes, rather than maintaining separate hardcoded coordinates.

**Deliverable:** a coherent Haram-to-Safa approach and distinct Safa, corridor,
 green-section, and Marwah views, with the existing seven-length simulation intact.

Reference: [Saudipedia: Safa and Marwa](https://saudipedia.com/en/safa-and-marwa).
Operational routes and temporary barriers should be treated as dated reference
conditions, not permanent navigation guarantees.

## 6. Improve people and movement

- Replace cone-shaped bodies with a modest set of better silhouettes, hands/feet,
  clothing volumes, and baked cloth folds. Keep facial detail simple.
- Use roughly 8–12 reusable visual variants as an initial art target; confirm the
  final count against draw-call and memory measurements.
- Add articulated walk cycles with speed-matched foot movement, subtle arm motion,
  and varied timing. Avoid floating feet and whole-body rocking as the main gait.
- Give nearby people better silhouettes and animation; reduce detail and update
  frequency farther away. Retain instancing, with a suitable shared/baked animation
  approach instead of a separate expensive animation setup for every person.
- Improve spacing and local avoidance so people do not intersect landmarks or
  repeatedly pass through each other. Make endpoint turns or off-camera loops
  replace the Mas'a's visible wrapping.
- Provide sparse and normal learning densities, and preserve reduced-motion behavior.

**Deliverable:** a convincing close-range walking group and a larger crowd that
moves naturally at the selected quality level without obscuring every objective.

## 7. Optimize, verify, and release the visual update

- Split large environments into visibility groups and stream landmark detail only
  where needed. Preserve the existing deferred scene loading.
- Evaluate mesh compression and KTX2/Basis textures with decoders matched to the
  bundled three.js revision. Preserve GPU instancing and compare decoded quality,
  startup time, and GPU memory before adopting either format.
- Export both panorama and real-time derivatives from the same landmark masters,
  layout, material sources, and scene version. Compare their fixed viewpoints.
- Add asset checks for missing textures, incorrect texture color spaces, broken UVs,
  flipped/mirrored artwork, export scale, collision alignment, and lost instancing.
- Re-run the counting, route, saved-session, loading/retry, and accessibility tests
  after layout or renderer changes. Exercise the entire tour on real devices.

Provisional performance targets, to confirm after baseline measurements:

| Measure | Target |
|---|---|
| Supported mobile scene | Sustained 30 FPS; 95th-percentile frame time at or below 33 ms |
| Desktop at 1080p | Aim for 60 FPS; benchmark a defined hardware profile |
| Initial Haram model payload | Keep at or below the current ~8.6 MB by streaming detail |
| Initial Mas'a resume payload | Keep close to the current ~3.2 MB before optional detail |
| Active mobile texture allocation | Initial planning ceiling of 128 MiB, estimated from formats and mip levels |
| Long-session behavior | No progressive memory growth or disruptive slowdowns during a 10-minute walkthrough |

**Deliverable:** fixed-view before/after comparisons, actual device measurements,
asset/provenance records, and a consistent visual update in both tour modes.

Technical references: [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html),
[KTX2Loader](https://threejs.org/docs/pages/KTX2Loader.html). The installed loader
already contains extension hooks for Basis textures, mesh compression, and GPU
instancing; compatible decoder/transcoder assets still need to be supplied and tested.

## Recommended order and first milestone

Sequence: **references → material/lighting pipeline → Kaaba section → Haram →
Mas'a → crowds → final optimization and validation**. Measure performance throughout,
not just at the end.

The first implementation milestone should be the referenced Kaaba corner and door,
Black Stone, Maqam, a small surrounding floor/arcade section, and convincing day/night
lighting. Deliver it as a browser preview and matching reference-camera images. This
establishes a practical visual standard before rebuilding the whole environment.

Specialist inputs are most valuable for Arabic kiswa artwork, landmark modeling,
and crowd clothing/animation. Engineering work can begin with material preservation,
lighting comparisons, shared layout data, and performance instrumentation. Schedule
estimates should follow the reference and asset audit, since existing reusable assets
and artwork availability will determine much of the effort.
