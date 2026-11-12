extends SceneTree

const WeaponSocketScript = preload("res://scripts/visuals/weapon_socket.gd")
const CharacterVisualScript = preload("res://scripts/visuals/character_visual.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var holder: Node3D = Node3D.new()
    root.add_child(holder)

    var skeleton: Skeleton3D = Skeleton3D.new()
    holder.add_child(skeleton)
    var hand_bone: int = skeleton.add_bone("RightHand")
    skeleton.set_bone_rest(hand_bone, Transform3D(Basis.IDENTITY, Vector3(0.7, 1.1, 0.0)))

    var socket = WeaponSocketScript.new()
    holder.add_child(socket)
    if not socket.bind_to_skeleton(skeleton, ["missing", "RightHand"]):
        _fail("실제 손뼈를 찾지 못했습니다.")
        return

    var sword: Node3D = Node3D.new()
    socket.add_child(sword)

    skeleton.set_bone_pose_scale(hand_bone, Vector3(1.8, 0.5, 1.3))
    skeleton.set_bone_pose_position(hand_bone, Vector3(0.5, 1.2, 0.0))
    socket.update_socket()
    var socket_scale: Vector3 = socket.global_transform.basis.get_scale()
    if not socket_scale.is_equal_approx(Vector3.ONE):
        _fail("손뼈가 늘어나면 무기까지 늘어나는 문제가 발견됐습니다.")
        return
    var expected: Vector3 = (skeleton.global_transform * skeleton.get_bone_global_pose(hand_bone)).origin
    if socket.global_position.distance_to(expected) > 0.0001:
        _fail("무기가 손뼈의 위치를 따라가지 않습니다.")
        return
    if not sword.global_transform.basis.get_scale().is_equal_approx(Vector3.ONE):
        _fail("손뼈 변형으로 별도 무기 메시에 배율이 발생했습니다.")
        return

    var visual = CharacterVisualScript.new()
    holder.add_child(visual)
    if visual.load_manifest("res://assets/characters/musashi/character.json"):
        _fail("실제 모델이 없는데 모델 연결이 성공했다고 표시했습니다.")
        return
    if not visual.status_message.contains("GLB 모델 미등록"):
        _fail("모델이 없는 상태를 사용자에게 알리지 못했습니다.")
        return

    visual.sync_from_fighter({"x": -1.75, "action": "idle", "hp": 100}, 1.75)
    if not is_equal_approx(visual.position.x, -1.75):
        _fail("전투 좌표와 시각 캐릭터 좌표 연동에 실패했습니다.")
        return

    print("PASS: rigid weapon attachment, missing-asset notice and visual-position sync")
    quit(0)


func _fail(message: String) -> void:
    push_error(message)
    quit(1)
