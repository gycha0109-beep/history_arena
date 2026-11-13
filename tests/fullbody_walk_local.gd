extends SceneTree
## Physical plausibility probe for one full-body walk. Requires the local CC0 GLB.
const Scene = preload("res://scenes/fullbody_walk_5s.tscn")

func _initialize() -> void:
    call_deferred("_check")

func _check() -> void:
    var scene = Scene.instantiate()
    root.add_child(scene)
    if not scene.qa_ready or scene.clip_seconds < 1.0:
        _fail("전신 모델의 보행 동작을 불러오지 못했습니다.")
        return
    var clip: Animation = scene.player.get_animation("Walk_forwards")
    print("FULLBODY_GODOT_TRACKS=",clip.get_track_count())
    if clip.get_track_count() < 50:
        _fail("모델 전체에 대한 원본 애니메이션 항목이 부족합니다.")
        return

    var ids = [
        scene.skeleton.find_bone("ball_l"),
        scene.skeleton.find_bone("ball_r"),
        scene.skeleton.find_bone("upperarm_l"),
        scene.skeleton.find_bone("upperarm_r"),
    ]
    if ids.has(-1):
        _fail("손/발 관련 골격이 없습니다.")
        return
    var ranges: Dictionary = {}
    var max_arm_step: float = 0.0
    var prev_left: Quaternion = Quaternion.IDENTITY
    var prev_right: Quaternion = Quaternion.IDENTITY
    for tick in range(301):
        scene.apply_frame(tick)
        var skel: Skeleton3D = scene.skeleton
        var time: float = float(tick) / scene.FPS
        var cycle: int = floori(time / scene.clip_seconds)
        var phase: float = fmod(time, scene.clip_seconds)
        for foot_index in range(2):
            var is_stance: bool = (
                (foot_index == 0 and phase >= 0.20 and phase <= 0.70)
                or (foot_index == 1 and phase >= 0.85 and phase <= 1.25)
            )
            if not is_stance:
                continue
            var world: Vector3 = skel.to_global(skel.get_bone_global_pose(ids[foot_index]).origin)
            var key: String = "%d_%d" % [cycle,foot_index]
            if not ranges.has(key):
                ranges[key] = Vector2(world.x,world.x)
            else:
                var old: Vector2 = ranges[key]
                ranges[key] = Vector2(minf(old.x,world.x),maxf(old.y,world.x))

        var ql: Quaternion = skel.get_bone_pose_rotation(ids[2])
        var qr: Quaternion = skel.get_bone_pose_rotation(ids[3])
        if tick > 0:
            max_arm_step = maxf(max_arm_step,maxf(prev_left.angle_to(ql),prev_right.angle_to(qr)))
        prev_left=ql
        prev_right=qr

    var worst_slip: float = 0.0
    for key in ranges:
        var region: Vector2 = ranges[key]
        worst_slip=maxf(worst_slip,region.y-region.x)
    var travel: float = scene.actor_root.position.x - (-2.95)
    if worst_slip > 0.03:
        _fail("지지 발이 3cm 넘게 이동합니다: %.4fm" % worst_slip)
        return
    if max_arm_step > deg_to_rad(8.0):
        _fail("팔의 프레임 간 회전이 8도를 초과합니다: %.2fdeg" % rad_to_deg(max_arm_step))
        return
    if absf(travel - 5.215) > 0.025:
        _fail("원본 보폭과 실제 이동 거리가 맞지 않습니다: %.3fm" % travel)
        return

    print("PASS: full-body %d imported tracks, both planted feet %.3fcm drift max, arms %.2fdeg max/frame, 300 frames %.3fm travel" % [
        clip.get_track_count(),100.0*worst_slip,rad_to_deg(max_arm_step),travel])
    quit(0)

func _fail(message: String) -> void:
    push_error(message)
    quit(1)
