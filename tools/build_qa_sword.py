"""Generate an original static katana mesh for rig/socket QA only.

This is an engineering prop, NOT the production Musashi weapon asset.
Usage:
  blender --background --python tools/build_qa_sword.py
"""
from pathlib import Path
import bpy
import math

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "samples" / "external" / "qa_katana.glb"
DEST.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def mat(name, color, metallic=0.0, roughness=0.5):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


steel = mat("Blade silver steel", (0.43, 0.54, 0.62), 0.9, 0.18)
edge = mat("Polished edge", (0.72, 0.82, 0.91), 0.93, 0.13)
black = mat("Indigo hilt wrap", (0.019, 0.028, 0.047), 0.1, 0.55)
bronze = mat("Antique bronze hardware", (0.44, 0.26, 0.095), 0.77, 0.25)


def cylinder(name, radius, depth, z, material, vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=(0, 0, z))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Small soft edges", "BEVEL")
    bevel.width = min(0.009, radius * 0.35)
    bevel.segments = 2
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


cylinder("Rigid wooden tsuka", 0.023, 0.29, 0.145, black)
cylinder("Metal pommel", 0.026, 0.035, 0.015, bronze)
cylinder("Blade collar", 0.026, 0.065, 0.315, bronze)
cylinder("Iron circular guard", 0.108, 0.017, 0.297, bronze, 32)

for z in (0.045 + i * 0.033 for i in range(7)):
    bpy.ops.mesh.primitive_torus_add(major_segments=18, minor_segments=5, location=(0, 0, z), major_radius=0.023, minor_radius=0.0027)
    obj = bpy.context.object
    obj.name = "Handle wrap band"
    obj.data.materials.append(bronze)

# Convex, tapered curved blade made of a single unskinned mesh.
stations = [
    (0.328, 0.000, 0.058, 0.013),
    (0.590, 0.008, 0.060, 0.012),
    (0.920, 0.035, 0.053, 0.010),
    (1.147, 0.065, 0.036, 0.007),
    (1.205, 0.083, 0.0008, 0.0008),
]
vertices = []
for z, curve_x, width, depth in stations:
    for px, py in ((-width / 2, -depth / 2),
                   (width / 2, -depth / 2),
                   (width / 2, depth / 2),
                   (-width / 2, depth / 2)):
        vertices.append((curve_x + px, py, z))
faces = [(3, 2, 1, 0)]
for i in range(len(stations) - 1):
    a, b = i * 4, (i + 1) * 4
    for j in range(4):
        nxt = (j + 1) % 4
        faces.append((a + j, a + nxt, b + nxt, b + j))
last = (len(stations) - 1) * 4
faces.append((last, last + 1, last + 2, last + 3))
mesh = bpy.data.meshes.new("Single unskinned blade mesh")
mesh.from_pydata(vertices, [], faces)
mesh.update()
obj = bpy.data.objects.new("Rigid forged katana blade", mesh)
bpy.context.collection.objects.link(obj)
mesh.materials.append(steel)
bevel = obj.modifiers.new("Blade chamfers", "BEVEL")
bevel.width = 0.002
bevel.segments = 2
obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")

# No mesh is parented to a bone; no armature, morph or animation is exported.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(DEST), export_format="GLB",
                          use_selection=True, export_animations=False,
                          export_yup=True)
print(f"QA_SWORD_READY={DEST} bytes={DEST.stat().st_size}")
