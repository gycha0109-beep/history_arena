extends Node3D
## 5-second continuous walk QA using an authorized CC0 clothed humanoid.
## This tests real leg cycles + root travel, NOT a final Musashi model.

const MODEL_PATH: String = "res://samples/external/camper_walk_cc0.glb"
const FRAMES: int = 300
const HZ: float = 60.0
const WALK_SPEED: float = 1.35

static func root_x_at_frame(tick: int) -> float:
    return -3.35 + float(clampi(tick, 0, FRAMES)) * WALK_SPEED / HZ


@onready var actor_root: Node3D = $Actor
@onready var camera: Camera3D = $Camera3D
@onready var status_label: Label = $HUD/Status

var walk_player: AnimationPlayer
var skeleton: Skeleton3D
var duration: float = 1.0666666
var frame: int = 0
var ready_to_render: bool = false
var last_foot_positions: Array[Vector3] = [Vector3.ZERO, Vector3.ZERO]
var planted_samples: Array[int] = [0, 0]
var stance_slip: Array[float] = [0.0, 0.0]
var max_stance_step: Array[float] = [0.0, 0.0]
var last_grounded: Array[bool] = [false, false]
var report_printed: bool = false


func _ready() -> void:
    _build_marked_floor()
    if not ResourceLoader.exists(MODEL_PATH):
        status_label.text = "실제 보행 파일 미등록: %s" % MODEL_PATH
        push_error(status_label.text)
        return
    var scene: PackedScene = load(MODEL_PATH) as PackedScene
    if scene == null:
        push_error("GLB 불러오기 실패")
        return
    var actor = scene.instantiate()
    actor_root.add_child(actor)
    skeleton = _find_skeleton(actor)
    walk_player = _find_player(actor)
    if skeleton == null or walk_player == null or not walk_player.has_animation("Walk"):
        push_error("실제 보행 애니메이션과 골격이 없는 모델입니다.")
        return

    duration = walk_player.get_animation("Walk").length
    if duration < 0.2:
        push_error("실제 보행 애니메이션 길이가 비정상적입니다.")
        return
    walk_player.play("Walk")
    walk_player.pause()
    ready_to_render = true
    apply_frame(0)
    print("WALK_5S_READY clip_duration=%.6f speed=%.3f" % [duration, WALK_SPEED])


func _physics_process(_delta: float) -> void:
    if not ready_to_render:
        return
    if frame < FRAMES:
        apply_frame(frame + 1)
    if frame == FRAMES and not report_printed:
        report_printed = true
        print("WALK_5S_QA frames=%d duration=%.2fsec distance=%.3fm cycles=%.3f left_slip=%.3fm right_slip=%.3fm left_samples=%d right_samples=%d max_step=(%.4f,%.4f)" % [
            FRAMES, FRAMES / HZ, FRAMES * WALK_SPEED / HZ,
            (FRAMES / HZ) / duration, stance_slip[0], stance_slip[1],
            planted_samples[0], planted_samples[1], max_stance_step[0], max_stance_step[1]
        ])


func apply_frame(tick: int) -> void:
    if not ready_to_render:
        return
    frame = clampi(tick, 0, FRAMES)
    var seconds: float = float(frame) / HZ
    var phase_time: float = fmod(seconds, duration)
    walk_player.seek(phase_time, true)

    # Source model walks in its local +Z. Turn the entire rig toward world +X.
    actor_root.rotation.y = PI * 0.5
    actor_root.position = Vector3(root_x_at_frame(frame), 0.0, 0.0)

    # Dolly camera tracks world displacement; stationary ground markers show real motion.
    camera.position = Vector3(actor_root.position.x + 0.4, 1.43, 5.25)
    camera.look_at(Vector3(actor_root.position.x + 0.36, 0.95, 0.0), Vector3.UP)

    _measure_feet(tick)
    status_label.text = "레전더리 배틀 · 실제 5초 보행 검증\n%.2f초 / 5.00초  ·  이동 %.2fm\n임시 CC0 인체 · 무사시 최종 모델 아님" % [
        seconds, seconds * WALK_SPEED
    ]


func _measure_feet(tick: int) -> void:
    for index in range(2):
        var foot_id: String = "LeftFoot" if index == 0 else "RightFoot"
        var bone_index: int = skeleton.find_bone(foot_id)
        var local_pos: Vector3 = skeleton.get_bone_global_pose(bone_index).origin
        var world: Vector3 = skeleton.to_global(local_pos)
        # Ankle bones rest around 0.20m; lower ankle height indicates a planted sole.
        var grounded: bool = world.y <= 0.217
        if tick > 0 and grounded and last_grounded[index]:
            var horizontal_step: float = Vector2(
                world.x - last_foot_positions[index].x,
                world.z - last_foot_positions[index].z
            ).length()
            # Looped clip seam is excluded from the stance check.
            var seconds: float = float(tick) / HZ
            if fmod(seconds, duration) > 0.018:
                stance_slip[index] += horizontal_step
                planted_samples[index] += 1
                max_stance_step[index] = maxf(max_stance_step[index], horizontal_step)
        last_foot_positions[index] = world
        last_grounded[index] = grounded


func _build_marked_floor() -> void:
    var wood := StandardMaterial3D.new()
    wood.albedo_color = Color(0.2, 0.165, 0.135)
    wood.roughness = 0.86
    var lines := StandardMaterial3D.new()
    lines.albedo_color = Color(0.30, 0.275, 0.25)
    lines.roughness = 0.82
    var floor_mesh := BoxMesh.new()
    floor_mesh.size = Vector3(34.0, 0.14, 5.5)
    var floor_instance := MeshInstance3D.new()
    floor_instance.mesh = floor_mesh
    floor_instance.material_override = wood
    floor_instance.position = Vector3(0, -0.07, 0)
    $Stage.add_child(floor_instance)
    for i in range(-18, 19):
        var line := MeshInstance3D.new()
        var m := BoxMesh.new()
        m.size = Vector3(0.018, 0.004, 5.4)
        line.mesh = m
        line.material_override = lines
        line.position = Vector3(i * 0.5, 0.003, 0)
        $Stage.add_child(line)
    for i in range(-7, 8):
        var post := MeshInstance3D.new()
        var box_mesh := BoxMesh.new()
        box_mesh.size = Vector3(0.14, 2.65, 0.18)
        post.mesh = box_mesh
        post.material_override = lines
        post.position = Vector3(float(i) * 2.0, 1.325, -2.55)
        $Stage.add_child(post)


func _find_skeleton(node: Node) -> Skeleton3D:
    if node is Skeleton3D:
        return node as Skeleton3D
    for child in node.get_children():
        var skel: Skeleton3D = _find_skeleton(child)
        if skel != null:
            return skel
    return null


func _find_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node as AnimationPlayer
    for child in node.get_children():
        var player: AnimationPlayer = _find_player(child)
        if player != null:
            return player
    return null
