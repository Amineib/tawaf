"""Bake static courtyard contact occlusion on the rented GPU, excluding crowds."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
import build_scene as bs
import common

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
out=os.path.abspath(args[0]); os.makedirs(out,exist_ok=True)
os.environ['UMRAH_CONTACT']=''  # never include a previous contact overlay in its own bake
bs.build_haram()
for o in bpy.data.collections['Pilgrims'].objects: o.hide_render=True
common.render_settings(1024,32)
assert bpy.context.scene.cycles.device=='GPU', 'Contact baking requires the rented GPU'
bpy.ops.mesh.primitive_plane_add(size=56,location=(0,0,.008))
plane=bpy.context.object;plane.name='Static contact bake receiver'
mat=common.principled('Contact receiver',(1,1,1),rough=1)
plane.data.materials.append(mat)
im=bpy.data.images.new('Static contact shading',width=1024,height=1024,alpha=True)
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.nodes.active=tex
bpy.ops.object.select_all(action='DESELECT');plane.select_set(True);bpy.context.view_layer.objects.active=plane
bpy.context.scene.world.color=(1,1,1)
bpy.context.scene.world.use_nodes=True
bpy.context.scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=1
bpy.context.scene.render.bake.margin=8
bpy.ops.object.bake(type='AO')
pixels=np.array(im.pixels[:],dtype=np.float32).reshape((-1,4))
ao=pixels[:,:3].mean(axis=1)
pixels[:,:3]=0
pixels[:,3]=np.clip((1-ao)*.42,0,.42)
im.pixels.foreach_set(pixels.ravel())
im.filepath_raw=os.path.join(out,'contact.png');im.file_format='PNG';im.save()
print('WROTE_CONTACT',im.filepath_raw,flush=True)
