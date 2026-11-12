# 5초 실제 보행 품질 검증 (2026-11-12)

## 현재 결과

**실제 5초 보행 영상이 생성됐습니다.** 단, 현재 캐릭터는 미야모토 무사시가 아닙니다.

- 샘플 캐릭터: Vibeassets에서 공개한 CC0 인체 모델(의상 착용, 24본, 실제 Walk/Run 모션 포함)
- [원본·사용 조건](https://vibeassets.io/a/zpepqtthci)
- 5초/60fps/300프레임/720×1280 MP4
- 실제 논리 이동: **6.75m** (1.35m/초, 매 프레임 일정하게 전진)
- 걷기 애니메이션 길이: 약 1.067초, 5초 동안 약 4.7주기
- 바닥 기준선과 배경 기둥을 고정하고 카메라만 추적하여 위치 이동을 확인
- 실제 발을 드는 동작과 번갈아 지지하는 발 동작이 검출됐으며, 로컬 테스트 통과
- **발 접지 미끄러짐은 0이 아님:** 5초간 접지 구간의 발 상대 이동 누적량 약 왼쪽 0.288m/오른쪽 0.487m. 접지 중 한 프레임의 최대 위치 변화 약 1.1cm/2.3cm. 더 정교한 실제 보행 검증 전까지 최종 품질로 승인하지 않음.

## 왜 이전 영상보다 의미가 있는가?

이전의 CesiumMan 이도류 QA는 캐릭터의 다리를 고정해 발 미끄러짐을 억제했고, 캐릭터가 실제로 앞으로 나아가지 않았습니다. 이번 장면은 **Walk 애니메이션을 재생하고, 그 보행 방향에 맞춰 캐릭터의 세계 좌표를 이동**시킵니다. 화면 속 캐릭터가 정지된 채 발만 움직이는지 여부는 고정된 바닥선의 상대 이동으로 구분합니다.

이것은 **실제 접근 보행의 기초 검증**일 뿐, 무사시의 최종 캐릭터·이도류 검격·그립·상대 피격의 시각 품질을 검증한 것이 아닙니다.

## 학원 PC 결과물

```text
D:\cha\History_arena\captures\walk\preview.html
D:\cha\History_arena\captures\walk\walk_5s.mp4
D:\cha\History_arena\captures\walk\walk_5s_poster.jpg
```

재현 명령:

```powershell
.\run-dev.cmd -Mode walkqa
```

GitHub에는 리깅 모델의 바이너리/렌더 MP4를 커밋하지 않고, 사용권 출처와 SHA256이 고정된 **CC0 모델을 안전하게 다운로드하는 스크립트**를 포함합니다. 파일 재사용과 라이선스는 원본 사이트의 실제 배포 조건을 따릅니다.

## 5초 보행 구현과 검증

- `scripts/preview/walk_five_seconds.gd`: 실제 Walk 모션의 60Hz 재생, 본체 이동, 카메라 추적, 접지 샘플 수집
- `scenes/walk_five_seconds.tscn`: 5초 세로 영상용 장면
- `tests/walk_five_seconds.gd`: CI에서도 실행되는 300프레임 이동 규칙 검사
- `tests/walk_qa_local.gd`: **실제 GLB가 있을 때** 발 들림·지지·이동량 검증
- `tools/fetch_walk_reference.py`: CC0 보행 소스 다운로드 및 SHA256 검증
- `tools/walk_5s_viewer.html`: HTML 영상 재생기

## 무사시 본 모델로 가기 위한 다음 작업

2026-11-12 시점에 추가 확보한 모델:

1. **손가락 163개 관절을 포함하는 CC0 남성 인체 기본 모델** (관절 총수 163개; 손가락 관절 포함): [Innerscene MakeHuman 기반 3D 모델](https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89). 로컬 파일 `samples/external/makehuman_finger_rig_cc0.glb`. **무사시용 의상/머리카락과 보행 애니메이션이 아직 없음.** 이 모델은 의상을 갖춘 최종 캐릭터가 아니므로 상품/영상에 그대로 쓰지 않음.
2. CC0 보행 참조 모델: `samples/external/camper_walk_cc0.glb`. **손가락 관절이 없으므로 이도류 실제 그립에 사용 불가.** 보행 모션 참고·리타기팅에만 사용.

다음 단계는 Blender에서 손가락 리그를 유지한 모델로 걷기 모션을 리타기팅하고 일본 검객 의상/머리카락을 제작하는 것입니다. 그 후에만 그립과 검술 애니메이션을 만듭니다. 임시 의상이나 검을 어설프게 붙여 전투 품질이 완성된 것처럼 보고하지 않습니다.

**주의:** 영상 내의 CC0 인체는 현대식 셔츠·바지 의상을 입고 있습니다. 사용자 승인 없는 최종 무사시 대체 모델로 사용하지 않습니다.
