"""Import the user-provided Tripo GLB and render four QA views in Blender 5.2."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/characters/musashi/tripo_h25_v1'
SOURCE=OUT/'musashi_h25_original.glb'
assert SOURCE.exists(), SOURCE
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert meshes, 'No mesh imported'
coords=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
mn=Vector((min(v[i] for v in coords) for i in range(3)))
mx=Vector((max(v[i] for v in coords) for i in range(3)))
mid=(mn+mx)/2
height=mx.z-mn.z
print('GLB_IMPORTED',len(meshes),'mesh objects',sum(len(o.data.vertices) for o in meshes),'vertices',sum(len(o.data.polygons) for o in meshes),'polygons',len(arms),'armatures',flush=True)
print('GLB_BOUNDS',tuple(round(v,4) for v in mn),tuple(round(v,4) for v in mx),flush=True)

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in {x.identifier for x in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items} else 'BLENDER_EEVEE'
scene.render.resolution_x=750
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('QA studio')
scene.world=world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.11,0.12,0.14,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.7

# Studio ground, separate from imported mesh
bpy.ops.mesh.primitive_plane_add(size=200,location=(mid.x,mid.y,mn.z-0.008))
floor=bpy.context.object
floor.name='QA_Studio_Floor'
mat=bpy.data.materials.new('QA_Ground')
mat.diffuse_color=(0.12,0.13,0.15,1)
floor.data.materials.append(mat)

def area(name,location,energy,size):
    bpy.ops.object.light_add(type='AREA',location=location)
    light=bpy.context.object
    light.name=name
    light.data.energy=energy
    light.data.shape='DISK'
    light.data.size=size
    direction=mid+Vector((0,0,0.2))-light.location
    light.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

area('Key softbox',mid+Vector((-2.0,-2.5,3.1)),550,4.0)
area('Fill softbox',mid+Vector((2.0,-1.2,2.0)),320,3.2)
area('Rim softbox',mid+Vector((0.0,2.5,3.2)),750,3.0)

bpy.ops.object.camera_add(location=mid+Vector((0,-2.5,0.4)))
camera=bpy.context.object
camera.name='QA_Orthographic_Camera'
camera.data.type='ORTHO'
camera.data.ortho_scale=max(1.32*height,1.30)
scene.camera=camera
target=Vector((mid.x,mid.y,mn.z+height*0.53))
angles=[
 ('01_front',(0,-2.5,0.12)),
 ('02_right',(2.5,0,0.12)),
 ('03_back',(0,2.5,0.12)),
 ('04_three_quarter',(1.75,-1.75,0.15)),
]
for name,offset in angles:
    camera.location=target+Vector(offset)
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('GLB_RENDER_OK',name,flush=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'musashi_h25_imported.blend'))
report={
 'source':SOURCE.name,
 'mesh_objects':len(meshes),
 'vertices':sum(len(o.data.vertices) for o in meshes),
 'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),
 'armatures':len(arms),
 'animations':len(bpy.data.actions),
 'materials':len(set(m.name for o in meshes for m in o.data.materials if m)),
 'bbox_min':list(mn),'bbox_max':list(mx),
 'height_in_source_units':height,
 'note':'Unrigged H2.5 base asset. Original GLB preserved.'
}
(OUT/'qa_mesh_stats.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('GLB_QA_COMPLETE',flush=True)
