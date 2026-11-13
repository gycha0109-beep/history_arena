extends Node3D
## Whole-body CC0 reference only: authored arms/torso/legs in a single Walk clip.
## No foot IK, layered arm animations or scripted joint rotations.
const SOURCE_FILE: String = "res://samples/external/kinemiq_two_sword_guard_walk.glb"
const WeaponSocketScript = preload("res://scripts/visuals/weapon_socket.gd")
const LONG_SWORD = "res://samples/external/qa_katana_rigid.glb"
const SHORT_SWORD = "res://samples/external/qa_wakizashi_rigid.glb"
const WALK_CLIP: String = "Walk_DualGuard"
const FPS: float = 60.0
const FRAME_LIMIT: int = 300
const MOTION_SPEED: float = 1.043

@onready var actor_root: Node3D = $Actor
@onready var camera: Camera3D = $Camera3D
@onready var status_label: Label = $HUD/Status
var player: AnimationPlayer
var skeleton: Skeleton3D
var clip_seconds: float = 1.0
var frame: int = 0
var qa_ready: bool = false
var floor_offset: float = 0.0
var first_position: Vector3 = Vector3.ZERO
var sockets: Array[Node3D] = []
var weapons: Array[Node3D] = []
var maximum_scale_error: float = 0.0
var maximum_grip_gap: float = 0.0


func _ready() -> void:
    # Load a system font at runtime without copying/distributing font files.
    var system_hangul: String = "C:/Windows/Fonts/malgun.ttf"
    if FileAccess.file_exists(system_hangul):
        var face := FontFile.new()
        face.data = FileAccess.get_file_as_bytes(system_hangul)
        status_label.add_theme_font_override("font",face)
    _build_marked_floor()
    if not ResourceLoader.exists(SOURCE_FILE):
        push_error("모션캡처 원본 GLB가 없습니다.")
        return
    var model = (load(SOURCE_FILE) as PackedScene).instantiate()
    actor_root.add_child(model)
    player = _find_player(model)
    skeleton = _find_skeleton(model)
    if player == null or skeleton == null or not player.has_animation(WALK_CLIP):
        push_error("모션캡처 Walk 동작 또는 인체 골격이 없습니다.")
        return
    clip_seconds = player.get_animation(WALK_CLIP).length
    player.play(WALK_CLIP)
    player.pause()
    player.seek(0.0, true)
    actor_root.rotation.y = PI * 0.5

    # Correct actor's global vertical offset using the skinned body's AABB,
    # not the ankle bone height as the sole height is model-dependent.
    floor_offset = _feet_min_global_y()
    if absf(floor_offset) > 0.4:
        print("Unexpected floor offset: ",floor_offset)
    if not _attach_dual_swords():
        push_error("??/??? ?? ?? ?? ??? ???? ?????.")
        return
    qa_ready = true
    apply_frame(0)
    first_position = actor_root.global_position
    print("FULLBODY_READY clip=", WALK_CLIP," length=",clip_seconds," floor=",floor_offset)


func _physics_process(_delta: float) -> void:
    if qa_ready and frame < FRAME_LIMIT:
        apply_frame(frame+1)
        if frame == FRAME_LIMIT:
            print("DUAL_WALK_DONE frames=300 distance=",MOTION_SPEED*5.0," weapons=",weapons.size()," max_scale_error=",maximum_scale_error)


func apply_frame(tick: int) -> void:
    frame = clampi(tick,0,FRAME_LIMIT)
    var seconds: float = float(frame)/FPS
    player.seek(fmod(seconds,clip_seconds),true)
    actor_root.position = Vector3(-2.95 + seconds*MOTION_SPEED, -floor_offset,0)
    # Update bones and both sword sockets in the SAME frame.
    skeleton.force_update_all_bone_transforms()
    for index in range(sockets.size()):
        sockets[index].update_socket()
        maximum_scale_error = maxf(maximum_scale_error,
            weapons[index].global_transform.basis.get_scale().distance_to(Vector3.ONE))
    camera.position = Vector3(actor_root.position.x+0.28,1.50,4.5)
    camera.look_at(Vector3(actor_root.position.x+0.32,1.10,0),Vector3.UP)
    status_label.text = "이도류 보행 · 오른손 장검 / 왼손 단검\n%.2f초 / 5.00초 · 이동 %.2fm\n검증용 인체 · 최종 무사시 모델 아님" % [
        seconds,seconds*MOTION_SPEED
    ]


func _attach_dual_swords() -> bool:
    if not ResourceLoader.exists(LONG_SWORD) or not ResourceLoader.exists(SHORT_SWORD):
        return false
    for side in range(2):
        var bone_name: String = "hand_r" if side == 0 else "hand_l"
        var socket = WeaponSocketScript.new()
        socket.name = "KatanaRight" if side == 0 else "WakizashiLeft"
        $Stage.add_child(socket)
        if not socket.bind_to_skeleton(skeleton,[bone_name]):
            return false
        var pack = load(LONG_SWORD if side == 0 else SHORT_SWORD) as PackedScene
        var model: Node3D = pack.instantiate() as Node3D
        socket.add_child(model)
        var idx: int = skeleton.find_bone(bone_name)
        var knuckle: int = skeleton.find_bone("middle_01_r" if side == 0 else "middle_01_l")
        var hand_pose: Transform3D = skeleton.get_bone_global_pose(idx)
        var knuckle_pose: Transform3D = skeleton.get_bone_global_pose(knuckle)
        # The grip is BETWEEN wrist and real middle-finger knuckle. Not an
        # extra hand mesh, and not the raw wrist origin.
        var palm_center: Vector3 = hand_pose.origin.lerp(knuckle_pose.origin,0.62)
        model.position = hand_pose.basis.orthonormalized().inverse() * (palm_center-hand_pose.origin)
        var outward: Vector3 = Vector3(0.62,0.78,0) if side==0 else Vector3(0.94,0.34,-0.02)
        var aim: Basis = Basis(Quaternion(Vector3.UP,outward.normalized()))
        model.basis = (socket.global_transform.basis.inverse() * aim).orthonormalized()
        model.scale = Vector3.ONE
        socket.update_socket()
        sockets.append(socket)
        weapons.append(model)
    return true


func _feet_min_global_y() -> float:
    var heights: Array[float] = []
    for tick in range(121):
        player.seek(float(tick) / 120.0 * clip_seconds, true)
        for id in ["ball_l", "ball_r"]:
            var bone_index: int = skeleton.find_bone(id)
            if bone_index >= 0:
                heights.append(skeleton.to_global(skeleton.get_bone_global_pose(bone_index).origin).y)
    player.seek(0.0,true)
    if heights.is_empty():
        return 0.0
    heights.sort()
    print("KINEMIQ_GROUND_BALL_Y=",heights[12])
    return heights[12] - 0.11


func _build_marked_floor() -> void:
    var wood := StandardMaterial3D.new()
    wood.albedo_color = Color(0.20,0.165,0.135)
    wood.roughness = 0.86
    var marks := StandardMaterial3D.new()
    marks.albedo_color = Color(0.36,0.34,0.32)
    var floor_mesh := BoxMesh.new()
    floor_mesh.size=Vector3(34,0.14,5.5)
    var floor_inst := MeshInstance3D.new()
    floor_inst.mesh=floor_mesh
    floor_inst.material_override=wood
    floor_inst.position=Vector3(0,-0.07,0)
    $Stage.add_child(floor_inst)
    for i in range(-18,19):
        var m := BoxMesh.new()
        m.size=Vector3(0.018,0.004,5.4)
        var line:=MeshInstance3D.new()
        line.mesh=m
        line.material_override=marks
        line.position=Vector3(float(i)*0.5,0.003,0)
        $Stage.add_child(line)


func _find_player(n: Node) -> AnimationPlayer:
    if n is AnimationPlayer: return n
    for c in n.get_children():
        var got=_find_player(c)
        if got != null: return got
    return null


func _find_skeleton(n: Node) -> Skeleton3D:
    if n is Skeleton3D: return n
    for c in n.get_children():
        var got=_find_skeleton(c)
        if got != null: return got
    return null
