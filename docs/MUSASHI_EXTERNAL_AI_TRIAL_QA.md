# 무사시 외부 AI 3D 변환 실험 — 2026-11-14

## 작업 결과
- 원본 설정 시트의 정면 축소본(256×256)을 집 PC로 이전하고 이미지 로드 확인. 이 자료는 생성 연결 시험용이며 고해상도 본생성용이 아님.
- Microsoft TRELLIS.2: 무료 ZeroGPU 사용 한도 오류로 3D 생성 실패.
- Stability AI Stable Fast 3D: 원격 Gradio 내부 오류로 3D 생성 실패.
- TencentARC InstantMesh: 이미지 전처리와 AI 다중시점 이미지 생성 성공. 후속 make3d 단계에서 무료 GPU 쿼터 0초 오류로 실패.
- 성공한 중간 산출물: assets/characters/musashi/rebuild_v1/instantmesh_trial/generated_multiview_clean.png (960×640, 6개 패널)
- 검토: assets/characters/musashi/rebuild_v1/instantmesh_trial/trial_review.html

## 품질
불합격. 실제 편집 가능한 GLB가 생성되지 않았으며 중간 이미지도 얼굴·머리·의상·손과 발·검이 목표와 불일치함.
기존 V3 캐릭터 모델과 게임은 변경하지 않았음.

## 다음 작업
1. Meshy 7.1/Tripo 유료 계정의 승인된 인증 또는 Hugging Face 무료 GPU 인증 및 쿼터 확보.
2. 원본 고해상도 정면/측면/후면 입력으로 실제 3D 생성.
3. 실제 GLB 수령 후 Blender 정면·측면·후면을 렌더링해 캐릭터 실루엣, 의상, 검을 검수.
4. 합격 이전 리깅·애니메이션 및 게임 모델 교체는 금지.

외부 AI 생성 서비스에 결제하거나 유료 GPU 작업을 실행하지 않았음.
Python 실험 의존성은 별도 .venv-mesh-ai에 격리하고 글로벌 pip 충돌 해결 확인.
