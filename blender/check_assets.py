"""Inspect and validate real-time glTF assets without Blender or a GPU."""
import argparse
import json
from pathlib import Path
import struct
import io


def document(path):
    raw=path.read_bytes()
    assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2, f'{path}: invalid GLB'
    assert struct.unpack_from('<I',raw,8)[0]==len(raw), f'{path}: truncated GLB'
    size,kind=struct.unpack_from('<II',raw,12)
    assert kind==0x4E4F534A, f'{path}: missing JSON chunk'
    return json.loads(raw[20:20+size])


def accessor_values(path, d, index):
    raw=path.read_bytes();start=28+struct.unpack_from('<I',raw,12)[0]
    a=d['accessors'][index];v=d['bufferViews'][a['bufferView']]
    fmt,size={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}[a['componentType']]
    components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    stride=v.get('byteStride',size*components);offset=start+v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from('<'+fmt*components,raw,offset+i*stride) for i in range(a['count'])]


def artwork_orientation(positions, uvs):
    # Curtain faces +y in Blender, -z in glTF. A viewer in front sees world
    # -x as screen-right; positive x/u covariance means mirrored lettering.
    xm=sum(p[0] for p in positions)/len(positions);um=sum(uv[0] for uv in uvs)/len(uvs)
    covariance=sum((p[0]-xm)*(uv[0]-um) for p,uv in zip(positions,uvs))
    assert covariance<0, 'Curtain artwork is horizontally mirrored in its front view'


def inspect(path, strict=False, delivery=False):
    d=document(path)
    tris=0
    for mesh in d['meshes']:
        for p in mesh['primitives']:
            assert p.get('mode',4)==4, f'{path}: unsupported primitive mode'
            count=d['accessors'][p.get('indices',p['attributes']['POSITION'])]['count']
            tris+=count//3
            assert 'NORMAL' in p['attributes'], f'{path}: missing normals'
            m=d['materials'][p['material']]
            textured=any(k in m for k in ('normalTexture','occlusionTexture','emissiveTexture')) or any(k.endswith('Texture') for k in m.get('pbrMetallicRoughness',{}))
            if textured: assert 'TEXCOORD_0' in p['attributes'], f'{path}: textured mesh has no UVs'
    roles={m.get('extras',{}).get('umrahRole') for m in d['materials']}
    if delivery:
        budget={'haram':8_600_000,'masa':3_300_000,'pilgrims':900_000}[path.stem]
        assert path.stat().st_size<=budget, f'{path}: delivery download budget exceeded'
    if strict:
        assert tris<220000, f'{path}: unique geometry budget exceeded'
        assert path.stat().st_size<12_000_000, f'{path}: download budget exceeded'
        assert 'EXT_mesh_gpu_instancing' in d.get('extensionsUsed',[]), f'{path}: instancing lost'
        for m in d['materials']:
            role=m.get('extras',{}).get('umrahRole')
            if role=='floor': assert 'metallicRoughnessTexture' in m['pbrMetallicRoughness'], 'Floor roughness map lost'
            if m['name']=='X_Kiswa': assert 'normalTexture' in m and 'metallicRoughnessTexture' in m['pbrMetallicRoughness'], 'Cloth maps lost'
        if path.stem=='haram':
            assert {'cloth','gold','silver','contact','glass'}<=roles, f'Missing landmark material roles: {roles}'
            assert any('Black Stone sculpted' in n.get('name','') for n in d['nodes']), 'Black Stone master missing'
            for mesh in d['meshes']:
                for primitive in mesh['primitives']:
                    if d['materials'][primitive['material']].get('extras',{}).get('umrahRole')=='embroidery':
                        artwork_orientation(accessor_values(path,d,primitive['attributes']['POSITION']),accessor_values(path,d,primitive['attributes']['TEXCOORD_0']))
    if delivery and path.stem=='pilgrims':
        assert len(d['meshes'])>=8, 'Eight crowd variants are required'
        for mesh in d['meshes']:
            for p in mesh['primitives']:
                assert '_UMRAH_GAIT' in p['attributes'], 'Crowd joint/gait data was lost during export'
    from PIL import Image
    raw=path.read_bytes();json_size=struct.unpack_from('<I',raw,12)[0];bin_start=28+json_size
    texture_bytes=0
    for source in d.get('images',[]):
        view=d['bufferViews'][source['bufferView']];offset=bin_start+view.get('byteOffset',0)
        with Image.open(io.BytesIO(raw[offset:offset+view['byteLength']])) as im:
            texture_bytes+=im.width*im.height*4*4/3  # RGBA8 plus mip pyramid
    return {'file':path.name,'bytes':path.stat().st_size,'uniqueTriangles':tris,'meshes':len(d['meshes']),
            'materials':len(d['materials']),'textures':len(d.get('textures',[])),
            'estimatedTextureMiB':round(texture_bytes/1048576,2),
            'materialRoles':sorted(r for r in roles if r),'extensions':d.get('extensionsUsed',[])}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--strict',action='store_true');p.add_argument('--delivery',action='store_true');p.add_argument('--output',type=Path)
    a=p.parse_args();report={'sceneVersion':'kaaba-v1','assets':[inspect(a.folder/(name+'.glb'),a.strict and name!='pilgrims',a.delivery) for name in ('haram','masa','pilgrims')]}
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
