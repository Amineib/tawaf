"""Render fixed review cameras in day/night on the GPU worker."""
import os,sys,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import build_scene as bs
import common
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
out=os.path.abspath(args[0]);os.makedirs(out,exist_ok=True)
spec=json.load(open(os.path.join(os.path.dirname(__file__),'visual-cameras.json')))
for light in ('day','night'):
    os.environ['UMRAH_TIME']=light
    bs.build_haram()
    # Keep the comparison subject unobscured by the procedural crowd.
    for o in bpy.data.collections['Pilgrims'].objects: o.hide_render=True
    common.render_settings(1400,64,exposure=.25 if light=='day' else .4)
    assert bpy.context.scene.cycles.device=='GPU', 'Use the rented GPU for review rendering'
    for c in spec['cameras']:
        p=os.path.join(out,c['id']+'-'+light+'.jpg')
        if os.path.exists(p):continue
        data=bpy.data.cameras.new(c['id']);data.type='PERSP';data.lens=c['lens']
        camera=bpy.data.objects.new(c['id'],data);bpy.context.scene.collection.objects.link(camera)
        camera.location=c['position'];camera.rotation_euler=(Vector(c['target'])-camera.location).to_track_quat('-Z','Y').to_euler()
        s=bpy.context.scene;s.camera=camera;s.render.resolution_y=1000;s.render.filepath=p
        bpy.ops.render.render(write_still=True)
        print('REVIEW_RENDER',p,flush=True)
