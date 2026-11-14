from pathlib import Path
from gradio_client import Client,handle_file
from huggingface_hub import get_token
import shutil,traceback,sys
root=Path(__file__).resolve().parents[1]
source=root/'assets/characters/musashi/rebuild_v1/reference_front_256.jpg'
out=root/'assets/characters/musashi/rebuild_v1/instantmesh_trial'
out.mkdir(parents=True,exist_ok=True)
try:
    c=Client('TencentARC/InstantMesh',hf_token=get_token(),verbose=False)
    print('INSTANTMESH_CONNECTED',flush=True)
    pre=c.predict(handle_file(str(source)),True,api_name='/preprocess')
    print('INSTANTMESH_PREPARED',str(pre)[:160],flush=True)
    mv=c.predict(handle_file(str(pre)),50,42,api_name='/generate_mvs')
    if mv and Path(mv).exists():
        from PIL import Image
        Image.open(mv).convert('RGB').save(out/'generated_multiview_clean.png')
    print('INSTANTMESH_MV',str(mv)[:160],flush=True)
    result=c.predict(api_name='/make3d')
    print('INSTANTMESH_RESULT',str(result)[:350],flush=True)
    for i,p in enumerate(result):
        if isinstance(p,str) and Path(p).is_file():
            ext=Path(p).suffix
            path=out/f'generated_{i}{ext}'
            shutil.copy2(p,path)
            print('INSTANTMESH_SAVED',path,path.stat().st_size,flush=True)
except Exception as e:
    print('INSTANTMESH_FAILED',str(e),flush=True)
    traceback.print_exc()
    sys.exit(2)
