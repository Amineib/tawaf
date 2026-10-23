# Visual reference ledger — Kaaba milestone

Scene version: `kaaba-v1`. Reference audit: 23 October 2026. Review status: **pending**.
This is an instructional reconstruction, not a surveyed or operational route map.

| Feature | Evidence | Implemented | Confidence / remaining approximation |
|---|---|---|---|
| Door | [Haram authority: door](https://alharamain.gov.sa/public/?page=kaaba-door-en&site=ur), accessed 2026-10-23 | Separate double-leaf gold door, 1.71 m wide × 3.18 m high, threshold and curtain separated | Published door dimensions; relief panels and mounting height remain approximate. Engraved Arabic is omitted pending artwork review. |
| Shadharwan | [Haram authority: Grand Mosque](https://alharamain.gov.sa/public/?page=masjid-haram-en), accessed 2026-10-23 | Sloping pale marble base with softened edges | Form/material supported; exact projection and height approximate. |
| Black Stone | [Haram authority](https://alharamain.gov.sa/public/?page=The_Black_Stone-en), [Saudipedia](https://saudipedia.com/en/the-black-stone), accessed 2026-10-23 | Recessed dark surface in an asymmetric rolled silver surround, at 1.5 m eye-level height | Height and silver surround supported. Frame outline and visible fragment shapes are approximations, not scan data. |
| Maqam | [Saudipedia](https://saudipedia.com/en/maqam-ibrahim), accessed 2026-10-23 | Open gilded grille, clear enclosure, small crown, white marble and green granite base | Material/form supported. Overall scale, grille arrangement and stone detail need photo comparison and review. Article dimensions describe different components; they were not treated as a survey of the whole enclosure. |
| Kiswa | [SPA: 1448 AH kiswa](https://www.spa.gov.sa/en/N2613391), dated 2026-06-16; [CC0 2016 curtain photograph](https://commons.wikimedia.org/wiki/File:Kiswah_of_the_Golden_Door_of_Kaaba_-_2016.jpg) | Woven black cloth, shallow drape geometry, separate embroidery border; original photographed lettering on a traced open-curtain mesh | **Artwork incomplete.** The curtain uses documented 2016 artwork with non-mirrored dedicated UVs. Hizam and other panels remain reserved; the old invented all-over lattice is removed. This is not a claim to reproduce the exact 1448 AH configuration. Arabic and placement review remain pending. |
| Kaaba footprint | [Saudipedia: four sides](https://saudipedia.com/en/a-list-of-the-dimensions-of-the-four-sides-of-the-holy-kaaba) | Existing coordinate frame retained in `blender/layout.json` | Approximate rectangular footprint retained so lessons and collision geometry stay aligned. Four wall lengths alone do not determine the plan. |
| Marble | [SPA: Grand Mosque marble](https://www.spa.gov.sa/en/N2511740), dated 2026-02-13 | Light stone with restrained surface normals and roughness variation | Scanned generic CC0 marble is a material stand-in, not a scan of the actual Mataf stone. |
| Surrounding architecture | Existing generator | Existing arcades, minarets and skyline retained for this milestone | Still schematic; full reference-matched rebuilding is a later plan phase. |
| Mas'a / green section | [Saudipedia: Safa and Marwa](https://saudipedia.com/en/safa-and-marwa) | Shared existing coordinates, improved material export | Current geometry and green-section distances remain approximate and unreviewed. |
| Pilgrims | Project-authored procedural meshes in `blender/pilgrims.py` | Eight adult body/clothing variants, simple faces, hands and footwear; clothing-aware foot paths and opposing arms | Stylized crowd silhouettes, not scans. Garment construction and close-range faces remain simplified; no specialist clothing review is claimed. |

## Rights and provenance

Official photographs above are design references only. No official photograph has
been embedded in the distributed models or used as a texture.

Generic scanned material sources are CC0:

- Poly Haven: [granite_tile](https://polyhaven.com/a/granite_tile),
  [white_stucco](https://polyhaven.com/a/white_stucco),
  [crepe_satin](https://polyhaven.com/a/crepe_satin),
  [sandstone_cracks](https://polyhaven.com/a/sandstone_cracks).
- ambientCG: [Marble021](https://ambientcg.com/view?id=Marble021),
  [Marble001](https://ambientcg.com/view?id=Marble001).
- Poly Haven sky references: [syferfontein_18d_clear_puresky](https://polyhaven.com/a/syferfontein_18d_clear_puresky)
  and [rogland_clear_night](https://polyhaven.com/a/rogland_clear_night).

The landmark geometry and fixed comparison cameras are project source. Contact
occlusion is baked from that static geometry, excluding pilgrims. Materials and
geometry are shared by panorama and real-time exports. glTF custom material roles
preserve the intended cloth, glass and contact-shading behavior in the browser.

The curtain source photograph is by Abdullah Shakoor, taken 7 May 2016, released
under [CC0](https://creativecommons.org/publicdomain/zero/1.0/) as documented on
its [Commons file page](https://commons.wikimedia.org/wiki/File:Kiswah_of_the_Golden_Door_of_Kaaba_-_2016.jpg).
The original is kept in `blender/artwork/sitara-2016.jpg`, with provenance in the
adjacent JSON file. The curtain mesh excludes the photographed door opening and
lower crowd; the exported texture is reduced in resolution. The image itself is
not redrawn, mirrored, or AI-restyled.

## Review checklist

- Compare the five fixed `blender/visual-cameras.json` views in daylight and at night.
- Check Black Stone recess, door scale, Hijr openings, Maqam silhouette and ground contact.
- Inspect the crowd lineup and close-up, then check moving feet, arm seams and pause/quality behavior in the live tour.
- Obtain accurate, licensed artwork; verify every Arabic face and UV orientation.
- Revisit the footprint, landmark offsets and modern architectural layout with corroborating references.
- Measure real Android/iPhone frame time, memory and ten-minute stability before
  accepting the provisional performance targets in the full plan.

No historical, Arabic/artwork, religious or survey review has been marked complete.
