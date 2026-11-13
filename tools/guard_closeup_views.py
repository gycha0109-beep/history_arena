"""Render uncropped real-skinned hand grip inspections and upper-body QA.
Designed for the existing Blender 5.2 dual-guard inspection scene.
"""
import bpy
import bmesh
from mathutils import Vector

def render_extra_views(arm, skin, sword_pivots, out, stage, scene, camera):
    # A duplicate of the real skinned mesh is cropped for visibility,
    # with exactly the SAME armature/weight data: no stand-in fingers.
    hands = {}
    for side in ("r", "l"):
        proxy = skin.copy()
        proxy.data = skin.data.copy()
        bpy.context.collection.objects.link(proxy)
        proxy.name = f"{side}_original_hand_and_forearm_inspection"
        selected = {"hand_" + side, "lowerarm_" + side}
        selected.update(
            n for n in arm.data.bones.keys()
            if n.endswith("_" + side)
            and n.startswith(("thumb_", "index_", "middle_", "ring_", "pinky_"))
        )
        ids = {g.index for g in proxy.vertex_groups if g.name in selected}
        keep = {
            v.index for v in proxy.data.vertices
            if any(g.group in ids and g.weight > .1 for g in v.groups)
        }
        bm = bmesh.new()
        bm.from_mesh(proxy.data)
        bm.verts.ensure_lookup_table()
        bmesh.ops.delete(
            bm, geom=[v for v in bm.verts if v.index not in keep], context="VERTS"
        )
        bm.to_mesh(proxy.data)
        bm.free()
        assert len(proxy.data.vertices) > 80, f"No real skinned fingers in {side}"
        hands[side] = proxy

    center = Vector((0, -.05, 1.28))
    # Upper body inspection includes both whole hands and weapons.
    camera.data.ortho_scale = 1.27
    scene.render.resolution_x = 1350
    scene.render.resolution_y = 1000
    camera.location = (1.45, -2.4, 1.53)
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(out / "dual_guard_upper_body.png")
    bpy.ops.render.render(write_still=True)
    print("CLOSEUP_RENDER", "upper_body", scene.render.filepath)
    skin.hide_render = True
    stage.hide_render = True
    for obj in bpy.data.objects:
        if obj.name in ("Eyes", "Eyebrows"):
            obj.hide_render = True
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    camera.data.ortho_scale = .49
    for side in ("r", "l"):
        other = "l" if side == "r" else "r"
        hands[other].hide_render = True
        hands[side].hide_render = False
        for o in sword_pivots[other].children_recursive:
            if o.type == "MESH":
                o.hide_render = True
        for o in sword_pivots[side].children_recursive:
            if o.type == "MESH":
                o.hide_render = False
        grip_center = sword_pivots[side].matrix_world.to_translation()
        bone = arm.pose.bones["hand_" + side]
        elbow = arm.pose.bones["lowerarm_" + side]
        forearm = (bone.head - elbow.head).normalized()
        axis = (
            arm.pose.bones["index_01_" + side].head
            - arm.pose.bones["pinky_01_" + side].head
        ).normalized()
        side_vec = forearm.cross(axis).normalized()
        if side_vec.length < .5:
            side_vec = Vector((1, 0, 0))
        offsets = {
            "finger_wrap": side_vec * .36 + Vector((0, -.15, .23)),
            "thumb_contact": side_vec * -.36 + Vector((0, -.08, .19)),
            "handle_overview": side_vec * .24 + forearm * -.13 + Vector((0, .23, .26)),
        }
        for name, offset in offsets.items():
            camera.location = grip_center + offset
            camera.rotation_euler = (grip_center-camera.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(out / f"{side}_{name}.png")
            bpy.ops.render.render(write_still=True)
            print("CLOSEUP_RENDER", side, name, scene.render.filepath)
    for p in hands.values():
        bpy.data.objects.remove(p, do_unlink=True)
    stage.hide_render = False
    skin.hide_render = False
    for o in sword_pivots["r"].children_recursive + sword_pivots["l"].children_recursive:
        if o.type == "MESH": o.hide_render = False
