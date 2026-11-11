extends Node3D

const MatchSessionScript = preload("res://scripts/core/match_session.gd")

@onready var status_label: Label = $HUD/Status

var session


func _ready() -> void:
    session = MatchSessionScript.new()
    session.begin(20261112)
    _update_status()


func _physics_process(_delta: float) -> void:
    session.advance_tick()
    if session.tick % 30 == 0:
        _update_status()


func _update_status() -> void:
    status_label.text = "레전더리 배틀 | 개발 기반 화면\n시뮬레이션 틱: %d\n캐릭터·전투 에셋 미연결" % session.tick
