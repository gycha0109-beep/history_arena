# 무사시 — 2026-11-14 인체 베이스 확보 결과

- 기존 V3는 불합격. 이 작업물도 무사시 외형 완성본 아님.
- 출처: Blender Studio Human Base Meshes v1.4.1 (CC0).
- 공식 다운로드: https://www.blender.org/download/demo-files/
- 압축 파일 검증: 50,643,039 bytes; Windows tar extraction succeeded.
- Blender 5.2.3에서 원본을 열고 사실형 남성 전신 메시/눈/멀티레졸루션을 확인.
- 실제 재제작 파일: assets/characters/musashi/rebuild_v1/musashi_anatomy_base_cc0.blend (12,581,784 bytes).
- 인체 메시 기본 정점: 10,582개, 원본 전체 높이 약 1.69m. 조형용 멀티레졸루션 유지.
- Cycles 4방향 렌더 성공: 01_front.png / 02_left_profile.png / 03_back.png / 04_three_quarter.png.
- HTML: assets/characters/musashi/rebuild_v1/musashi_anatomy_base_preview.html
- 재생성: run-musashi-base-review.cmd (외부 CC0 자료가 없으면 자동 다운로드).

## 한계 및 다음 우선순위
1. 이 자료는 피부/얼굴/의상/머리/무기의 완성도를 검증할 대상이 아니다. 회색 인체보다 수준이 나아졌다고 주장하지 않는다.
2. 사용자의 목표 시트는 동양인 얼굴, 검고 풍성한 묶은 머리, 찢긴 검은 겹옷과 붉은 띠, 사실적 소재가 전부 표현되어야 한다.
3. 기존 자동 생성 옷/헤어를 다시 덧씌우지 않는다. 고품질 다중 시점 이미지→3D 생성 또는 직접 제작된 사실적 로닌 에셋을 검토한다.
4. 추천 실험: Meshy 7.1 Image to 3D > High Detail + Multi-view + A-pose. 정면/측면/후면만 중립 상태로 넣고, 전투 자세 참고 이미지는 분리한다.
5. 생성된 고품질 후보를 실제 GLB/FBX/BLEND 파일로 확보하고, 얼굴/머리/의상/후면 실루엣을 4방향에서 동일 캐릭터인지 검수한다.
6. 후보가 목표를 통과한 후에만 리토폴로지/스키닝/걷기/격투를 재개한다.

상태: **고품질 무사시 외형 미제작 / 인체 원형만 확보**.
