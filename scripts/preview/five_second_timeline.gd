extends RefCounted
## Exactly 300 authored simulation frames (5 seconds at 60Hz).
## This is an animation-quality shot, never represented as an AI-generated outcome.

const FPS: int = 60
const DURATION_FRAMES: int = 300


func sample(frame: int) -> Dictionary:
    var f: int = clampi(frame, 0, DURATION_FRAMES)
    var musashi_x: float = -2.4
    var bruce_x: float = 2.4
    var musashi_action: String = "idle"
    var bruce_action: String = "idle"
    var musashi_move: String = ""
    var phase: String = "대치"

    if f >= 40 and f < 105:
        var movement: float = float(f - 40) / 65.0
        musashi_x = lerpf(-2.4, -0.8, movement)
        bruce_x = lerpf(2.4, 1.6, movement)
        musashi_action = "walk"
        bruce_action = "walk"
        phase = "접근"
    elif f >= 105:
        musashi_x = -0.8
        bruce_x = 1.6

    if f >= 105 and f < 156:
        musashi_action = "attack"
        musashi_move = "quick_cut"
        phase = "검격"

    if f >= 130 and f < 170:
        bruce_action = "stunned"
        phase = "피격 반응"
    elif f >= 170 and f < 230:
        phase = "자세 회복"
    elif f >= 230:
        phase = "대치 복귀"

    return {
        "frame": f,
        "phase": phase,
        "a": {
            "id": "musashi",
            "x": musashi_x,
            "hp": 100,
            "action": musashi_action,
            "move": musashi_move,
        },
        "b": {
            "id": "bruce_lee",
            "x": bruce_x,
            "hp": 87 if f >= 130 else 100,
            "action": bruce_action,
            "move": "",
        },
    }
