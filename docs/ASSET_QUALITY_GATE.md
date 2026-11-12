# 실제 캐릭터 파일 검사 — 사용 지침

> 목적: Meshy·Mixamo·Blender에서 내보낸 GLB를 Godot에 넣기 **전에**, 파일 자체의 누락·스켈레톤·애니메이션·검 변형 위험을 빠르게 발견합니다.

## 작업 순서

1. **Meshy Animate에서 무사시 모델을 만든 후 사람형 자동 리깅**
   - 신체가 제대로 연결되는지, 손가락과 발목이 무너지지 않는지 확인
   - **리깅 골격 템플릿은 가능하면 Mixamo를 선택**해 이후 모션 재사용 비용 절약
   - 첫 단계에서 Idle, Walk, 검격, HitReact를 하나의 캐릭터에 적용할 수 있는지 확인
2. **GLB로 내보내기**. 기본 애니메이션을 한 파일에 담을 수 없다면 Blender에서 동일한 스켈레톤을 기준으로 결합/베이크
3. **무사시 검은 캐릭터 모델에서 분리**하여 애니메이션·스킨 없는 정적 GLB로 내보내기
4. 다음 정확한 위치에 복사

```text
assets/characters/musashi/models/musashi.glb
assets/characters/bruce_lee/models/bruce_lee.glb
assets/weapons/katana.glb
```

5. 캐릭터 설정 `assets/characters/*/character.json`에서 애니메이션 클립 이름과 `hand_bone_candidates`를 실제 파일에 맞게 조정
6. `run-dev.cmd -Mode audit`로 파일 구조 검사
7. 검사 통과 후 `run-dev.cmd -Mode preview`, 마지막으로 `run-dev.cmd -Mode record`로 5초 결과 확인

## 검사 명령

```powershell
# 모두 검사 (무사시 모델·검 및 이소룡 모델 필요)
.\run-dev.cmd -Mode audit

# 무사시 모델과 검만 준비됐을 때
python .\tools\asset_audit.py --character musashi

# 구조화된 출력
python .\tools\asset_audit.py --json
```

`python -m unittest discover -s tools/tests -p "test_*.py" -v`는 별도 외부 에셋 없이 감사 프로그램 자체를 검증합니다.

## 자동으로 확인하는 항목

| 검사 대상 | 확인 |
|---|---|
| GLB 형식 | 정상적인 glTF 2.0 헤더와 JSON 데이터 |
| 사람 모델 | 실제 메시, 스킨, 손을 포함하는 충분한 뼈 |
| 동작 | 대기·걷기·공격·피격 클립 이름과 누락 여부 |
| 검 부착 | 무사시 설정의 손뼈 후보와 GLB 속 실제 뼈 이름 |
| 검 | **독립된 정적 메시인지**, 검 자체에 스킨·모프·애니메이션이 있는지 |
| 성능 경고 | 지나치게 많은 삼각형, 비기본 메시/관절 배율 애니메이션 |
| 누락된 모델 | 파일이 없으면 검사 실패 처리 |

**통과의 의미:** 파일 구조가 현재 게임 연결 규약과 일치한다는 뜻입니다.

**아직 확인하지 못하는 것:** 얼굴 완성도, 발 미끄러짐, 손목 관절 웨이트, 옷 메시 관통, 프레임별 검 시각 길이, 조명과 카메라 연출, GTX 1070의 실제 성능. 이 항목은 Godot에서 모델을 재생·녹화하고 영상을 직접 확인해야 합니다.

## 외부 도구의 역할

Meshy는 **모델/리깅/기본 모션 생산**에 우선 활용합니다. 공식 Animate 문서에서 Mixamo 템플릿 골격과 GLB 내보내기를 지원합니다. Blender는 **기본 모션에 없는 검격, 실제 타격과 피격 맞춤, 무기 그립 조정 및 모션 결합**용입니다. Mixamo는 Meshy 모션으로 부족할 때 기본 모션을 보완합니다.

따라서 **Meshy→Mixamo→Blender를 무조건 전부 거칠 필요는 없습니다.** 매번 도구를 추가하는 대신, 첫 검사에서 통과할 수 있는 가장 짧은 경로를 채택합니다.

참고:
- https://docs.meshy.ai/en/webapp/guides/3d-model/rigging
- https://docs.meshy.cn/en/webapp/guides/animate
- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html

## 현재 작업 상태

- 검사 도구와 자동 테스트: GitHub에 구현
- 실제 Meshy/Blender GLB 파일 확보: **미완료**
- 학원 PC `D:\cha\History_arena` 내용 확인 및 실행: **연결 장애로 미완료**
- Godot에서 실제 그래픽 품질·영상 검증: **미완료**

소스 파일과 계약/라이선스가 필요한 실제 모델은 자동으로 생성·다운로드된 것으로 간주하지 않습니다.
