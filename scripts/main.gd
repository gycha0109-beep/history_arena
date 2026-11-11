extends Node3D

const CombatScript = preload("res://scripts/core/combat_simulator.gd")

@onready var status_label: Label = $HUD/Status

var combat
var next_seed: int = 20261112


func _ready() -> void:
    _start_new_match()


func _start_new_match() -> void:
    combat = CombatScript.new()
    combat.begin(next_seed)
    next_seed += 1
    _update_status()


func _physics_process(_delta: float) -> void:
    if combat == null or combat.is_finished():
        return
    combat.advance_tick()
    if combat.session.tick % 6 == 0 or combat.is_finished():
        _update_status()


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

    status_label.text = "레전더리 배틀 | 자동 대전 계산 실험\n" \
        + "무사시 HP: %d  위치: %.2f  동작: %s\n" % [a.health, a.x, a.action] \
        + "이소룡 HP: %d  위치: %.2f  동작: %s\n" % [b.health, b.x, b.action] \
        + "경기 시간: %.1f초 | %s\n" % [float(combat.session.tick) / 60.0, match_status] \
        + "R키: 새 시드로 재대결\n" \
        + "주의: 실제 캐릭터 모델·모션·영상 연출은 아직 미연결"
