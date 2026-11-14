from pathlib import Path
import shutil, traceback, sys, json
from gradio_client import Client, handle_file
ROOT=Path(__file__).resolve().parents[1]
inp=ROOT/"assets/characters/musashi/rebuild_v1/reference_front_256.jpg"
out=ROOT/"assets/characters/musashi/rebuild_v1/sf3d_trial"
out.mkdir(parents=True,exist_ok=True)
assert inp.is_file()
print("SF3D_INPUT",str(inp),inp.stat().st_size,flush=True)
try:
    c=Client("stabilityai/stable-fast-3d",verbose=False)
    print("SF3D_CONNECTED",flush=True)
    result=c.predict(handle_file(str(inp)), 0.85, "None", -1, 1024,api_name="/run_button")
    print("SF3D_RESULT",str(result)[:500],flush=True)
    if isinstance(result, (tuple,list)):
        for k,i in enumerate(result):
            if isinstance(i,str) and Path(i).is_file():
                extension=Path(i).suffix.lower()
                if extension not in (".glb",".png",".jpg",".jpeg",".webp"): extension=".bin"
                path=out/("musashi_sf3d_model.glb" if extension==".glb" else f"result_{k}"+extension)
                shutil.copy2(i,path)
                print("SF3D_SAVED",str(path),path.stat().st_size,flush=True)
    glbs=list(out.glob("*.glb"))
    if not glbs: raise RuntimeError("No GLB returned from public Space")
    (out/"manifest.json").write_text(json.dumps({"provider":"stabilityai/stable-fast-3d", "source":"reference_front_256.jpg", "output":glbs[0].name,"status":"NOT_APPROVED"},indent=2),encoding="utf-8")
except Exception as e:
    print("SF3D_FAILED",str(e),flush=True)
    traceback.print_exc()
    sys.exit(2)
