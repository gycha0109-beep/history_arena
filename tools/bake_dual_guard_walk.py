"""Bake a separate two-handed sword-guard walk on one compatible 67-bone rig.

Legs, pelvis and foot contact are copied bit-for-bit from the validated walk.
Upper arms use *static* poses sampled from the same author's Walk_carrying clip;
fingers use the original sword-holding clip. No runtime wrist rotations/IK.
This is a motion QA reference, not a production Musashi model.
"""
from __future__ import annotations
import json, math, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"samples"/"external"
SOURCE=ROOT/"kinemiq_full_body_walks.glb"
OUT=ROOT/"kinemiq_two_sword_guard_walk.glb"
CLIP_DIR=ROOT/"kinemiq_cc0"/"GLB"

def open_glb(path):
    b=path.read_bytes()
    magic,ver,length=struct.unpack_from("<4sII",b,0)
    assert magic==b"glTF" and ver==2 and length==len(b)
    jl,jt=struct.unpack_from("<II",b,12);assert jt==0x4e4f534a
    d=json.loads(b[20:20+jl]); off=20+jl;bl,bt=struct.unpack_from("<II",b,off);assert bt==0x004e4942
    return d,bytearray(b[off+8:off+8+bl])

def rows(d,b,i):
    a=d["accessors"][i];v=d["bufferViews"][a["bufferView"]]
    width={"SCALAR":1,"VEC3":3,"VEC4":4}[a["type"]]
    assert a["componentType"]==5126
    at=v.get("byteOffset",0)+a.get("byteOffset",0);stride=v.get("byteStride",width*4)
    return [list(struct.unpack_from("<"+"f"*width,b,at+j*stride)) for j in range(a["count"])]

def append(d,b,data):
    width=len(data[0]); assert width in (1,3,4)
    b.extend(bytes(-len(b)%4));start=len(b)
    for row in data:b.extend(struct.pack("<"+"f"*width,*row))
    vi=len(d["bufferViews"]);d["bufferViews"].append({"buffer":0,"byteOffset":start,"byteLength":len(b)-start})
    ai=len(d["accessors"]);d["accessors"].append({
        "bufferView":vi,"componentType":5126,"count":len(data),
        "type":{1:"SCALAR",3:"VEC3",4:"VEC4"}[width],
        "min":[min(row[k] for row in data) for k in range(width)],
        "max":[max(row[k] for row in data) for k in range(width)]
    })
    return ai

def normalize(q):
    n=math.sqrt(sum(x*x for x in q))
    return [x/n for x in q]

def slerp(a,b,p):
    a=normalize(a);b=normalize(b);dot=sum(x*y for x,y in zip(a,b))
    if dot<0:b=[-x for x in b];dot=-dot
    if dot>.9995:return normalize([x*(1-p)+y*p for x,y in zip(a,b)])
    theta=math.acos(max(-1,min(1,dot)))
    return normalize([(math.sin((1-p)*theta)*x+math.sin(p*theta)*y)/math.sin(theta)
                     for x,y in zip(a,b)])

def lookup_action(path,t=0.40):
    d,b=open_glb(path)
    anim=d["animations"][0]
    result={}
    for ch in anim["channels"]:
        if ch["target"]["path"]!="rotation":continue
        name=d["nodes"][ch["target"]["node"]].get("name","")
        sm=anim["samplers"][ch["sampler"]]
        times=[x[0] for x in rows(d,b,sm["input"])]
        qs=rows(d,b,sm["output"])
        if t<=times[0]:q=qs[0]
        elif t>=times[-1]:q=qs[-1]
        else:
            index=next(i for i in range(1,len(times)) if times[i]>=t)
            q=slerp(qs[index-1],qs[index],(t-times[index-1])/(times[index]-times[index-1]))
        result[name]=q
    return result

d,b=open_glb(SOURCE)
names={i:n.get("name","") for i,n in enumerate(d["nodes"])}
src=next(a for a in d["animations"] if a["name"]=="Walk_forwards")
carrying=lookup_action(CLIP_DIR/"Walk_carrying.glb",t=0.5)
grip=lookup_action(CLIP_DIR/"Idle_with_a_sword.glb",t=0.45)

new={"name":"Walk_DualGuard","samplers":[],"channels":[]}
arms={"clavicle_l","upperarm_l","lowerarm_l","hand_l","clavicle_r","upperarm_r","lowerarm_r","hand_r"}
number_patched=0
for channel in src["channels"]:
    idx=channel["sampler"];sm=dict(src["samplers"][idx]); name=names[channel["target"]["node"]]
    channel_new={"sampler":len(new["samplers"]),"target":dict(channel["target"])}
    if channel["target"]["path"]=="rotation" and (name in arms or name.startswith(("thumb_","index_","middle_","ring_","pinky_"))):
        before=rows(d,b,sm["output"])
        if name in arms:
            # Both arms in the source's proper two-handed carrying posture.
            # Keep only a trace of original walk swing so weapons do not flap.
            fixed=carrying[name]
            adjusted=[slerp(fixed,old,0.055) for old in before]
        else:
            if name.endswith("_l") and name.replace("_l","_r") in grip:
                # Mirror the verified curled right sword-grip finger pose.
                right=grip[name.replace("_l","_r")]
                fixed=[right[0],-right[1],-right[2],right[3]]
            else:
                fixed=grip.get(name,carrying.get(name))
            adjusted=[normalize(fixed) for _ in before] if fixed else before
        sm["output"]=append(d,b,adjusted)
        number_patched+=1
    new["samplers"].append(sm)
    new["channels"].append(channel_new)

assert number_patched>=40,number_patched
d["animations"].append(new)
b.extend(bytes(-len(b)%4));d["buffers"][0]["byteLength"]=len(b)
j=json.dumps(d,separators=(",",":")).encode("utf8");j+=b" "*(-len(j)%4)
raw=struct.pack("<4sII",b"glTF",2,12+8+len(j)+8+len(b))+struct.pack("<II",len(j),0x4e4f534a)+j+struct.pack("<II",len(b),0x004e4942)+b
OUT.write_bytes(raw)
print("DUAL_GUARD_WALK",OUT,"bytes",len(raw),"altered_upper_and_finger_tracks",number_patched,
      "untouched_original_leg_tracks",len(src["channels"])-number_patched)
