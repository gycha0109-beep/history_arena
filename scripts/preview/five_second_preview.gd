extends Node3D

const TimelineScript = preload("res://scripts/preview/five_second_timeline.gd")
const CharacterVisualScript = preload("res://scripts/visuals/character_visual.gd")

@onready var actors: Node3D = $Actors
@onready var status: Label = $HUD/Status

var timeline = TimelineScript.new()
var frame: int = 0
var visuals: Array = []
var asset_messages: Array[String] = []


func _ready() -> void:
    for fighter_id in ["musashi", "bruce_lee"]:
        var visual = CharacterVisualScript.new()
        visual.name = fighter_id
        actors.add_child(visual)
        var manifest_path: String = "res://assets/characters/%s/character.json" % fighter_id
        visual.load_manifest(manifest_path)
        visuals.append(visual)
        asset_messages.append(visual.status_message)
    set_preview_frame(0)


func _physics_process(_delta: float) -> void:
    if frame < TimelineScript.DURATION_FRAMES:
        set_preview_frame(frame + 1)


func set_preview_frame(new_frame: int) -> void:
    frame = clampi(new_frame, 0, TimelineScript.DURATION_FRAMES)
    var pose: Dictionary = timeline.sample(frame)
    if visuals.size() == 2:
        visuals[0].sync_from_fighter(pose["a"], float(pose["b"]["x"]))
        visuals[1].sync_from_fighter(pose["b"], float(pose["a"]["x"]))

    var readiness: String = " / ".join(asset_messages)
    var has_missing: bool = false
    for visual in visuals:
        if not visual.ready_for_preview:
            has_missing = true
            break

    if has_missing:
        status.text = "그래픽 에셋 미등록 · 5초 동작 검증 대기\n%s\n%d / %d프레임 · %s" % [
            readiness, frame, TimelineScript.DURATION_FRAMES, pose["phase"]]
    else:
        status.text = "5초 애니메이션 동기화 시험 · %d / %d프레임\n%s\n화질 검증은 실제 녹화 영상으로 판단" % [
            frame, TimelineScript.DURATION_FRAMES, pose["phase"]]
