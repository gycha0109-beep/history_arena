extends SceneTree
## Local-only quality assertion: requires external CesiumMan and two QA sword GLBs.
## Not used in CI because these third-party/derived assets are gitignored.

const Scene = preload("res://scenes/qa_rigged_sample.tscn")


func _initialize() -> void:
    call_deferred("_run")


func _run() -> void:
    var scene = Scene.instantiate()
    root.add_child(scene)
    if not scene.qa_ready or scene.weapons.size() != 2:
        _fail("두 자루 무기와 리깅 모델이 준비되지 않았습니다.")
        return

    scene.apply_frame(0)
    var first_long: Vector3 = _sword_axis(scene.weapons[0])
    var first_short: Vector3 = _sword_axis(scene.weapons[1])
    if first_long.length() < 0.01 or first_short.length() < 0.01:
        _fail("검날 길이를 측정할 수 없습니다.")
        return
    if first_long.length() <= first_short.length()*1.25:
        _fail("장검이 단검보다 충분히 길지 않습니다.")
        return

    for t in range(301):
        scene.apply_frame(t)
        if scene.max_scale_errors[0] > 0.001 or scene.max_scale_errors[1] > 0.001:
            _fail("검 크기가 모션 도중 달라졌습니다.")
            return
        if scene.max_grip_errors[0] > 0.001 or scene.max_grip_errors[1] > 0.001:
            _fail("손과 손잡이가 떨어졌습니다.")
            return
        for foot in ["leg_joint_L_5", "leg_joint_R_5"]:
            var idx: int = scene.skeleton.find_bone(foot)
            var foot_world: Vector3 = (
                scene.skeleton.global_transform * scene.skeleton.get_bone_global_pose(idx)
            ).origin
            if absf(foot_world.y) > 0.06:
                _fail("%s가 발을 바닥에서 지나치게 들었습니다: %.4f" % [foot, foot_world.y])
                return

    if scene.head_z_max - scene.head_z_min > 0.03:
        _fail("머리 상하 움직임이 3cm를 초과합니다.")
        return
    if scene.max_head_pitch_degrees > 2.0:
        _fail("머리 회전이 2도를 초과합니다.")
        return

    scene.apply_frame(140)
    var changed_long: Vector3 = _sword_axis(scene.weapons[0])
    var changed_short: Vector3 = _sword_axis(scene.weapons[1])
    if first_long.normalized().angle_to(changed_long.normalized()) < 0.12:
        _fail("장검 검격 동작에 충분한 방향 변화가 없습니다.")
        return
    if first_short.normalized().angle_to(changed_short.normalized()) < 0.09:
        _fail("단검 방어 동작에 충분한 방향 변화가 없습니다.")
        return

    print("PASS: 2 real GLB swords, both feet planted, closed grips, head stable, 300 frames")
    quit(0)


func _sword_axis(sword: Node3D) -> Vector3:
    var blade: MeshInstance3D = _find_blade(sword)
    if blade == null:
        return Vector3.ZERO
    var tip: Vector3 = Vector3.ZERO
    var length_squared: float = 0.0
    for surface in range(blade.mesh.get_surface_count()):
        var verts: PackedVector3Array = blade.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
        for vert in verts:
            var world: Vector3 = blade.to_global(vert)
            var distance: float = world.distance_squared_to(sword.global_position)
            if distance > length_squared:
                length_squared = distance
                tip = world
    return tip - sword.global_position


func _find_blade(node: Node) -> MeshInstance3D:
    if node is MeshInstance3D and "stable blade" in node.name:
        return node
    for ch in node.get_children():
        var found: MeshInstance3D = _find_blade(ch)
        if found != null:
            return found
    return null


func _fail(message: String) -> void:
    push_error(message)
    quit(1)
