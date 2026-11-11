extends Node3D

const CombatScript = preload("res://scripts/core/combat_simulator.gd")
const CharacterVisualScript = preload("res://scripts/visuals/character_visual.gd")

@onready var status_label: Label = $HUD/Status

var combat
var next_seed: int = 20261112
var visuals: Array = []
var asset_status: Array[String] = []


func _ready() -> void:
    _setup_visuals()
    _start_new_match()


func _setup_visuals() -> void:
    var actor_root: Node3D = Node3D.new()
    actor_root.name = "Characters"
    add_child(actor_root)
    for fighter_id in ["musashi", "bruce_lee"]:
        var visual = CharacterVisualScript.new()
        visual.name = str(fighter_id)
        actor_root.add_child(visual)
        visual.load_manifest("res://assets/characters/%s/character.json" % fighter_id)
        visuals.append(visual)
        asset_status.append(visual.status_message)


func _start_new_match() -> void:
    combat = CombatScript.new()
    combat.begin(next_seed)
    next_seed += 1
    for visual in visuals:
        visual.has_previous_position = false
        visual.animation_state = ""
    _sync_visuals()
    _update_status()


func _physics_process(_delta: float) -> void:
    if combat == null or combat.is_finished():
        return
    combat.advance_tick()
    _sync_visuals()
    if combat.session.tick % 6 == 0 or combat.is_finished():
        _update_status()


func _sync_visuals() -> void:
    for index in range(visuals.size()):
        var fighter = combat.fighters[index]
        var opponent = combat.fighters[1 - index]
        visuals[index].sync_from_fighter(fighter.snapshot(), opponent.x)


func _unhandled_key_input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_R:
            _start_new_match()


func _update_status() -> void:
    var a = combat.fighters[0]
    var b = combat.fighters[1]
    var match_status: String = "진행 중"
    if combat.is_finished():
        match_status = "종료 | 승자: %s" % combat.winner

    status_label.text = "레전더리 배틀 | 3D 에셋 연동 시험\n" \
        + "무사시 HP: %d  위치: %.2f  동작: %s\n" % [a.health, a.x, a.action] \
        + "이소룡 HP: %d  위치: %.2f  동작: %s\n" % [b.health, b.x, b.action] \
        + "경기 시간: %.1f초 | %s\n" % [float(combat.session.tick) / 60.0, match_status] \
        + "R키: 새 시드로 재대결\n" \
        + "에셋 상태: %s" % " / ".join(asset_status)
