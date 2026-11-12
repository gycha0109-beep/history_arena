# 개발 환경 설정 (Windows)

## 확정 버전

- **Godot 4.7.2 안정판, 표준 GDScript 빌드** — [공식 다운로드](https://godotengine.org/download/archive/4.7.2-stable/)
- Blender, Mixamo, Python, FFmpeg는 기술 선택을 확정했으나 **정확한 설치 버전은 PC 환경 점검 후 고정**
- Git 및 Git LFS 사용

## 저장소 받기

```powershell
git clone https://github.com/gycha0109-beep/history_arena.git
cd history_arena
git lfs install
git lfs pull
```

1. Godot 실행 → 프로젝트 가져오기 → `project.godot` 선택
2. `F5`로 메인 씬 실행
3. 바닥·카메라·개발 상태 문구가 보이는지 확인
4. 최초 실행에서는 캐릭터와 전투 AI가 아직 나타나지 않는 것이 정상

## 자동 검사 (Godot 실행 파일이 PATH에 있을 때)

```powershell
godot --headless --editor --path . --quit
godot --headless --path . --script res://tests/smoke.gd
```

GitHub에서도 `Actions → Godot 기본 검사` 결과 확인 가능.

## 이전 로컬 프로젝트

기존 `D:\cha\History_arena`의 파일은 **현재 확인되지 않았음**. 이 저장소를 바로 덮어씌우지 말고, PC에 접근할 때 파일·라이선스·애니메이션 원본·재사용 가능 코드부터 확인한다.

## Windows 원클릭 실행

```powershell
.\run-dev.cmd -Mode test
.\run-dev.cmd -Mode battle
.\run-dev.cmd -Mode preview
.\run-dev.cmd -Mode record
```

- Godot 4.7.2 표준판을 사용하고 실행 파일이 PATH에 없으면 `-GodotPath '절대경로'` 지정
- 녹화는 `musashi.glb`, `bruce_lee.glb`, `katana.glb`가 있는 경우에만 시작
- 프로젝트의 기존 로컬 파일이 있다면 `git status`로 수정 사항을 보존하고 원격 최신본을 병합할 것
- 상세: [5초 장면 실행 지침](FIVE_SECOND_PREVIEW.md)

## 3D 모델을 받았을 때

`run-dev.cmd -Mode audit`로 GLB 형식, 필수 애니메이션, 손뼈, 검의 스킨/모프/애니메이션 여부를 먼저 확인하세요. 검사 통과 이후 `run-dev.cmd -Mode preview`와 `run-dev.cmd -Mode record`를 실행합니다. 실제 모델이 없는 경우 검사 실패는 정상입니다.

자세한 내용: [3D 모델 연결 전 검사](ASSET_QUALITY_GATE.md)
