extends SceneTree
## Verifies actual 5-second dual-grip gait in local, license-cleared QA assets.
## The test is deliberately NOT called "final Musashi quality": this is a prototype.

const SCENE = preload("res://scenes/dual_guard_walk_5s.tscn")
const REQUIRED_BONES = [
    "hand_r", "hand_l", "middle_01_r", "middle_01_l",
    "index_01_r", "index_02_r", "index_01_l", "index_02_l",
    "ball_r", "ball_l"
]

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var scene = SCENE.instantiate()
    root.add_child(scene)
    if not scene.qa_ready or scene.weapons.size() != 2 or scene.sockets.size() != 2:
        _fail("양손 장검·단검이 실제로 연결되지 않았습니다.")
        return

    var skeleton: Skeleton3D = scene.skeleton
    for name in REQUIRED_BONES:
        if skeleton.find_bone(name) < 0:
            _fail("실제 손가락·발 리깅이 누락됐습니다: " + name)
            return
    if scene.sockets[0].bone_index == scene.sockets[1].bone_index:
        _fail("두 검이 같은 손에 연결됐습니다.")
        return

    var original: Animation = scene.player.get_animation("Walk_forwards")
    var dual: Animation = scene.player.get_animation("Walk_DualGuard")
    if original.length < 1.0 or absf(original.length-dual.length) > 0.001:
        _fail("검을 든 보행과 원본 보행의 주기가 다릅니다.")
        return

    var worst_foot_delta: float = 0
    var sword_max_scale: float = 0
    var min_body_clearance: float = 1000.0
    var max_grip_gap: float = 0
    var max_arm_step_deg: float = 0
    var previous_arms: Array[Quaternion] = []
    for tick in range(301):
        scene.apply_frame(tick)
        var clock: float = fmod(float(tick)/scene.FPS,scene.clip_seconds)
        var ground: Array[Vector3] = []
        for name in ["ball_l","ball_r"]:
            ground.append(skeleton.get_bone_global_pose(
                skeleton.find_bone(name)).origin)

        for hand_index in range(2):
            var index: int = skeleton.find_bone("middle_01_r" if hand_index==0 else "middle_01_l")
            var knuckle_world: Vector3 = skeleton.to_global(skeleton.get_bone_global_pose(index).origin)
            var sword: Node3D = scene.weapons[hand_index]
            var p: Vector3 = sword.global_position
            max_grip_gap = maxf(max_grip_gap,p.distance_to(knuckle_world))
            sword_max_scale = maxf(sword_max_scale,
                sword.global_transform.basis.get_scale().distance_to(Vector3.ONE))
            var torso: Vector3 = skeleton.to_global(skeleton.get_bone_global_pose(
                skeleton.find_bone("spine_02")).origin)
            var tip_dir: Vector3 = sword.global_transform.basis.y.normalized()
            # Blade samples, excluding the guard and the first 10cm around the hands.
            for length in [0.20,0.35,0.50]:
                var blade_sample: Vector3 = p + tip_dir * length
                if blade_sample.y > 0.95 and blade_sample.y < 1.55:
                    min_body_clearance = minf(min_body_clearance,
                        Vector2(blade_sample.x-torso.x,blade_sample.z-torso.z).length())

        var current_arms: Array[Quaternion] = []
        for name in ["upperarm_l","upperarm_r"]:
            current_arms.append(skeleton.get_bone_pose_rotation(skeleton.find_bone(name)))
        if not previous_arms.is_empty():
            for i in range(2):
                max_arm_step_deg=maxf(max_arm_step_deg,
                    rad_to_deg(previous_arms[i].angle_to(current_arms[i])))
        previous_arms=current_arms

        if tick % 10 == 0:
            scene.player.play("Walk_forwards")
            scene.player.pause()
            scene.player.seek(clock,true)
            for index in range(2):
                var bone_name: String = "ball_l" if index==0 else "ball_r"
                var original_p: Vector3 = skeleton.get_bone_global_pose(
                    skeleton.find_bone(bone_name)).origin
                worst_foot_delta=maxf(worst_foot_delta,
                    original_p.distance_to(ground[index]))
            scene.player.play("Walk_DualGuard")
            scene.player.pause()
            scene.player.seek(clock,true)

    if worst_foot_delta > 0.003:
        _fail("기존에 통과한 발걸음이 검 장착 후 변형됐습니다: %.5fm" % worst_foot_delta)
        return
    if sword_max_scale > 0.001:
        _fail("걸을 때 검 길이가 늘어났습니다.")
        return
    if max_grip_gap > 0.10:
        _fail("손가락과 손잡이 사이가 너무 멉니다: %.3fm" % max_grip_gap)
        return
    if max_arm_step_deg > 9.0:
        _fail("보행 중 팔이 한 프레임에 갑자기 크게 회전합니다.")
        return
    if min_body_clearance < 0.16:
        _fail("근사 몸통 경계에 검날이 접근합니다: %.3fm" % min_body_clearance)
        return
    print("PASS dual sword 5s QA: fingers=yes swords=2 foot_delta=%.5fm scale_error=%.8f max_hand_gap=%.4fm arm_max_step=%.3fdeg body_clearance=%.3fm" % [
        worst_foot_delta,sword_max_scale,max_grip_gap,max_arm_step_deg,min_body_clearance])
    quit(0)

func _fail(message: String) -> void:
    push_error(message)
    quit(1)
