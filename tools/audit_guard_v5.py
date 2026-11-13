"""Inspect actual blade edge axes and indexed left-finger mesh penetration for V4."""
import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"captures/qa/dual_grip_guard_v5"
bpy.ops.wm.open_mainfile(filepath=str(OUT/"dual_guard_upperbody_work.blend"))
skin=bpy.data.objects["SuperHero_Male"]
results={}
for side,pivotname in (("r","katana_r_rigid_grip"),("l","wakizashi_l_rigid_grip")):
    pivot=bpy.data.objects[pivotname]
    axis=(pivot.matrix_world.to_3x3() @ Vector((0,0,1))).normalized()
    edge=(pivot.matrix_world.to_3x3() @ Vector((1,0,0))).normalized()
    results[side]={"blade_axis":[round(x,4) for x in axis],"edge_axis":[round(x,4) for x in edge]}
    print("GUARD_EDGE_AXIS",side,results[side]["edge_axis"])
assert results["r"]["edge_axis"][0]<-.7 and results["l"]["edge_axis"][0]>.7,"Blades not deliberately opposed"
pivot=bpy.data.objects["wakizashi_l_rigid_grip"]
center=pivot.matrix_world.translation.copy()
axis=(pivot.matrix_world.to_3x3() @ Vector((0,0,1))).normalized()
groupids={g.index for g in skin.vertex_groups if g.name.startswith("index_") and g.name.endswith("_l")}
indices=[v.index for v in skin.data.vertices if any(g.group in groupids and g.weight>=.48 for g in v.groups)]
deps=bpy.context.evaluated_depsgraph_get()
e=skin.evaluated_get(deps);mesh=e.to_mesh()
counts={"penetrating":0,"severely_penetrating":0,"surface_contact":0,"inside_handle_range":0}
try:
 for idx in indices:
    rel=e.matrix_world @ mesh.vertices[idx].co-center
    z=rel.dot(axis)
    if abs(z)>.102:continue
    counts["inside_handle_range"]+=1
    r=(rel-axis*z).length
    if r<.0185:
        counts["penetrating"]+=1
        if r<.012:counts["severely_penetrating"]+=1
    elif r<.028:counts["surface_contact"]+=1
finally:e.to_mesh_clear()
results["left_index"]=counts
(OUT/"grip_audit.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
print("LEFT_INDEX_GEOMETRY_AUDIT",counts)
assert counts["penetrating"]<=5 and counts["severely_penetrating"]==0,"Left index still intersects the handle severely"
print("V5_STRUCTURAL_QA_PASS")
