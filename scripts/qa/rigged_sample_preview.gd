extends Node3D
## Five-second dual-wield QA. Uses licensed local sample model ONLY for rig testing.
## Production Musashi requires a proper two-hand, finger-rigged combat animation.

const WeaponSocketScript = preload("res://scripts/visuals/weapon_socket.gd")
const MODEL_PATH: String = "res://samples/external/CesiumMan.glb"
const LONG_PATH: String = "res://samples/external/qa_katana_dual.glb"
const SHORT_PATH: String = "res://samples/external/qa_wakizashi_dual.glb"
const R_HAND: String = "Skeleton_arm_joint_R__3_"
const L_HAND: String = "Skeleton_arm_joint_L__2_"
const ROOT_BONE: String = "Skeleton_torso_joint_1"
const NECK_BONE: String = "Skeleton_neck_joint_1"
const HEAD_BONE: String = "Skeleton_neck_joint_2"
const FRAMES: int = 300

@onready var camera: Camera3D = $Camera3D
@onready var status_label: Label = $HUD/Status

var skeleton: Skeleton3D
var player: AnimationPlayer
var sockets: Array = []
var weapons: Array[Node3D] = []
var wrists: Array[int] = []
var root_bone: int = -1
var neck_bone: int = -1
var head_bone: int = -1
var root_neutral: Vector3
var neck_neutral: Quaternion
var head_neutral_basis: Basis
var qa_ready: bool = false
var current_frame: int = 0
var max_scale_errors: Array[float] = [0.0, 0.0]
var max_grip_errors: Array[float] = [0.0, 0.0]
var max_head_pitch_degrees: float = 0.0
var head_z_min: float = 1000.0
var head_z_max: float = -1000.0
var report_printed: bool = false
var grounded_poses: Dictionary = {}


func _ready() -> void:
    camera.look_at(Vector3(0, 1.0, 0), Vector3.UP)
    for path in [MODEL_PATH, LONG_PATH, SHORT_PATH]:
        if not ResourceLoader.exists(path):
            push_error("Dual-wield QA is missing local GLB: " + path)
            return

    var human: Node3D = (load(MODEL_PATH) as PackedScene).instantiate() as Node3D
    $Actors.add_child(human)
    skeleton = _find_skeleton(human)
    player = _find_player(human)
    if skeleton == null or player == null or not player.has_animation("Animation"):
        push_error("QA humanoid needs Skeleton3D and Animation clip.")
        return

    wrists = [skeleton.find_bone(R_HAND), skeleton.find_bone(L_HAND)]
    root_bone = skeleton.find_bone(ROOT_BONE)
    neck_bone = skeleton.find_bone(NECK_BONE)
    head_bone = skeleton.find_bone(HEAD_BONE)
    if wrists.has(-1) or root_bone < 0 or neck_bone < 0 or head_bone < 0:
        push_error("Missing one or more required rig bones for dual-wield QA.")
        return

    player.play("Animation")
    player.pause()  # stop automatic updates from overwriting authored wrist/leg/head poses
    # Snapshot each leg from the actual planted-foot phase of the source walk.
    for setup in [{"prefix": "leg_joint_L_", "time": 1.12}, {"prefix": "leg_joint_R_", "time": 0.11}]:
        player.seek(float(setup["time"]), true)
        for index in range(skeleton.get_bone_count()):
            if skeleton.get_bone_name(index).begins_with(str(setup["prefix"])):
                grounded_poses[index] = skeleton.get_bone_pose(index)
    player.seek(0.12, true)
    root_neutral = skeleton.get_bone_pose_position(root_bone)
    neck_neutral = skeleton.get_bone_pose_rotation(neck_bone)
    head_neutral_basis = skeleton.get_bone_global_pose(head_bone).basis.orthonormalized()

    for slot in range(2):
        var hand_name: String = R_HAND if slot == 0 else L_HAND
        var sword_file: String = LONG_PATH if slot == 0 else SHORT_PATH
        var socket = WeaponSocketScript.new()
        socket.name = "RightHandKatana" if slot == 0 else "LeftHandWakizashi"
        $Actors.add_child(socket)
        if not socket.bind_to_skeleton(skeleton, [hand_name]):
            push_error("Cannot bind hand to sword: " + hand_name)
            return
        var weapon: Node3D = (load(sword_file) as PackedScene).instantiate() as Node3D
        weapon.name = "LongSword" if slot == 0 else "ShortSword"
        socket.add_child(weapon)
        weapon.position = Vector3.ZERO
        weapon.rotation = Vector3.ZERO
        weapon.scale = Vector3.ONE
        sockets.append(socket)
        weapons.append(weapon)

    qa_ready = true
    apply_frame(0)
    status_label.text = "이도류 검사: 오른손 장검 + 왼손 단검, 손잡이 폐합, 머리 안정화"


func _physics_process(_delta: float) -> void:
    if not qa_ready:
        return
    if current_frame < FRAMES:
        apply_frame(current_frame + 1)
    if current_frame == FRAMES and not report_printed:
        report_printed = true
        var head_bob: float = head_z_max - head_z_min
        print("DUAL_WIELD_QA frames=%d sword_count=2 long_scale_error=%.8f short_scale_error=%.8f grip_error=(%.7f,%.7f) head_vertical_range=%.4f head_rotation_max_deg=%.4f" % [
            FRAMES, max_scale_errors[0], max_scale_errors[1],
            max_grip_errors[0], max_grip_errors[1], head_bob, max_head_pitch_degrees])
        status_label.text = "이도류 테스트: 장검 + 단검 | 검 크기 오차 %.6f / %.6f | 머리 흔들림 %.3fm" % [
            max_scale_errors[0], max_scale_errors[1], head_bob]


func apply_frame(tick: int) -> void:
    if not qa_ready:
        return
    current_frame = clampi(tick, 0, FRAMES)
    var t: float = float(current_frame) / 60.0
    # Don't loop the exaggerated sample walk throughout the whole shot.
    # Small, deliberate stance changes, then guard recovery.
    var motion_t: float = 0.12
    if t >= 1.2 and t < 2.7:
        motion_t = lerpf(0.12, 0.65, _smooth((t-1.2)/1.5))
    elif t >= 2.7 and t < 3.7:
        motion_t = lerpf(0.65, 0.12, _smooth((t-2.7)/1.0))
    player.seek(motion_t, true)
    # Guard stance: feet remain planted, no continuous walk-cycle stepping.
    for index in grounded_poses.keys():
        skeleton.set_bone_pose(int(index), grounded_poses[index])

    # Reduce inherited hip bounce and freeze independently animated neck turns.
    var root_now: Vector3 = skeleton.get_bone_pose_position(root_bone)
    skeleton.set_bone_pose_position(root_bone, Vector3(root_now.x, root_now.y,
        lerpf(root_neutral.z, root_now.z, 0.13)))
    skeleton.set_bone_pose_rotation(neck_bone, neck_neutral)
    var head: Transform3D = skeleton.get_bone_global_pose(head_bone)
    skeleton.set_bone_global_pose(head_bone, Transform3D(
        head_neutral_basis, head.origin))

    # Both skinned wrists and their sword sockets rotate together, to a
    # deliberate two-sword guard/sweep/recovery instead of dangling blades.
    var attack: float = 0.0
    if t >= 1.45 and t < 2.15:
        attack = _smooth((t-1.45)/0.7)
    elif t >= 2.15 and t < 3.1:
        attack = 1.0 - _smooth((t-2.15)/0.95)

    var long_guard: Vector3 = Vector3(0.65, 0.76, 0.10).normalized()
    var short_guard: Vector3 = Vector3(-0.72, 0.66, 0.18).normalized()
    var long_cut: Vector3 = Vector3(0.97, 0.17, -0.12).normalized()
    var short_parry: Vector3 = Vector3(-0.91, 0.32, 0.10).normalized()
    var desired_dirs: Array[Vector3] = [
        long_guard.lerp(long_cut, attack).normalized(),
        short_guard.lerp(short_parry, attack).normalized(),
    ]

    for slot in range(2):
        var pose: Transform3D = skeleton.get_bone_global_pose(wrists[slot])
        # Imported Blender sword blade points along local +Y.
        var orientation_world: Basis = Basis(Quaternion(Vector3.UP, desired_dirs[slot]))
        var orientation_skeleton: Basis = (
            skeleton.global_transform.basis.inverse() * orientation_world
        ).orthonormalized()
        skeleton.set_bone_global_pose(wrists[slot],
            Transform3D(orientation_skeleton, pose.origin))
        sockets[slot].update_socket()
        var scale: Vector3 = weapons[slot].global_transform.basis.get_scale()
        max_scale_errors[slot] = maxf(max_scale_errors[slot],
            scale.distance_to(Vector3.ONE))
        var wrist_world: Vector3 = (
            skeleton.global_transform * skeleton.get_bone_global_pose(wrists[slot])
        ).origin
        max_grip_errors[slot] = maxf(max_grip_errors[slot],
            wrist_world.distance_to(weapons[slot].global_position))

    var new_head: Transform3D = skeleton.get_bone_global_pose(head_bone)
    head_z_min = minf(head_z_min, new_head.origin.z)
    head_z_max = maxf(head_z_max, new_head.origin.z)
    var head_angle: float = rad_to_deg(
        head_neutral_basis.get_rotation_quaternion().angle_to(
            new_head.basis.get_rotation_quaternion()))
    max_head_pitch_degrees = maxf(max_head_pitch_degrees, head_angle)


func _smooth(t: float) -> float:
    var u: float = clampf(t, 0, 1)
    return u * u * (3.0 - 2.0 * u)


func _find_skeleton(node: Node) -> Skeleton3D:
    if node is Skeleton3D:
        return node as Skeleton3D
    for child in node.get_children():
        var found: Skeleton3D = _find_skeleton(child)
        if found != null:
            return found
    return null


func _find_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node as AnimationPlayer
    for child in node.get_children():
        var found: AnimationPlayer = _find_player(child)
        if found != null:
            return found
    return null
