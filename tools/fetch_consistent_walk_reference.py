"""Fetch and verify the CC0 full-body gait reference pack (not committed)."""
from pathlib import Path
import hashlib
import io
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "samples" / "external"
PACK = DEST / "Kinemiq_Free_Animations_CC0_GLB.zip"
EXTRACT = DEST / "kinemiq_cc0"
URL = "https://huggingface.co/datasets/Kinemiq/free-game-animations/resolve/main/KinemIQ_Free_Animations_CC0_GLB.zip?download=true"
SHA256 = "64ca5ab4a92c9da079c5e88ca509391b0a58a24ccf2a1307b16e2f0fc6b23ffc"


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    if not PACK.exists():
        print("Downloading original CC0 gait asset...")
        try:
            req = urllib.request.Request(URL, headers={"User-Agent":"LegendaryBattle-CC0-QA/1.0"})
            with urllib.request.urlopen(req, timeout=45) as response:
                data = response.read(8_000_000)
        except Exception as exc:
            print("Download failed:", exc)
            return 1
        if hashlib.sha256(data).hexdigest() != SHA256:
            print("Asset SHA256 mismatch. Refusing unverified file.")
            return 1
        PACK.write_bytes(data)
    if hashlib.sha256(PACK.read_bytes()).hexdigest() != SHA256:
        print("Asset SHA256 mismatch. Existing file not overwritten.")
        return 1

    with zipfile.ZipFile(PACK) as zf:
        names = zf.namelist()
        if not any(name.endswith("KinemIQ_Mannequin.glb") for name in names):
            print("Missing mannequin")
            return 1
        for member in names:
            path = Path(member)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe zip path")
            if path.suffix.lower() not in (".glb",".txt"):
                continue
            dst = EXTRACT / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                dst.write_bytes(zf.read(member))
    print("VERIFIED_CC0_WALK_SOURCE",EXTRACT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
