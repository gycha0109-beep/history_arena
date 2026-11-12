# 학원 PC 실물 3D 에셋 연결 검증 — 2026-11-12

이 문서는 **최종 무사시/이소룡 캐릭터의 품질 증명서가 아닙니다.** Godot 실물 3D 모델 임포트, Blender 검 생성, 손뼈 추종, 비변형 검, 세로 영상 출력이 기술적으로 동작한다는 시험 기록입니다.

## 현장 환경
- 로컬 저장소: `D:\cha\History_arena` (처음에는 빈 폴더였으며 공식 GitHub 저장소를 복제함)
- GPU: **GTX 1060 3GB** (기존 GTX 1070 가정과 다름)
- Godot: 4.7.2 stable / Compatibility renderer / OpenGL
- Blender: 5.2.3 LTS
- Python: 3.12.10; FFmpeg: 9.0.2
- 개발용 PowerShell 파일은 Windows PowerShell 5.1 호환을 위해 **UTF-8 BOM**으로 저장

## 실제 실행 결과
- Godot 프로젝트 불러오기 및 기존 자동 검사 5개 실행 성공
- 실제 AI 자동 대전 **40경기 생성** 성공: 무사시 34승, 이소룡 6승. 현재는 임시 수치이며 역사적 밸런스 판단이나 완성형 AI가 아님
- 테스트용 공개 3D 인체 모델을 GLB로 임포트: 메시 1, 골격 1, 애니메이션 플레이어 1
- Blender 스크립트로 스킨·모프·애니메이션 없는 독립형 검 GLB 생성 후 임포트
- 손뼈를 추종하는 무기 소켓 연결: **300프레임, 최대 검 소켓 배율 오차 약 0.0000001**
- 실제 관절 이동 경로 측정값: 누적 약 3.2046m
- 720×1280 세로 60fps 영상 **300프레임, 5초** Godot Movie Maker → FFmpeg MP4 출력
- 본 현장 시험 장면의 처리시간은 대략 실제 재생시간 정도였으나, 리소스가 단순하므로 최종 품질/성능의 근거로 삼지 않음

## 실제 결과물
- 로컬 영상: `captures/qa/rig_motion_probe_final.mp4`
- 로컬 HTML 재생기: `captures/qa/preview.html`
- 위 결과는 테스트 자산 기반이며 `captures/`와 `samples/external/`은 GitHub 커밋 대상에서 제외됨
- 캡처의 인물과 검은 **게임 최종 그래픽이 아님**. 임시 모델은 고품질 반실사 무사시/이소룡 모델로 재사용하지 않음

## 새로 추가한 도구
- `tools/probe_glb.gd`: Godot의 GLB 메시·골격·애니메이션 이름 출력
- `tools/build_qa_sword.py`: Blender에서 독립형 QA 검 모델 생성
- `scenes/qa_rigged_sample.tscn` 및 `scripts/qa/rigged_sample_preview.gd`: 실물 3D 골격에 검을 연결해 5초 재생하고 무기 배율 오차 출력
- `project.godot`의 `movie` 설정: **720×1280 출력 크기**와 화면 내 405×720 창 크기를 별도 지정하여 학원 PC 모니터 크기 제한 회피

## 테스트 모델 라이선스
- 모델 출처: [Khronos glTF Sample Assets / CesiumMan](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CesiumMan)
- 이 파일은 컴퓨터의 `samples/external/`에만 저장했습니다.
- 모델을 공개 영상/게임에 사용하기 전에는 **원본 README와 별도 LICENSES 조건을 확인**하고 필요한 고지·출처 표시를 적용해야 합니다.
- 이 프로젝트의 원본 검은 QA 전용 스크립트로 생성했으며 최종 무기 자산은 따로 제작합니다.

## 품질 이슈 및 다음 작업
1. **무사시/이소룡 실제 리깅 모델 미확보** — Meshy 또는 사용권이 명확한 고품질 모델 필요
2. **실제 검격/피격 모션 미확보** — 기본 걷기 애니메이션과 공격 동작을 혼동하면 안 됨
3. **공격 시 팔, 검 위치와 상대 피격 시간 동기화 미검증**
4. **검 그립 방향과 캐릭터 발 접지**, 의상 메시 변형과 2인 카메라 구도 보정 필요
5. 3GB 그래픽 메모리를 전제로 고품질 렌더 성능 및 출력 단계 분리 점검

PC에서 검증용 모델을 직접 실행하려면 먼저 테스트용 GLB 파일을 `samples/external/CesiumMan.glb`, `samples/external/qa_katana.glb` 경로에 준비한 뒤 `res://scenes/qa_rigged_sample.tscn`을 실행합니다. 샘플 파일은 GitHub에 포함하지 않습니다.

## ?? ?? ? ??? 5? ?? (2026-11-12)

- ??? ??? + ?? ????? ?? ??, ??? ??, ??? ?? ??
- ?? ? ??? ??? ??? ?? ?? ?? ?? ?? (?? ??? ?? ??)
- ?? ?? ????? ?? ??? ?? ?? ?? ??? ???? ?? ??
- ? ? ?? ?? ??, ?? ?? ?? ? ?? ?? ??
- **5?/300???/720?1280/60fps** MP4 ? HTML ??? ?? ??
- ? ?? ?? ?? ?? ? 0.0000002 ??, ?? ?? ??? ? 5.6mm
- `run-dev.cmd -Mode dualqa` ?? ??. ??: [DUAL_WIELD_QA.md](DUAL_WIELD_QA.md).

?? ???/??? ??? ??? ??? ?? ?? ??? ?? ???? ?? ?? ?? ??? ???? ????.
