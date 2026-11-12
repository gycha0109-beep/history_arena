# Meshy → Blender/Mixamo → Godot 캐릭터 연결 실행서 v0.2

> **2026-11-12 상태:** 3D 모델/모션/검을 불러오는 코드를 구현했으며, 아래 모델 파일은 아직 실제로 확보하지 못했습니다. Meshy 계정/제작 크레딧 없이 모델 생성 완료라고 표시하지 않습니다.

## 기술 선정 근거

- **Godot 4.7.2**: 현재 프로젝트 안정판 고정. 4.8은 베타로 출시 중이므로 안정화 전 교체하지 않음.
- **Meshy**: 리깅된 캐릭터 GLB/FBX 및 기본 걷기/달리기 출력이 가능한 후보. 결과의 얼굴, 손, 의상 형태 일관성은 *실제 생성 결과로 평가*.
- **Mixamo**: Adobe 계정으로 기본 모션 활용. Adobe 공식 FAQ에 상업 영상과 게임 사용 가능하다고 명시. 전투 고유 검격은 Blender에서 재작업 필요.
- **Blender**: 캐릭터·모션·무기를 하나의 유효한 스켈레톤으로 정리하고 GLB로 출력.
- **Godot**: GLB가 권장되는 3D 씬/애니메이션 형식, 별도 리깅 에셋 임포트가 가능.

참고:
- https://godotengine.org/download/archive/
- https://docs.meshy.ai/en/api/rigging
- https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html
- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html
- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html

## 1. Meshy 첫 후보 생성

### 첫 번째 목표: 무사시

**생성용 텍스트 프롬프트(영문, 복사용)**

```text
Full-body high-quality semi-realistic 3D character of a Japanese master swordsman inspired by Miyamoto Musashi, late Sengoku / early Edo period. Historically grounded layered indigo and charcoal kimono, hakama trousers, tied sleeves, traditional sandals, weathered but anatomically believable adult male face, dark hair tied back, natural human proportions and expressive hands, physically based fabric and skin materials. One complete standing human character centered, neutral relaxed A-pose, arms and fingers visibly separated from torso, feet grounded, face forward. Game-ready clean topology, consistent geometry from all views. No sword or scabbard attached to the body, no baked lighting, plain transparent studio background.
```

**제외 프롬프트(해당 기능 지원 시)**

```text
weapon fused to hand, deformed fingers, extra limbs, uneven arms, asymmetrical legs, stretched face, floating clothing, crossed arms, dynamic pose, fighting stance, extreme perspective, illustration only, 2D render, sculptural pedestal, text, watermark, low poly faceted face
```

기준은 **실제 3D 모델의 여러 각도에서 얼굴·손·의상·발의 형태가 유지되는지**입니다. 단일 정면 이미지가 좋아도 측면·후면이 무너지면 채택하지 않습니다.

### 두 번째 목표: 이소룡

```text
Full-body semi-realistic 3D game character representing the legendary martial artist Bruce Lee, athletic lean male physique, accurate natural anatomy and balanced facial proportions, classic simple martial arts training outfit in dark tones, bare hands and feet, short dark hair, neutral A-pose, hands and fingers clearly separated from torso, straight legs, front facing studio pose, riggable clean topology, high-quality physically based material, symmetrical body proportions, no weapons, no text, no backdrop props, no dramatic action pose.
```

브랜드·초상 이용 가능 조건과 모델 생성 플랫폼의 최신 약관은 게시 전 확인합니다.

### 품질 채택 기준

- 정상적인 골격과 분리된 손/손가락
- 모델을 360도 회전시켜도 비율과 의상 품질 유지
- 리깅 후 팔꿈치·무릎·손목 회전에서 메시가 깨지지 않음
- 연속 동작에서 옷의 심각한 몸통 관통이나 손목 비틀림 없음
- **무사시 검은 몸에 합쳐 생성하지 않음** (검은 별도 GLB)

Meshy 결과가 기준 미달이면 다시 생성 비용을 투입하기보다, 라이선스가 확인된 기존 3D 모델을 찾아 적용합니다.

## 2. Blender/Mixamo에서 작업

1. Meshy 결과를 Blender에서 열고 메쉬, 머티리얼, 스켈레톤, 손뼈 목록 확인.
2. Mixamo FBX 모션을 사용할 때는 두 모델의 리그/뼈대 불일치를 리타기팅. 뼈 이름만 같은 것은 충분하지 않음.
3. 뼈를 기준으로 각 모션을 모델에 굽고, 게임 액션 이름을 **Idle / Walk / QuickCut / HeavyCut / HitReact / KO** 등으로 통일.
4. **검은 별도 3D 모델**로 만들고 손잡이 기준점을 원점에 설정. 손/검 결합 위치는 Godot 설정 JSON으로 보정.
5. 게임이 계산하는 좌우 위치 이동과 리깅의 루트 이동이 중복되지 않도록, 첫 구현에서는 **이동 모션을 제자리 모션(in-place)**으로 통일.
6. 모델 GLB에 스켈레톤과 애니메이션을 넣어 내보내고, Godot에서 실제 모션 이름 확인.

## 3. 경로와 파일 규격

```text
assets/
  characters/
    musashi/
      character.json
      models/musashi.glb           ← 실제 GLB 필요
    bruce_lee/
      character.json
      models/bruce_lee.glb         ← 실제 GLB 필요
  weapons/
    katana.glb                    ← 실제 GLB 필요
```

GLB가 확보되면 위 경로에 배치합니다. 텍스처가 GLB에 포함되어야 로딩이 간결합니다. 게임 코드는 위 경로의 자원을 자동으로 읽도록 준비돼 있습니다.

### 필수 조건

- 캐릭터 GLB에는 `Skeleton3D`와 `AnimationPlayer`가 있어야 합니다.
- 무사시 손뼈 후보: `RightHand`, `mixamorig:RightHand`, `mixamorig_RightHand`, `Hand.R`, `hand_r`. 실제 뼈 이름이 다르면 `character.json`에 기입.
- 최소 `idle`, `walk`, `attack_light`, `hit_react`에 해당하는 모션을 GLB에서 찾을 수 있어야 연결 성공.
- 모델 애니메이션 이름이 다른 경우 `animation_clips` 배열에 **Godot에서 보이는 정확한 이름** 추가.
- 무사시 손잡이 위치와 각도는 `grip_position` 및 `grip_rotation_degrees`로 조정.

## 4. 왜 무기를 별도 파일로 두는가

`scripts/visuals/weapon_socket.gd`는 손뼈의 세계 위치·회전만 읽어 별도 무기 노드에 반영하며, **손뼈의 배율·비틀림이 검의 배율로 전파되지 않도록 직교정규화**합니다.

이는 과거 발생한 **검이 늘어나거나 줄어드는 현상**의 한 원인을 구조적으로 방지합니다. 단, Blender에서 검 원본 메시 자체가 변형되는 키프레임이나 잘못된 검 모델 치수가 있다면 별도 검증이 필요합니다.

## 5. 프로그램에서 확인

- Godot로 프로젝트 실행(F5)
- GLB가 없으면 전투 계산은 계속 진행되지만 화면에는 **모델 미등록 상태**가 표시됩니다.
- GLB를 추가한 뒤 기본 애니메이션을 자동 검색하여 재생.
- 검 소켓은 손뼈를 따라 움직이되 배율 변화를 전달하지 않음.
- Godot 자동 검사에서 뼈 위치 추종과 검 배율 불변 검증.
- 품질 통과는 **실제 5초 모션 영상**으로만 판정합니다. 자동 검사 통과와 구분.

## 다음 필요 항목

- Meshy에서 출력된 **실제 무사시 GLB** 및 사용권/비용 확인.
- 무사시 검(GLB), 검격/피격 모션을 포함하도록 Blender에서 정리.
- 이소룡 GLB와 모션 추가.
- GTX 1070에서 두 모델의 화면 품질 및 성능 검증.
