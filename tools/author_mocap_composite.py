#!/usr/bin/env python3
"""Bake a reference-only gait composite into a separate GLB.

Original mocap hip/leg keys are preserved. Artist-authored walk upper-body
bone rotation curves are added as an actual animation clip, not procedurally
modified per frame. A small left-ankle clearance curve is also baked.
Third-party source and derived GLBs remain gitignored under samples/external.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "samples" / "external" / "soldier_mocap_ref.glb"
OUTPUT = ROOT / "samples" / "external" / "soldier_walk_composite.glb"
SOURCE_LOWER = "mocap_walk_F@1.1733"
SOURCE_UPPER = "walk"
FINAL_CLIP = "mocap_walk_composite"
UPPER_BLEND = 0.50
ANKLE_CLEARANCE_DEGREES = 24.0
ANKLE_WINDOW = (0.53, 0.82)


def align4(buf: bytearray) -> None:
    buf.extend(b"\x00" * (-len(buf) % 4))


def normalize(q: list[float]) -> list[float]:
    norm = math.sqrt(sum(x*x for x in q))
    return [x/norm for x in q]


def slerp(a: list[float], b: list[float], t: float) -> list[float]:
    a, b = normalize(a), normalize(b)
    dot = sum(x*y for x,y in zip(a,b))
    if dot < 0:
        b = [-x for x in b]; dot = -dot
    dot = min(1.0, max(-1.0, dot))
    if dot > .9995:
        return normalize([x*(1-t)+y*t for x,y in zip(a,b)])
    angle = math.acos(dot)
    sf = math.sin((1-t)*angle)/math.sin(angle)
    sg = math.sin(t*angle)/math.sin(angle)
    return normalize([x*sf+y*sg for x,y in zip(a,b)])


def quat_mul(a: list[float], b: list[float]) -> list[float]:
    x,y,z,w = a; X,Y,Z,W = b
    return [
        w*X+x*W+y*Z-z*Y,
        w*Y-x*Z+y*W+z*X,
        w*Z+x*Y-y*X+z*W,
        w*W-x*X-y*Y-z*Z
    ]


def clearance(t: float) -> float:
    lo,hi=ANKLE_WINDOW
    if t <= lo or t >= hi:return 0.0
    u=(t-lo)/(hi-lo)
    return math.sin(math.pi*u)**2


def main() -> None:
    data=SOURCE.read_bytes()
    magic,version,length=struct.unpack_from("<4sII",data,0)
    assert magic==b"glTF" and version==2 and length==len(data)
    json_len,json_tag=struct.unpack_from("<II",data,12)
    assert json_tag==0x4e4f534a
    doc=json.loads(data[20:20+json_len])
    bin_header=20+json_len
    bin_len,bin_tag=struct.unpack_from("<II",data,bin_header)
    assert bin_tag==0x004e4942
    blob=bytearray(data[bin_header+8:bin_header+8+bin_len])
    assert len(blob)==bin_len
    nodes=doc["nodes"]

    def accessor_values(index: int) -> list[list[float]]:
        a=doc["accessors"][index]
        v=doc["bufferViews"][a["bufferView"]]
        assert a["componentType"]==5126, (index,a)
        num={"SCALAR":1,"VEC3":3,"VEC4":4}[a["type"]]
        stride=v.get("byteStride",4*num)
        begin=v["byteOffset"]+a.get("byteOffset",0)
        return [list(struct.unpack_from("<"+"f"*num,blob,begin+i*stride))
                for i in range(a["count"])]

    def append_float_accessor(samples: list[list[float]]) -> int:
        width=len(samples[0])
        assert width in (1,3,4)
        align4(blob)
        start=len(blob)
        for row in samples:
            blob.extend(struct.pack("<"+"f"*width,*row))
        view=len(doc["bufferViews"])
        doc["bufferViews"].append({"buffer":0,"byteOffset":start,"byteLength":len(blob)-start})
        acc=len(doc["accessors"])
        doc["accessors"].append({"bufferView":view,"componentType":5126,
                                 "count":len(samples),
                                 "type":{1:"SCALAR",3:"VEC3",4:"VEC4"}[width],
                                 "min":[min(row[k] for row in samples) for k in range(width)],
                                 "max":[max(row[k] for row in samples) for k in range(width)]})
        return acc

    def get_anim(name: str) -> dict:
        return next(a for a in doc["animations"] if a["name"]==name)

    source_lower=get_anim(SOURCE_LOWER)
    source_upper=get_anim(SOURCE_UPPER)
    length=max(row[0] for channel in source_lower["channels"]
               for row in accessor_values(source_lower["samplers"][channel["sampler"]]["input"]))
    print("SOURCE_MOCAP_DURATION",length)
    upper_length=max(row[0] for channel in source_upper["channels"]
                     for row in accessor_values(source_upper["samplers"][channel["sampler"]]["input"]))
    print("SOURCE_UPPER_DURATION",upper_length)

    new={"name":FINAL_CLIP,"samplers":[],"channels":[]}
    def add_channel(node_id: int, path: str, input_acc: int, output_acc: int,
                    interpolation="LINEAR") -> None:
        si=len(new["samplers"])
        new["samplers"].append({"input":input_acc,"output":output_acc,"interpolation":interpolation})
        new["channels"].append({"sampler":si,"target":{"node":node_id,"path":path}})

    # Copy original captured hip/leg transforms. Adjust only LEFT FOOT's toe
    # clearance during its early swing, using an authored, finite animation curve.
    for channel in source_lower["channels"]:
        sampler=source_lower["samplers"][channel["sampler"]]
        target=channel["target"]
        node_id=target["node"]
        node_name=nodes[node_id].get("name","")
        path=target["path"]
        inp=sampler["input"]; out=sampler["output"]
        if node_name.endswith("LeftFoot") and path=="rotation":
            orig_t=[r[0] for r in accessor_values(inp)]
            orig_q=accessor_values(out)
            def sample_q(t):
                if t<=orig_t[0]:return orig_q[0]
                if t>=orig_t[-1]:return orig_q[-1]
                for j in range(1,len(orig_t)):
                    if t<=orig_t[j]:
                        return slerp(orig_q[j-1],orig_q[j],
                                     (t-orig_t[j-1])/(orig_t[j]-orig_t[j-1]))
                return orig_q[-1]
            times=[length*i/120 for i in range(121)]
            values=[]
            for t in times:
                q=sample_q(t)
                angle=math.radians(ANKLE_CLEARANCE_DEGREES)*clearance(t)
                correction=[math.sin(angle/2),0,0,math.cos(angle/2)]
                values.append(quat_mul(q,correction))
            inp=append_float_accessor([[t] for t in times])
            out=append_float_accessor(values)
        add_channel(node_id,path,inp,out,sampler.get("interpolation","LINEAR"))

    # Bake genuine authored arm/torso motion, but limit its amplitude to
    # physically plausible small walk swings. The source's "walk" arm keyframes
    # include extreme poses that cannot be used as-is.
    upper_names=("Spine","Spine1","Spine2","Neck","Head",
                 "LeftShoulder","LeftArm","LeftForeArm","LeftHand",
                 "RightShoulder","RightArm","RightForeArm","RightHand")
    angles={"Spine":3,"Spine1":4,"Spine2":4,"Neck":2,"Head":2,
            "LeftShoulder":9,"RightShoulder":9,
            "LeftArm":20,"RightArm":20,
            "LeftForeArm":16,"RightForeArm":16,
            "LeftHand":10,"RightHand":10}

    def at_time(ts,quats,t):
        if t<=ts[0]:return quats[0]
        if t>=ts[-1]:return quats[-1]
        for j in range(1,len(ts)):
            if t<=ts[j]:
                return slerp(quats[j-1],quats[j],(t-ts[j-1])/(ts[j]-ts[j-1]))
        return quats[-1]

    def limited(rest,q,part):
        dot=abs(sum(x*y for x,y in zip(normalize(rest),normalize(q))))
        delta=2*math.acos(min(1,max(-1,dot)))
        limit=math.radians(angles[part])
        f=min(UPPER_BLEND,limit/max(delta,1e-6))
        return slerp(rest,q,f)

    added=[]
    for channel in source_upper["channels"]:
        target=channel["target"]
        name=nodes[target["node"]].get("name","")
        part=name.split(":")[-1]
        if part not in upper_names or target["path"]!="rotation":continue
        sampler=source_upper["samplers"][channel["sampler"]]
        old_times=[r[0] for r in accessor_values(sampler["input"])]
        old_quats=accessor_values(sampler["output"])
        rest=nodes[target["node"]].get("rotation",[0,0,0,1])
        ticks=[length*i/120 for i in range(121)]
        smooth=[]
        for t in ticks:
            src_t=t*(upper_length/length)
            q=limited(rest,at_time(old_times,old_quats,src_t),part)
            if part == "Spine":
                tilt = math.radians(8.0)
                q = quat_mul([math.sin(tilt/2),0,0,math.cos(tilt/2)],q)
            if part in ("LeftArm", "RightArm"):
                # Gentle opposing arm swings baked into the actual animation.
                direction = 1.0 if part == "LeftArm" else -1.0
                theta = math.radians(10.0) * direction * math.sin(2*math.pi*t/length)
                q = quat_mul([math.sin(theta/2),0,0,math.cos(theta/2)],q)
            smooth.append(q)
        # The original "walk" is not loop-matched. Close the clip smoothly
        # so shoulders/arms never pop on each 1.2-second repeat.
        for i in range(105,121):
            u=(i-105)/15
            u=u*u*(3-2*u)
            smooth[i]=slerp(smooth[i],smooth[0],u)
        add_channel(target["node"],"rotation",
                    append_float_accessor([[t] for t in ticks]),
                    append_float_accessor(smooth))
        added.append(part)
    assert len(added)>=10,added
    doc["animations"].append(new)
    align4(blob)
    doc["buffers"][0]["byteLength"]=len(blob)
    jbytes=json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    jbytes+=b" " * (-len(jbytes)%4)
    out=bytearray(struct.pack("<4sII",b"glTF",2,12+8+len(jbytes)+8+len(blob)))
    out.extend(struct.pack("<II",len(jbytes),0x4e4f534a));out.extend(jbytes)
    out.extend(struct.pack("<II",len(blob),0x004e4942));out.extend(blob)
    OUTPUT.write_bytes(out)
    print("AUTHORED_GLB",OUTPUT,"BYTES",len(out),"UPPER_BONES",added,
          "FOOT_CLEARANCE_DEGREES",ANKLE_CLEARANCE_DEGREES)


if __name__=="__main__":
    main()
