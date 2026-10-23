"""Reusable human silhouettes, with cloth profiles and semantic gait attributes.

Faces stay deliberately simple. Eight adult variants share a small material set;
the browser animates their tagged limbs in instanced vertex shaders.
"""
import math
import bpy
from mathutils import Vector


class Shape:
    def __init__(self):
        self.vertices=[];self.faces=[];self.materials=[];self.gait=[]

    def vertex(self, p, gait):
        self.vertices.append(tuple(p));self.gait.append(gait)
        return len(self.vertices)-1

    def face(self, indices, material):
        self.faces.append(tuple(indices));self.materials.append(material)

    def loft(self, rings, material=0, gait=(0,0,1), segments=16, folds=0, cap=True):
        rows=[]
        for z,w,d,cy in rings:
            row=[]
            for j in range(segments):
                a=j*math.tau/segments
                ripple=1+folds*(math.sin(a*7+.3*z)+.35*math.sin(a*11-z))
                row.append(self.vertex((w*math.cos(a)*ripple,cy+d*math.sin(a)*ripple,z),gait))
            rows.append(row)
        for lower,upper in zip(rows,rows[1:]):
            for j in range(segments):
                k=(j+1)%segments;self.face((lower[j],lower[k],upper[k],upper[j]),material)
        if cap:
            self.face(tuple(reversed(rows[0])),material);self.face(rows[-1],material)

    def ellipsoid(self, center, radii, material=1, gait=(0,0,1), segments=10, rings=6):
        cx,cy,cz=center;rx,ry,rz=radii
        rows=[]
        for k in range(1,rings):
            t=math.pi*k/rings
            rows.append([self.vertex((cx+rx*math.sin(t)*math.cos(j*math.tau/segments),
                                      cy+ry*math.sin(t)*math.sin(j*math.tau/segments),cz+rz*math.cos(t)),gait) for j in range(segments)])
        top=self.vertex((cx,cy,cz+rz),gait);bottom=self.vertex((cx,cy,cz-rz),gait)
        for j in range(segments):
            k=(j+1)%segments;self.face((top,rows[0][j],rows[0][k]),material)
            self.face((bottom,rows[-1][k],rows[-1][j]),material)
        for upper,lower in zip(rows,rows[1:]):
            for j in range(segments):
                k=(j+1)%segments;self.face((upper[j],lower[j],lower[k],upper[k]),material)

    def limb(self,a,b,r1,r2,material,gait,segments=8):
        a,b=Vector(a),Vector(b);axis=(b-a).normalized()
        u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
        rows=[]
        for t,r in ((0,r1),(.12,r1),(.88,r2),(1,r2*.8)):
            c=a.lerp(b,t)
            rows.append([self.vertex(c+(u*math.cos(j*math.tau/segments)+v*math.sin(j*math.tau/segments))*r,gait) for j in range(segments)])
        for lower,upper in zip(rows,rows[1:]):
            for j in range(segments):
                k=(j+1)%segments;self.face((lower[j],lower[k],upper[k],upper[j]),material)
        self.face(tuple(reversed(rows[0])),material);self.face(rows[-1],material)

    def arm(self,side,covered):
        rows=[];gait=(side,3,1)
        for z,x,y,r in ((.84,.27,.04,.033),(1.00,.28,.024,.045),(1.10,.285,.012,.047),(1.29,.26,.004,.061),(1.38,.235,0,.067),(1.43,.235,0,.046),(1.46,.235,0,.006)):
            if covered:r*=1.12
            rows.append([self.vertex((side*x+r*math.cos(j*math.tau/12),y+r*.88*math.sin(j*math.tau/12),z),gait) for j in range(12)])
        for lower,upper in zip(rows,rows[1:]):
            for j in range(12):
                k=(j+1)%12;self.face((lower[j],lower[k],upper[k],upper[j]),0 if covered else 1)
        self.face(tuple(reversed(rows[0])),0 if covered else 1)
        self.face(rows[-1],0 if covered else 1)


def pose(point, tag, phase):
    """Clothing-aware foot paths and opposing arms, shared with the browser."""
    x,y,z=point;side,part,h=tag
    step=phase*side
    if part==2:
        # Hidden knees stay inside the wrap; ankles follow the foot recovery arc.
        # The upper calf remains tucked under the hem instead of floating free.
        weight=max(0,min(1,(.27*h-z)/(.15*h)))
        y+=.23*h*math.sin(step)*weight
        z+=.075*h*max(0,math.cos(step))*weight
    if part==3:
        angle=-.28*math.sin(step)*.65;zz=z-1.40*h
        y,z=y*math.cos(angle)-zz*math.sin(angle),y*math.sin(angle)+zz*math.cos(angle)+1.40*h
    if part==5:y+=.012*h*math.sin(phase)*max(0,min(1,(.96*h-z)/(.7*h)))
    return x,y,z


def make(coll,realtime=False):
    from common import random_color_mat, principled, link
    robe_white=random_color_mat('Pilgrim cloth ivory',[(.82,.81,.77),(.91,.90,.87),(.76,.76,.73)],rough=.83,sheen=.18)
    robe_black=random_color_mat('Pilgrim cloth charcoal',[(.018,.019,.022),(.035,.033,.038),(.05,.047,.05)],rough=.86,sheen=.12)
    robe_neutral=random_color_mat('Pilgrim cloth neutral',[(.40,.37,.32),(.27,.30,.33),(.64,.62,.57)],rough=.83,sheen=.15)
    skin=random_color_mat('Pilgrim Skin',[(.54,.35,.23),(.32,.19,.12),(.68,.48,.34),(.76,.58,.44),(.23,.13,.08)],rough=.65,sheen=.05)
    detail=principled('Pilgrim dark details',(.026,.020,.016),rough=.78)
    for m in (robe_white,robe_black,robe_neutral):m['umrahRole']='pilgrimCloth'
    skin['umrahRole']='pilgrimSkin';detail['umrahRole']='pilgrimDetail'
    specs=[('pilgrim_man',False,robe_white,1.00,1.00,5,True),
           ('pilgrim_man_b',False,robe_white,1.04,1.12,4,False),
           ('pilgrim_man_c',False,robe_white,.94,.91,3,True),
           ('pilgrim_man_d',False,robe_white,.99,1.17,2,True),
           ('pilgrim_woman_w',True,robe_white,.94,.97,2,False),
           ('pilgrim_woman_b',True,robe_black,.98,1.03,3,False),
           ('pilgrim_woman_c',True,robe_neutral,.92,1.00,2,False),
           ('pilgrim_woman_b2',True,robe_black,1.02,.94,1,False)]
    out=[]
    for index,(name,covered,robe,height,width,weight,hair) in enumerate(specs):
        s=Shape()
        # Profiled clothing: shoulders, waist, hips, overlapping wrap and hem.
        if covered:
            s.loft([(.07,.26,.16,0),(.24,.25,.16,0),(.56,.235,.155,0),(.92,.205,.14,0),(1.18,.205,.135,0),(1.37,.23,.125,0),(1.44,.19,.10,0)],folds=.03,gait=(0,5,1),segments=24,cap=False)
        else:
            s.loft([(.23,.205,.145,0),(.30,.215,.15,0),(.55,.208,.145,0),(.78,.197,.14,0),(.96,.185,.13,0)],folds=.03,gait=(0,5,1),segments=24,cap=False)
            s.loft([(.94,.185,.14,0),(1.06,.198,.145,0),(1.28,.228,.14,0),(1.40,.28,.13,0),(1.45,.255,.115,0),(1.48,.19,.095,0),(1.50,.10,.075,0),(1.51,.055,.06,0)],folds=.012,segments=24,cap=False)
            # Rolled waist edge and diagonal cloth overlap, rather than a cone.
            s.loft([(.94,.19,.14,0),(.985,.19,.14,0)],folds=.008,segments=24,cap=False)
        for side in (-1,1):
            arm=(side,3,1)
            s.arm(side,covered)
            s.ellipsoid((side*.27,.045,.79),(.036,.026,.067),1,arm,segments=8,rings=6)
            s.ellipsoid((side*.24,.064,.81),(.018,.018,.035),1,arm,segments=8,rings=4)
            # Covered limbs use ankle paths; feet and soles sit on the floor.
            # Covered legs are omitted, so an animated knee cannot cut through
            # an abaya or the upper ihram wrap. Men show only the lower calf.
            if not covered:s.limb((side*.10,.003,.25),(side*.10,0,.10),.043,.033,1,(side,2,1))
            s.ellipsoid((side*.10,.055,.058),(.050,.115,.045),2 if covered else 1,(side,2,1),segments=10,rings=6)
            s.ellipsoid((side*.10,.052,.018),(.055,.12,.017),2,(side,2,1),segments=10,rings=4)
            if not covered:s.ellipsoid((side*.10,.045,.091),(.054,.028,.014),2,(side,2,1),segments=8,rings=4)
        # Neck and a shaped chin/cranium avoid the old ball-on-a-cone silhouette.
        s.limb((0,0,1.43),(0,0,1.56),.052,.047,1,(0,0,1),segments=10)
        if covered:
            s.loft([(1.27,.19,.13,-.01),(1.39,.26,.145,-.01),(1.50,.145,.125,-.01),(1.54,.10,.10,-.01)],folds=.012,segments=24,cap=False)
            s.ellipsoid((0,0,1.64),(.12,.115,.155),0,segments=14,rings=10)
            s.ellipsoid((0,.106,1.635),(.069,.025,.102),1,segments=12,rings=8)
        else:
            s.loft([(1.50,.045,.055,.015),(1.54,.077,.083,.008),(1.63,.104,.095,0),(1.71,.097,.086,-.006),(1.77,.055,.05,-.008),(1.79,.012,.012,-.008)],1,segments=14)
            if hair:s.loft([(1.69,.103,.093,-.006),(1.71,.102,.091,-.006),(1.77,.060,.055,-.008),(1.796,.013,.013,-.008)],2,segments=18,cap=False)
        s.vertices=[(x*width,y,z*height) for x,y,z in s.vertices]
        s.gait=[(side,part,height) for side,part,_ in s.gait]
        if not realtime:s.vertices=[pose(p,g,index*.78+.35) for p,g in zip(s.vertices,s.gait)]
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(s.vertices,[],s.faces);mesh.update()
        for m in (robe,skin,detail):mesh.materials.append(m)
        for polygon,mi in zip(mesh.polygons,s.materials):polygon.material_index=mi;polygon.use_smooth=True
        attr=mesh.attributes.new(name='_UMRAH_GAIT',type='FLOAT_VECTOR',domain='POINT')
        attr.data.foreach_set('vector',[v for tag in s.gait for v in tag])
        o=link(bpy.data.objects.new(name,mesh),coll);o.hide_render=True;o.hide_viewport=True
        o['crowdFamily']='woman' if covered else 'man';o['crowdHeight']=height;o['crowdWeight']=weight
        out.append((o,weight))
    return out
