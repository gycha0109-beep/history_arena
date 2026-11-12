extends SceneTree
## Local test uses licensed external animated humanoid (not checked into Git).
const Scene = preload("res://scenes/walk_five_seconds.tscn")

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var scene = Scene.instantiate()
    root.add_child(scene)
    if not scene.ready_to_render:
        _fail("실제 걷기 모델 및 애니메이션이 준비되지 않았습니다.")
        return
    if scene.walk_player.get_animation("Walk").length < 0.5:
        _fail("걷기 클립이 지나치게 짧습니다.")
        return

    var min_y: Array[float] = [999.0,999.0]
    var max_y: Array[float] = [-999.0,-999.0]
    for frame in range(301):
        scene.apply_frame(frame)
        for index in range(2):
            var name: String = "LeftFoot" if index == 0 else "RightFoot"
            var bone_id: int = scene.skeleton.find_bone(name)
            if bone_id < 0:
                _fail("다리/발 골격이 누락됐습니다: " + name)
                return
            var pose: Vector3 = scene.skeleton.to_global(
                scene.skeleton.get_bone_global_pose(bone_id).origin)
            min_y[index] = minf(min_y[index], pose.y)
            max_y[index] = maxf(max_y[index], pose.y)

    for index in range(2):
        var lift: float = max_y[index] - min_y[index]
        if lift < 0.045:
            _fail("실제로 발을 들어 걷지 않습니다: 발 움직임 %.3fm" % lift)
            return
        if scene.planted_samples[index] < 80:
            _fail("충분한 지지 발 구간이 없습니다.")
            return
        var avg_stance_slip: float = scene.stance_slip[index] / scene.planted_samples[index]
        if avg_stance_slip > 0.0020:
            _fail("발 접지 구간의 평균 미끄러짐이 큽니다: %.4fm/프레임" % avg_stance_slip)
            return
        if scene.max_stance_step[index] > 0.005:
            _fail("발 접지 중 순간적으로 움직임이 큽니다.")
            return

    if scene.largest_target_error > 0.09:
        _fail("?? ???? ?? ??? ?? ??? 9cm? ????.")
        return
    if absf(scene.actor_root.position.x - 1.15) > 0.01:
        _fail("5초 종료 시 실제 X좌표가 6.75m 전진하지 않았습니다.")
        return
    print("PASS: 5s IK foot planting, 4.5m travel, both feet swing and low planted-frame motion")
    quit(0)

func _fail(message: String) -> void:
    push_error(message)
    quit(1)
