extends Node3D
## Asset-import and rigid-sword QA scene, NOT a game-character preview.
## Uses Khronos CesiumMan (CC BY 4.0) if locally provided.

const WeaponSocketScript = preload("res://scripts/visuals/weapon_socket.gd")

@onready var camera: Camera3D = $Camera3D
@onready var status_label: Label = $HUD/Status

const HUMANOID_PATH: String = "res://samples/external/CesiumMan.glb"
const KATANA_PATH: String = "res://samples/external/qa_katana.glb"
const BONE_NAMES: Array[String] = ["Skeleton_arm_joint_R__3_", "Skeleton_arm_joint_R__2_", "Skeleton_arm_joint_R"]

var armature: Skeleton3D
var animation_player: AnimationPlayer
var sword_socket
var sword_model: Node3D
var animation_length: float = 1.0
var rendered_ticks: int = 0
var start_bone: Vector3
var last_bone: Vector3
var travel: float = 0.0
var worst_scale_error: float = 0.0
var report_written: bool = false


func _ready() -> void:
    camera.look_at(Vector3(0, 1.15, 0), Vector3.UP)
    if not ResourceLoader.exists(HUMANOID_PATH) or not ResourceLoader.exists(KATANA_PATH):
        push_error("테스트용 3D 인체/검 GLB 파일이 누락되었습니다.")
        return

    var humanoid: PackedScene = load(HUMANOID_PATH) as PackedScene
    var sword_scene: PackedScene = load(KATANA_PATH) as PackedScene
    if humanoid == null or sword_scene == null:
        push_error("GLB를 Godot 3D 씬으로 읽지 못했습니다.")
        return

    var human: Node3D = humanoid.instantiate() as Node3D
    $Actors.add_child(human)
    armature = _find_skeleton(human)
    animation_player = _find_animation_player(human)
    if armature == null or animation_player == null or not animation_player.has_animation("Animation"):
        push_error("모델의 3D 골격·Animation 클립이 없습니다.")
        return

    sword_socket = WeaponSocketScript.new()
    sword_socket.name = "RigidSwordSocket"
    $Actors.add_child(sword_socket)
    if not sword_socket.bind_to_skeleton(armature, BONE_NAMES):
        push_error("오른팔 장착 지점을 찾지 못했습니다.")
        return

    sword_model = sword_scene.instantiate() as Node3D
    sword_socket.add_child(sword_model)
    sword_model.position = Vector3(0, 0, 0)
    sword_model.rotation_degrees = Vector3(0, 90, 0)
    sword_model.scale = Vector3.ONE

    animation_player.play("Animation")
    animation_length = maxf(animation_player.current_animation_length, 0.1)
    _apply_tick(0)
    start_bone = sword_socket.global_position
    last_bone = start_bone
    status_label.text = "실제 3D 골격 + 독립 검 메시 | 임시 품질 검사"


func _physics_process(_delta: float) -> void:
    if sword_socket == null:
        return
    if rendered_ticks < 300:
        rendered_ticks += 1
        _apply_tick(rendered_ticks)
    if rendered_ticks == 300 and not report_written:
        report_written = true
        status_label.text = "검 크기 변형 최대 오차 %.5f | 관절 이동 합계 %.3fm" % [
            worst_scale_error, travel
        ]
        print("QA_RIG_MOTION frames=300 max_scale_error=%.7f bone_travel=%.4f" % [worst_scale_error, travel])


func _apply_tick(tick: int) -> void:
    var seconds: float = float(tick) / 60.0
    animation_player.seek(fmod(seconds, animation_length), true)
    sword_socket.update_socket()
    var scale: Vector3 = sword_socket.global_transform.basis.get_scale()
    var error: float = scale.distance_to(Vector3.ONE)
    worst_scale_error = maxf(worst_scale_error, error)
    if tick > 0:
        travel += last_bone.distance_to(sword_socket.global_position)
    last_bone = sword_socket.global_position


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
