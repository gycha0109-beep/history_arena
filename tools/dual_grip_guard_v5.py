"""Dual sword guard visual QA. Keeps the authored full-body idle, actual skinned fingers
and rigid sword geometry. Swords are posed WITH the hands, never independently aimed.
Blender 5.2.3 LTS. Experimental visual evidence only.
"""
from pathlib import Path
import math, bpy, json
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"captures"/"qa"/"dual_grip_guard_v5"
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/"samples/external/kinemiq_dual_guard_idle.glb"))
arm=next(o for o in bpy.data.objects if o.type=="ARMATURE")
for tr in arm.animation_data.nla_tracks:tr.mute=tr.name!="Idle_DualGuard"
bpy.context.scene.frame_set(1)
swordparts={}
# Import ALL weapon meshes before editing the armature pose. Blender glTF import
# evaluates NLA again and previously reset unbaked arm movements.
for side,name in (("r","katana"),("l","wakizashi")):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/f"samples/external/qa_{name}_rigid.glb"))
    swordparts[side]=[o for o in bpy.data.objects if o not in before]
bpy.context.scene.frame_set(1)
initial_bones={b.name:(tuple(b.head_local),tuple(b.tail_local)) for b in arm.data.bones}
initial_grips={}
for side in ("r","l"):
    hand=arm.pose.bones["hand_"+side]
    if side=="r":
        center=Vector((-.283,-.038,.893))
    else:
        center=(arm.pose.bones["middle_02_l"].head+arm.pose.bones["ring_02_l"].head)*.5+Vector((.002,-.005,.017))
    axis=(arm.pose.bones["index_01_"+side].head-arm.pose.bones["pinky_01_"+side].head).normalized()
    initial_grips[side]={
        "point_local":hand.matrix.inverted() @ center,
        "axis_local":hand.matrix.to_3x3().inverted() @ axis
    }

def aim_segment(name, child, target):
    pb=arm.pose.bones[name]
    cb=arm.pose.bones[child]
    pivot=pb.head.copy()
    current=(cb.head-pivot).normalized()
    desired=(Vector(target)-pivot).normalized()
    q=current.rotation_difference(desired)
    pb.matrix=(Matrix.Translation(pivot) @ q.to_matrix().to_4x4()
               @ Matrix.Translation(-pivot) @ pb.matrix.copy())
    bpy.context.view_layer.update()
    print("ARM_TARGET",name,"origin",tuple(round(x,3) for x in pivot),
          "child",tuple(round(x,3) for x in arm.pose.bones[child].head))

def forearm_pose(upper,lower,hand,elbow,wrist):
    aim_segment(upper,lower,elbow)
    aim_segment(lower,hand,wrist)

# Turn the thorax slightly: right shoulder leads, head returns toward opponent.
for bone_name,yaw in (("spine_02",11.0),("spine_03",6.0)):
    if bone_name not in arm.pose.bones:
        continue
    pb=arm.pose.bones[bone_name]
    pt=pb.head.copy()
    q=Matrix.Rotation(math.radians(yaw),4,"Z")
    pb.matrix=Matrix.Translation(pt) @ q @ Matrix.Translation(-pt) @ pb.matrix.copy()
    bpy.context.view_layer.update()

# Targets are initial candidates, not verified martial-arts poses.
# Do not change any hip/leg bones. Both upper and lower arms reach toward the opponent.
forearm_pose("upperarm_r","lowerarm_r","hand_r",(-.29,-.15,1.22),(-.11,-.40,1.30))
forearm_pose("upperarm_l","lowerarm_l","hand_l",(.32,-.11,1.18),(.24,-.33,1.08))

# Orient actual finger joints and palm toward a forward guard. The sword follows.
targets={
    "r":Vector((.10,-.82,.56)).normalized(),
    "l":Vector((-.02,-.97,.24)).normalized()
}
for side in ("r","l"):
    # First roll the FOREARM about its own axis, preserving wrist position.
    # This avoids forcing all sword direction correction into the wrist joint.
    fore=arm.pose.bones["lowerarm_"+side]
    wrist=arm.pose.bones["hand_"+side]
    elbow=fore.head.copy()
    fore_axis=(wrist.head-elbow).normalized()
    a=(arm.pose.bones["index_01_"+side].head-arm.pose.bones["pinky_01_"+side].head).normalized()
    b=targets[side]
    proj_a=(a-fore_axis*a.dot(fore_axis)).normalized()
    proj_b=(b-fore_axis*b.dot(fore_axis)).normalized()
    twist=math.atan2(fore_axis.dot(proj_a.cross(proj_b)),proj_a.dot(proj_b))
    from mathutils import Quaternion
    twist=max(-math.radians(62),min(math.radians(62),twist))
    twist_q=Quaternion(fore_axis,twist)
    fore.matrix=(Matrix.Translation(elbow) @ twist_q.to_matrix().to_4x4()
                 @ Matrix.Translation(-elbow) @ fore.matrix.copy())
    bpy.context.view_layer.update()
    hand=arm.pose.bones["hand_"+side]
    origin=hand.head.copy()
    current_axis=(arm.pose.bones["index_01_"+side].head-
                  arm.pose.bones["pinky_01_"+side].head).normalized()
    q=current_axis.rotation_difference(targets[side])
    angle=math.degrees(q.angle)
    print("HAND_AXES",side,"FOREARM_TWIST",round(math.degrees(twist),1),
          "WRIST_CHANGE",round(angle,1),"AXIS",tuple(round(x,3) for x in current_axis))
    assert angle<65,(side,angle)
    hand.matrix=(Matrix.Translation(origin) @ q.to_matrix().to_4x4()
                 @ Matrix.Translation(-origin) @ hand.matrix.copy())
    bpy.context.view_layer.update()

# Correct the LEFT index independently of the other fingers, using its own
# local knuckle axis. Keep a lightly touching curl instead of burying it in grip.
index_bone=arm.pose.bones["index_01_l"]
index_bone.rotation_quaternion=(index_bone.rotation_quaternion @ Quaternion(Vector((1,0,0)), math.radians(18))).normalized()
bpy.context.view_layer.update()
print("LEFT_INDEX_CORRECTION_DEG",18)

# Raise the downward-looking idle gaze without changing pelvis or gait.
for head_name,up_angle in (("neck_01",-3.0),("Head",-9.0)):
    pb=arm.pose.bones[head_name]
    head_pivot=pb.head.copy()
    rot=Matrix.Rotation(math.radians(up_angle),4,"X")
    pb.matrix=(Matrix.Translation(head_pivot) @ rot
               @ Matrix.Translation(-head_pivot) @ pb.matrix.copy())
    bpy.context.view_layer.update()

# Bake the selected static pose into its OWN Blender action. Without this,
# adding later geometry or rendering can re-evaluate the original NLA and
# silently reset the arms while the rigid swords stay in their old locations.
saved_pose={p.name:p.matrix_basis.copy() for p in arm.pose.bones}
for tr in arm.animation_data.nla_tracks:
    tr.mute=True
arm.animation_data.action=None
arm.animation_data.action=bpy.data.actions.new("DualGuardStaticQA")
for pb in arm.pose.bones:
    pb.matrix_basis=saved_pose[pb.name]
    pb.keyframe_insert(data_path="location",frame=1)
    pb.keyframe_insert(data_path="rotation_quaternion",frame=1)
    pb.keyframe_insert(data_path="scale",frame=1)
bpy.context.scene.frame_set(1)
print("BAKED_WRISTS",tuple(round(v,3) for v in arm.pose.bones["hand_r"].head),
      tuple(round(v,3) for v in arm.pose.bones["hand_l"].head))
assert arm.pose.bones["hand_r"].head.y < -.15, "Right wrist reversion after action bake"

def attach_sword(side,name):
    # Recover grip center and handle axis from the ORIGINAL hand-local frame,
    # then transform them by the NEW arm/hand pose. Do not reuse raw world coordinates.
    hand=arm.pose.bones["hand_"+side]
    bind=initial_grips[side]
    center=hand.matrix @ bind["point_local"]
    axis=(hand.matrix.to_3x3() @ bind["axis_local"]).normalized()
    if side=="l":
        # The former grip was positioned INSIDE the left index/middle fingers.
        # Radial correction uses the posed handle axis, not a hardcoded world offset.
        outward=Vector((-1,0,0))
        outward=(outward-axis*outward.dot(axis)).normalized()
        center+=outward*.0275
    imported=swordparts[side]
    pivot=bpy.data.objects.new(f"{name}_{side}_rigid_grip",None)
    bpy.context.collection.objects.link(pivot)
    for o in imported:
        if o.parent in imported:continue
        o.parent=pivot
    pivot.location=center
    pivot.rotation_mode="QUATERNION"
    # A single rotation-difference does NOT constrain blade edge roll.
    # Choose opposing OUTWARD cutting-edge planes for two-sword use.
    edge_hint=Vector((-1.0,0,-.20)) if side=="r" else Vector((1.0,0,.20))
    edge_x=(edge_hint-axis*edge_hint.dot(axis)).normalized()
    edge_y=axis.cross(edge_x).normalized()
    edge_x=edge_y.cross(axis).normalized()
    basis=Matrix(((edge_x.x,edge_y.x,axis.x),
                  (edge_x.y,edge_y.y,axis.y),
                  (edge_x.z,edge_y.z,axis.z)))
    pivot.rotation_quaternion=basis.to_quaternion()
    print("EDGE_DIRECTION",side,tuple(round(q,3) for q in edge_x))
    assert edge_x.x < -.7 if side=="r" else edge_x.x > .7
    bpy.context.view_layer.update()
    world=pivot.matrix_world.copy()
    pivot.parent=arm
    pivot.parent_type="BONE"
    pivot.parent_bone="hand_"+side
    pivot.matrix_world=world
    bpy.context.view_layer.update()
    # Enforce rigid scale and position near the actual fingers, not just the wrist.
    assert all(abs(c-1)<1e-4 for c in pivot.scale)
    middle=arm.pose.bones["middle_02_"+side].head
    gap=(middle-center).length
    print("DEBUG_GRIP",side,"hand",tuple(round(x,3) for x in hand.head),"middle",tuple(round(x,3) for x in middle),
          "base",tuple(round(x,3) for x in arm.pose.bones["middle_01_"+side].head),"center",tuple(round(x,3) for x in center))
    print("WEAPON_BIND",name,side,"center",tuple(round(x,3) for x in center),
          "middle_distance",round(gap,3),"pivot_world",tuple(round(x,3) for x in pivot.matrix_world.to_translation()))
    assert gap<.072,(name,gap)
    return pivot

right=attach_sword("r","katana")
left=attach_sword("l","wakizashi")

# Preserve the same original skeleton, with explicitly separate QA pose.
assert initial_bones=={b.name:(tuple(b.head_local),tuple(b.tail_local)) for b in arm.data.bones}
assert arm.pose.bones["hand_r"].head.x<arm.pose.bones["hand_l"].head.x

# Stage and neutral skin shading.
skin=bpy.data.objects.get("SuperHero_Male")
if skin:
    skin.data.materials.clear()
    material=bpy.data.materials.new("Neutral matte actor")
    material.diffuse_color=(.48,.53,.61,1)
    material.use_nodes=True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.45,.52,.62,1)
    material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.84
    skin.data.materials.append(material)

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.014))
floor=bpy.context.object;floor.name="QA stage"
stage_mat=bpy.data.materials.new("Floor dark");stage_mat.diffuse_color=(.10,.11,.14,1)
stage_mat.use_nodes=True
stage_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.10,.11,.14,1)
stage_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.83
floor.data.materials.append(stage_mat)

scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=720;scene.render.resolution_y=1280;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG";scene.view_settings.view_transform="AgX"
scene.render.film_transparent=False
scene.world=bpy.data.worlds.new("QA ambience")
scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.025,.035,.053,1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.35

def lamp(location,power,size):
    bpy.ops.object.light_add(type="AREA",location=location)
    o=bpy.context.object;o.data.energy=power;o.data.size=size
    o.rotation_euler=(Vector((0,-.04,1.04))-o.location).to_track_quat("-Z","Y").to_euler()
lamp((2.5,-2.0,4.0),850,3.0)
lamp((-2,0,3.3),550,2.5)
lamp((1.0,2.5,2.9),250,1.7)

bpy.ops.object.camera_add(location=(2.4,-3.1,1.62))
camera=bpy.context.object;scene.camera=camera
camera.data.type="ORTHO";camera.data.ortho_scale=3.12
views=[
    ("three_quarter",(2.4,-3.1,1.62)),
    ("front",(0,-3.8,1.56)),
    ("side",(3.8,0,1.56))
]
def fit_whole_actor_and_weapons(cam):
    # Evaluate the actual skinned body and both RIGID sword meshes; fit every
    # visible model to the vertical review frame without clipping blade tips.
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    points=[]
    for original in [skin]+[obj for parts in swordparts.values() for obj in parts if obj.type=="MESH"]:
        if original is None or original.type!="MESH":
            continue
        obj=original.evaluated_get(deps)
        mesh=obj.to_mesh()
        try:
            # For a few thousand vertices, real evaluated bounds are cheap.
            points.extend(obj.matrix_world @ v.co for v in mesh.vertices)
        finally:
            obj.to_mesh_clear()
    assert points, "No actual mesh bounds for camera framing"
    basis=cam.matrix_world.to_3x3()
    right_axis=basis @ Vector((1,0,0))
    up_axis=basis @ Vector((0,1,0))
    xs=[p.dot(right_axis) for p in points]
    ys=[p.dot(up_axis) for p in points]
    mid_x=(min(xs)+max(xs))/2
    mid_y=(min(ys)+max(ys))/2
    old_pos=cam.location.copy()
    cam.location += right_axis*(mid_x-old_pos.dot(right_axis))
    cam.location += up_axis*(mid_y-old_pos.dot(up_axis))
    scene_width=(max(xs)-min(xs))
    scene_height=(max(ys)-min(ys))
    cam.data.ortho_scale=max(2.50,scene_height*1.13,scene_width/(720/1280)*1.13)
    print("CAMERA_FIT",round(scene_width,3),round(scene_height,3),round(cam.data.ortho_scale,3))

for name,point in views:
    camera.location=point
    camera.rotation_euler=(Vector((0,-.025,.99))-camera.location).to_track_quat("-Z","Y").to_euler()
    fit_whole_actor_and_weapons(camera)
    scene.render.filepath=str(OUT/(f"dual_guard_{name}.png"))
    bpy.ops.render.render(write_still=True)
    print("VIEW_RENDERED",name,scene.render.filepath)

import sys
sys.path.insert(0,str(ROOT/"tools"))
from guard_closeup_views import render_extra_views
render_extra_views(arm,skin,{"r":right,"l":left},OUT,floor,scene,camera)
# Make the saved Blender work file open on the entire guard, not a hand crop.
scene.render.resolution_x=720
scene.render.resolution_y=1280
camera.location=views[0][1]
camera.rotation_euler=(Vector((0,-.025,.99))-camera.location).to_track_quat("-Z","Y").to_euler()
fit_whole_actor_and_weapons(camera)
for obj in bpy.data.objects:
    if obj.name in ("Eyes","Eyebrows"):
        obj.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"dual_guard_upperbody_work.blend"))
report={"status":"visual_candidate_not_approved","upper_body_edited":["spine_02","spine_03","upperarm_r","lowerarm_r","hand_r","upperarm_l","lowerarm_l","hand_l"],"original_legs_unchanged":True,"sword_scale_rigid":True,"fingers_original_mesh":True,"views":[v[0] for v in views]}
(OUT/"dual_guard_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("DUAL_GUARD_QA_READY",OUT)
