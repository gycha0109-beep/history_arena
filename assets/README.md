# 제작 에셋 보관 규칙

실제 모델과 모션이 확보되기 전에는 **임시 자료를 최종 캐릭터라고 표시하지 않습니다.**

- `assets/characters/<character_id>/models/`: 사용 권리를 확인한 캐릭터 모델(GLB 등)
- `assets/characters/<character_id>/animations/`: 대기·이동·공격·피격 모션
- `assets/weapons/`: 무기 모델 및 부착 규격
- `assets/environments/`: 전투 배경
- `assets/effects/`: 검격·타격·카메라 연출용 이펙트
- `assets/audio/`: 효과음과 음악
- 각 외부 파일은 출처, 저작권자, 라이선스, 변형·상업적 사용 가능 여부 기록
- Blender 원본 및 대용량 파일은 Git LFS로 관리; Git LFS가 활성화되지 않았다면 대형 파일을 커밋하지 않음

자세한 기준: [에셋 제작 지침](../docs/ASSET_PIPELINE.md)

- [Meshy / Blender / Mixamo → Godot 실제 파일 경로 및 연결 규약](../docs/MESHY_TO_GODOT.md)
- 캐릭터별 `character.json`은 경로·모션 이름·무기 손잡이 오프셋을 지정합니다.
- 아직 `musashi.glb`, `bruce_lee.glb`, `katana.glb`는 확보되지 않았습니다.

## ???(2026-11-12)

???? `katana.glb`(??? ??)? `wakizashi.glb`(?? ??)? ?? ?????. `assets/characters/musashi/character.json`? `weapons` ???? ? ?? ?? ??? ?? ??? ?????. ???? ? ??? ???? ??? ???? ?? ??? ??? ???? ????.
