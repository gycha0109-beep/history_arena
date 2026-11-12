# 5초 장면 실행과 영상 출력

> **이 장면은 AI 경기 결과가 아니라 그래픽·애니메이션 품질을 확인하기 위한 고정 연출입니다.**
> 대치 0~0.67초 → 접근 0.67~1.75초 → 검격 1.75~2.60초 → 이소룡 피격 2.17~2.83초 → 회복·대치 5초 종료.

## 현재 구현된 내용

- 60FPS 기준으로 정확히 300프레임을 구성하는 고정 시간표
- 무사시·이소룡의 위치와 공격·피격 상태를 공통 규약으로 전달
- 실제 GLB를 등록하면 모델의 걷기/공격/피격 애니메이션이 시간표에 따라 전환
- 무사시 검은 캐릭터 손뼈를 따라가되 뼈 배율이 전달되지 않도록 별도 연결
- 모델이 누락되면 누락 상태를 화면에 표시
- 장면 구성·이동·피격 구간을 GitHub 자동 검사로 검증
- Windows에서 미리보기/자동검사/AVI·MP4 영상 출력 명령 추가

## 바로 실행하기 (Windows)

프로젝트를 GitHub 최신본과 동기화한 뒤 폴더에서 아래를 실행합니다. **기존 로컬 프로젝트는 확인 전 덮어쓰지 마세요.**

```powershell
.\run-dev.cmd -Mode test       # 모든 자동 검사
.\run-dev.cmd -Mode preview    # 5초 연출 미리보기
.\run-dev.cmd -Mode battle     # AI 자동 대전 계산 화면
.\run-dev.cmd -Mode record     # 모델이 모두 있을 때만 5초 AVI/MP4 녹화
```

표준 Godot 4.7.2가 PATH에 없으면 `-GodotPath 'C:\...\Godot_v4.7.2-stable_win64.exe'`를 지정합니다.

Godot에서 `res://scenes/preview_five_seconds.tscn`을 직접 열어 F6으로 실행할 수도 있습니다.

## 실제 캐릭터 파일 연결

아래 경로가 필요합니다.

```text
assets/characters/musashi/models/musashi.glb
assets/characters/bruce_lee/models/bruce_lee.glb
assets/weapons/katana.glb
```

각 캐릭터 GLB는 `Skeleton3D`와 `AnimationPlayer`에 `idle`, `walk`, `attack_light`, `hit_react`의 실제 클립이 있어야 합니다. 이름이 다르면 각 캐릭터의 `character.json`에서 수정합니다. **별도 모션 GLB를 폴더에 넣는 것만으로 자동으로 같은 리그에 합쳐지지 않으므로**, 먼저 Meshy 또는 Blender에서 통합 내보내기해야 합니다.

에셋 확보부터 내보내기까지 세부 절차: [Meshy → Godot](MESHY_TO_GODOT.md).

## 녹화

`run-dev.cmd -Mode record`는 세 모델 파일이 없으면 의도적으로 중단합니다. 파일이 있을 경우 Godot Movie Maker의 `--write-movie`와 `--quit-after 300`으로 5초 AVI를 저장하고, FFmpeg가 설치되어 있으면 MP4로 변환합니다.

- AVI: `captures/preview_5s.avi`
- MP4: `captures/preview_5s.mp4`
- 시도 해상도: 720×1280, 60fps (창/모니터 설정에 따라 실제 출력 크기 확인 필요)
- 완성 영상 목표: 1080×1920 세로형; 환경 성능 측정 전까지 확정 성능 주장 금지

기술 참고: https://docs.godotengine.org/en/stable/tutorials/animation/creating_movies.html

## 남은 품질 검증

- 실존 인물에 맞는 모델 품질/표정/의상/비율
- 캐릭터의 걷기, 검격, 회피, 피격 모션의 실제 자연스러움
- 발 미끄러짐, 검 손잡이/검날 각도, 공격과 피격 타이밍
- 카메라 구도, 실루엣 가독성, 촬영·인코딩 결과
- GTX 1070에서 렌더링 가능성
- 모델·모션·음원 및 실존 인물의 이용 권한

**금지:** GLB가 없는 상태의 빈 무대나 모델 누락 경고를 완성된 전투 영상이라고 소개하지 않는다.

## 녹화 전 추가 검사

`run-dev.cmd -Mode record` 명령은 GLB 파일뿐 아니라 `tools/asset_audit.py`를 통해 리깅·기본 동작·손뼈·검의 정적 모델 여부를 확인하고, Godot에서도 실제 모션 연결 검증이 통과한 경우에만 영상을 출력합니다. 별도 구조 검사: `run-dev.cmd -Mode audit`. [검사 설명](ASSET_QUALITY_GATE.md).

## ??? ??

?? ??? ?? ? ?? ?? ??? **??? ??? + ?? ????**? ?????. ?? ?? ?? ? `katana.glb`, `wakizashi.glb`, ??????? ?? GLB?? ? ??? ?????. 300??? ?? ??? ?? ??? ?? ?? `dual_cross`? ??????. ?? ?? ?? ?????? ?? `run-dev.cmd -Mode dualqa` ??? [DUAL_WIELD_QA.md](DUAL_WIELD_QA.md)? ?????.
