"""H100 review renders for the eight improved pilgrim silhouettes."""
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
out=os.path.abspath(args[0]);os.makedirs(out,exist_ok=True)


def render(name,indices,positions,location,target,lens):
    common.reset();coll=common.collection('People review')
    variants=common.make_pilgrim_meshes(coll)
    for i,pos in zip(indices,positions):
        common.instance(variants[i][0],'Review person '+str(i),pos,coll=coll)
    floor=common.principled('Review floor',(.18,.21,.19),rough=.85)
    common.box('Floor',(200,200,.08),(0,0,-.045),floor,coll)
    common.flat_world((.22,.25,.23),.7)
    for p,power,size in (((-3,4,6),900,5),((4,-2,5),650,4)):
        light=bpy.data.lights.new('Softbox','AREA');light.energy=power;light.shape='DISK';light.size=size
        obj=bpy.data.objects.new('Softbox',light);coll.objects.link(obj);obj.location=p
        obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new(name);data.type='PERSP';data.lens=lens
    cam=bpy.data.objects.new(name,data);coll.objects.link(cam);cam.location=location
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    common.render_settings(1600,64,exposure=.2)
    assert bpy.context.scene.cycles.device=='GPU'
    scene=bpy.context.scene;scene.camera=cam;scene.render.resolution_y=1000
    scene.render.filepath=os.path.join(out,name+'.jpg');bpy.ops.render.render(write_still=True)
    print('PEOPLE_REVIEW',scene.render.filepath,flush=True)


render('people-lineup',range(8),[((i-3.5)*.82,0,0) for i in range(8)],(0,9.4,2.3),(0,0,.95),43)
render('people-detail',(1,5),[(-.52,0,0),(.52,0,0)],(2.4,4.8,1.9),(0,0,1),53)
