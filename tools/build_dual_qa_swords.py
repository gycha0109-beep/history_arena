"""Create two rigid QA swords with a palm-centered grip and a visible closed-hand proxy.
QA-only: mesh fingers must be replaced by skinned fingers on final production rigs.
Blender 5.2.3+; output files are local samples/external and NOT committed.
"""
from pathlib import Path
import bpy
import math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "samples" / "external"
OUT.mkdir(parents=True, exist_ok=True)

def material(name, rgb, metallic=0, roughness=.5):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    n = m.node_tree.nodes.get("Principled BSDF")
    n.inputs["Base Color"].default_value = (*rgb, 1)
    n.inputs["Metallic"].default_value = metallic
    n.inputs["Roughness"].default_value = roughness
    return m

steel = material("Tempered steel", (.34,.43,.54), .88,.24)
bright = material("Hamon shine", (.70,.77,.86), .9,.22)
hilt = material("Indigo wrapped handle", (.026,.035,.075), .15,.53)
bronze = material("Subtle aged bronze", (.31,.25,.12), .68,.33)
hand = material("QA closed hand - skinned rig replacement needed", (.83,.87,.89), .05,.67)

def new_cyl(name, radius, height, center, mat, vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=height, location=center)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bevel = o.modifiers.new("Smooth edges", "BEVEL")
    bevel.width = min(.004, radius*.25)
    bevel.segments = 2
    o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return o

def segment(name, a, b, radius, mat, vertices=10):
    d=Vector(b)-Vector(a)
    center=(Vector(a)+Vector(b))*.5
    o=new_cyl(name,radius,d.length,center,mat,vertices)
    o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    return o

def ellipsoid(name, center, dims, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=center)
    o=bpy.context.object
    o.name=name
    o.scale=dims
    o.data.materials.append(mat)
    return o

def build(name, length, grip, blade_width, left=False):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # The origin is the palm's center, NOT the pommel/guard/blade tip.
    # Local +Z points toward the blade tip, and sword scale remains 1.
    new_cyl("Grip at palm origin", .0185, grip, (0,0,-.008),hilt)
    new_cyl("Tsuba guard - reduced diameter", .061 if not left else .049, .010, (0,0,grip*.5-.01), bronze,32)
    new_cyl("Pommel",.022,.023,(0,0,-grip*.5+.005), bronze)
    new_cyl("Habaki",.022,.04,(0,0,grip*.5+.026),bronze)
    for i in range(7 if not left else 5):
        z=-grip*.41 + i*(grip*.82 / (6 if not left else 4))
        bpy.ops.mesh.primitive_torus_add(major_segments=14,minor_segments=4,
                location=(0,0,z),major_radius=.018,minor_radius=.0016)
        bpy.context.object.name="Handle wrap line"
        bpy.context.object.data.materials.append(bronze)

    start=grip*.5+.036
    stations=[
        (start,0,blade_width,.011),
        (start+length*.34,length*.013,blade_width*1.0,.011),
        (start+length*.69,length*.04,blade_width*.82,.009),
        (start+length*.92,length*.075,blade_width*.42,.005),
        (start+length,length*.11,.0005,.0005),
    ]
    verts=[]
    for z,arc,width,depth in stations:
        verts.extend([(arc-width*.5,-depth*.5,z),(arc+width*.5,-depth*.5,z),
                      (arc+width*.5,depth*.5,z),(arc-width*.5,depth*.5,z)])
    faces=[(3,2,1,0)]
    for i in range(len(stations)-1):
        a,b=4*i,4*(i+1)
        for j in range(4):
            k=(j+1)%4
            faces.append((a+j,a+k,b+k,b+j))
    n=4*(len(stations)-1)
    faces.append((n,n+1,n+2,n+3))
    mesh=bpy.data.meshes.new("Rigid curved blade mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    sword=bpy.data.objects.new(name+" full-length stable blade",mesh)
    bpy.context.collection.objects.link(sword)
    sword.data.materials.append(steel)
    bevel=sword.modifiers.new("Light edge bevel","BEVEL")
    bevel.width=.002
    bevel.segments=2
    sword.modifiers.new("Weighted normals","WEIGHTED_NORMAL")

    # Visual closed-hand proxy around the center of the hilt.
    # White fingers curl around dark handle: not just a sword dangling by wrist.
    # Must be removed once a final rig has real articulated fingers.
    ellipsoid("Palm enclosing handle", (-.025,-.023,-.005),(.043,.035,.053),hand)
    # Four curved finger arches across visible, camera-facing side
    for i in range(4):
        zz=-.042+i*.027
        segment(f"Finger_{i}_base",(-.045,-.02,zz),(-.030,.020,zz+.003),.010,hand)
        segment(f"Finger_{i}_curl",(-.030,.020,zz+.003),(.005,.035,zz+.005),.009,hand)
        segment(f"Finger_{i}_tip",(.005,.035,zz+.005),(.024,.008,zz+.005),.008,hand)
    segment("Thumb wrapped over opposite side",(-.018,-.043,.061),(.018,-.021,.036),.014,hand)

    # Every mesh is rigid, with zero armature, shape keys and keyframed scaling.
    bpy.ops.object.select_all(action="SELECT")
    dest=OUT/name
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format="GLB",
                            use_selection=True,export_animations=False,export_yup=True)
    print(f"DUAL_SWORD_READY={dest} bytes={dest.stat().st_size} grip_center=0 blade={length}")

build("qa_katana_dual.glb", .83, .27, .042, False)
build("qa_wakizashi_dual.glb", .49, .205, .035, True)
