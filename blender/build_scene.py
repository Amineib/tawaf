"""Generate the Umrah tour scenes and render 360-degree panoramas.

Usage (pip install bpy, or run inside Blender's Python):
    python build_scene.py haram  OUT_DIR  RES_X  SAMPLES  [camera ...]
    python build_scene.py masa   OUT_DIR  RES_X  SAMPLES  [camera ...]

Writes OUT_DIR/<scene>.blend, OUT_DIR/<camera>.jpg and OUT_DIR/<scene>_views.json
(yaw/pitch of points of interest per camera, used by the web viewer).

Layout of the Haram scene (metres, Kaaba centred on the origin):
    Black Stone corner  (+x,+y)   = east
    Iraqi corner        (-x,+y)   = north
    Shami corner        (-x,-y)   = west
    Yemeni corner       (+x,-y)   = south
    Door + Maqam Ibrahim on the +y (north-east) side, Hijr Ismail on -x side.
    Tawaf runs counter-clockwise seen from above: Kaaba on the pilgrim's left.
This is a stylised reconstruction for orientation, not a survey-accurate model.
"""
import sys, os, json, math, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from common import *

KX, KY, KH = 5.85, 6.45, 13.1          # Kaaba half-widths and height
BLACK_STONE = (KX + 0.12, KY + 0.12, 1.5)
YEMENI = (KX + 0.1, -KY - 0.1, 1.5)
MAQAM = (2.0, 17.0, 0.0)
EYE = 1.6


# =================================================================== HARAM

def build_haram():
    s = reset()
    night = os.environ.get('UMRAH_TIME') == 'night'
    rnd = random.Random(7)
    arch = collection('Architecture')
    kc = collection('Kaaba')
    people = collection('Pilgrims')

    floor_m = marble('Mataf marble', base=(0.88, 0.86, 0.82), vein=(0.74, 0.73, 0.70), tile=1.2, scale=0.5, rough=0.32, tex='marble_white', tex_size=2.4)
    floor_m.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.0
    wall_m = marble('Arcade marble', base=(0.84, 0.82, 0.78), vein=(0.70, 0.68, 0.64), tile=0.8, rough=0.35, tex='marble_warm', tex_size=2.0, seams=False)
    stone_m = textured('Granite', 'granite', 1.2, fallback=(0.10, 0.09, 0.09), rough=0.25, coat=0.4, tint=(0.45, 0.42, 0.42), rough_mul=0.5)
    dome_m = principled('Dome lead', (0.42, 0.43, 0.45), rough=0.45, metal=0.3)
    gold_m = principled('Gold', (1.0, 0.74, 0.32), rough=0.25, metal=1.0)
    silver_m = principled('Silver', (0.9, 0.9, 0.92), rough=0.2, metal=1.0)
    blackstone_m = principled('Black Stone', (0.03, 0.025, 0.025), rough=0.35)
    cream_m = textured('Cream stone', 'stucco', 4.0, fallback=(0.80, 0.74, 0.64), rough=0.6, tint=(0.95, 0.88, 0.76))
    city_m = facade('Hotels', (0.74, 0.70, 0.63), night=night)
    tower_m = facade('Tower facade', (0.80, 0.74, 0.64), night=night, win_w=2.2, floor_h=4.2, lit_strength=8.0)
    glass_m = principled('Dark glass', (0.05, 0.07, 0.09), rough=0.08, metal=0.6)
    green_m = emissive('Green start light', (0.05, 1.0, 0.25), 25)
    shade_m = principled('Interior shade', (0.18, 0.17, 0.16), rough=0.8)
    cooler_m = principled('Zamzam cooler', (0.85, 0.86, 0.88), rough=0.25, metal=0.5)

    # ---- mataf floor
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=70, fill_type='NGON')
    f = bpy.context.object; f.name = 'Mataf floor'; f.data.materials.append(floor_m)
    for c in f.users_collection: c.objects.unlink(f)
    arch.objects.link(f)
    # wider ground under the city
    g = box('Ground', (2000, 2000, 1), (0, 0, -0.52), principled('Ground', (0.55, 0.5, 0.44), rough=0.9), arch)

    # ---- Kaaba
    kaaba = box('Kaaba', (2 * KX, 2 * KY, KH), (0, 0, KH / 2), kiswa_black(), kc)
    sh = box('Shadharwan', (2 * KX + 0.7, 2 * KY + 0.7, 0.32), (0, 0, 0.16), wall_m, kc)
    roof = box('Roof parapet', (2 * KX + 0.04, 2 * KY + 0.04, 0.25), (0, 0, KH + 0.12), principled('Roof', (0.05, 0.05, 0.05), rough=0.6), kc)
    band_h = 0.95
    band = box('Hizam band', (2 * KX + 0.03, 2 * KY + 0.03, band_h), (0, 0, KH * 0.68), gold_ornament('Hizam', 0.07, band_h / 2, 2.6), kc)
    # gold panels under the band (abstract ornaments)
    pan_m = gold_ornament('Panel ornament', 0.10, None, 4.0)
    for side in range(4):
        horiz = side in (0, 2)
        n = 4
        for i in range(n):
            t = (i + 0.5) / n * 2 - 1
            if horiz:
                y = KY + 0.03 if side == 0 else -KY - 0.03
                loc = (t * (KX - 1.2), y, KH * 0.68 - 1.6)
                box(f'Panel{side}{i}', (0.9, 0.04, 1.6), loc, pan_m, kc)
            else:
                x = KX + 0.03 if side == 1 else -KX - 0.03
                loc = (x, t * (KY - 1.2), KH * 0.68 - 1.6)
                box(f'Panel{side}{i}', (0.04, 0.9, 1.6), loc, pan_m, kc)
    # door curtain (sitara) on the north-east (+y) wall, near the Black Stone corner
    box('Door curtain', (3.4, 0.08, 6.0), (2.3, KY + 0.06, 2.1 + 3.0), gold_ornament('Sitara', 0.16, None, 3.0), kc)
    box('Door threshold', (2.2, 0.3, 0.12), (2.3, KY + 0.18, 2.1), gold_m, kc)
    # Mizab (golden waterspout) over Hijr Ismail
    box('Mizab', (2.4, 0.35, 0.3), (-KX - 1.2, 0, KH - 0.3), gold_m, kc)
    # Black Stone in its silver frame
    bpy.ops.mesh.primitive_torus_add(major_radius=0.33, minor_radius=0.08, major_segments=32, minor_segments=10)
    t = bpy.context.object; t.name = 'Black Stone frame'; t.data.materials.append(silver_m)
    for c in t.users_collection: c.objects.unlink(t)
    kc.objects.link(t)
    t.location = BLACK_STONE
    t.rotation_mode = 'QUATERNION'; t.rotation_quaternion = Vector((1, 1, 0)).to_track_quat('Z', 'Y')
    t.scale = (1, 1.25, 1)
    bs = sphere('Black Stone', 0.27, BLACK_STONE, blackstone_m, (1, 1, 1), kc)
    bs.rotation_mode = 'QUATERNION'; bs.rotation_quaternion = t.rotation_quaternion; bs.scale = (1, 1.2, 0.35)

    # ---- Hijr Ismail (semicircular wall, part of the Kaaba)
    arc_wall('Hijr Ismail', -KX, 0, 8.4, 6.6, math.radians(105), math.radians(255), 1.4, 1.3, wall_m, coll=kc)

    # ---- Maqam Ibrahim
    mx, my, _ = MAQAM
    cylinder('Maqam base', 0.95, 0.55, (mx, my, 0), stone_m, segs=8, coll=kc, smooth=False)
    cylinder('Maqam cage', 0.72, 1.7, (mx, my, 0.55), gold_ornament('Maqam lattice', 0.2, None, 7.0), segs=8, coll=kc, smooth=False)
    sphere('Maqam dome', 0.72, (mx, my, 2.25), gold_m, (1, 1, 0.75), kc)
    cylinder('Maqam finial', 0.05, 0.55, (mx, my, 2.75), gold_m, segs=8, coll=kc)

    # ---- Mataf arcades: 4 levels, pointed arches, around r=48
    R, NB, LH = 48.0, 52, 8.0
    for lvl in range(4):
        z0 = lvl * LH
        bm = bmesh.new()
        for i in range(NB):
            a0, a1 = 2 * math.pi * i / NB, 2 * math.pi * (i + 1) / NB
            arcade_bays(bm, (R * math.cos(a0), R * math.sin(a0)), (R * math.cos(a1), R * math.sin(a1)),
                        z0, LH, pier=0.9, spring_frac=0.55 if lvl == 0 else 0.5)
        o = obj_from_bm(f'Arcade L{lvl}', bm, [wall_m], arch)
        solidify(o, 1.0, -1)
        # columns
        col_src = cylinder(f'Column L{lvl}', 0.55, LH, (R, 0, z0), wall_m, segs=24, coll=arch)
        spring = z0 + LH * (0.55 if lvl == 0 else 0.5)
        base1 = cylinder(f'Base L{lvl}', 0.78, 0.35, (R, 0, z0), wall_m, segs=24, coll=arch)
        base2 = cylinder(f'Base2 L{lvl}', 0.66, 0.2, (R, 0, z0 + 0.35), wall_m, segs=24, coll=arch)
        cap1 = cylinder(f'Capital L{lvl}', 0.62, 0.3, (R, 0, spring - 0.75), wall_m, segs=24, coll=arch, r2=0.85)
        cap2 = box(f'Abacus L{lvl}', (1.9, 1.9, 0.35), (R, 0, spring - 0.45), wall_m, arch)
        for i in range(1, NB):
            a = 2 * math.pi * i / NB
            p = (R * math.cos(a), R * math.sin(a))
            instance(col_src, f'Col{lvl}_{i}', (*p, z0), coll=arch)
            instance(base1, f'Base{lvl}_{i}', (*p, z0), coll=arch)
            instance(base2, f'Base2{lvl}_{i}', (*p, z0 + 0.35), coll=arch)
            instance(cap1, f'Cap{lvl}_{i}', (*p, spring - 0.75), coll=arch)
            ab = instance(cap2, f'Abacus{lvl}_{i}', (*p, spring - 0.45), rot_z=a, coll=arch)
        cap2.rotation_euler.z = 0.0
        # cornice band under each floor slab, then the slab
        annulus(f'Cornice L{lvl}', R - 1.55, R - 0.4, z0 + LH - 0.25, 0.45, wall_m, coll=arch)
        annulus(f'Slab L{lvl + 1}', R - 1.2, 66, z0 + LH, 0.9, wall_m, coll=arch)
        # balustrade: top rail, bottom rail, turned balusters
        zt = z0 + LH
        annulus(f'Rail top L{lvl + 1}', R - 1.3, R - 0.9, zt + 1.15, 0.15, wall_m, coll=arch)
        annulus(f'Rail low L{lvl + 1}', R - 1.25, R - 0.95, zt + 0.15, 0.15, wall_m, coll=arch)
        if lvl == 0:
            bal = cylinder('Baluster', 0.09, 0.85, (0, 0, -50), wall_m, segs=10, coll=arch, r2=0.06)
        nbal = int(2 * math.pi * (R - 1.1) / 0.42)
        for j in range(nbal):
            a = 2 * math.pi * j / nbal
            instance(bal, f'Bal{lvl}_{j}', ((R - 1.1) * math.cos(a), (R - 1.1) * math.sin(a), zt + 0.15), coll=arch)
    # back wall with a second arcade so the arches read as deep
    bm = bmesh.new()
    for lvl in range(4):
        for i in range(NB):
            a0, a1 = 2 * math.pi * i / NB, 2 * math.pi * (i + 1) / NB
            Rb = 60
            arcade_bays(bm, (Rb * math.cos(a0), Rb * math.sin(a0)), (Rb * math.cos(a1), Rb * math.sin(a1)),
                        lvl * LH, LH, pier=1.6, spring_frac=0.55)
    o = obj_from_bm('Inner arcade', bm, [wall_m], arch)
    solidify(o, 0.8, -1)
    annulus('Back wall', 65.5, 66.5, 4 * LH, 4 * LH, shade_m, coll=arch)
    # domes on the roof
    dsrc = sphere('Dome', 2.6, (R + 6, 0, 4 * LH), dome_m, (1, 1, 0.85), arch, segs=20, rings=10)
    drum = cylinder('Drum', 2.7, 0.8, (R + 6, 0, 4 * LH - 0.1), wall_m, segs=20, coll=arch)
    for i in range(1, NB):
        a = 2 * math.pi * (i) / NB
        p = ((R + 6) * math.cos(a), (R + 6) * math.sin(a))
        instance(dsrc, f'Dome{i}', (*p, 4 * LH), scale=(1, 1, 0.85), coll=arch)
        instance(drum, f'Drum{i}', (*p, 4 * LH - 0.1), coll=arch)
    # green light marking the start line of tawaf, on the arcade facing the Black Stone
    d = Vector((1, 1, 0)).normalized()
    box('Tawaf start light', (0.5, 0.5, 1.4), (*(d * (R - 0.75)).xy, 3.2), green_m, arch, rot_z=math.radians(45))

    # ---- warm lamps hanging in every arcade bay (stand-ins for the chandeliers)
    lamp_m = emissive('Arcade lamp', (1.0, 0.82, 0.58), 70.0 if night else 40.0)
    shade_g = principled('Lamp brass', (0.85, 0.62, 0.30), rough=0.3, metal=1.0)
    lamp = sphere('Lamp', 0.35, (0, 0, -100), lamp_m, coll=arch, segs=12, rings=6)
    cap = cylinder('Lamp cap', 0.42, 0.25, (0, 0, -100), shade_g, segs=12, coll=arch)
    for lvl in range(4):
        for i in range(NB):
            a_ = 2 * math.pi * (i + 0.5) / NB
            for rr in (R + 4.5, R + 10.5):
                p = (rr * math.cos(a_), rr * math.sin(a_))
                instance(lamp, f'Lamp{lvl}_{i}_{rr}', (*p, lvl * LH + 5.6), coll=arch)
                instance(cap, f'Cap{lvl}_{i}_{rr}', (*p, lvl * LH + 5.85), coll=arch)

    # ---- Zamzam coolers along the arcade
    cool = cylinder('Zamzam cooler', 0.28, 1.0, (0, 0, 0), cooler_m, segs=16, coll=arch)
    for k in range(18):
        a = math.radians(20 + k * 20)
        instance(cool, f'Cooler{k}', ((R - 2.2) * math.cos(a), (R - 2.2) * math.sin(a), 0), coll=arch)

    # ---- minarets
    def minaret(name, x, y, h=95):
        cylinder(name + ' base', 3.2, 22, (x, y, 0), cream_m, segs=4, coll=arch, smooth=False).rotation_euler.z = math.radians(45)
        cylinder(name + ' shaft', 2.2, h - 30, (x, y, 22), cream_m, segs=8, coll=arch, smooth=False)
        for zz in (h * 0.45, h * 0.7):
            cylinder(name + ' balcony', 3.1, 1.2, (x, y, zz), cream_m, segs=8, coll=arch, smooth=False)
        cylinder(name + ' top', 1.6, 12, (x, y, h - 8), cream_m, segs=8, coll=arch, smooth=False)
        cylinder(name + ' cone', 1.7, 6, (x, y, h + 4), gold_m, segs=8, coll=arch, r2=0.05, smooth=False)
        if night:
            for zz in (h * 0.45 + 1.25, h * 0.7 + 1.25):
                annulus(name + ' light', 3.0, 3.15, zz, 0.25, minaret_light, segs=24, coll=arch).location = (x, y, 0)
            # floodlight on the minaret aimed into the courtyard
            spot(name + ' flood', (x * 0.98, y * 0.98, h * 0.7), (0, 0, 0), 1.2e5, angle_deg=34, blend=0.7, radius=1.5, coll=arch)
    minaret_light = emissive('Minaret light', (0.92, 1.0, 0.9), 12.0)
    for i, ang in enumerate([20, 70, 115, 160, 205, 250, 295, 340]):
        rr = 78 + (i % 3) * 14
        minaret(f'Minaret{i}', rr * math.cos(math.radians(ang)), rr * math.sin(math.radians(ang)))
    # outer mosque mass
    annulus('Outer mosque', 70, 120, 26, 26, cream_m, segs=96, coll=arch)
    annulus('Outer mosque parapet', 118, 120, 30, 4, cream_m, segs=96, coll=arch)

    # ---- the clock tower complex to the south (Yemeni-corner side)
    south = Vector((1, -1, 0)).normalized()
    c = south * 340
    rz = math.radians(45)
    box('Clock tower', (62, 62, 300), (c.x, c.y, 150), tower_m, arch, rot_z=rz)
    box('Clock tower setback', (56, 56, 80), (c.x, c.y, 340), tower_m, arch, rot_z=rz)
    for zz in (300, 380):   # cornices at the setbacks
        box('Setback cornice', (64, 64, 2.5), (c.x, c.y, zz), cream_m, arch, rot_z=rz)
    box('Clock tower mid', (50, 50, 60), (c.x, c.y, 410), tower_m, arch, rot_z=rz)
    box('Clock block', (48, 48, 56), (c.x, c.y, 468), glass_m, arch, rot_z=rz)
    face_m = principled('Clock face', (0.92, 0.92, 0.9), rough=0.4, emission=(1, 1, 0.95), estrength=(14.0 if night else 0.6))
    ring_m = emissive('Clock ring', (0.15, 1.0, 0.35), 20.0) if night else gold_m
    for k in range(4):            # four faces, one per side
        dirv = Vector((math.cos(rz + k * math.pi / 2 + math.pi / 4), math.sin(rz + k * math.pi / 2 + math.pi / 4), 0))
        dirv = Vector((round(dirv.x, 6), round(dirv.y, 6), 0)).normalized()
        cyl = cylinder(f'Clock face {k}', 20, 0.6, (0, 0, 0), face_m, segs=48, coll=arch)
        cyl.location = (c.x + dirv.x * 24.5, c.y + dirv.y * 24.5, 468)
        cyl.rotation_mode = 'QUATERNION'; cyl.rotation_quaternion = dirv.to_track_quat('Z', 'Y')
        bpy.ops.mesh.primitive_torus_add(major_radius=20.5, minor_radius=0.8, major_segments=64, minor_segments=8)
        tr = bpy.context.object; tr.name = f'Clock rim {k}'; tr.data.materials.append(ring_m)
        tr.location = (c.x + dirv.x * 24.9, c.y + dirv.y * 24.9, 468)
        tr.rotation_mode = 'QUATERNION'; tr.rotation_quaternion = cyl.rotation_quaternion
    cylinder('Clock crown', 14, 30, (c.x, c.y, 496), gold_m, segs=8, coll=arch, r2=6, smooth=False)
    cylinder('Clock spire', 6, 95, (c.x, c.y, 526), cream_m, segs=8, coll=arch, r2=0.8, smooth=False)
    bpy.ops.mesh.primitive_torus_add(major_radius=7, minor_radius=1.4, major_segments=40, minor_segments=8)
    cr = bpy.context.object; cr.name = 'Crescent'; cr.data.materials.append(gold_m)
    cr.location = (c.x, c.y, 630); cr.rotation_euler = (math.radians(90), 0, rz)
    for k, (dx, dy, h) in enumerate([(-130, -60, 240), (-60, -150, 230), (70, 90, 250), (-150, 40, 200)]):
        p = c + Vector((dx, dy, 0))
        box(f'Tower{k}', (55, 55, h), (p.x, p.y, h / 2), tower_m, arch, rot_z=rz)
        box(f'Tower crown{k}', (40, 40, 18), (p.x, p.y, h + 9), cream_m, arch, rot_z=rz)
    # podium
    box('Podium', (260, 160, 70), (c.x, c.y, 35), tower_m, arch, rot_z=rz)

    # ---- surrounding city
    src = box('Hotel', (1, 1, 1), (0, 0, 0), city_m, arch)
    src.hide_render = True
    for k in range(140):
        ang = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(170, 420)
        p = Vector((rr * math.cos(ang), rr * math.sin(ang), 0))
        if (p - c).length < 170:
            continue
        w, dpt, h = rnd.uniform(25, 60), rnd.uniform(25, 60), rnd.uniform(25, 140)
        o = instance(src, f'Hotel{k}', (p.x, p.y, h / 2), rot_z=ang, scale=(w, dpt, h), coll=arch)
        o.hide_render = False

    # ---- pilgrims
    variants = make_pilgrim_meshes(people)
    cams = haram_cameras_spec()
    def free(p):
        x, y = p
        if abs(x) < KX + 0.9 and abs(y) < KY + 0.9:
            return False
        # inside Hijr wall band
        ex, ey = (x + KX) / 9.9, y / 8.1
        if x < -KX and 0.72 < ex * ex + ey * ey < 1.15:
            return False
        if math.hypot(x - MAQAM[0], y - MAQAM[1]) < 1.6:
            return False
        for cname, (cx, cy, cz, fw) in cams.items():
            if cz < 3 and math.hypot(x - cx, y - cy) < 3.2:
                return False
        return True
    placed = []
    n = 0
    tries = 0
    while n < 1700 and tries < 40000:
        tries += 1
        r = 7.2 + 34 * (rnd.random() ** 1.5)
        a = rnd.uniform(0, 2 * math.pi)
        p = (r * math.cos(a), r * math.sin(a))
        if not free(p):
            continue
        if any((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 < 0.42 for q in placed[-700:]):
            continue
        placed.append(p)
        heading = a + math.pi / 2 + rnd.gauss(0, 0.2)          # counter-clockwise
        o = pick(variants, rnd)
        inst = instance(o, f'P{n}', (p[0], p[1], 0), rot_z=heading - math.pi / 2,
                        scale=rnd.uniform(0.9, 1.08), coll=people)
        inst.hide_render = False; inst.hide_viewport = False
        n += 1
    # a few on the upper levels
    for k in range(260):
        lvl = rnd.choice([1, 2, 3])
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(R + 0.5, R + 9)
        o = pick(variants, rnd)
        inst = instance(o, f'U{k}', (r * math.cos(a), r * math.sin(a), lvl * LH), rot_z=a, scale=rnd.uniform(0.9, 1.05), coll=people)
        inst.hide_render = False

    if night:
        night_world(0.03)
        # floodlights on the arcade roof aimed at the court around the Kaaba
        for i in range(24):
            a = 2 * math.pi * (i + 0.5) / 24
            tgt = (24 * math.cos(a + 0.3), 24 * math.sin(a + 0.3), 0)
            spot(f'Flood{i}', ((R + 2) * math.cos(a), (R + 2) * math.sin(a), 4 * LH + 4), tgt, 3e4, angle_deg=55, blend=0.8, radius=1.0, coll=arch)
        sun = ('night',)
    else:
        sun = hdri_world(sun_az_deg=40, strength=1.4)
    if sun is None:
        sky_world(sun_elev_deg=34, sun_az_deg=40, strength=0.32, sun_strength=4.2)
    elif not night:
        print(f'HDRI sun at azimuth {sun[0]:.0f} deg, elevation {sun[1]:.0f} deg', flush=True)

    for cname, (x, y, z, fw) in cams.items():
        pano_camera(cname, (x, y, z), fw)

    pois = {
        'kaaba': (0, 0, 7), 'black_stone': BLACK_STONE, 'yemeni': YEMENI,
        'door': (2.3, KY, 5.0), 'hijr': (-KX - 8.0, 0, 1.0), 'mizab': (-KX - 1.2, 0, KH - 0.3),
        'maqam': (MAQAM[0], MAQAM[1], 1.6), 'start_light': (*(d * (R - 0.75)).xy, 3.2),
        'clock': (c.x, c.y, 470), 'zamzam': ((R - 2.2) * math.cos(math.radians(80)), (R - 2.2) * math.sin(math.radians(80)), 0.6),
        'gate': (0.0, 62.0, 4.0),
    }
    return pois


def haram_cameras_spec():
    d = Vector((1, 1, 0)).normalized()
    start = Vector((KX, KY, 0)) + d * 8.5
    y = Vector((1, -1, 0)).normalized()
    yem = Vector((KX, -KY, 0)) + y * 7.0
    return {
        # name: (x, y, z, forward heading in degrees)
        'entry': (math.cos(math.radians(80)) * 55.5, math.sin(math.radians(80)) * 55.5, EYE, 260),
        'start': (start.x, start.y, EYE, 225),
        'hijr': (-KX - 12.5, 3.0, EYE, 0),
        'yemeni': (yem.x, yem.y, EYE, 135),
        'maqam': (MAQAM[0] + 0.4, MAQAM[1] + 3.0, EYE, 260),
    }


# =================================================================== MAS'A

SAFA_X, MARWA_X = 0.0, 400.0
GREEN = (150.0, 205.0)


def build_masa():
    s = reset()
    rnd = random.Random(11)
    arch = collection('Architecture')
    people = collection('Pilgrims')
    floor_m = marble('Masa marble', base=(0.86, 0.85, 0.82), vein=(0.76, 0.75, 0.73), tile=1.0, scale=0.6, tex='marble_white', tex_size=2.0)
    wall_m = marble('Masa wall', base=(0.86, 0.84, 0.80), vein=(0.72, 0.70, 0.66), tile=0.9, rough=0.3, tex='marble_warm', tex_size=2.0, seams=False)
    ceil_m = textured('Ceiling', 'stucco', 3.0, fallback=(0.90, 0.88, 0.84), rough=0.6, tint=(1.0, 0.97, 0.92))
    rock_m = textured('Rock', 'rock', 2.5, fallback=(0.30, 0.24, 0.19), rough=0.85, normal_strength=1.0, tint=(0.42, 0.36, 0.32), desat=0.35)
    rail_m = principled('Brass rail', (0.85, 0.66, 0.36), rough=0.3, metal=1.0)
    glass_m = principled('Glass', (0.9, 0.95, 0.95), rough=0.02)
    glass_m.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 1.0
    light_m = emissive('Ceiling light', (1.0, 0.92, 0.80), 12.0)
    green_m = emissive('Green lights', (0.1, 1.0, 0.3), 8.0)
    dark_m = principled('Shade', (0.2, 0.19, 0.18), rough=0.8)
    sign_m = principled('Sign', (0.05, 0.25, 0.15), rough=0.5, emission=(0.05, 0.25, 0.15), estrength=0.3)

    X0, X1, HW, H = -30, 430, 22, 12
    box('Floor', (X1 - X0, 2 * HW, 0.2), ((X0 + X1) / 2, 0, -0.1), floor_m, arch)
    # ceiling: main span + plates around a round opening over each hill
    box('Ceiling', (MARWA_X - 28, 2 * HW, 0.8), (MARWA_X / 2, 0, H + 0.4), ceil_m, arch)
    for cx in (SAFA_X - 8, MARWA_X + 8):
        x_lo, x_hi = (X0, 14) if cx < 100 else (MARWA_X - 14, X1)
        hole_lo, hole_hi = cx - 11, cx + 11
        if hole_lo > x_lo:
            box('Ceiling', (hole_lo - x_lo, 2 * HW, 0.8), ((x_lo + hole_lo) / 2, 0, H + 0.4), ceil_m, arch)
        if x_hi > hole_hi:
            box('Ceiling', (x_hi - hole_hi, 2 * HW, 0.8), ((hole_hi + x_hi) / 2, 0, H + 0.4), ceil_m, arch)
        for sy in (-1, 1):
            box('Ceiling', (22, HW - 11, 0.8), (cx, sy * (11 + (HW - 11) / 2), H + 0.4), ceil_m, arch)
        plate = annulus('Dome plate', 11, 15.6, H + 0.78, 0.8, ceil_m, coll=arch)
        plate.location = (cx, 0, -0.02)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=11)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01], context='VERTS')
        o = obj_from_bm('Dome', bm, [ceil_m], arch, smooth=True)
        o.location = (cx, 0, H + 0.8)
        solidify(o, 0.4)
        ring_l = annulus('Dome light ring', 10.4, 10.9, H + 1.0, 0.2, light_m, coll=arch)
        ring_l.location = (cx, 0, 0)
    # end walls
    box('Safa end wall', (1, 2 * HW, H + 12), (X0, 0, (H + 12) / 2), wall_m, arch)
    box('Marwa end wall', (1, 2 * HW, H + 12), (X1, 0, (H + 12) / 2), wall_m, arch)
    # side walls: arcade + shade behind
    for sy in (-1, 1):
        bm = bmesh.new()
        x = X0
        while x < X1:
            arcade_bays(bm, (x, sy * HW), (x + 9, sy * HW), 0, H, pier=1.4, spring_frac=0.55)
            x += 9
        o = obj_from_bm('Side arcade', bm, [wall_m], arch)
        solidify(o, 0.8)
        box('Side shade', (X1 - X0, 1, H), ((X0 + X1) / 2, sy * (HW + 4), H / 2), dark_m, arch)
    # columns + capitals, rows at y = +-11
    col = box('Column', (1.3, 1.3, H), (0, 0, H / 2), wall_m, arch)
    cap = box('Capital', (1.8, 1.8, 0.5), (0, 0, H - 0.25), wall_m, arch)
    col.hide_render = cap.hide_render = True
    gsrc = box('Green band', (1.36, 1.36, 0.35), (0, 0, 0), green_m, arch)
    gsrc.hide_render = True
    x = 14
    k = 0
    while x < MARWA_X - 12:
        for yy in (-11, 11):
            a = instance(col, f'Col{k}', (x, yy, H / 2), coll=arch); a.hide_render = False
            b = instance(cap, f'Cap{k}', (x, yy, H - 0.25), coll=arch); b.hide_render = False
            if GREEN[0] <= x <= GREEN[1]:
                g = instance(gsrc, f'GB{k}', (x, yy, 8.5), coll=arch); g.hide_render = False
            k += 1
        x += 9
    # ceiling light panels and green strips
    lp = box('Light panel', (6, 1.2, 0.08), (0, 0, 0), light_m, arch)
    lp.hide_render = True
    gs = box('Green strip', (8, 0.35, 0.12), (0, 0, 0), green_m, arch)
    gs.hide_render = True
    x = 18
    k = 0
    while x < MARWA_X - 16:
        for yy in (-16.5, -5.5, 5.5, 16.5):
            o = instance(lp, f'L{k}', (x, yy, H - 0.06), coll=arch); o.hide_render = False
            if GREEN[0] <= x <= GREEN[1]:
                g = instance(gs, f'G{k}', (x, yy + 1.4, H - 0.08), coll=arch); g.hide_render = False
            k += 1
        x += 9
    # lane dividers
    steel_m = principled('Steel', (0.7, 0.7, 0.72), rough=0.3, metal=1.0)
    post = cylinder('Post', 0.04, 0.95, (0, 0, 0), steel_m, segs=8, coll=arch)
    post.hide_render = True
    for yy in (-2.5, 2.5):
        box('Rail', (MARWA_X - 30, 0.07, 0.07), (MARWA_X / 2, yy, 0.95), steel_m, arch)
        box('Rail low', (MARWA_X - 30, 0.04, 0.04), (MARWA_X / 2, yy, 0.45), steel_m, arch)
        xx = 15
        while xx < MARWA_X - 15:
            p = instance(post, f'Post{yy}_{xx}', (xx, yy, 0), coll=arch); p.hide_render = False
            xx += 3
    # direction signs over the lanes
    for xx in (60, 140, 220, 300):
        for yy in (-11, 11):
            box('Sign', (0.15, 5.5, 0.9), (xx + 4.5, yy * 0.75, 8.8), sign_m, arch)

    # Safa and Marwah: platforms, rocks, glass screens
    box('Safa platform', (24, 30, 0.6), (SAFA_X - 12, 0, 0.3), floor_m, arch)
    rock('Safa rock', (7.5, 6.5, 3.2), (SAFA_X - 15, 0, 0.6), rock_m, seed=3, coll=arch)
    box('Marwa platform', (24, 30, 0.4), (MARWA_X + 12, 0, 0.2), floor_m, arch)
    rock('Marwa rock', (6.5, 5.0, 1.9), (MARWA_X + 15, 0, 0.4), rock_m, seed=9, coll=arch)
    for cx, sgn, zf in ((SAFA_X - 15, 1, 0.6), (MARWA_X + 15, -1, 0.4)):
        bm = bmesh.new()
        for i in range(25):
            t0 = math.radians(-80 + 160 * i / 25) + (0 if sgn > 0 else math.pi)
            t1 = math.radians(-80 + 160 * (i + 1) / 25) + (0 if sgn > 0 else math.pi)
            p0 = (cx + 9.5 * math.cos(t0), 8 * math.sin(t0)); p1 = (cx + 9.5 * math.cos(t1), 8 * math.sin(t1))
            v = [bm.verts.new((p0[0], p0[1], zf)), bm.verts.new((p1[0], p1[1], zf)),
                 bm.verts.new((p1[0], p1[1], zf + 1.1)), bm.verts.new((p0[0], p0[1], zf + 1.1))]
            bm.faces.new(v)
        o = obj_from_bm('Hill screen', bm, [glass_m], arch)
        solidify(o, 0.04)
        bm = bmesh.new()
        for i in range(25):
            t0 = math.radians(-80 + 160 * i / 25) + (0 if sgn > 0 else math.pi)
            t1 = math.radians(-80 + 160 * (i + 1) / 25) + (0 if sgn > 0 else math.pi)
            p0 = (cx + 9.5 * math.cos(t0), 8 * math.sin(t0)); p1 = (cx + 9.5 * math.cos(t1), 8 * math.sin(t1))
            v = [bm.verts.new((p0[0], p0[1], zf + 1.1)), bm.verts.new((p1[0], p1[1], zf + 1.1)),
                 bm.verts.new((p1[0], p1[1], zf + 1.18)), bm.verts.new((p0[0], p0[1], zf + 1.18))]
            bm.faces.new(v)
        o = obj_from_bm('Hill rail', bm, [rail_m], arch)
        solidify(o, 0.08)

    # pilgrims: towards Marwah on +y side, towards Safa on -y side
    variants = make_pilgrim_meshes(people)
    cams = masa_cameras_spec()
    n = 0
    placed = []
    tries = 0
    while n < 1300 and tries < 30000:
        tries += 1
        xx = rnd.uniform(SAFA_X + 1, MARWA_X - 1)
        yy = rnd.uniform(-HW + 2, HW - 2)
        if abs(yy) < 3.0 or any(abs(yy - c) < 1.0 and (xx - 14) % 9 < 1.0 for c in (-11, 11)):
            continue
        if any(math.hypot(xx - cx, yy - cy) < 3.2 for (cx, cy, cz, fw) in cams.values()):
            continue
        if any((xx - p[0]) ** 2 + (yy - p[1]) ** 2 < 0.5 for p in placed[-300:]):
            continue
        placed.append((xx, yy))
        heading = 0.0 if yy > 0 else math.pi
        o = pick(variants, rnd)
        inst = instance(o, f'P{n}', (xx, yy, 0), rot_z=heading - math.pi / 2 + rnd.gauss(0, 0.15),
                        scale=rnd.uniform(0.9, 1.08), coll=people)
        inst.hide_render = False; inst.hide_viewport = False
        n += 1
    # people standing on the hills
    for (cx, zf) in ((SAFA_X - 4, 0.6), (MARWA_X + 4, 0.4)):
        for k in range(40):
            xx = cx + rnd.uniform(-3, 3); yy = rnd.uniform(-12, 12)
            if any(math.hypot(xx - c[0], yy - c[1]) < 3.0 for c in cams.values()):
                continue
            o = pick(variants, rnd)
            face_rock = math.pi / 2 if cx < 100 else -math.pi / 2
            inst = instance(o, f'H{cx}_{k}', (xx, yy, zf), rot_z=face_rock + rnd.gauss(0, 0.4), coll=people)
            inst.hide_render = False

    flat_world((0.9, 0.85, 0.75), 0.25)
    for cname, (x, y, z, fw) in cams.items():
        pano_camera(cname, (x, y, z), fw)
    pois = {
        'safa_rock': (SAFA_X - 15, 0, 2.5), 'marwa_rock': (MARWA_X + 15, 0, 1.6),
        'to_marwa': (MARWA_X, 6, 2.0), 'to_safa': (SAFA_X, -6, 2.0),
        'green_lights': (GREEN[1] - 15, 6, H), 'green_end': (GREEN[1], 6, 9.0),
        'divider': (100, 2.5, 0.5),
    }
    return pois


def masa_cameras_spec():
    return {
        'safa': (SAFA_X + 3.0, 4.0, EYE, 0),
        'green': (GREEN[0] + 18, 6.0, EYE, 0),
        'marwa': (MARWA_X - 3.0, -4.0, EYE, 0),
    }


# =================================================================== main

if __name__ == '__main__':
    argv = sys.argv[1:]
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    scene_name, out_dir, res, samples = argv[0], argv[1], int(argv[2]), int(argv[3])
    only = argv[4:]
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    pois = build_haram() if scene_name == 'haram' else build_masa()
    sfx = '_night' if os.environ.get('UMRAH_TIME') == 'night' else ''
    render_settings(res, samples, exposure=(0.25 if not sfx else 0.4) if scene_name == 'haram' else 0.35)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, f'{scene_name}{sfx}.blend'))
    print(f'built {scene_name} in {time.time() - t0:.1f}s, objects={len(bpy.data.objects)}', flush=True)
    views = {}
    for cam in [o for o in bpy.data.objects if o.type == 'CAMERA']:
        views[cam.name] = {k: view_angles(cam, v) for k, v in pois.items()}
    with open(os.path.join(out_dir, f'{scene_name}_views.json'), 'w') as f:
        json.dump(views, f, indent=1)
    s = bpy.context.scene
    for cam in [o for o in bpy.data.objects if o.type == 'CAMERA']:
        if only and cam.name not in only:
            continue
        if os.environ.get('UMRAH_RESUME') and os.path.exists(os.path.join(out_dir, f'{cam.name}{sfx}.jpg')):
            print(f'skip {cam.name} (already rendered)', flush=True)
            continue
        s.camera = cam
        s.render.filepath = os.path.join(out_dir, f'{cam.name}{sfx}.jpg')
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'rendered {cam.name} in {time.time() - t1:.1f}s', flush=True)
