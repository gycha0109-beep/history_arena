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
