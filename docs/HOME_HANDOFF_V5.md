# 레전더리 배틀 — 집 PC 이어서 작업하기

최신 보류 작업: **무사시 양손 검의 V5 정지 자세 검수** (최종 시각 승인 전).
- 작업 브랜치: `experiment/mocap-walk-evaluation`
- 검토용 PR #10은 Draft. **main 병합 금지.**
- 원래 검증된 `Walk_DualGuard` 보행은 절대 다시 만들거나 덮어쓰지 말 것.

## 집에서 처음 내려받는 경우

```powershell
git clone --branch experiment/mocap-walk-evaluation https://github.com/gycha0109-beep/history_arena.git
cd history_arena
git lfs install
git lfs pull
```

이미 저장소가 있는 경우:

```powershell
git switch experiment/mocap-walk-evaluation
git pull --ff-only origin experiment/mocap-walk-evaluation
git lfs pull
```

**Git LFS 필수**: `*.glb`, `*.blend`, `*.mp4`는 GitHub LFS로 내려받습니다. 받기 전에 LFS 포인터를 실제 모델로 오인하지 마세요.

## 집에서 바로 열고 이어서 작업

- **영상·사진·손 확대·V4 비교 HTML**
  `captures/qa/dual_grip_guard_v5/dual_grip_guard_preview.html`
- **Blender에서 열고 손가락·검·팔 자세 수정**
  `captures/qa/dual_grip_guard_v5/dual_guard_upperbody_work.blend`
- **현재 제작 소스**
  `tools/dual_grip_guard_v5.py` (Blender 5.2.3 기준)
- **다시 렌더링하고 HTML 열기**
  `run-next-qa.cmd`

실행 전 필요: Blender 5.2.x, Python 3, FFmpeg. 시스템 PATH에 Python/FFmpeg가 있어야 합니다. Blender가 통상 위치에 없다면 다음처럼 실행 파일 경로를 지정합니다.

```powershell
$env:BLENDER_EXE = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
.\run-next-qa.cmd
```

게임 엔진으로 기존 보행을 다시 검사하려면 **Godot 4.7.2**도 설치해야 합니다. `run-dev.cmd -Mode dualwalkqa`는 해당 PC에 Godot/Blender/FFmpeg가 필요합니다.

## 함께 업로드한 소스 데이터
- `samples/external/kinemiq_dual_guard_idle.glb` — V5 정지 자세 원본 골격
- `samples/external/kinemiq_two_sword_guard_walk.glb` — 검증된 이도류 걷기 골격
- `samples/external/kinemiq_full_body_walks.glb` — 검증된 기본 전신 보행
- `samples/external/kinemiq_cc0/GLB/Idle_with_a_sword.glb`, `Walk_carrying.glb` — 기초 참조 동작
- `samples/external/qa_katana_rigid.glb`, `qa_wakizashi_rigid.glb` — 고정 길이 시험용 검
- `captures/qa/dual_grip_guard_v5/` — 결과 동영상·손 확대 사진·Blender 파일
- `captures/qa/dual_grip_guard_v4/dual_guard_angles_5s.mp4` — 비교 영상

GitHub에 포함된 모델은 **검수용 임시 자료**입니다. 최종 무사시 외형 및 검술 애니메이션의 완성품이 아닙니다.

## 반드시 고칠 문제
1. 왼손 검지 관통은 줄었으나 표본 3개가 여전히 손잡이 안에 있음. 중지·약지 관통도 남아 있음.
2. 오른팔의 비틀림이 과도하며 손목·어깨 자연스러움 추가 조정 필요.
3. 현재 영상은 **3방향 정지 컷**이며 실제 걷기/공격 연속 애니메이션이 아님.

**현재 변경은 Draft 검토용 브랜치에만 보관**하며 시각 승인 전에는 `main`에 병합하지 않습니다.
