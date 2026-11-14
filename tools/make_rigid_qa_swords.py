"""Create rigid QA swords WITHOUT fake hand/finger meshes.
Swords only; final fingers come from the actual skinned humanoid rig.
"""
from pathlib import Path
import bpy

DIR=Path(r"D:\cha\History_arena\samples\external")
for key in ("katana","wakizashi"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    original=DIR/("qa_"+key+"_dual.glb")
    bpy.ops.import_scene.gltf(filepath=str(original))
    for obj in list(bpy.data.objects):
        if obj.type != "MESH":
            continue
        name=obj.name.lower()
        if name.startswith("palm") or name.startswith("finger") or name.startswith("thumb"):
            bpy.data.objects.remove(obj,do_unlink=True)
    for obj in bpy.data.objects:
        if obj.type=="MESH":
            for mod in list(obj.modifiers):
                if mod.type in ("ARMATURE",):obj.modifiers.remove(mod)
    out=DIR/("qa_"+key+"_rigid.glb")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=str(out),export_format="GLB",
                               use_selection=True,export_animations=False)
    print("SWORD_NO_FAKE_HAND",out,out.stat().st_size,
          "mesh_count",len([obj for obj in bpy.data.objects if obj.type=="MESH"]))
