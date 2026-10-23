"""Shared helpers for the Umrah virtual tour scene generators (Blender 5.x, bpy).

Everything is procedural: no external textures or models are needed, so the
scenes can be regenerated on any machine with `python build_scene.py ...` or
from Blender's Scripting tab.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector

# ---------------------------------------------------------------- basics

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    return s


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def obj_from_bm(name, bm, mats=(), coll=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return link(bpy.data.objects.new(name, me), coll)


def instance(src, name, loc, rot_z=0.0, scale=1.0, coll=None):
    """Linked duplicate: shares mesh data, cheap in memory and render."""
    o = bpy.data.objects.new(name, src.data)
    o.location = loc
    o.rotation_euler = (0, 0, rot_z)
    o.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    return link(o, coll)


def box(name, size, loc, mat, coll=None, rot_z=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = obj_from_bm(name, bm, [mat], coll)
    o.location = loc
    o.rotation_euler.z = rot_z
    return o


def cylinder(name, r, h, loc, mat, segs=24, coll=None, r2=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r,
                          radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, h / 2))
    o = obj_from_bm(name, bm, [mat], coll, smooth=smooth)
    o.location = loc
    return o


def sphere(name, r, loc, mat, scale=(1, 1, 1), coll=None, segs=24, rings=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    o = obj_from_bm(name, bm, [mat], coll, smooth=True)
    o.location = loc
    o.scale = scale
    return o


# ---------------------------------------------------------------- materials

ASSETS = os.environ.get('UMRAH_ASSETS',
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets'))


def tex_path(key, kind):
    p = os.path.join(ASSETS, 'tex', key, kind + '.jpg')
    return p if os.path.exists(p) else None


def pbr_layer(mat, key, size=2.0, normal_strength=0.6, rough_mul=1.0, rough_add=0.0,
              desat=0.0, tint=None, use_color=True):
    """Drive an existing Principled BSDF with scanned PBR maps (box-projected in
    object space, so it works on any mesh without UVs). size = metres per repeat.
    Returns the colour output socket (or None) so callers can multiply on top."""
    col_p, nor_p, rou_p = (tex_path(key, k) for k in ('color', 'normal', 'rough'))
    if not col_p:
        return None
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    b = _bsdf(mat)
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size, 1 / size, 1 / size)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])

    def img(path, noncolor):
        n = N.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            n.image.colorspace_settings.name = 'Non-Color'
        n.projection = 'BOX'
        n.projection_blend = 0.25
        L.new(mp.outputs['Vector'], n.inputs['Vector'])
        return n
    out = None
    if use_color:
        c = img(col_p, False)
        out = c.outputs['Color']
        if desat or tint:
            hsv = N.new('ShaderNodeHueSaturation')
            hsv.inputs['Saturation'].default_value = 1.0 - desat
            L.new(out, hsv.inputs['Color'])
            out = hsv.outputs['Color']
        if tint:
            mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0
            mx.inputs[7].default_value = (*tint, 1)
            L.new(out, mx.inputs[6])
            out = mx.outputs[2]
        L.new(out, b.inputs['Base Color'])
    if rou_p:
        r = img(rou_p, True)
        m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY_ADD'
        m1.inputs[1].default_value = rough_mul; m1.inputs[2].default_value = rough_add
        m1.use_clamp = True
        L.new(r.outputs['Color'], m1.inputs[0])
        L.new(m1.outputs[0], b.inputs['Roughness'])
    if nor_p:
        n = img(nor_p, True)
        nm = N.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = normal_strength
        L.new(n.outputs['Color'], nm.inputs['Color'])
        L.new(nm.outputs['Normal'], b.inputs['Normal'])
    return out


def facade(name, wall=(0.80, 0.74, 0.64), night=False, win_w=1.6, floor_h=3.4, gap=1.0,
           lit=(1.0, 0.78, 0.48), lit_strength=6.0):
    """Building facade with a grid of windows, computed in world space so it
    works on scaled/instanced boxes. Day: dark reflective glass. Night: a random
    mix of warm lit and dark windows."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    out = N['Material Output']
    wall_b = N['Principled BSDF']
    wall_b.inputs['Base Color'].default_value = (*wall, 1)
    wall_b.inputs['Roughness'].default_value = 0.7
    if tex_path('stucco', 'normal'):
        pbr_layer(m, 'stucco', 4.0, normal_strength=0.4, use_color=False, rough_add=0.3)
    glass = N.new('ShaderNodeBsdfPrincipled')
    glass.inputs['Base Color'].default_value = (0.06, 0.09, 0.12, 1)
    glass.inputs['Metallic'].default_value = 0.5
    glass.inputs['Roughness'].default_value = 0.08
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])
    add = N.new('ShaderNodeMath'); add.operation = 'ADD'
    L.new(sep.outputs[0], add.inputs[0]); L.new(sep.outputs[1], add.inputs[1])
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(add.outputs[0], comb.inputs[0]); L.new(sep.outputs[2], comb.inputs[1])
    brick = N.new('ShaderNodeTexBrick')
    brick.offset = 0.0; brick.squash = 1.0
    brick.inputs['Scale'].default_value = 1.0
    brick.inputs['Brick Width'].default_value = win_w + gap
    brick.inputs['Row Height'].default_value = floor_h
    brick.inputs['Mortar Size'].default_value = gap / 2
    brick.inputs['Mortar Smooth'].default_value = 0.0
    brick.inputs['Bias'].default_value = -0.3 if night else 0.0
    brick.inputs['Color1'].default_value = (1, 1, 1, 1)
    brick.inputs['Color2'].default_value = (0.05, 0.05, 0.05, 1)
    brick.inputs['Mortar'].default_value = (0, 0, 0, 1)
    L.new(comb.outputs[0], brick.inputs['Vector'])
    mask = N.new('ShaderNodeMath'); mask.operation = 'GREATER_THAN'; mask.inputs[1].default_value = 0.01
    L.new(brick.outputs['Color'], mask.inputs[0])
    if night:
        bw = N.new('ShaderNodeRGBToBW'); L.new(brick.outputs['Color'], bw.inputs[0])
        st = N.new('ShaderNodeMath'); st.operation = 'MULTIPLY'; st.inputs[1].default_value = lit_strength
        L.new(bw.outputs[0], st.inputs[0])
        glass.inputs['Emission Color'].default_value = (*lit, 1)
        L.new(st.outputs[0], glass.inputs['Emission Strength'])
    mix = N.new('ShaderNodeMixShader')
    L.new(mask.outputs[0], mix.inputs['Fac'])
    L.new(wall_b.outputs[0], mix.inputs[1]); L.new(glass.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def textured(name, key, size=2.0, fallback=(0.8, 0.8, 0.8), rough=0.5, **kw):
    """Principled material from a scanned texture set, falling back to a flat colour."""
    coat = kw.pop('coat', 0.0)
    m = principled(name, fallback, rough=rough, coat=coat)
    pbr_layer(m, key, size, **kw)
    return m


def _bsdf(mat):
    return mat.node_tree.nodes['Principled BSDF']


def principled(name, color, rough=0.5, metal=0.0, sheen=0.0, spec=0.5,
               emission=None, estrength=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = _bsdf(m)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Coat Weight'].default_value = coat
    if emission:
        b.inputs['Emission Color'].default_value = (*emission, 1)
        b.inputs['Emission Strength'].default_value = estrength
    return m


def emissive(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs[0])
    return m


def marble(name, base=(0.86, 0.85, 0.82), vein=(0.62, 0.62, 0.62),
           tile=1.2, rough=0.18, scale=0.35, tex=None, tex_size=1.6, seams=True):
    """Polished white marble with tile seams. Uses a scanned texture set
    (tex key) when present, otherwise procedural veining."""
    if tex and tex_path(tex, 'color'):
        m = principled(name, base, rough=rough, coat=0.0)
        col = pbr_layer(m, tex, tex_size, normal_strength=0.12, rough_mul=0.19, rough_add=0.28)
        if seams:
            nt = m.node_tree; N, L = nt.nodes, nt.links
            tc = N.new('ShaderNodeTexCoord')
            brick = N.new('ShaderNodeTexBrick')
            brick.inputs['Scale'].default_value = 1.0 / tile
            brick.inputs['Mortar Size'].default_value = 0.004
            brick.offset = 0.0
            for k in ('Color1', 'Color2'):
                brick.inputs[k].default_value = (1, 1, 1, 1)
            brick.inputs['Mortar'].default_value = (0.86, 0.86, 0.86, 1)
            L.new(tc.outputs['Object'], brick.inputs['Vector'])
            mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0
            L.new(col, mx.inputs[6]); L.new(brick.outputs['Color'], mx.inputs[7])
            L.new(mx.outputs[2], _bsdf(m).inputs['Base Color'])
        return m
    m = principled(name, base, rough=rough, coat=0.25)
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = _bsdf(m)
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    noise = N.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3.0
    noise.inputs['Detail'].default_value = 12.0
    noise.inputs['Distortion'].default_value = 2.2
    L.new(mp.outputs['Vector'], noise.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (*vein, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (*base, 1)
    L.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    # tile seams
    brick = N.new('ShaderNodeTexBrick')
    brick.inputs['Scale'].default_value = 1.0 / tile
    brick.inputs['Mortar Size'].default_value = 0.006
    brick.offset = 0.0
    L.new(tc.outputs['Object'], brick.inputs['Vector'])
    brick.inputs['Color1'].default_value = (1, 1, 1, 1)
    brick.inputs['Color2'].default_value = (1, 1, 1, 1)
    brick.inputs['Mortar'].default_value = (0.9, 0.9, 0.9, 1)
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    L.new(ramp.outputs['Color'], mix.inputs[6])
    L.new(brick.outputs['Color'], mix.inputs[7])
    L.new(mix.outputs[2], b.inputs['Base Color'])
    return m


def kiswa_black(name='Kiswa'):
    """Black silk with a faint woven pattern (no lettering is reproduced)."""
    m = principled(name, (0.008, 0.008, 0.009), rough=0.6, sheen=0.2, spec=0.12)
    if tex_path('satin', 'normal'):
        pbr_layer(m, 'satin', 0.25, normal_strength=0.5, rough_mul=0.4, rough_add=0.5, use_color=False)
        return m
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = _bsdf(m)
    tc = N.new('ShaderNodeTexCoord')
    vor = N.new('ShaderNodeTexVoronoi')
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.inputs['Scale'].default_value = 1.6
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    L.new(vor.outputs['Distance'], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def gold_ornament(name, coverage=0.06, band_half=None, scale=2.2):
    """Black cloth with an abstract gold arabesque lattice.

    Deliberately abstract: the real kiswa carries Quranic calligraphy, which
    should be produced (or licensed) with care later, not invented by code.
    coverage: thickness of gold lines (0..0.5). band_half: if given, adds gold
    border strips at local z = +-band_half.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    out = N['Material Output']
    black = N['Principled BSDF']
    black.inputs['Base Color'].default_value = (0.012, 0.012, 0.013, 1)
    black.inputs['Roughness'].default_value = 0.55
    black.inputs['Sheen Weight'].default_value = 0.7
    gold = N.new('ShaderNodeBsdfPrincipled')
    gold.inputs['Base Color'].default_value = (1.0, 0.72, 0.30, 1)
    gold.inputs['Metallic'].default_value = 1.0
    gold.inputs['Roughness'].default_value = 0.32
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    add = N.new('ShaderNodeMath'); add.operation = 'ADD'
    L.new(sep.outputs[0], add.inputs[0]); L.new(sep.outputs[1], add.inputs[1])
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(add.outputs[0], comb.inputs[0])
    zs = N.new('ShaderNodeMath'); zs.operation = 'MULTIPLY'; zs.inputs[1].default_value = 1.8
    L.new(sep.outputs[2], zs.inputs[0]); L.new(zs.outputs[0], comb.inputs[1])
    vor = N.new('ShaderNodeTexVoronoi')
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.voronoi_dimensions = '2D'
    vor.inputs['Scale'].default_value = scale
    vor.inputs['Randomness'].default_value = 0.15
    L.new(comb.outputs[0], vor.inputs['Vector'])
    lt = N.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = coverage
    L.new(vor.outputs['Distance'], lt.inputs[0])
    mask = lt
    if band_half is not None:
        ab = N.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
        L.new(sep.outputs[2], ab.inputs[0])
        gt = N.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
        gt.inputs[1].default_value = band_half - 0.09
        L.new(ab.outputs[0], gt.inputs[0])
        mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
        L.new(lt.outputs[0], mx.inputs[0]); L.new(gt.outputs[0], mx.inputs[1])
        mask = mx
    mix = N.new('ShaderNodeMixShader')
    L.new(mask.outputs[0], mix.inputs['Fac'])
    L.new(black.outputs[0], mix.inputs[1])
    L.new(gold.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def random_color_mat(name, colors, rough=0.6, sheen=0.4):
    """Per-object colour variation through Object Info > Random."""
    m = principled(name, colors[0], rough=rough, sheen=sheen)
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    info = N.new('ShaderNodeObjectInfo')
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    els[0].position = 0.0; els[0].color = (*colors[0], 1)
    els[1].position = 1.0 / len(colors); els[1].color = (*colors[1 % len(colors)], 1)
    for i, c in enumerate(colors[2:], start=2):
        e = els.new(i / len(colors)); e.color = (*c, 1)
    L.new(info.outputs['Random'], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], _bsdf(m).inputs['Base Color'])
    return m


# ---------------------------------------------------------------- shapes

def annulus(name, r_in, r_out, z, thick, mat, segs=128, coll=None):
    bm = bmesh.new()
    rings = []
    for (r, zz) in [(r_in, z), (r_out, z), (r_out, z - thick), (r_in, z - thick)]:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs),
                                    r * math.sin(2 * math.pi * i / segs), zz))
                      for i in range(segs)])
    for k in range(4):
        a, b = rings[k], rings[(k + 1) % 4]
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    return obj_from_bm(name, bm, [mat], coll)


def arch_profile(span, spring, pointed=0.18, n=14):
    """Points (t, z) of an arch from t=0 to t=span. pointed>0 -> Islamic pointed arch."""
    pts = []
    r = span / 2 * (1 + pointed)
    for i in range(n + 1):
        t = i / n
        # two circular arcs meeting at the crown
        x = span * t
        if t <= 0.5:
            cxx = r
            dx = x - cxx
        else:
            cxx = span - r
            dx = x - cxx
        z = spring + math.sqrt(max(r * r - dx * dx, 0.0))
        pts.append((x, z))
    return pts


def arcade_bays(bm, p0, p1, z0, height, pier=1.0, spring_frac=0.6, pointed=0.18):
    """Add one bay's spandrel (wall above an arch) between ground points p0->p1."""
    p0 = Vector((p0[0], p0[1], 0)); p1 = Vector((p1[0], p1[1], 0))
    d = p1 - p0
    L = d.length
    u = d.normalized()
    span = L - 2 * pier
    spring = height * spring_frac
    prof = arch_profile(span, spring, pointed)
    crown = max(z for _, z in prof)
    if crown > height - 0.4:
        s = (height - 0.4 - spring) / (crown - spring)
        prof = [(t, spring + (z - spring) * s) for t, z in prof]
    top = height
    # piers (flat faces at each end)
    for a, b in [(0, pier), (L - pier, L)]:
        q = [p0 + u * a, p0 + u * b]
        v = [bm.verts.new((q[0].x, q[0].y, z0)), bm.verts.new((q[1].x, q[1].y, z0)),
             bm.verts.new((q[1].x, q[1].y, z0 + top)), bm.verts.new((q[0].x, q[0].y, z0 + top))]
        bm.faces.new(v)
    # spandrel strips
    for (t0, za), (t1, zb) in zip(prof[:-1], prof[1:]):
        a = p0 + u * (pier + t0); b = p0 + u * (pier + t1)
        v = [bm.verts.new((a.x, a.y, z0 + za)), bm.verts.new((b.x, b.y, z0 + zb)),
             bm.verts.new((b.x, b.y, z0 + top)), bm.verts.new((a.x, a.y, z0 + top))]
        bm.faces.new(v)


def solidify(obj, thick, offset=0.0):
    mod = obj.modifiers.new('solid', 'SOLIDIFY')
    mod.thickness = thick
    mod.offset = offset
    return mod


def arc_wall(name, cx, cy, a, b, ang0, ang1, thick, h, mat, segs=48, coll=None):
    """Elliptic arc wall (used for Hijr Ismail)."""
    bm = bmesh.new()
    rows = []
    for k, (ra, rb, z) in enumerate([(a, b, 0), (a, b, h), (a + thick, b + thick, h), (a + thick, b + thick, 0)]):
        row = []
        for i in range(segs + 1):
            t = ang0 + (ang1 - ang0) * i / segs
            row.append(bm.verts.new((cx + ra * math.cos(t), cy + rb * math.sin(t), z)))
        rows.append(row)
    for k in range(3):
        A, B = rows[k], rows[k + 1]
        for i in range(segs):
            bm.faces.new((A[i], A[i + 1], B[i + 1], B[i]))
    for end in (0, segs):
        bm.faces.new([rows[k][end] for k in range(4)])
    return obj_from_bm(name, bm, [mat], coll)


def rock(name, size, loc, mat, seed=1, coll=None):
    """Displaced icosphere for the rocky outcrops of Safa and Marwah."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    rnd = random.Random(seed)
    from mathutils import noise
    off = Vector((rnd.random() * 10, rnd.random() * 10, rnd.random() * 10))
    for v in bm.verts:
        n = noise.fractal(v.co * 1.7 + off, 0.6, 2.0, 5)
        v.co *= 1.0 + 0.32 * n
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], max(v.co.z, -0.2) * size[2]))
    o = obj_from_bm(name, bm, [mat], coll, smooth=True)
    o.location = loc
    return o


# ---------------------------------------------------------------- pilgrims

def make_pilgrim_meshes(coll, realtime=False):
    from pilgrims import make
    return make(coll, realtime=realtime)


def pick(variants, rnd):
    tot = sum(w for _, w in variants)
    x = rnd.random() * tot
    for o, w in variants:
        x -= w
        if x <= 0:
            return o
    return variants[-1][0]


# ---------------------------------------------------------------- camera / world / render

def pano_camera(name, loc, forward_deg):
    """Equirectangular camera. forward_deg = world heading of the image centre
    (0 = +X, 90 = +Y, counter-clockwise)."""
    cam = bpy.data.cameras.new(name)
    cam.type = 'PANO'
    cam.panorama_type = 'EQUIRECTANGULAR'
    cam.clip_start = 0.05
    cam.clip_end = 5000
    o = link(bpy.data.objects.new(name, cam))
    o.location = loc
    f = Vector((math.cos(math.radians(forward_deg)), math.sin(math.radians(forward_deg)), 0))
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = f.to_track_quat('-Z', 'Y')
    o['forward_deg'] = forward_deg
    return o


def view_angles(cam_obj, target):
    """(yaw, pitch) in degrees for the web viewer: yaw 0 = image centre,
    positive = to the right; pitch positive = up."""
    d = Vector(target) - cam_obj.location
    heading = math.degrees(math.atan2(d.y, d.x))
    yaw = (cam_obj['forward_deg'] - heading + 540) % 360 - 180
    pitch = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
    return round(yaw, 1), round(pitch, 1)


def sky_world(sun_elev_deg=32, sun_az_deg=45, strength=1.0, sun_strength=4.5):
    s = bpy.context.scene
    w = bpy.data.worlds.new('Sky')
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = False
    sky.sun_elevation = math.radians(sun_elev_deg)
    sky.sun_rotation = math.radians(90 - sun_az_deg)
    bg = nt.nodes['Background']
    bg.inputs['Strength'].default_value = strength
    tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1.0
    tint.inputs[7].default_value = (1.0, 0.9, 0.78, 1)
    nt.links.new(sky.outputs[0], tint.inputs[6])
    nt.links.new(tint.outputs[2], bg.inputs[0])
    # Sun lamp for crisp shadows
    ld = bpy.data.lights.new('Sun', 'SUN')
    ld.energy = sun_strength
    ld.angle = math.radians(0.6)
    ld.color = (1.0, 0.95, 0.86)
    lo = link(bpy.data.objects.new('Sun', ld))
    el, az = math.radians(sun_elev_deg), math.radians(sun_az_deg)
    to_sun = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    lo.rotation_mode = 'QUATERNION'
    lo.rotation_quaternion = (-to_sun).to_track_quat('-Z', 'Y')
    return w


def hdri_world(sun_az_deg=40.0, strength=1.0, sun_boost=True):
    """Image-based sky (Poly Haven HDRI), rotated so its sun sits at sun_az_deg
    (0 = +X, counter-clockwise). Returns (azimuth, elevation) of the sun, or None
    when the HDRI file is missing (callers then fall back to sky_world)."""
    path = os.path.join(ASSETS, 'sky.hdr')
    if not os.path.exists(path):
        return None
    import numpy as np
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    lum = px[..., 0] * 0.2126 + px[..., 1] * 0.7152 + px[..., 2] * 0.0722
    y, x = np.unravel_index(int(np.argmax(lum)), lum.shape)   # row 0 = bottom
    u, v = (x + 0.5) / w, (y + 0.5) / h
    # Blender equirect lookup: u = -atan2(dir.y, dir.x) / 2pi + 0.5
    src_az = (0.5 - u) * 2 * math.pi
    elev = (v - 0.5) * math.pi
    s = bpy.context.scene
    wd = bpy.data.worlds.new('HDRI')
    s.world = wd
    wd.use_nodes = True
    nt = wd.node_tree
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = img
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    # rotating the lookup vector by -delta moves the sky by +delta
    delta = math.radians(sun_az_deg) - src_az
    mp.inputs['Rotation'].default_value = (0, 0, -delta)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    bg = nt.nodes['Background']
    bg.inputs['Strength'].default_value = strength
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    return math.degrees(src_az + delta), math.degrees(elev)


def night_world(strength=0.6):
    """Night sky: Poly Haven night HDRI if present, else a deep blue gradient."""
    path = os.path.join(ASSETS, 'sky_night.hdr')
    s = bpy.context.scene
    w = bpy.data.worlds.new('Night'); s.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    if os.path.exists(path):
        env = nt.nodes.new('ShaderNodeTexEnvironment')
        env.image = bpy.data.images.load(path, check_existing=True)
        nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    else:
        tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Generated'], sep.inputs[0])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.035, 0.03, 0.04, 1)
        ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (0.004, 0.008, 0.025, 1)
        nt.links.new(sep.outputs[2], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    return w


def spot(name, loc, target, energy, angle_deg=70, blend=0.6, color=(1.0, 0.94, 0.86), radius=0.6, coll=None):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = energy; ld.spot_size = math.radians(angle_deg); ld.spot_blend = blend
    ld.color = color; ld.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, ld), coll)
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    return o


def flat_world(color, strength):
    s = bpy.context.scene
    w = bpy.data.worlds.new('Flat')
    s.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (*color, 1)
    bg.inputs['Strength'].default_value = strength
    return w


def render_settings(res_x, samples, exposure=0.0):
    s = bpy.context.scene
    s.render.resolution_x = res_x
    s.render.resolution_y = res_x // 2
    s.render.resolution_percentage = 100
    c = s.cycles
    c.device = 'CPU'
    want = os.environ.get('UMRAH_DEVICE', 'CPU').upper()     # CPU | OPTIX | CUDA
    if want != 'CPU':
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for kind in ([want] + [k for k in ('OPTIX', 'CUDA') if k != want]):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
            except Exception:
                continue
            gpus = [d for d in prefs.devices if d.type == kind]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == kind
                c.device = 'GPU'
                print('Cycles device:', kind, [d.name for d in gpus], flush=True)
                break
        if c.device != 'GPU':
            raise RuntimeError(f'Requested {want} GPU is unavailable; refusing a silent CPU render')
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.03
    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.max_bounces = 6
    c.diffuse_bounces = 3
    c.glossy_bounces = 2
    c.transmission_bounces = 2
    c.transparent_max_bounces = 4
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.sample_clamp_indirect = 8.0
    s.render.use_persistent_data = True
    s.view_settings.view_transform = 'AgX'
    try:
        s.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    s.view_settings.exposure = exposure
    s.render.image_settings.file_format = 'JPEG'
    s.render.image_settings.quality = 88
