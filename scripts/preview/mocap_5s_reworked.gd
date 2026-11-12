extends Node3D
## Independent visual comparison only. Uses a captured mocap walking clip.
## No scripted foot IK, fake foot track, or forced joint rotations.
const SOURCE_FILE: String = "res://samples/external/soldier_walk_composite.glb"
const WALK_CLIP: String = "mocap_walk_composite"
const FPS: float = 60.0
const FRAME_LIMIT: int = 300
const MOTION_SPEED: float = 1.1733

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


func _ready() -> void:
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
    qa_ready = true
    apply_frame(0)
    first_position = actor_root.global_position
    print("MOCAP_READY clip=", WALK_CLIP," length=",clip_seconds," floor=",floor_offset)


func _physics_process(_delta: float) -> void:
    if qa_ready and frame < FRAME_LIMIT:
        apply_frame(frame+1)
        if frame == FRAME_LIMIT:
            print("MOCAP_WALK_DONE frames=300 distance=", MOTION_SPEED*5.0)


func apply_frame(tick: int) -> void:
    frame = clampi(tick,0,FRAME_LIMIT)
    var seconds: float = float(frame)/FPS
    player.seek(fmod(seconds,clip_seconds),true)
    actor_root.position = Vector3(-2.95 + seconds*MOTION_SPEED, -floor_offset,0)
    camera.position = Vector3(actor_root.position.x+0.45,1.50,5.6)
    camera.look_at(Vector3(actor_root.position.x+0.36,0.95,0),Vector3.UP)
    status_label.text = "5초 실제 걷기·상체·왼발 보정 비교\n%.2f초 / 5.00초 · 이동 %.2fm\n임시 군인 모델 · 무사시 최종 캐릭터 아님" % [
        seconds,seconds*MOTION_SPEED
    ]


func _feet_min_global_y() -> float:
    # Calibrate using BOTH toes over one complete authored walking cycle.
    # The old first-frame ankle-minus-11cm estimate buried the shoe toes
    # ~2–3cm inside the floor, producing the apparent left-foot snag.
    var heights: Array[float] = []
    for sample in range(121):
        player.seek(minf(float(sample) / 120.0 * clip_seconds, clip_seconds - 0.00001), true)
        for id in ["mixamorig_LeftToeBase", "mixamorig_RightToeBase"]:
            var index: int = skeleton.find_bone(id)
            if index >= 0:
                heights.append(skeleton.to_global(
                    skeleton.get_bone_global_pose(index).origin).y)
    player.seek(0.0, true)
    if heights.is_empty():
        return 0.0
    heights.sort()
    var ground_reference: float = heights[int(heights.size() * 0.08)]
    print("GROUND_REFERENCE_TOE_Y=", ground_reference)
    return ground_reference - 0.008


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
