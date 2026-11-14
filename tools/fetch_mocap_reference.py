#!/usr/bin/env python3
"""Fetch public third-party reference animation strictly for internal visual QA.

Sources and licensing are documented in docs/MOCAP_GAIT_COMPARISON.md.
The output is excluded from the repository. Never overwrite user assets.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/cktang88/3d-fps/main/public/assets/models/characters/soldier.glb"
EXPECTED_SHA256 = "6f229176b1ca49ff33605718ebfcca7fcee8f65d6d311ce3c86693df9310d2d7"
DEST = Path(__file__).resolve().parents[1] / "samples" / "external" / "soldier_mocap_ref.glb"


def main() -> int:
    if DEST.is_file():
        digest = hashlib.sha256(DEST.read_bytes()).hexdigest()
        if digest == EXPECTED_SHA256:
            print(f"REFERENCE OK: {DEST}")
            return 0
        print("원본 검증 값이 달라 기존 파일을 보존했습니다.")
        return 1
    DEST.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(
            urllib.request.Request(URL, headers={"User-Agent": "LegendaryBattleQA/1.0"}),
            timeout=40,
        ) as response:
            data = response.read(15_000_000)
    except Exception as err:
        print(f"참조 모델 다운로드 실패: {err}")
        return 1
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        print("참조 모델 검증 실패. 파일을 저장하지 않았습니다.")
        return 1
    DEST.write_bytes(data)
    print(f"REFERENCE DOWNLOADED: {DEST} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
