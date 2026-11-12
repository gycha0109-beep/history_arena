from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asset_audit import audit_character, audit_weapon, load_glb, AuditError


def write_fixture_glb(path: Path, *, weapon=False, bad_bone=False,
                      missing_attack=False, skinned_weapon=False,
                      animated_weapon=False) -> None:
    nodes = [{"name": "RightHand" if i == 11 and not bad_bone else f"HumanBone{i}"}
             for i in range(12)]
    data = {
        "asset": {"version": "2.0"},
        "nodes": nodes,
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "accessors": [{"count": 300}],
    }
    if weapon:
        if skinned_weapon:
            data["skins"] = [{"joints": list(range(12))}]
        if animated_weapon:
            data["animations"] = [{"name": "stretch", "channels": [
                {"target": {"node": 0, "path": "scale"}}
            ]}]
    else:
        data["skins"] = [{"joints": list(range(12))}]
        data["animations"] = [{"name": name} for name in
                              ("Idle", "Walk", "HitReact") +
                              (() if missing_attack else ("QuickCut",))]
    json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
    padded_json = json_bytes + b" " * ((-len(json_bytes)) % 4)
    glb_length = 12 + 8 + len(padded_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, glb_length)
                     + struct.pack("<II", len(padded_json), 0x4E4F534A)
                     + padded_json)


def create_manifest(root: Path) -> Path:
    path = root / "assets/characters/musashi/character.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "id": "musashi",
        "model_path": "res://assets/characters/musashi/models/musashi.glb",
        "weapon_path": "res://assets/weapons/katana.glb",
        "hand_bone_candidates": ["RightHand"],
        "animation_clips": {
            "idle": ["Idle"], "walk": ["Walk"],
            "attack_light": ["QuickCut"], "hit_react": ["HitReact"],
        },
    }), encoding="utf-8")
    return path


class GlbAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.manifest = create_manifest(self.root)
        self.model = self.root / "assets/characters/musashi/models/musashi.glb"
        self.weapon = self.root / "assets/weapons/katana.glb"

    def _write_complete_fixture(self) -> None:
        write_fixture_glb(self.model)
        write_fixture_glb(self.weapon, weapon=True)

    def test_valid_character_and_rigid_sword_structure(self) -> None:
        self._write_complete_fixture()
        report = audit_character(self.manifest, self.root)
        self.assertEqual([], report["errors"])
        self.assertEqual(100, report["summary"]["triangles_estimate"])
        self.assertEqual(12, report["summary"]["bones"])

    def test_missing_model_is_rejected(self) -> None:
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("파일이 없습니다" in error for error in report["errors"]))

    def test_missing_attack_clip_is_rejected(self) -> None:
        write_fixture_glb(self.model, missing_attack=True)
        write_fixture_glb(self.weapon, weapon=True)
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("attack_light" in error for error in report["errors"]))

    def test_wrong_hand_bone_is_rejected(self) -> None:
        write_fixture_glb(self.model, bad_bone=True)
        write_fixture_glb(self.weapon, weapon=True)
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("손뼈" in error for error in report["errors"]))

    def test_skinned_sword_is_rejected(self) -> None:
        write_fixture_glb(self.weapon, weapon=True, skinned_weapon=True)
        report = audit_weapon(self.weapon)
        self.assertTrue(any("스킨/뼈" in error for error in report["errors"]))

    def test_animated_sword_is_rejected(self) -> None:
        write_fixture_glb(self.weapon, weapon=True, animated_weapon=True)
        report = audit_weapon(self.weapon)
        self.assertTrue(any("애니메이션" in error for error in report["errors"]))

    def test_corrupt_glb_is_rejected(self) -> None:
        self.model.parent.mkdir(parents=True, exist_ok=True)
        self.model.write_bytes(b"wrong format")
        with self.assertRaises(AuditError):
            load_glb(self.model)


if __name__ == "__main__":
    unittest.main()
