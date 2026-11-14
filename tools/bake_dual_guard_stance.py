"""Build a stationary full-body dual-sword stance from KinemIQ's authored sword idle.
Original walk rig, rest pose, and foot tracks are not modified. CC0 visual QA only.
"""
import json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"samples"/"external"
SRC=ROOT/"kinemiq_two_sword_guard_walk.glb"
IDLE=ROOT/"kinemiq_cc0"/"GLB"/"Idle_with_a_sword.glb"
OUT=ROOT/"kinemiq_dual_guard_idle.glb"
def read(path):
 data=path.read_bytes()
 magic,version,total=struct.unpack_from("<4sII",data)
 assert magic==b"glTF" and version==2 and total==len(data)
 size,kind=struct.unpack_from("<II",data,12)
 assert kind==0x4e4f534a
 obj=json.loads(data[20:20+size])
 off=20+size
 bsize,btype=struct.unpack_from("<II",data,off)
 assert btype==0x004e4942
 return obj,bytearray(data[off+8:off+8+bsize])
def values(obj,binary,index):
 acc=obj["accessors"][index];view=obj["bufferViews"][acc["bufferView"]]
 size={"SCALAR":1,"VEC3":3,"VEC4":4}[acc["type"]]
 stride=view.get("byteStride",4*size)
 start=view.get("byteOffset",0)+acc.get("byteOffset",0)
 assert acc["componentType"]==5126
 return [list(struct.unpack_from("<"+"f"*size,binary,start+i*stride)) for i in range(acc["count"])]
def insert(obj,binary,items):
 size=len(items[0])
 binary.extend(bytes(-len(binary)%4))
 offset=len(binary)
 for row in items:binary.extend(struct.pack("<"+"f"*size,*row))
 view_id=len(obj["bufferViews"])
 obj["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(binary)-offset})
 index=len(obj["accessors"])
 obj["accessors"].append({"bufferView":view_id,"componentType":5126,"count":len(items),"type":{1:"SCALAR",3:"VEC3",4:"VEC4"}[size],"min":[min(row[k] for row in items) for k in range(size)],"max":[max(row[k] for row in items) for k in range(size)]})
 return index
def sample(ts, vs, t, is_rotation):
 if t<=ts[0][0]:return vs[0]
 if t>=ts[-1][0]:return vs[-1]
 for i in range(1,len(ts)):
  if ts[i][0]>=t:
   ratio=(t-ts[i-1][0])/(ts[i][0]-ts[i-1][0])
   a=vs[i-1];b=vs[i]
   if not is_rotation:return [x+(y-x)*ratio for x,y in zip(a,b)]
   dot=sum(x*y for x,y in zip(a,b))
   if dot<0:b=[-x for x in b];dot=-dot
   if dot>.9995:
    c=[x+(y-x)*ratio for x,y in zip(a,b)];norm=math.sqrt(sum(x*x for x in c));return [x/norm for x in c]
   theta=math.acos(max(-1,min(1,dot)))
   return [(math.sin((1-ratio)*theta)*x+math.sin(ratio*theta)*y)/math.sin(theta) for x,y in zip(a,b)]
 raise AssertionError("failed to sample")
source,buffer=read(SRC)
idle,other=read(IDLE)
nodes={node.get("name",""):i for i,node in enumerate(source["nodes"])}
action=idle["animations"][0]
animation={"name":"Idle_DualGuard","samplers":[],"channels":[]}
right_grip={}
for source_channel in action["channels"]:
 target=source_channel["target"]
 name=idle["nodes"][target["node"]].get("name","")
 if target["path"]=="rotation" and name.endswith("_r") and name.startswith(("thumb_","index_","middle_","ring_","pinky_")):
  sp=action["samplers"][source_channel["sampler"]]
  right_grip[name]=sample(values(idle,other,sp["input"]),values(idle,other,sp["output"]),0.45,True)
time_index=insert(source,buffer,[[0.0],[5.0]])
for channel in action["channels"]:
 target=channel["target"];name=idle["nodes"][target["node"]].get("name","")
 path=target["path"]
 if name not in nodes or path not in ("rotation","translation","scale"):continue
 sampler=action["samplers"][channel["sampler"]]
 times=values(idle,other,sampler["input"])
 output=values(idle,other,sampler["output"])
 assert sampler.get("interpolation","LINEAR")=="LINEAR"
 frame=sample(times,output,0.45,path=="rotation")
 if path=="rotation" and name.endswith("_l"):
  match=name[:-2]+"_r"
  if match in right_grip:
   q=right_grip[match]
   frame=[q[0],-q[1],-q[2],q[3]]
 output_index=insert(source,buffer,[frame,frame])
 sampler_id=len(animation["samplers"])
 animation["samplers"].append({"input":time_index,"output":output_index,"interpolation":"LINEAR"})
 animation["channels"].append({"sampler":sampler_id,"target":{"node":nodes[name],"path":path}})
assert len(animation["channels"])>=60,len(animation["channels"])
source["animations"].append(animation)
buffer.extend(bytes(-len(buffer)%4));source["buffers"][0]["byteLength"]=len(buffer)
j=json.dumps(source,separators=(",",":")).encode()
j+=b" "*(-len(j)%4)
raw=struct.pack("<4sII",b"glTF",2,12+8+len(j)+8+len(buffer))+struct.pack("<II",len(j),0x4e4f534a)+j+struct.pack("<II",len(buffer),0x004e4942)+buffer
OUT.write_bytes(raw)
print("IDLE_DUAL_GUARD_READY",len(animation["channels"]),"static tracks, 5s",len(raw),"bytes")
