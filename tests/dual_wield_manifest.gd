extends SceneTree

const SocketScript = preload("res://scripts/visuals/weapon_socket.gd")
const CombatScript = preload("res://scripts/core/combat_simulator.gd")
const CharacterVisualScript = preload("res://scripts/visuals/character_visual.gd")


func _initialize() -> void:
    call_deferred("_run")


func _run() -> void:
    var json_path: String = "res://assets/characters/musashi/character.json"
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(json_path))
    if typeof(parsed) != TYPE_DICTIONARY:
        _fail("무사시 설정 JSON을 읽지 못했습니다.")
        return
    var weapon_specs: Variant = parsed.get("weapons", [])
    if typeof(weapon_specs) != TYPE_ARRAY or weapon_specs.size() != 2:
        _fail("무사시는 두 자루의 검을 사용해야 합니다.")
        return

    var got_hands: Dictionary = {}
    var got_ids: Dictionary = {}
    for spec in weapon_specs:
        if typeof(spec) != TYPE_DICTIONARY:
            _fail("이도류 검 설정은 객체여야 합니다.")
            return
        var hand: String = str(spec.get("hand", ""))
        var id: String = str(spec.get("id", ""))
        if got_hands.has(hand) or got_ids.has(id):
            _fail("검의 장착 손 또는 ID가 중복되었습니다.")
            return
        got_hands[hand] = true
        got_ids[id] = true
        if typeof(spec.get("hand_bone_candidates")) != TYPE_ARRAY:
            _fail("손뼈 후보 목록이 없습니다.")
            return
        if spec["hand_bone_candidates"].is_empty():
            _fail("손뼈 후보 목록이 비었습니다.")
            return

    if not got_hands.has("right") or not got_hands.has("left"):
        _fail("검 두 자루를 서로 다른 손에 장착해야 합니다.")
        return
    if not got_ids.has("katana") or not got_ids.has("wakizashi"):
        _fail("장검과 단검이 모두 정의돼야 합니다.")
        return
    if got_ids.size() != 2:
        _fail("불필요한 검이 추가되었습니다.")
        return

    var parent: Node3D = Node3D.new()
    root.add_child(parent)
    var skeleton: Skeleton3D = Skeleton3D.new()
    parent.add_child(skeleton)
    var right: int = skeleton.add_bone("RightHand")
    var left: int = skeleton.add_bone("LeftHand")
    skeleton.set_bone_rest(right, Transform3D(Basis.IDENTITY, Vector3(0.6, 1.2, 0)))
    skeleton.set_bone_rest(left, Transform3D(Basis.IDENTITY, Vector3(-0.6, 1.2, 0)))

    var sockets: Array = []
    for name in ["RightHand", "LeftHand"]:
        var socket = SocketScript.new()
        parent.add_child(socket)
        if not socket.bind_to_skeleton(skeleton, [name]):
            _fail("검 소켓 연결에 실패했습니다: " + name)
            return
        sockets.append(socket)
    if sockets[0].bone_index == sockets[1].bone_index:
        _fail("두 소켓이 같은 손에 연결됐습니다.")
        return

    skeleton.set_bone_pose_scale(right, Vector3(1.4, 0.8, 1.2))
    skeleton.set_bone_pose_scale(left, Vector3(0.8, 1.3, 1.0))
    skeleton.set_bone_pose_position(right, Vector3(0.7, 1.4, 0))
    skeleton.set_bone_pose_position(left, Vector3(-0.7, 1.4, 0))
    for socket in sockets:
        socket.update_socket()
        if not socket.global_transform.basis.get_scale().is_equal_approx(Vector3.ONE):
            _fail("검 소켓이 손뼈의 배율을 그대로 받아 변형됐습니다.")
            return

    var lee: Variant = JSON.parse_string(FileAccess.get_file_as_string(
        "res://assets/characters/bruce_lee/character.json"))
    if typeof(lee) != TYPE_DICTIONARY or typeof(lee.get("weapons")) != TYPE_ARRAY:
        _fail("이소룡의 비무장 설정이 잘못됐습니다.")
        return
    if not lee["weapons"].is_empty():
        _fail("이소룡은 맨손 캐릭터여야 합니다.")
        return

    var combat_moves: Dictionary = CombatScript.MOVES["musashi"]
    var clips: Dictionary = parsed["animation_clips"]
    for move_name in ["quick_cut", "heavy_cut", "wakizashi_cut", "dual_cross"]:
        if not combat_moves.has(move_name):
            _fail("무사시의 검술 기술이 누락됐습니다: " + move_name)
            return
    for motion_name in ["attack_light", "attack_heavy", "attack_offhand", "attack_dual"]:
        if not clips.has(motion_name) or clips[motion_name].is_empty():
            _fail("이도류 공격 애니메이션 설정이 없습니다: " + motion_name)
            return
    var visual = CharacterVisualScript.new()
    if visual._map_attack("wakizashi_cut") != "attack_offhand":
        _fail("단검 공격과 애니메이션 연결이 잘못됐습니다.")
        return
    if visual._map_attack("dual_cross") != "attack_dual":
        _fail("양손 합동 공격과 애니메이션 연결이 잘못됐습니다.")
        return
    visual.free()
    print("PASS: katana right, wakizashi left, 4 sword moves, independent rigid grips")
    quit(0)


func _fail(message: String) -> void:
    push_error(message)
    quit(1)
