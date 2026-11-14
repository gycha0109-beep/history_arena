# 2026-11-13 — 5초 양손 검 전투 보행 기술 검증

## 무엇이 완료됐는가

**기존 5초 전신 보행을 기반으로 오른손 장검과 왼손 단검을 동시에 든 영상**을 실제 Godot 4.7.2에서 녹화했습니다.

- 시각 모델: Quaternius/KinemIQ CC0 전신 인체(검증용). **무사시 외형은 아님**
- 원본 발/무릎/골반/척추 보행: 그대로 유지. 기존 `Walk_forwards`와 새 `Walk_DualGuard`의 300프레임에서 발끝 관절 변형 없음
- 양팔: 같은 제작자의 `Walk_carrying` 양손 가드 포즈를 같은 골격에 미리 구워서 적용. 보행 중 팔이 따로 팔딱거리지 않도록 원본 보행 팔 움직임은 약 5.5%만 혼합
- 실제 손가락 골격: 오른손/왼손 각각의 손가락에 원본 검 대기 포즈 기반 관절 회전이 기록되어 있음
- 무기: 한 손에 한 자루, `qa_katana_rigid.glb`, `qa_wakizashi_rigid.glb`. 이전에 사용한 **검 모델에 달린 가짜 손바닥·손가락 메시 완전 제거**
- 각 검의 위치는 실제 손목에서 손가락 관절을 향하는 손바닥 중앙 기준이며, 검은 독립된 고정 길이 모델로 따라감
- 검은 몸통 바깥쪽을 향하도록 배치. 300프레임 검사상 근사 몸통 중심선과 검날 사이 최소 거리 약 **0.547m**
- Godot 출력: 720×1280, 60fps, 300프레임, 5초, 실제 이동 약 **5.215m**
- 검사: 5초 동안 두 검·손목 다른 뼈에 부착, 발 관절 원본 대비 차이 0, 최대 검 크기 배율 오차 약 0.0000002, 손잡이 중심과 중지 관절 사이 최대 약 4.43cm, 팔 프레임별 회전 변화 최대 약 0.15도.

## 확인할 파일

```text
D:\cha\History_arena\captures\qa\dual_guard_walk_preview.html
D:\cha\History_arena\captures\qa\dual_guard_walk_5s.mp4
D:\cha\History_arena\captures\qa\dual_guard_hand_closeup.png
```

재제작: `run-dev.cmd -Mode dualwalkqa`.

## 주의: 아직 최종 게임 그래픽이 아님

이 결과를 실제 무사시 모델·고품질 이도류 검술·완벽한 손가락 그립의 증거로 사용하면 안 됩니다.

- **실제 무사시 모델 미확보:** 현재는 회색 CC0 인체. 일본 복식·안면·머리카락 등 최종 그래픽 미구현
- **손의 실제 접촉:** 손잡이와 손바닥이 가까우나 엄지·손가락 전체가 정확히 눌러 잡는지 최종 모델에서 메시 접촉 검사 필요. 현재 손잡이와 중지 관절 최대 4.4cm는 '완벽한 그립'이라고 볼 수 없음
- **검객 특유의 보행:** 원본 안정적인 걷기와 가드를 결합한 검증용 동작이며 고유한 이도류 발놀림은 별도 제작 필요
- **간섭 검사:** 몸통까지의 근사 거리를 검사했을 뿐, 양손/팔꿈치/복식과 무기 전체 삼각형 충돌 검사는 미완료
- 실제 역사적 무사시 동작, 공격·피격·검 궤적·이소룡 반응 연결도 미완료

## 외부 자산

- CC0 원본: [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html) / KinemIQ 재배포 자료
- 다운로드 SHA256은 `tools/fetch_consistent_walk_reference.py`로 검증
- 원본 GLB 및 파생 GLB/영상은 `samples/external` 및 `captures`에만 유지하고 GitHub에 바이너리 포함하지 않음
