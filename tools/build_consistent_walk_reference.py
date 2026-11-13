from pathlib import Path
import json,struct
root=Path(__file__).resolve().parents[1]/"samples"/"external"
src=root/"kinemiq_cc0"
def read(p):
 b=p.read_bytes();magic,ver,size=struct.unpack_from("<4sII",b,0);assert magic==b"glTF" and ver==2 and size==len(b)
 n,tag=struct.unpack_from("<II",b,12);assert tag==0x4e4f534a
 d=json.loads(b[20:20+n]);off=20+n;bn,tag=struct.unpack_from("<II",b,off);assert tag==0x004e4942
 return d,bytearray(b[off+8:off+8+bn])
def samples(d,b,i):
 a=d["accessors"][i];v=d["bufferViews"][a["bufferView"]];w={"SCALAR":1,"VEC3":3,"VEC4":4}[a["type"]];assert a["componentType"]==5126
 st=v.get("byteOffset",0)+a.get("byteOffset",0);step=v.get("byteStride",4*w)
 return [list(struct.unpack_from("<"+"f"*w,b,st+j*step)) for j in range(a["count"])]
def rewrite(d,b,i,rows):
 a=d["accessors"][i];v=d["bufferViews"][a["bufferView"]];w=len(rows[0]);st=v.get("byteOffset",0)+a.get("byteOffset",0);step=v.get("byteStride",4*w)
 for j,row in enumerate(rows):struct.pack_into("<"+"f"*w,b,st+j*step,*row)
 a["min"]=[min(row[k] for row in rows) for k in range(w)];a["max"]=[max(row[k] for row in rows) for k in range(w)]
def pad(b):b.extend(bytes(-len(b)%4))
main,mb=read(src/"KinemIQ_Mannequin.glb")
node_map={n["name"]:i for i,n in enumerate(main["nodes"]) if "name" in n}
for name in ("Walk_forwards","Walk_formal"):
 d,b=read(src/"GLB"/(name+".glb"));anim=d["animations"][0]
 mapping={i:node_map[n["name"]] for i,n in enumerate(d["nodes"]) if n.get("name") in node_map}
 assert len(mapping)>=65 and len(anim["channels"])>=60
 channel=next(c for c in anim["channels"] if d["nodes"][c["target"]["node"]].get("name")=="pelvis" and c["target"]["path"]=="translation")
 sm=anim["samplers"][channel["sampler"]];ts=[v[0] for v in samples(d,b,sm["input"])];vals=samples(d,b,sm["output"]);length=ts[-1]-ts[0]
 delta=[vals[-1][k]-vals[0][k] for k in range(3)];assert length>0.5 and abs(delta[1])>0.5
 rewrite(d,b,sm["output"],[[v[k]-(t-ts[0])/length*delta[k] for k in range(3)] for t,v in zip(ts,vals)])
 pad(mb);shift=len(mb);view_base=len(main["bufferViews"]);acc_base=len(main["accessors"])
 for view in d["bufferViews"]:
  v=dict(view);assert v.get("buffer",0)==0;v["byteOffset"]=v.get("byteOffset",0)+shift;main["bufferViews"].append(v)
 for acc in d["accessors"]:
  a=dict(acc);a["bufferView"]+=view_base;main["accessors"].append(a)
 mb.extend(b)
 copied={"name":name,"samplers":[{"input":sm["input"]+acc_base,"output":sm["output"]+acc_base,"interpolation":sm.get("interpolation","LINEAR")} for sm in anim["samplers"]],"channels":[{"sampler":c["sampler"],"target":{"node":mapping[c["target"]["node"]],"path":c["target"]["path"]}} for c in anim["channels"]]}
 main["animations"].append(copied)
 print("FULL_BODY",name,"channels",len(copied["channels"]),"seconds",round(length,3),"meters_per_second",round(abs(delta[1])/length,3),"root_delta",delta)
pad(mb);main["buffers"][0]["byteLength"]=len(mb)
js=json.dumps(main,separators=(",",":")).encode("utf8");js+=b" "*(-len(js)%4)
out=struct.pack("<4sII",b"glTF",2,12+8+len(js)+8+len(mb))+struct.pack("<II",len(js),0x4e4f534a)+js+struct.pack("<II",len(mb),0x004e4942)+mb
p=root/"kinemiq_full_body_walks.glb";p.write_bytes(out);print("OUTPUT",p,len(out))
