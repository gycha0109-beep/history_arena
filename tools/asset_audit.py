#!/usr/bin/env python3
"""Check exported GLB structure before attempting a Godot animation preview.

Standard-library only. This is a structural audit, not a visual-quality or
rig-weight validation. It never modifies imported binary assets.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any

GLB_MAGIC = b"glTF"
JSON_CHUNK = 0x4E4F534A
MAX_FILE_BYTES = 600 * 1024 * 1024

REQUIRED_MOTIONS = ("idle", "walk", "attack_light", "hit_react")


class AuditError(Exception):
    pass


def load_glb(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AuditError(f"파일이 없습니다: {path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise AuditError(f"파일 크기가 600MB를 초과합니다: {path}")
    with path.open("rb") as fp:
        header = fp.read(12)
        if len(header) != 12:
            raise AuditError("GLB 헤더가 잘렸습니다.")
        magic, version, total_length = struct.unpack("<4sII", header)
        if magic != GLB_MAGIC or version != 2:
            raise AuditError("glTF 2.0 GLB 파일이 아닙니다.")
        if total_length != path.stat().st_size:
            raise AuditError("GLB 헤더의 길이와 실제 파일 크기가 다릅니다.")
        chunk_header = fp.read(8)
        if len(chunk_header) != 8:
            raise AuditError("GLB JSON 청크가 없습니다.")
        chunk_len, chunk_type = struct.unpack("<II", chunk_header)
        if chunk_type != JSON_CHUNK or chunk_len % 4 != 0:
            raise AuditError("첫 GLB 청크가 정상적인 JSON이 아닙니다.")
        if chunk_len > total_length - 20:
            raise AuditError("GLB JSON 청크가 파일 범위를 벗어났습니다.")
        raw_json = fp.read(chunk_len)
        if len(raw_json) != chunk_len:
            raise AuditError("GLB JSON 데이터가 잘렸습니다.")
    try:
        document = json.loads(raw_json.decode("utf-8").rstrip(" \t\r\n\x00"))
    except (ValueError, UnicodeError) as exc:
        raise AuditError(f"GLB JSON을 읽지 못했습니다: {exc}") from exc
    if not isinstance(document, dict) or document.get("asset", {}).get("version") != "2.0":
        raise AuditError("glTF 2.0 asset 정보가 없습니다.")
    return document


def _nodes(document: dict[str, Any]) -> list[dict[str, Any]]:
    return document.get("nodes", [])


def _skin_bone_names(document: dict[str, Any]) -> set[str]:
    nodes = _nodes(document)
    names: set[str] = set()
    for skin in document.get("skins", []):
        for index in skin.get("joints", []):
            if isinstance(index, int) and 0 <= index < len(nodes):
                names.add(str(nodes[index].get("name", "")))
    return names


def _animation_names(document: dict[str, Any]) -> list[str]:
    return [str(animation.get("name", f"Animation_{i}"))
            for i, animation in enumerate(document.get("animations", []))]


def _triangle_estimate(document: dict[str, Any]) -> int:
    total = 0
    accessors = document.get("accessors", [])
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                continue
            index = primitive.get("indices")
            if isinstance(index, int) and 0 <= index < len(accessors):
                total += int(accessors[index].get("count", 0)) // 3
            else:
                vertex_accessor = primitive.get("attributes", {}).get("POSITION")
                if isinstance(vertex_accessor, int) and 0 <= vertex_accessor < len(accessors):
                    total += int(accessors[vertex_accessor].get("count", 0)) // 3
    return total


def audit_character(manifest_path: Path, root: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "type": "character", "manifest": str(manifest_path),
        "errors": [], "warnings": [], "summary": {},
    }
    errors: list[str] = report["errors"]
    warnings: list[str] = report["warnings"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"캐릭터 설정을 읽지 못했습니다: {exc}")
        return report
    if not isinstance(manifest, dict):
        errors.append("캐릭터 설정은 JSON 객체여야 합니다.")
        return report
    fighter_id = str(manifest.get("id", "unknown"))
    report["id"] = fighter_id

    model_uri = str(manifest.get("model_path", ""))
    if not model_uri.startswith("res://") or not model_uri.lower().endswith(".glb"):
        errors.append("model_path는 res://로 시작하는 GLB 경로여야 합니다.")
        return report
    model_path = root / model_uri.removeprefix("res://")
    try:
        doc = load_glb(model_path)
    except AuditError as exc:
        errors.append(f"{fighter_id} 모델: {exc}")
        return report

    mesh_count = len(doc.get("meshes", []))
    skins = doc.get("skins", [])
    bones = _skin_bone_names(doc)
    anims = _animation_names(doc)
    report["summary"] = {
        "file": str(model_path),
        "meshes": mesh_count,
        "skins": len(skins),
        "bones": len(bones),
        "triangles_estimate": _triangle_estimate(doc),
        "animation_names": anims,
    }
    if mesh_count == 0:
        errors.append("모델에 3D 메시가 없습니다.")
    if len(skins) == 0:
        errors.append("스킨·뼈 정보가 없습니다. 리깅된 GLB로 내보내세요.")
    if len(bones) < 10:
        errors.append("인체 관절이 지나치게 적습니다. 스켈레톤을 확인하세요.")
    if not anims:
        errors.append("애니메이션이 없습니다. 필수 동작을 포함해 내보내세요.")

    clips = manifest.get("animation_clips", {})
    if not isinstance(clips, dict):
        errors.append("animation_clips는 동작별 이름 목록이어야 합니다.")
        clips = {}
    for motion in REQUIRED_MOTIONS:
        configured = clips.get(motion, [])
        if not isinstance(configured, list) or not configured:
            errors.append(f"필수 동작 {motion}에 후보 이름이 없습니다.")
        elif not any(str(item) in anims for item in configured):
            errors.append(f"필수 동작 {motion} 미발견. 실제 클립: {', '.join(anims)}")

    hand_names = manifest.get("hand_bone_candidates", [])
    if not isinstance(hand_names, list):
        errors.append("hand_bone_candidates는 이름 목록이어야 합니다.")
        hand_names = []
    weapon_uri = str(manifest.get("weapon_path", ""))
    if weapon_uri:
        if not any(str(name) in bones for name in hand_names):
            errors.append(f"검을 연결할 손뼈를 찾지 못했습니다. 실제 뼈 이름 예: {', '.join(sorted(bones)[:16])}")
        if not weapon_uri.startswith("res://") or not weapon_uri.lower().endswith(".glb"):
            errors.append("weapon_path는 res://로 시작하는 GLB 경로여야 합니다.")
        else:
            weapon_path = root / weapon_uri.removeprefix("res://")
            weapon_report = audit_weapon(weapon_path)
            report["weapon"] = weapon_report
            errors.extend(weapon_report["errors"])
            warnings.extend(weapon_report["warnings"])

    if _triangle_estimate(doc) > 180_000:
        warnings.append("삼각형이 18만 개 이상입니다. GTX 1070 실시간 화면 성능을 측정하세요.")
    if any(node.get("scale", [1, 1, 1]) != [1, 1, 1] for node in _nodes(doc)):
        warnings.append("비기본 배율을 사용하는 노드가 있습니다. 모델 크기와 손잡이 위치를 확인하세요.")
    for anim in doc.get("animations", []):
        if any(channel.get("target", {}).get("path") == "scale" for channel in anim.get("channels", [])):
            warnings.append("스케일 애니메이션이 있습니다. 관절/메시 비율 왜곡 여부를 확인하세요.")
            break

    return report


def audit_weapon(path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "type": "weapon", "file": str(path), "errors": [], "warnings": [], "summary": {},
    }
    errors: list[str] = report["errors"]
    try:
        doc = load_glb(path)
    except AuditError as exc:
        errors.append(f"검 모델: {exc}")
        return report
    meshes = doc.get("meshes", [])
    report["summary"] = {
        "meshes": len(meshes),
        "triangles_estimate": _triangle_estimate(doc),
    }
    if not meshes:
        errors.append("검 모델에 3D 메시가 없습니다.")
    if doc.get("skins"):
        errors.append("검이 스킨/뼈에 묶여 있습니다. 검은 별도 고정 모델로 내보내세요.")
    if doc.get("animations"):
        errors.append("검 파일에 애니메이션이 있습니다. 길이 변형 위험이 있으므로 정적 모델을 사용하세요.")
    if any(mesh.get("weights") or any(primitive.get("targets") for primitive in mesh.get("primitives", []))
           for mesh in meshes):
        errors.append("검에 모프 변형이 있습니다. 검 길이가 변하지 않도록 정적 메시를 사용하세요.")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Meshy/Blender GLB 리깅·모션·검 구조 검사")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--character", choices=("musashi", "bruce_lee"), default=None)
    parser.add_argument("--json", action="store_true", help="검사 결과를 JSON으로 출력")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    targets = [args.character] if args.character else ["musashi", "bruce_lee"]
    reports = [
        audit_character(root / "assets" / "characters" / target / "character.json", root)
        for target in targets
    ]
    passed = all(not report["errors"] for report in reports)
    if args.json:
        print(json.dumps({"passed": passed, "characters": reports}, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"[{'통과' if not report['errors'] else '실패'}] {report.get('id', 'unknown')}")
            summary = report.get("summary", {})
            if summary:
                print(f"  메시 {summary.get('meshes', 0)}, 뼈 {summary.get('bones', 0)}, "
                      f"삼각형 추정 {summary.get('triangles_estimate', 0)}")
            for error in report["errors"]:
                print(f"  오류: {error}")
            for warning in report["warnings"]:
                print(f"  주의: {warning}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
