"""Standalone CC0 human anatomy base for the Musashi rebuild, NOT a finished character.
Source: Blender Studio Human Base Meshes 1.4.1, https://www.blender.org/download/demo-files/
License: CC0. Keep reference version in source_candidates, unchanged.
Run with Blender 5.2+ in background.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT / "assets/source_candidates/blender_human_base_meshes/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
OUT=ROOT / "assets/characters/musashi/rebuild_v1"
OUT.mkdir(parents=True,exist_ok=True)
assert SOURCE.is_file(), f"Missing CC0 source: {SOURCE}"

bpy.ops.wm.read_factory_settings(use_empty=True)
names=["GEO-body_male_realistic","GEO-body_male_realistic.eye.L","GEO-body_male_realistic.eye.R"]
with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
    missing=[n for n in names if n not in src.objects]
    assert not missing, f"Missing objects: {missing}"
    dst.objects=list(names)
for obj in dst.objects:
    bpy.context.scene.collection.objects.link(obj)
body=dst.objects[0]
offset=body.location.copy()
for obj in dst.objects:
    obj.location-=offset
    obj.name="MUSASHI_BASE_"+obj.name
body=bpy.data.objects["MUSASHI_BASE_"+names[0]]
for mod in body.modifiers:
    if mod.type=="MULTIRES":
        mod.levels=min(2,mod.total_levels)
        mod.sculpt_levels=min(2,mod.total_levels)
        mod.render_levels=min(2,mod.total_levels)

def make_mat(name,color,roughness=0.8,sss=0.0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    shader=m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*color,1)
    shader.inputs["Roughness"].default_value=roughness
    if sss: shader.inputs["Subsurface Weight"].default_value=sss
    return m

skin=make_mat("Anatomy check - neutral skin, NOT character texture",(0.49,0.33,0.24),0.77,0.09)
white=make_mat("Anatomy check - eyes",(.72,.70,.64),0.25)
body.data.materials.clear()
body.data.materials.append(skin)
for n in names[1:]:
    obj=bpy.data.objects["MUSASHI_BASE_"+n]
    obj.data.materials.clear(); obj.data.materials.append(white)
    
# A backdrop and studio lights belong to the comparison stage, not the source mesh.
def mesh_plane():
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-0.006))
    obj=bpy.context.object;obj.name="QA_STUDIO_FLOOR"
    obj.data.materials.append(make_mat("Slate backdrop",(0.055,.060,.067),0.96))
mesh_plane()
world=bpy.data.worlds.new("QA Studio Ambient")
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.14,0.15,0.17,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.5

def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA')
    ob=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(ob)
    ob.location=loc;data.energy=power;data.shape='DISK';data.size=size
    direction=Vector((0,0,1.05))-ob.location
    ob.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
area("QA_KEY",(1.8,-2.2,4),650,3.0)
area("QA_FILL",(-2.1,-1,2),320,3.0)
area("QA_RIM",(-.6,2,3.2),800,2.5)

cam_data=bpy.data.cameras.new("QA_camera")
camera=bpy.data.objects.new("QA_camera",cam_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera=camera
cam_data.type='ORTHO';cam_data.ortho_scale=2.12

scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.render.resolution_x=600
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'

blend=OUT/'musashi_anatomy_base_cc0.blend'
for filename,xyz in [
    ('01_front.png',(0,-3.5,1.13)),
    ('02_left_profile.png',(3.5,0,1.13)),
    ('03_back.png',(0,3.5,1.13)),
    ('04_three_quarter.png',(2.55,-2.7,1.22)),
]:
    camera.location=xyz
    target=Vector((0,0,0.86))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/filename)
    bpy.ops.render.render(write_still=True)
    print("MUSASHI_RENDER_OK",filename,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
print("MUSASHI_REBUILD_BASE_OK",blend, "body_vertices",len(body.data.vertices),flush=True)
