from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "https://vibeassets.io/download/zpepqtthci?combined=1"
EXPECTED_SHA256 = "940444190abb1f3731675678277e9c3f27be1783966987f0a02ccd9fd1405193"
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "samples" / "external" / "camper_walk_cc0.glb"


def main() -> int:
    if DEST.is_file():
        current = hashlib.sha256(DEST.read_bytes()).hexdigest()
        if current == EXPECTED_SHA256:
            print(f"CC0 WALK REFERENCE OK: {DEST}")
            return 0
        print("기존 모델 파일의 SHA256이 다른 버전입니다. 임의로 덮어쓰지 않습니다.")
        return 1

    DEST.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "LegendaryBattle-AssetQA/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            body = response.read(12_000_000)
    except Exception as exc:
        print(f"공개 CC0 모델을 받지 못했습니다: {exc}")
        return 1

    got = hashlib.sha256(body).hexdigest()
    if got != EXPECTED_SHA256:
        print(f"다운로드 SHA256 불일치: {got}. 저장하지 않았습니다.")
        return 1
    DEST.write_bytes(body)
    print(f"CC0 WALK REFERENCE DOWNLOAD OK: {DEST} / {len(body)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
