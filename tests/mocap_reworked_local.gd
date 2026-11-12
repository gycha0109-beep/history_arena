extends SceneTree
## Local-only validation. The third-party GLB sources are intentionally gitignored.
const SCENE = preload("res://scenes/mocap_5s_reworked.tscn")

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var scene = SCENE.instantiate()
    root.add_child(scene)
    if not scene.qa_ready or scene.clip_seconds < 1.0:
        _fail("합성된 실제 5초 보행 모션을 불러오지 못했습니다.")
        return
    var animation: Animation = scene.player.get_animation("mocap_walk_composite")
    if animation.get_track_count() < 20:
        _fail("상체 동작이 없어 불완전한 보행 기록입니다.")
        return
    var left_toe: int = scene.skeleton.find_bone("mixamorig_LeftToeBase")
    var arm: int = scene.skeleton.find_bone("mixamorig_LeftArm")
    if left_toe < 0 or arm < 0:
        _fail("발가락 또는 팔 관절이 없습니다.")
        return
    var min_swing_height: float = INF
    var min_arm_angle: float = INF
    var max_arm_angle: float = 0.0
    var arm_initial: Quaternion = Quaternion.IDENTITY
    for tick in range(301):
        scene.apply_frame(tick)
        var phase: float = fmod(float(tick) / 60.0, scene.clip_seconds)
        var toe: Vector3 = scene.skeleton.to_global(
            scene.skeleton.get_bone_global_pose(left_toe).origin)
        var q: Quaternion = scene.skeleton.get_bone_pose_rotation(arm)
        if tick == 0:
            arm_initial = q
        var angle: float = arm_initial.angle_to(q)
        min_arm_angle = minf(min_arm_angle, angle)
        max_arm_angle = maxf(max_arm_angle, angle)
        if phase >= 0.63 and phase <= 0.75:
            min_swing_height = minf(min_swing_height, toe.y)
    if min_swing_height < 0.02:
        _fail("왼발 전진 구간 발끝의 지면 여유가 2cm 미만입니다: %.4f" % min_swing_height)
        return
    if max_arm_angle < 0.02:
        _fail("상체와 팔에 실제 보행 애니메이션이 없습니다.")
        return
    if max_arm_angle > 0.85:
        _fail("팔 회전이 지나쳐 모션이 부자연스럽습니다.")
        return
    print("PASS: 5s composite walk, left toe minimum swing height %.4fm, arm angular motion %.2fdeg, 300 frames" % [
        min_swing_height, rad_to_deg(max_arm_angle)])
    quit(0)

func _fail(reason: String) -> void:
    push_error(reason)
    quit(1)
