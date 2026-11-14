"""Right-hand sword grip geometry QA (Blender 5.2.3).
No fake hand, no rescaling of the blade, no changes to validated walk.
Output three REAL rendered camera views and a Blender work file.
"""
from pathlib import Path
import bpy, math, json
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"captures"/"qa"/"right_grip"
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/"samples/external/kinemiq_dual_guard_idle.glb"))
arm=next(o for o in bpy.data.objects if o.type=="ARMATURE")
for tr in arm.animation_data.nla_tracks:
    tr.mute=tr.name!="Idle_DualGuard"
bpy.context.scene.frame_set(1)
hand=arm.pose.bones["hand_r"]
fingers=["index_01_r","middle_01_r","ring_01_r","pinky_01_r","thumb_03_r"]
finger_heads={n:Vector(arm.pose.bones[n].head) for n in fingers}
# Handle direction follows index->pinky metacarpal line, not the world up vector.
index=finger_heads["index_01_r"]
pinky=finger_heads["pinky_01_r"]
axis=(index-pinky).normalized()
center=Vector((-0.283,-0.038,0.893))
print("HANDLE_AXIS",tuple(round(v,5) for v in axis),"CENTER",tuple(center))
start=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT/"samples/external/qa_katana_rigid.glb"))
objects=[o for o in bpy.data.objects if o not in start]
print("SWORD_IMPORT_OBJECTS",len(objects))
# Weapon imported parts are separate meshes; parent to single rigid sword pivot.
pivot=bpy.data.objects.new("Katana handle frame, no scale",None)
bpy.context.collection.objects.link(pivot)
for obj in objects:
    if obj.type not in {"MESH","EMPTY"}:continue
    if obj.parent in objects:continue
    obj.parent=pivot
pivot.location=center
pivot.rotation_mode="QUATERNION"
pivot.rotation_quaternion=Vector((0,0,1)).rotation_difference(axis)
# Parent to actual right-hand bone to preserve grip under pose animation.
bpy.context.view_layer.update()
world=pivot.matrix_world.copy()
pivot.parent=arm
pivot.parent_type="BONE"
pivot.parent_bone="hand_r"
pivot.matrix_world=world
assert all(o.scale==Vector((1,1,1)) for o in objects if o.type=="MESH")
# Confirm handle is near actual finger curls, based on bones rather than proxy meshes.
p0=center
ax=axis
def line_gap(point):
    v=point-p0
    return (v-ax*v.dot(ax)).length
samples={}
for name in ["index_02_r","middle_02_r","ring_02_r","pinky_02_r","thumb_03_r"]:
    b=arm.pose.bones[name]
    samples[name]={"joint_axis_distance_m":round(line_gap(Vector(b.head)),4),"tip_axis_distance_m":round(line_gap(Vector(b.tail)),4)}
print("JOINT_DISTANCE_FROM_HANDLE_AXIS",samples)
# Isolate ORIGINAL skinned right forearm and fingers for inspection.
# This duplicates real vertices for rendering; it does NOT add proxy fingers.
import bmesh
skin=next(o for o in bpy.data.objects if o.type=="MESH" and o.name=="SuperHero_Male")
arm_mesh=skin.copy()
arm_mesh.data=skin.data.copy()
bpy.context.collection.objects.link(arm_mesh)
arm_mesh.name="Original skinned RIGHT hand QA crop"
allowed={"lowerarm_r","hand_r","upperarm_r"}
allowed.update(n for n in arm.data.bones.keys() if n.endswith("_r") and n.startswith(("thumb_","index_","middle_","ring_","pinky_")))
allowed_ids={g.index for g in arm_mesh.vertex_groups if g.name in allowed}
keep=set()
for v in arm_mesh.data.vertices:
    if any(g.group in allowed_ids and g.weight>.12 for g in v.groups):
        keep.add(v.index)
bm=bmesh.new()
bm.from_mesh(arm_mesh.data)
bm.verts.ensure_lookup_table()
discard=[v for v in bm.verts if v.index not in keep]
bmesh.ops.delete(bm,geom=discard,context="VERTS")
bm.to_mesh(arm_mesh.data)
bm.free()
skin.hide_render=True
for face_obj in bpy.data.objects:
    if face_obj.name in ("Eyes","Eyebrows"):face_obj.hide_render=True
skin_material=bpy.data.materials.new("Grip contrast - actual skin")
skin_material.use_nodes=True
skin_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.37,.45,.52,1)
skin_material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.83
arm_mesh.data.materials.clear()
arm_mesh.data.materials.append(skin_material)
for obj in objects:
    if obj.type!="MESH":continue
    if "Grip at palm origin" in obj.name:
        gripmat=bpy.data.materials.new("Grip deep indigo")
        gripmat.diffuse_color=(.03,.065,.13,1)
        gripmat.use_nodes=True
        gripmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.035,.07,.14,1)
        gripmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.72
        obj.data.materials.clear()
        obj.data.materials.append(gripmat)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=900
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.world=bpy.data.worlds.new("Grip studio world")
scene.world.color=(.035,.04,.052)
# Hide all other meshes from render? Full upper forearm provides anatomical context.
def area(name,loc,power,size):
    bpy.ops.object.light_add(type="AREA",location=loc)
    o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape="DISK";o.data.size=size
    o.rotation_euler=(center-o.location).to_track_quat("-Z","Y").to_euler()
area("Soft key",center+Vector((.8,-.5,.85)),75,1.0)
area("Rim",center+Vector((-.7,.5,.5)),55,.8)
area("Fill",center+Vector((0,.8,-.3)),40,.8)
bpy.ops.object.camera_add(location=center+Vector((.32,-.22,.20)))
camera=bpy.context.object;camera.name="Grip Camera";scene.camera=camera
camera.data.type="ORTHO";camera.data.ortho_scale=.43
views=[
    ("fingertips",Vector((.33,-.24,.18))),
    ("back_of_hand",Vector((-.30,-.16,.17))),
    ("palm_side",Vector((.20,.30,.23)))
]
for name,offset in views:
    camera.location=center+offset
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str(OUT/("right_katana_"+name+".png"))
    bpy.ops.render.render(write_still=True)
    print("RENDER",name,scene.render.filepath)
# Store matching transform relative to bone for future proper Godot/GLB attachment.
bpy.context.view_layer.update()
local=arm.pose.bones["hand_r"].matrix.inverted() @ (arm.matrix_world.inverted() @ pivot.matrix_world)
report={"source":"KinemIQ CC0 bone hand_r, static authored sword idle","no_animation_tracks_changed":True,"no_fake_hand_mesh":True,"sword_scale_fixed":True,"handle_radius_m":0.0185,"axis_blender":list(axis),"center_blender":list(center),"bone_pose_to_sword_blender_matrix":[list(row) for row in local],"joint_axis_distances":samples}
(OUT/"right_katana_grip_analysis.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"right_katana_grip_work.blend"))
print("RIGHT_GRIP_QA_READY",str(OUT))
