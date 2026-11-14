"""Validate real V4 HTML media, five-second 60 fps video and Blender QA file."""
from pathlib import Path
from html.parser import HTMLParser
import subprocess,json
out=Path(__file__).resolve().parents[1]/"captures/qa/dual_grip_guard_v5"
class References(HTMLParser):
 def __init__(self):
  super().__init__()
  self.paths=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for key in ("href","src"):
   path=a.get(key,"")
   if path and not path.startswith(("http://","https://","#")):
    self.paths.append(path)
html=out/"dual_grip_guard_preview.html"
assert html.is_file()
refs=References()
refs.feed(html.read_text(encoding="utf-8"))
missing=[p for p in refs.paths if not (out/p).is_file()]
assert not missing, missing
assert len(refs.paths)>=18,len(refs.paths)
video=out/"dual_guard_angles_5s.mp4"
info=json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate,nb_frames","-show_entries","format=duration","-of","json",str(video)],text=True))
v=info["streams"][0]
assert (v["width"],v["height"],v["r_frame_rate"],int(v["nb_frames"]))==(720,1280,"60/1",300),v
assert abs(float(info["format"]["duration"])-5)<.01
assert (out/"dual_guard_upperbody_work.blend").is_file()
audit=json.loads((out/"grip_audit.json").read_text(encoding="utf-8"))
assert audit["left_index"]["penetrating"]<=5
print("V5_HTML_QA_OK",len(refs.paths),"links")
print("V5_VIDEO_QA_OK",v["width"],v["height"],v["r_frame_rate"],v["nb_frames"],info["format"]["duration"])
print("V5_GRIP_QA_OK",audit["left_index"])
