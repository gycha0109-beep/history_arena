from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asset_audit import audit_character, audit_weapon, load_glb, AuditError


def write_glb(path: Path, *, weapon=False, bad_right=False, missing_attack=False,
              skinned_weapon=False, animated_weapon=False) -> None:
    nodes = []
    for index in range(12):
        name = f"HumanBone{index}"
        if index == 10:
            name = "LeftHand"
        if index == 11 and not bad_right:
            name = "RightHand"
        nodes.append({"name": name})
    doc = {
        "asset": {"version": "2.0"},
        "nodes": nodes,
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "accessors": [{"count": 300}],
    }
    if weapon:
        if skinned_weapon:
            doc["skins"] = [{"joints": list(range(12))}]
        if animated_weapon:
            doc["animations"] = [{"name": "stretch", "channels": [
                {"target": {"node": 0, "path": "scale"}}
            ]}]
    else:
        doc["skins"] = [{"joints": list(range(12))}]
        names = ["Idle", "Walk", "HitReact"]
        if not missing_attack:
            names.extend(["QuickCut", "WakizashiCut", "DualCross"])
        doc["animations"] = [{"name": name} for name in names]
    raw = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    padded = raw + b" " * ((-len(raw)) % 4)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(padded))
                     + struct.pack("<II", len(padded), 0x4E4F534A) + padded)


def manifest_for(root: Path) -> Path:
    path = root / "assets/characters/musashi/character.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": "musashi",
        "model_path": "res://assets/characters/musashi/models/musashi.glb",
        "weapons": [
            {"id": "katana", "hand": "right",
             "model_path": "res://assets/weapons/katana.glb",
             "hand_bone_candidates": ["RightHand"],
             "grip_position": [0, 0, 0], "grip_rotation_degrees": [0, 0, 0]},
            {"id": "wakizashi", "hand": "left",
             "model_path": "res://assets/weapons/wakizashi.glb",
             "hand_bone_candidates": ["LeftHand"],
             "grip_position": [0, 0, 0], "grip_rotation_degrees": [0, 0, 0]},
        ],
        "animation_clips": {
            "idle": ["Idle"], "walk": ["Walk"],
            "attack_light": ["QuickCut"], "hit_react": ["HitReact"],
            "attack_offhand": ["WakizashiCut"], "attack_dual": ["DualCross"],
        },
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class DualSwordAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = manifest_for(self.root)
        self.model = self.root / "assets/characters/musashi/models/musashi.glb"
        self.katana = self.root / "assets/weapons/katana.glb"
        self.wakizashi = self.root / "assets/weapons/wakizashi.glb"

    def _complete(self) -> None:
        write_glb(self.model)
        write_glb(self.katana, weapon=True)
        write_glb(self.wakizashi, weapon=True)

    def _edit_manifest(self, mutate) -> None:
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        mutate(data)
        self.manifest.write_text(json.dumps(data), encoding="utf-8")

    def test_two_independent_swords_pass(self) -> None:
        self._complete()
        report = audit_character(self.manifest, self.root)
        self.assertEqual([], report["errors"])
        self.assertEqual(2, len(report["weapons"]))
        self.assertEqual(["right", "left"], [x["hand"] for x in report["weapons"]])
        self.assertEqual(12, report["summary"]["bones"])
        self.assertTrue(any("손가락 관절" in w for w in report["warnings"]))

    def test_missing_model_rejected(self) -> None:
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("파일이 없습니다" in e for e in report["errors"]))

    def test_missing_attack_rejected(self) -> None:
        self._complete()
        write_glb(self.model, missing_attack=True)
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("attack_light" in e for e in report["errors"]))

    def test_wrong_hand_bone_rejected(self) -> None:
        self._complete()
        write_glb(self.model, bad_right=True)
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("손뼈" in e for e in report["errors"]))

    def test_missing_offhand_sword_rejected(self) -> None:
        self._complete()
        self.wakizashi.unlink()
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("wakizashi" in e and "파일이 없습니다" in e for e in report["errors"]))

    def test_both_swords_on_same_hand_rejected(self) -> None:
        self._complete()
        def mutate(data):
            data["weapons"][1]["hand"] = "right"
            data["weapons"][1]["hand_bone_candidates"] = ["RightHand"]
        self._edit_manifest(mutate)
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("중복" in e or "같은 손뼈" in e for e in report["errors"]))

    def test_only_one_sword_rejected(self) -> None:
        self._complete()
        self._edit_manifest(lambda data: data["weapons"].pop())
        report = audit_character(self.manifest, self.root)
        self.assertTrue(any("모두 필요" in e for e in report["errors"]))

    def test_skinned_sword_rejected(self) -> None:
        write_glb(self.katana, weapon=True, skinned_weapon=True)
        report = audit_weapon(self.katana)
        self.assertTrue(any("스킨/뼈" in e for e in report["errors"]))

    def test_animated_sword_rejected(self) -> None:
        write_glb(self.wakizashi, weapon=True, animated_weapon=True)
        report = audit_weapon(self.wakizashi)
        self.assertTrue(any("애니메이션" in e for e in report["errors"]))

    def test_corrupt_glb_rejected(self) -> None:
        self.model.parent.mkdir(parents=True, exist_ok=True)
        self.model.write_bytes(b"corrupt")
        with self.assertRaises(AuditError):
            load_glb(self.model)


if __name__ == "__main__":
    unittest.main()
