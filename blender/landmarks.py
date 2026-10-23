"""Shared Kaaba-area masters for panorama and glTF derivatives.

Dimensions without survey evidence remain approximations (see docs/visual-reference-ledger.md).
Embroidery regions deliberately contain no invented Arabic lettering.
"""
import math
import os
import bpy
import bmesh
from mathutils import Vector
from common import box, cylinder, sphere, arc_wall, principled, kiswa_black, obj_from_bm


def material(name, color, role, **kw):
    m = principled(name, color, **kw)
    m['umrahRole'] = role
    return m


def bevel(obj, width=0.025, segments=2):
    m = obj.modifiers.new('Edge highlights', 'BEVEL')
    m.width = width
    m.segments = segments
    return obj


def rod(name, a, b, radius, mat, coll, segments=8):
    a, b = Vector(a), Vector(b)
    o = cylinder(name, radius, (b - a).length, a, mat, segs=segments, coll=coll)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    return o


def cloth_face(name, center, tangent, normal, width, height, mat, coll):
    """Actual shallow drape geometry; metre-scaled UVs survive glTF export."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    rows = []
    nx, nz = 96, 16
    c, u, n = Vector(center), Vector(tangent), Vector(normal)
    for iz in range(nz + 1):
        z = iz * height / nz
        row = []
        for ix in range(nx + 1):
            x = (ix / nx - .5) * width
            fade = math.sin(math.pi * ix / nx) ** .4
            lower = .3 + .7 * (1 - z / height) ** 3
            folds = (.018 * math.sin(x * 12.5 + .15 * math.sin(z * .8))
                     + .008 * math.sin(x * 27.0 + z * .18)) * lower * fade
            seam = .006 * math.exp(-((math.sin(x * math.pi / 1.45)) / .075) ** 2)
            row.append(bm.verts.new(c + u * x + Vector((0, 0, z)) + n * (.025 + folds + seam)))
        rows.append(row)
    for iz in range(nz):
        for ix in range(nx):
            f = bm.faces.new((rows[iz][ix], rows[iz + 1][ix], rows[iz + 1][ix + 1], rows[iz][ix + 1]))
            for loop, (xx, zz) in zip(f.loops, ((ix, iz), (ix, iz + 1), (ix + 1, iz + 1), (ix + 1, iz))):
                loop[uv].uv = (xx * width / nx / .25, zz * height / nz / .25)
    bm.normal_update()
    o = obj_from_bm(name, bm, [mat], coll, smooth=True)
    o.data['umrahUV'] = True
    return o


def frame(name, x, y, z, w, h, depth, mat, coll, rail=.035):
    # Front faces face +y. A modest frame profile catches light at walking range.
    for dx in (-w / 2, w / 2):
        bevel(box(name + ' stile', (rail, depth, h), (x + dx, y, z), mat, coll), .008)
    for dz in (-h / 2, h / 2):
        bevel(box(name + ' rail', (w, depth, rail), (x, y, z + dz), mat, coll), .008)


def sitara(x, y, bottom, coll):
    """Trace the open curtain in the CC0 photograph, preserving its Arabic UVs.

    Uses the photographed 2016 artwork. No lettering is generated or mirrored.
    The source's door and people are outside this mesh's UV silhouette.
    """
    image_path=os.path.join(os.path.dirname(__file__),'artwork','sitara-2016.jpg')
    mat=material('Sitara sourced 2016 artwork',(1,1,1),'embroidery',rough=.62,metal=.55)
    mat['umrahTexture']=image_path
    nt=mat.node_tree;tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(image_path,check_existing=True)
    nt.links.new(tex.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
    points=((0,0),(2349,0),(2349,4320),(1445,4320),(1440,3040),(1320,2630),(1240,2160),
            (1160,2160),(1030,2630),(940,3040),(920,4320),(0,4320))
    bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap')
    # Viewed from +y with z up, screen-right is WORLD -x. Keeping +x here
    # mirrors Arabic even when the UV coordinates themselves are unreversed.
    verts=[bm.verts.new((x-(px/2349-.5)*3.4,y,bottom+(1-py/4320)*6.65)) for px,py in points]
    face=bm.faces.new(verts)
    for loop,(px,py) in zip(face.loops,points):loop[uv].uv=(px/2349,1-py/5184)
    bm.normal_update()
    if face.normal.y<0:face.normal_flip()
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    o=obj_from_bm('Sitara photographed embroidery',bm,[mat],coll)
    o.data['umrahUV']=True
    o['artworkSource']='CC0 Abdullah Shakoor, 2016-05-07; see artwork/provenance.json'


def black_stone(kx, ky, coll, silver, stone):
    c = Vector((kx + .055, ky + .055, 1.5))
    u, n = Vector((-1, 1, 0)).normalized(), Vector((1, 1, 0)).normalized()
    # Sculpted asymmetric sheet surround, with a rolled inner lip and a recess.
    bm = bmesh.new()
    rings = []
    for rx, rz, depth in ((.355, .48, -.02), (.33, .45, .065), (.235, .325, .105), (.19, .275, .012)):
        row = []
        for j in range(64):
            a = j * math.tau / 64
            wobble = 1 + .028 * math.sin(3 * a) + .018 * math.cos(5 * a)
            row.append(bm.verts.new(c + u * (rx * math.cos(a) * wobble) + Vector((0, 0, rz * math.sin(a))) + n * depth))
        rings.append(row)
    for a, b in zip(rings, rings[1:]):
        for j in range(64):
            k = (j + 1) % 64
            bm.faces.new((a[j], a[k], b[k], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    obj_from_bm('Black Stone sculpted silver surround', bm, [silver], coll, smooth=True)
    o = sphere('Black Stone recessed surface', .205, c - n * .035, stone, coll=coll, segs=32, rings=16)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = n.to_track_quat('Z', 'Y')
    o.scale = (1, 1.38, .22)
    # Fragment boundaries are visual approximations, not a scan of the sacred stone.
    for j, (x, z, r) in enumerate(((-.075,.11,.062),(.045,.13,.052),(-.09,-.025,.075),(.055,.005,.068),(.01,-.13,.072))):
        o = sphere('Black Stone surface fragment', r, c + u*x + Vector((0,0,z)) - n*.005, stone, coll=coll, segs=12, rings=8)
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = n.to_track_quat('Z', 'Y'); o.scale = (1, 1.1, .12)


def maqam(position, coll, gold, marble, granite):
    x, y, _ = position
    cylinder('Maqam marble plinth', .94, .16, (x,y,.01), marble, segs=8, coll=coll, smooth=False)
    cylinder('Maqam green granite inset', .80, .11, (x,y,.17), granite, segs=8, coll=coll, smooth=False)
    for z, r in ((.28,.73),(.36,.70),(1.82,.70),(1.94,.75)):
        bevel(cylinder('Maqam moulding', r, .055, (x,y,z), gold, segs=8, coll=coll, smooth=False), .012)
    glass = material('Maqam clear glass', (.72,.82,.80), 'glass', rough=.14, spec=.5)
    b = glass.node_tree.nodes['Principled BSDF']; b.inputs['Alpha'].default_value=.18
    if hasattr(glass, 'surface_render_method'): glass.surface_render_method='DITHERED'
    elif hasattr(glass, 'blend_method'): glass.blend_method='BLEND'
    cylinder('Maqam glass enclosure', .655, 1.45, (x,y,.36), glass, segs=8, coll=coll, smooth=False)
    stone = material('Maqam protected stone', (.40,.29,.17), 'stone', rough=.78)
    bevel(box('Maqam protected stone', (.50,.50,.50), (x,y,.57), stone, coll), .035)
    # Open mesh, rather than an opaque cylinder painted with a lattice texture.
    for i in range(8):
        a, b = i*math.tau/8, (i+1)*math.tau/8
        p = Vector((x+.69*math.cos(a),y+.69*math.sin(a),.36))
        q = Vector((x+.69*math.cos(b),y+.69*math.sin(b),.36))
        rod('Maqam corner post', p, p+Vector((0,0,1.49)), .027, gold, coll)
        for k in range(1,5):
            v = p.lerp(q,k/5)
            rod('Maqam fine grille',v,v+Vector((0,0,1.44)),.009,gold,coll,6)
        for z in (.47,.77,1.07,1.37,1.67):
            rod('Maqam grille cross rail',(p.x,p.y,z),(q.x,q.y,z),.012,gold,coll,6)
    sphere('Maqam gilded crown', .735, (x,y,1.96), gold, (1,1,.59), coll, segs=32,rings=16)
    cylinder('Maqam crown neck', .12,.15,(x,y,2.37),gold,segs=16,coll=coll,r2=.065)
    sphere('Maqam finial',.065,(x,y,2.56),gold,(1,1,1.7),coll,segs=12,rings=8)


def build(kx, ky, kh, maqam_position, coll, marble, granite):
    silk = kiswa_black(); silk['umrahRole']='cloth'
    gold = material('Landmark gold', (.83,.51,.13), 'gold', rough=.29, metal=1)
    silver = material('Black Stone silver', (.82,.84,.86), 'silver', rough=.18, metal=1)
    stone = material('Black Stone', (.025,.017,.015), 'stone', rough=.29)
    dark = material('Kiswa reserved artwork', (.009,.009,.010), 'cloth', rough=.76, sheen=.25)
    # Rounded backing eliminates razor-sharp highlights through the cloth corners.
    bevel(box('Kaaba backing', (2*kx-.035,2*ky-.035,kh), (0,0,kh/2), silk, coll), .045)
    for label, c, u, n, w in (
        ('door',(0,ky,0),(1,0,0),(0,1,0),2*kx),
        ('east',(kx,0,0),(0,-1,0),(1,0,0),2*ky),
        ('west',(0,-ky,0),(-1,0,0),(0,-1,0),2*kx),
        ('hijr',(-kx,0,0),(0,1,0),(-1,0,0),2*ky)):
        cloth_face('Kiswa drape '+label,c,u,n,w,kh,silk,coll)
    # Sloping marble shadharwan, rather than a vertical rectangular step.
    bm=bmesh.new(); rings=[]
    for pad,z in ((.40,.015),(.085,.32)):
        rings.append([bm.verts.new((sx*(kx+pad),sy*(ky+pad),z)) for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))])
    for j in range(4): bm.faces.new((rings[0][j],rings[0][(j+1)%4],rings[1][(j+1)%4],rings[1][j]))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bevel(obj_from_bm('Shadharwan sloping marble',bm,[marble],coll),.015)
    bevel(box('Roof parapet',(2*kx+.045,2*ky+.045,.22),(0,0,kh+.1),dark,coll),.025)
    # Correct material separation; artwork remains explicitly pending in the ledger.
    band_z, band_h = kh*.68, .78
    box('Hizam textile',(2*kx+.085,2*ky+.085,band_h),(0,0,band_z),dark,coll)
    for z in (band_z-band_h/2+.055,band_z+band_h/2-.055):
        for d in (-.022,.022):
            box('Hizam embroidery border',(2*kx+.10,2*ky+.10,.012),(0,0,z+d),gold,coll)
    # Separate solid gold double door: authority documents 1.71 x 3.18 m.
    dx, dy, base, dw, dh = 2.3, ky+.092, 2.1, 1.71, 3.18
    bevel(box('Kaaba gold door',(dw,.12,dh),(dx,dy,base+dh/2),gold,coll),.018)
    recess=material('Door recessed gold',(.49,.27,.065),'gold',rough=.38,metal=1)
    for sx in (-1,1):
        for z,h in ((base+.65,.92),(base+1.81,1.10),(base+2.78,.48)):
            px=dx+sx*dw*.25
            box('Door recessed panel',(.61,.015,h),(px,dy+.069,z),recess,coll)
            frame('Door raised moulding',px,dy+.085,z,.64,h+.03,.04,gold,coll,.026)
    box('Door central joint',(.014,.008,dh-.08),(dx,dy+.08,base+dh/2),recess,coll)
    frame('Door surround',dx,dy+.025,base+dh/2,dw+.13,dh+.13,.16,gold,coll,.065)
    bevel(box('Door threshold',(dw+.2,.37,.13),(dx,dy+.09,base-.015),gold,coll),.02)
    for sx in (-1,1):
        sphere('Door handle',.035,(dx+sx*.11,dy+.13,base+1.17),gold,(.75,.65,1.9),coll,segs=12,rings=8)
    sitara(dx,dy+.17,base+.45,coll)
    # Open channel and downward lip of the mizab.
    for sy in (-1,1): box('Mizab side',(2.40,.045,.24),(-kx-1.17,sy*.18,kh-.23),gold,coll)
    box('Mizab channel',(2.4,.39,.045),(-kx-1.17,0,kh-.35),gold,coll)
    box('Mizab lip',(.06,.39,.34),(-kx-2.38,0,kh-.39),gold,coll)
    black_stone(kx,ky,coll,silver,stone)
    wall=arc_wall('Hijr Ismail',-kx,0,8.4,6.6,math.radians(105),math.radians(255),1.4,1.3,marble,coll=coll)
    bevel(wall,.045,3)
    cap=arc_wall('Hijr polished coping',-kx,0,8.36,6.56,math.radians(105),math.radians(255),1.48,.12,marble,coll=coll)
    cap.location.z=1.28;bevel(cap,.035,3)
    maqam(maqam_position,coll,gold,marble,granite)
