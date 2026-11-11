extends RefCounted
## Logical fighter state. Visual character assets are deliberately separate.

var fighter_id: String
var display_name: String
var x: float
var speed: float
var health: int = 100
var action: String = "idle"
var active_move: String = ""
var move_frame: int = 0
var hit_applied: bool = false
var stun_left: int = 0
var cooldown: int = 0


func _init(p_id: String, p_name: String, p_x: float, p_speed: float) -> void:
    fighter_id = p_id
    display_name = p_name
    x = p_x
    speed = p_speed


func snapshot() -> Dictionary:
    return {
        "id": fighter_id,
        "x": snappedf(x, 0.0001),
        "hp": health,
        "action": action,
        "move": active_move,
        "move_frame": move_frame,
        "stun": stun_left,
    }
