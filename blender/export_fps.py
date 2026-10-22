"""Export the Haram and Mas'a scenes as GLB files for the real-time 3D Explore mode.

    python export_fps.py OUT_DIR [ASSETS_DIR]

Writes OUT_DIR/haram.glb, OUT_DIR/masa.glb, OUT_DIR/pilgrims.glb and OUT_DIR/tex/*.jpg
(only used during export: textures are embedded in the GLBs).

What changes compared to the rendered scenes:
- Procedural Cycles materials are replaced by exporter-friendly ones (image textures on
  box-projected UVs, flat colours, emission), since glTF cannot carry node graphs.
- Linked duplicates (columns, balusters, lamps, hotels...) are grouped under empties so
  the exporter writes them with GPU instancing (EXT_mesh_gpu_instancing).
- Pilgrims are left out of the scenes and exported once in pilgrims.glb; the web app
  places and animates the crowd itself.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector

args = sys.argv[1:]
if '--' in args:
    args = args[args.index('--') + 1:]
OUT = os.path.abspath(args[0])
if len(args) > 1:
    os.environ['UMRAH_ASSETS'] = os.path.abspath(args[1])
os.makedirs(os.path.join(OUT, 'tex'), exist_ok=True)

import build_scene as bs
import common
from PIL import Image, ImageDraw

TEXRES = 1024

# ------------------------------------------------------------------ textures

def tex_file(key, kind, tint=None, desat=0.0, name=None):
    """1K JPEG copy of an asset texture, optionally tinted (glTF has no colour nodes)."""
    src = common.tex_path(key, kind)
    if not src:
        return None
    out = os.path.join(OUT, 'tex', f'{name or key}_{kind}.jpg')
    if not os.path.exists(out):
        im = Image.open(src).convert('RGB').resize((TEXRES, TEXRES), Image.LANCZOS)
        if kind == 'color' and (tint or desat):
            import numpy as np
            a = np.asarray(im).astype('float32') / 255.0
            if desat:
                g = a.mean(axis=2, keepdims=True)
                a = a * (1 - desat) + g * desat
            if tint:
                a = a * np.array(tint, dtype='float32')
            im = Image.fromarray((a.clip(0, 1) * 255).astype('uint8'))
        im.save(out, quality=85)
    return out


def lattice_tex(name, line=0.08, border=None, cells=4, size=512):
    """Abstract gold arabesque lattice on black silk (placeholder, no calligraphy)."""
    out = os.path.join(OUT, 'tex', f'{name}.jpg')
    if os.path.exists(out):
        return out
    im = Image.new('RGB', (size, size), (6, 6, 7))
    d = ImageDraw.Draw(im)
    gold = (214, 166, 82)
    w = max(2, int(size * line / cells))
    step = size / cells
    for i in range(-cells, 2 * cells + 1):
        x = i * step
        d.line([(x, 0), (x + size, size)], fill=gold, width=w)
        d.line([(x, size), (x + size, 0)], fill=gold, width=w)
    for i in range(cells + 1):
        for j in range(cells + 1):
            cx, cy = i * step, j * step
            r = step * 0.16
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=gold, width=w)
    if border:
        bh = int(size * border)
        d.rectangle([0, 0, size, bh], fill=gold)
        d.rectangle([0, size - bh, size, size], fill=gold)
        d.rectangle([0, bh + 6, size, bh + 10], fill=(150, 110, 50))
        d.rectangle([0, size - bh - 10, size, size - bh - 6], fill=(150, 110, 50))
    im.save(out, quality=88)
    return out


# ------------------------------------------------------------------ materials

def new_mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, emission=None, estrength=0.0,
            img=None, nrm=None, nstrength=0.5, alpha=1.0):
    m = bpy.data.materials.new('X_' + name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emission:
        b.inputs['Emission Color'].default_value = (*emission, 1)
        b.inputs['Emission Strength'].default_value = estrength
    if img:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(img, check_existing=True)
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if nrm:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(nrm, check_existing=True)
        t.image.colorspace_settings.name = 'Non-Color'
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = nstrength
        nt.links.new(t.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    return m


def spec_for(name):
    """(material factory, uv tile size in metres or None) for an original material name."""
    n = name.split('.')[0]
    T = lambda key, **kw: (tex_file(key, 'color', **kw), tex_file(key, 'normal'))
    if n in ('Mataf marble', 'Masa marble'):
        c, nr = T('marble_white')
        return (lambda: new_mat(n, rough=0.22, img=c, nrm=nr, nstrength=0.25)), 2.4
    if n in ('Arcade marble', 'Masa wall'):
        c, nr = T('marble_warm')
        return (lambda: new_mat(n, rough=0.35, img=c, nrm=nr, nstrength=0.3)), 2.0
    if n == 'Granite':
        c, nr = T('granite', tint=(0.45, 0.42, 0.42))
        return (lambda: new_mat(n, rough=0.25, img=c, nrm=nr)), 1.2
    if n in ('Cream stone', 'Ceiling'):
        c, nr = T('stucco', tint=(0.95, 0.88, 0.76) if n == 'Cream stone' else (1.0, 0.97, 0.92))
        return (lambda: new_mat(n, rough=0.7, img=c, nrm=nr, nstrength=0.4)), 4.0
    if n == 'Rock':
        c, nr = T('rock', tint=(0.42, 0.36, 0.32), desat=0.35)
        return (lambda: new_mat(n, rough=0.85, img=c, nrm=nr, nstrength=1.0)), 2.5
    if n == 'Kiswa':
        c, nr = (None, tex_file('satin', 'normal'))
        return (lambda: new_mat(n, color=(0.012, 0.012, 0.013), rough=0.75, nrm=nr, nstrength=0.4)), 0.25
    if n == 'Hizam':
        return (lambda: new_mat(n, color=(1, 1, 1), rough=0.4, metal=0.6, img=lattice_tex('hizam', 0.07, 0.14, 2))), 0.95
    if n in ('Panel ornament', 'Sitara'):
        return (lambda: new_mat(n, color=(1, 1, 1), rough=0.4, metal=0.6, img=lattice_tex('panel', 0.1, None, 3))), 0.9
    if n == 'Maqam lattice':
        return (lambda: new_mat(n, color=(1, 1, 1), rough=0.35, metal=0.7, img=lattice_tex('maqam', 0.2, None, 3))), 0.5
    if n in ('Hotels', 'Tower facade'):
        col = (0.74, 0.70, 0.63) if n == 'Hotels' else (0.80, 0.74, 0.64)
        return (lambda: new_mat(n, color=col, rough=0.8)), None
    return None, None


def copy_simple(m):
    """Principled-only material: keep its constant values, drop node graphs."""
    b = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    em = None
    out = m.node_tree.nodes.get('Material Output') if m.use_nodes else None
    if out and out.inputs['Surface'].links:
        src = out.inputs['Surface'].links[0].from_node
        if src.type == 'EMISSION':
            em = (tuple(src.inputs['Color'].default_value[:3]), src.inputs['Strength'].default_value)
    if em:
        return new_mat(m.name, color=(0, 0, 0), rough=0.6, emission=em[0], estrength=em[1])
    if not b:
        return new_mat(m.name)
    g = lambda k: b.inputs[k].default_value
    es = g('Emission Strength')
    return new_mat(m.name, color=tuple(g('Base Color')[:3]), rough=g('Roughness'), metal=g('Metallic'),
                   emission=tuple(g('Emission Color')[:3]) if es > 0 else None, estrength=es)


def box_uv(me, size):
    """Box-projected UVs in object space (u,v in tiles of `size` metres), offset by half a tile."""
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co
            if ax == 2:
                u, v = co.x, co.y
            elif ax == 0:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            l[uv].uv = (u / size + 0.5, v / size + 0.5)
    bm.to_mesh(me)
    bm.free()


# ------------------------------------------------------------------ scene prep

def prepare():
    sc = bpy.context.scene
    # drop lights, cameras, pilgrims
    for o in list(bpy.data.objects):
        if o.type in ('LIGHT', 'CAMERA'):
            bpy.data.objects.remove(o, do_unlink=True)
    pc = bpy.data.collections.get('Pilgrims')
    if pc:
        for o in list(pc.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    # apply modifiers so UVs are computed on final geometry
    dg = bpy.context.evaluated_depsgraph_get()
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.modifiers]:
        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        o.modifiers.clear()
        o.data = me
    # replace materials (per mesh data, so instances share the result)
    cache = {}
    for me in {o.data for o in bpy.data.objects if o.type == 'MESH'}:
        sizes = []
        for i, m in enumerate(me.materials):
            if m is None:
                continue
            if m.name not in cache:
                fac, size = spec_for(m.name)
                cache[m.name] = (fac() if fac else copy_simple(m), size)
            nm, size = cache[m.name]
            me.materials[i] = nm
            if size:
                sizes.append(size)
        if sizes:
            box_uv(me, min(sizes))
    # group linked duplicates under empties for GPU instancing
    groups = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent is None and not o.hide_render:
            groups.setdefault(o.data.name, []).append(o)
    n = 0
    for name, objs in groups.items():
        if len(objs) < 4:
            continue
        e = bpy.data.objects.new('INST_' + name, None)
        sc.collection.objects.link(e)
        for o in objs:
            mw = o.matrix_world.copy()
            o.parent = e
            o.matrix_world = mw
        n += 1
    tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render)
    print(f'prepared: {len(bpy.data.objects)} objects, {n} instance groups, ~{tris} polygons (incl. instances)', flush=True)


def export(path, selection=False):
    kw = dict(filepath=path, export_format='GLB', export_apply=True, export_cameras=False,
              export_lights=False, export_image_format='JPEG', export_yup=True,
              use_renderable=not selection, use_selection=selection)
    for k, v in (('export_gpu_instances', True), ('export_jpeg_quality', 82)):
        kw[k] = v
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop('export_jpeg_quality', None)
        bpy.ops.export_scene.gltf(**kw)
    print(f'wrote {path}  {os.path.getsize(path) / 1e6:.1f} MB', flush=True)


if __name__ == '__main__':
    os.environ.pop('UMRAH_TIME', None)
    bs.build_haram(); prepare(); export(os.path.join(OUT, 'haram.glb'))
    bs.build_masa(); prepare(); export(os.path.join(OUT, 'masa.glb'))
    # pilgrims: the four faceless variants, one mesh each, at the origin
    common.reset()
    coll = common.collection('Pilgrims')
    vs = common.make_pilgrim_meshes(coll)
    for o, w in vs:
        o.hide_render = False; o.hide_viewport = False
        for i, m in enumerate(o.data.materials):
            o.data.materials[i] = copy_simple(m)
    bpy.ops.object.select_all(action='DESELECT')
    for o, w in vs:
        o.select_set(True)
    export(os.path.join(OUT, 'pilgrims.glb'), selection=True)
