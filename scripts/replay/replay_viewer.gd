extends Node3D
## Read a real AI match from recorded 60Hz snapshots.
## All character positions, HP and actions come from the record, not a re-simulation.

const ReplayReaderScript = preload("res://scripts/replay/replay_reader.gd")
const CharacterVisualScript = preload("res://scripts/visuals/character_visual.gd")

@onready var actors: Node3D = $Actors
@onready var status_label: Label = $HUD/Status

var reader = ReplayReaderScript.new()
var visuals: Array = []
var missing_assets: Array[String] = []
var paused: bool = false
var replay_loaded: bool = false
var current_file: String = ""


func _ready() -> void:
    for fighter_id in ["musashi", "bruce_lee"]:
        var visual = CharacterVisualScript.new()
        visual.name = fighter_id
        actors.add_child(visual)
        visual.load_manifest("res://assets/characters/%s/character.json" % fighter_id)
        missing_assets.append(visual.status_message)
        visuals.append(visual)

    var desired_file: String = _find_replay_arg()
    if desired_file.is_empty():
        status_label.text = "기록된 경기 파일이 없습니다.\n먼저 run-dev.cmd -Mode batch를 실행하세요."
        return
    load_replay(desired_file)


func _find_replay_arg() -> String:
    var args: PackedStringArray = OS.get_cmdline_user_args()
    for index in range(args.size() - 1):
        if args[index] == "--replay":
            return args[index + 1]
    return ""


func load_replay(path: String) -> bool:
    replay_loaded = false
    current_file = path
    if not reader.load_file(path):
        status_label.text = "경기 기록을 열지 못했습니다: %s" % reader.last_error
        return false
    replay_loaded = true
    paused = false
    _display_tick(0)
    return true


func _physics_process(_delta: float) -> void:
    if replay_loaded and not paused and reader.current_tick < reader.get_last_tick():
        _display_tick(reader.current_tick + 1)


func _display_tick(tick: int) -> void:
    var frame: Dictionary = reader.seek(tick)
    if frame.is_empty():
        return

    var a: Dictionary = frame["a"]
    var b: Dictionary = frame["b"]
    if visuals.size() == 2:
        visuals[0].sync_from_fighter(a, float(b["x"]))
        visuals[1].sync_from_fighter(b, float(a["x"]))

    var events: Array = reader.get_events_at(reader.current_tick)
    var event_label: String = ""
    for event in events:
        if str(event.get("type", "")) == "hit":
            var hit_data: Dictionary = event.get("data", {})
            event_label = "%s 타격 → %s (피해 %d)" % [
                hit_data.get("attacker", ""), hit_data.get("defender", ""),
                int(hit_data.get("damage", 0))
            ]
        elif str(event.get("type", "")) == "result":
            event_label = "경기 종료: %s" % reader.get_winner()

    status_label.text = "기록된 AI 대전 · %s\n" % current_file.get_file()
    status_label.text += "진행: %.2f / %.2f초  |  %s\n" % [
        reader.current_tick / 60.0, reader.get_last_tick() / 60.0,
        "일시 정지" if paused else "재생 중"
    ]
    status_label.text += "무사시 HP %d / 이소룡 HP %d  |  승자: %s\n" % [
        int(a["hp"]), int(b["hp"]), reader.get_winner()
    ]
    if not event_label.is_empty():
        status_label.text += event_label + "\n"
    status_label.text += "스페이스: 일시정지  |  좌우 화살표: 1초 이동  |  Home: 처음\n"
    if not missing_assets.is_empty():
        status_label.text += "모델·모션 상태: %s" % " / ".join(missing_assets)


func _unhandled_key_input(event: InputEvent) -> void:
    if not replay_loaded or not event is InputEventKey:
        return
    if not event.pressed or event.echo:
        return
    match event.keycode:
        KEY_SPACE:
            paused = not paused
            _display_tick(reader.current_tick)
        KEY_LEFT:
            paused = true
            _display_tick(reader.current_tick - 60)
        KEY_RIGHT:
            paused = true
            _display_tick(reader.current_tick + 60)
        KEY_HOME:
            paused = true
            _display_tick(0)
