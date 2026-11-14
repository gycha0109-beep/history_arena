"""Free-public TRELLIS.2 ZeroGPU test for a user-provided character image.
No paid API or GPU job. Output is experimental and needs visual QA.
"""
from pathlib import Path
import shutil, sys, time, traceback, json
from gradio_client import Client, handle_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets/characters/musashi/rebuild_v1/trellis2_trial"
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/"assets/characters/musashi/rebuild_v1/reference_front_256.jpg"
assert SOURCE.exists(),f"Missing uploaded front reference: {SOURCE}"
print("TRIAL_SOURCE", SOURCE, "bytes",SOURCE.stat().st_size,flush=True)
client=Client("microsoft/TRELLIS.2", verbose=False)
print("TRIAL_CONNECTED",flush=True)
try:
    client.predict(api_name="/start_session")
    print("TRIAL_SESSION_STARTED",flush=True)
    try:
        preprocessed=client.predict(handle_file(str(SOURCE)),api_name="/preprocess_image")
        print("TRIAL_PREPROCESSED",str(preprocessed)[:240],flush=True)
        inp=handle_file(str(preprocessed))
    except Exception as e:
        print("TRIAL_PREPROCESS_FAILED",str(e)[:450],flush=True)
        inp=handle_file(str(SOURCE))
    html=client.predict(
        inp, 104729, "512",
        7.5, 0.7, 12, 5.0,
        7.5, 0.5, 12, 3.0,
        1.0, 0.0, 12, 3.0,
        api_name="/image_to_3d",
    )
    print("TRIAL_GENERATION_RESPONSE",str(html)[:300],flush=True)
    file_result=client.predict(150000,1024,api_name="/extract_glb")
    print("TRIAL_EXTRACT_RESPONSE",str(file_result)[:500],flush=True)
    candidates=[x for x in (file_result if isinstance(file_result,(list,tuple)) else [file_result]) if isinstance(x,str) and Path(x).is_file()]
    if not candidates:
        raise RuntimeError("No downloaded GLB from extract_glb output")
    final=OUT/"musashi_trellis2_512_trial.glb"
    shutil.copy2(candidates[0],final)
    assert final.stat().st_size>4096, "GLB output unexpectedly small"
    (OUT/"trial_manifest.json").write_text(json.dumps({
        "provider":"microsoft/TRELLIS.2 public ZeroGPU Space",
        "input":str(SOURCE.relative_to(ROOT)),
        "input_size_px":256,
        "resolution":"512",
        "model_path":str(final.relative_to(ROOT)),
        "status":"UNREVIEWED",
    },indent=2),encoding="utf-8")
    print("TRIAL_GLB_SAVED",str(final),"bytes",final.stat().st_size,flush=True)
except Exception as e:
    print("TRIAL_FAILED",str(e),flush=True)
    traceback.print_exc()
    sys.exit(2)
finally:
    try:client.predict(api_name="/end_session")
    except Exception:pass
