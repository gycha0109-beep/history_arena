extends Node3D
## Optional visual layer for the logical fighter.
## Missing 3D assets never prevent the simulation from running.

const WeaponSocketScript = preload("res://scripts/visuals/weapon_socket.gd")

var fighter_id: String = ""
var ready_for_preview: bool = false
var status_message: String = ""
var manifest: Dictionary = {}
var model_root: Node3D
var skeleton: Skeleton3D
var animation_player: AnimationPlayer
var weapon_sockets: Array = []
var animation_state: String = ""
var previous_x: float = 0.0
var has_previous_position: bool = false


func load_manifest(manifest_path: String) -> bool:
    ready_for_preview = false
    if not FileAccess.file_exists(manifest_path):
        status_message = "설정 파일이 없습니다: %s" % manifest_path
        return false

    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
    if typeof(parsed) != TYPE_DICTIONARY:
        status_message = "설정 파일의 JSON 형식이 올바르지 않습니다."
        return false
    manifest = parsed
    fighter_id = str(manifest.get("id", "unknown"))
    var model_path: String = str(manifest.get("model_path", ""))
    if model_path.is_empty() or not ResourceLoader.exists(model_path):
        status_message = "%s: GLB 모델 미등록" % fighter_id
        return false

    var model_scene: PackedScene = load(model_path) as PackedScene
    if model_scene == null:
        status_message = "%s: 모델을 3D 씬으로 읽지 못했습니다." % fighter_id
        return false

    var root_instance: Node = model_scene.instantiate()
    if not root_instance is Node3D:
        root_instance.free()
        status_message = "%s: GLB 루트가 3D 노드가 아닙니다." % fighter_id
        return false

    model_root = root_instance as Node3D
    add_child(model_root)
    skeleton = _find_skeleton(model_root)
    animation_player = _find_animation_player(model_root)
    if skeleton == null:
        status_message = "%s: Skeleton3D가 없습니다. 리깅 모델이 필요합니다." % fighter_id
        return false
    if animation_player == null:
        status_message = "%s: AnimationPlayer가 없습니다. 모션이 필요합니다." % fighter_id
        return false

    if not _attach_weapons():
        return false

    var missing_clips: Array[String] = []
    var required_motions: Array[String] = ["idle", "walk", "attack_light", "hit_react"]
    if fighter_id == "musashi":
        required_motions.append_array(["attack_offhand", "attack_dual"])
    for required in required_motions:
        if not _has_clip(required):
            missing_clips.append(required)
    if not missing_clips.is_empty():
        status_message = "%s: 모션 클립 이름을 확인하세요: %s" % [fighter_id, ", ".join(missing_clips)]
        return false

    ready_for_preview = true
    status_message = "%s: 3D 모델·기본 모션 연결됨 (화질 미검증)" % fighter_id
    return true


func _attach_weapons() -> bool:
    weapon_sockets.clear()
    var specs: Variant = manifest.get("weapons", [])
    if typeof(specs) != TYPE_ARRAY:
        status_message = "%s: weapons는 무기 목록이어야 합니다." % fighter_id
        return false
    if fighter_id == "musashi" and specs.size() != 2:
        status_message = "무사시는 오른손 장검과 왼손 단검이 모두 필요합니다."
        return false

    var attached_bones: Dictionary = {}
    var attached_hands: Dictionary = {}
    for entry in specs:
        if typeof(entry) != TYPE_DICTIONARY:
            status_message = "%s: 무기 설정은 객체여야 합니다." % fighter_id
            return false
        var weapon_config: Dictionary = entry
        var weapon_id: String = str(weapon_config.get("id", "unknown"))
        var handedness: String = str(weapon_config.get("hand", ""))
        if handedness not in ["left", "right"] or attached_hands.has(handedness):
            status_message = "%s: %s 무기의 장착 손이 없거나 중복입니다." % [fighter_id, weapon_id]
            return false
        var weapon_path: String = str(weapon_config.get("model_path", ""))
        if not weapon_path.begins_with("res://") or not ResourceLoader.exists(weapon_path):
            status_message = "%s: %s 별도 GLB 미등록" % [fighter_id, weapon_id]
            return false
        var bone_candidates: Variant = weapon_config.get("hand_bone_candidates", [])
        if typeof(bone_candidates) != TYPE_ARRAY or bone_candidates.is_empty():
            status_message = "%s: %s의 손뼈 후보가 없습니다." % [fighter_id, weapon_id]
            return false
        var sword_scene: PackedScene = load(weapon_path) as PackedScene
        if sword_scene == null:
            status_message = "%s: %s 무기 모델을 읽지 못했습니다." % [fighter_id, weapon_id]
            return false

        var socket = WeaponSocketScript.new()
        socket.name = "Grip_%s_%s" % [handedness, weapon_id]
        add_child(socket)
        if not socket.bind_to_skeleton(skeleton, bone_candidates):
            status_message = "%s: %s 손뼈를 찾을 수 없습니다." % [fighter_id, weapon_id]
            return false
        if attached_bones.has(socket.bone_index):
            status_message = "%s: 두 자루의 검이 같은 손뼈에 연결됐습니다." % fighter_id
            return false
        attached_bones[socket.bone_index] = true
        attached_hands[handedness] = true

        var weapon_instance: Node = sword_scene.instantiate()
        if not weapon_instance is Node3D:
            weapon_instance.free()
            status_message = "%s: %s 검 모델 루트가 3D가 아닙니다." % [fighter_id, weapon_id]
            return false
        socket.add_child(weapon_instance)

        var offset: Variant = weapon_config.get("grip_position", [0.0, 0.0, 0.0])
        var angles: Variant = weapon_config.get("grip_rotation_degrees", [0.0, 0.0, 0.0])
        if typeof(offset) != TYPE_ARRAY or typeof(angles) != TYPE_ARRAY:
            status_message = "%s: %s 손잡이 설정 형식 오류" % [fighter_id, weapon_id]
            return false
        if offset.size() != 3 or angles.size() != 3:
            status_message = "%s: %s 손잡이 좌표는 숫자 세 개여야 합니다." % [fighter_id, weapon_id]
            return false
        var grip: Node3D = weapon_instance as Node3D
        grip.position = Vector3(float(offset[0]), float(offset[1]), float(offset[2]))
        grip.rotation_degrees = Vector3(float(angles[0]), float(angles[1]), float(angles[2]))
        grip.scale = Vector3.ONE
        weapon_sockets.append(socket)

    if fighter_id == "musashi" and not (attached_hands.has("right") and attached_hands.has("left")):
        status_message = "이도류는 두 손에 각각 한 자루씩 장착해야 합니다."
        return false
    return true


func sync_from_fighter(fighter_state: Dictionary, opponent_x: float) -> void:
    var new_x: float = float(fighter_state.get("x", 0.0))
    var moved: bool = has_previous_position and absf(new_x - previous_x) > 0.001
    position.x = new_x
    rotation.y = PI / 2.0 if opponent_x > new_x else -PI / 2.0
    previous_x = new_x
    has_previous_position = true

    if not ready_for_preview:
        return

    var combat_action: String = str(fighter_state.get("action", "idle"))
    var desired: String = "idle"
    if int(fighter_state.get("hp", 100)) <= 0:
        desired = "ko"
    elif combat_action == "stunned":
        desired = "hit_react"
    elif combat_action == "attack":
        var attack_name: String = str(fighter_state.get("move", ""))
        desired = _map_attack(attack_name)
    elif moved:
        desired = "walk"

    if desired != animation_state:
        animation_state = desired
        _play_named_clip(desired)


func _map_attack(move_name: String) -> String:
    match move_name:
        "quick_cut", "jab":
            return "attack_light"
        "heavy_cut", "side_kick":
            return "attack_heavy"
        "wakizashi_cut":
            return "attack_offhand"
        "dual_cross":
            return "attack_dual"
        _:
            return "idle"


func _has_clip(state_name: String) -> bool:
    if animation_player == null:
        return false
    var clips: Dictionary = manifest.get("animation_clips", {})
    var names: Array = clips.get(state_name, [])
    for requested in names:
        if animation_player.has_animation(str(requested)):
            return true
    return false


func _play_named_clip(state_name: String) -> void:
    if animation_player == null:
        return
    var clips: Dictionary = manifest.get("animation_clips", {})
    var names: Array = clips.get(state_name, [])
    for requested in names:
        var requested_name: String = str(requested)
        if animation_player.has_animation(requested_name):
            animation_player.play(requested_name, 0.1)
            return
    if state_name != "idle":
        _play_named_clip("idle")
    else:
        push_warning("%s: 'idle' 애니메이션을 찾을 수 없습니다. GLB 안의 클립 이름을 확인하세요." % fighter_id)


func _find_skeleton(node: Node) -> Skeleton3D:
    if node is Skeleton3D:
        return node as Skeleton3D
    for child in node.get_children():
        var found: Skeleton3D = _find_skeleton(child)
        if found != null:
            return found
    return null


func _find_animation_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node as AnimationPlayer
    for child in node.get_children():
        var found: AnimationPlayer = _find_animation_player(child)
        if found != null:
            return found
    return null
