extends RefCounted
## Headless 1D combat rules for real AI-vs-AI match simulation.
## No final graphics, motion capture, camera or exact replay playback yet.

const MatchSessionScript = preload("res://scripts/core/match_session.gd")
const FighterStateScript = preload("res://scripts/core/fighter_state.gd")

const TICKS_PER_SECOND: int = 60
const MAX_TICKS: int = 75 * TICKS_PER_SECOND
const ARENA_HALF_WIDTH: float = 6.5
const MIN_SEPARATION: float = 0.65
const RULESET_VERSION: String = "combat_proto_v1"

const MOVES: Dictionary = {
    "musashi": {
        "quick_cut": {"startup": 10, "active": 5, "recovery": 20, "range": 2.65, "damage": 13, "stun": 16, "cooldown": 8},
        "heavy_cut": {"startup": 21, "active": 5, "recovery": 35, "range": 2.9, "damage": 25, "stun": 26, "cooldown": 15},
    },
    "bruce_lee": {
        "jab": {"startup": 6, "active": 3, "recovery": 11, "range": 1.5, "damage": 7, "stun": 10, "cooldown": 4},
        "side_kick": {"startup": 12, "active": 5, "recovery": 24, "range": 2.0, "damage": 15, "stun": 19, "cooldown": 9},
    },
}

var session
var fighters: Array = []
var frames: Array[Dictionary] = []
var rng: RandomNumberGenerator = RandomNumberGenerator.new()
var stale_ticks: int = 0
var winner: String = ""
var finished: bool = false


func begin(match_seed: int) -> void:
    session = MatchSessionScript.new()
    session.begin(match_seed)
    rng.seed = match_seed
    fighters = [
        FighterStateScript.new("musashi", "무사시", -3.0, 2.15),
        FighterStateScript.new("bruce_lee", "이소룡", 3.0, 3.45),
    ]
    frames.clear()
    stale_ticks = 0
    winner = ""
    finished = false
    session.record_event("roster", {"a": "musashi", "b": "bruce_lee"})
    _capture_frame()


func is_finished() -> bool:
    return finished


func advance_tick() -> void:
    if finished:
        return

    session.advance_tick()
    stale_ticks += 1

    for fighter in fighters:
        _progress_action(fighter)

    # Collect both active hits before changing either fighter's state.
    # This makes simultaneous trades possible and avoids slot-order priority.
    var pending_hits: Array[Dictionary] = []
    for index in range(fighters.size()):
        var attacker = fighters[index]
        var defender = fighters[1 - index]
        if attacker.action != "attack" or attacker.hit_applied:
            continue
        var move: Dictionary = MOVES[attacker.fighter_id][attacker.active_move]
        var startup: int = int(move["startup"])
        if attacker.move_frame >= startup and attacker.move_frame < startup + int(move["active"]):
            attacker.hit_applied = true
            if absf(attacker.x - defender.x) <= float(move["range"]):
                pending_hits.append({
                    "attacker": index,
                    "defender": 1 - index,
                    "move": attacker.active_move,
                    "damage": int(move["damage"]),
                    "stun": int(move["stun"]),
                })
            else:
                session.record_event("whiff", {"fighter": attacker.fighter_id, "move": attacker.active_move})

    for hit in pending_hits:
        var attacker = fighters[int(hit["attacker"])]
        var defender = fighters[int(hit["defender"])]
        defender.health = maxi(0, defender.health - int(hit["damage"]))
        defender.stun_left = maxi(defender.stun_left, int(hit["stun"]))
        defender.action = "stunned"
        defender.active_move = ""
        defender.move_frame = 0
        session.record_event("hit", {
            "attacker": attacker.fighter_id,
            "defender": defender.fighter_id,
            "move": hit["move"],
            "damage": hit["damage"],
            "remaining_hp": defender.health,
        })
        stale_ticks = 0

    var ko_a: bool = fighters[0].health <= 0
    var ko_b: bool = fighters[1].health <= 0
    if ko_a or ko_b:
        if ko_a and ko_b:
            _finish("draw", "double_ko")
        elif ko_a:
            _finish("bruce_lee", "ko")
        else:
            _finish("musashi", "ko")
    elif session.tick >= MAX_TICKS:
        var a_hp: int = fighters[0].health
        var b_hp: int = fighters[1].health
        if a_hp == b_hp:
            _finish("draw", "timeout")
        elif a_hp > b_hp:
            _finish("musashi", "timeout")
        else:
            _finish("bruce_lee", "timeout")
    else:
        _decide_for_fighter(0)
        _decide_for_fighter(1)

    _capture_frame()


func _progress_action(fighter) -> void:
    if fighter.cooldown > 0:
        fighter.cooldown -= 1

    if fighter.action == "stunned":
        fighter.stun_left -= 1
        if fighter.stun_left <= 0:
            fighter.stun_left = 0
            fighter.action = "idle"
        return

    if fighter.action != "attack":
        return

    fighter.move_frame += 1
    var move: Dictionary = MOVES[fighter.fighter_id][fighter.active_move]
    var total: int = int(move["startup"]) + int(move["active"]) + int(move["recovery"])
    if fighter.move_frame >= total:
        fighter.cooldown = int(move["cooldown"])
        fighter.action = "idle"
        fighter.active_move = ""
        fighter.move_frame = 0
        fighter.hit_applied = false


func _decide_for_fighter(index: int) -> void:
    var fighter = fighters[index]
    var opponent = fighters[1 - index]
    if fighter.action != "idle":
        return

    var distance: float = absf(fighter.x - opponent.x)
    var desired_distance: float = 2.15 if fighter.fighter_id == "musashi" else 1.35
    var pressure: float = 1.5 if stale_ticks >= 6 * TICKS_PER_SECOND else 1.0
    var step_size: float = fighter.speed * pressure / float(TICKS_PER_SECOND)

    if fighter.fighter_id == "musashi" and distance < 1.05 and rng.randf() < 0.6:
        _move_away(fighter, opponent, step_size)
        return

    if distance > desired_distance:
        if rng.randf() < 0.84:
            _move_toward(fighter, opponent, step_size)
        return

    if fighter.cooldown != 0:
        return

    var attack_probability: float = 0.12 if pressure == 1.0 else 0.22
    if rng.randf() > attack_probability:
        return

    var selected_move: String = _choose_move(fighter, distance)
    if selected_move.is_empty():
        return

    fighter.action = "attack"
    fighter.active_move = selected_move
    fighter.move_frame = 0
    fighter.hit_applied = false
    session.record_event("attack_started", {"fighter": fighter.fighter_id, "move": selected_move})


func _choose_move(fighter, distance: float) -> String:
    var choices: Array[String]
    if fighter.fighter_id == "musashi":
        choices = ["quick_cut", "heavy_cut"]
    else:
        choices = ["jab", "side_kick"]

    var weighted: Array[String] = []
    for move_name in choices:
        var move: Dictionary = MOVES[fighter.fighter_id][move_name]
        if distance > float(move["range"]):
            continue
        # Short techniques are preferred; longer ones still appear.
        weighted.append(move_name)
        if move_name == "quick_cut" or move_name == "jab":
            weighted.append(move_name)

    if weighted.is_empty():
        return ""
    return weighted[rng.randi_range(0, weighted.size() - 1)]


func _move_toward(fighter, opponent, amount: float) -> void:
    if fighter.x < opponent.x:
        fighter.x = minf(fighter.x + amount, opponent.x - MIN_SEPARATION)
    else:
        fighter.x = maxf(fighter.x - amount, opponent.x + MIN_SEPARATION)
    fighter.x = clampf(fighter.x, -ARENA_HALF_WIDTH, ARENA_HALF_WIDTH)


func _move_away(fighter, opponent, amount: float) -> void:
    if fighter.x < opponent.x:
        fighter.x -= amount
    else:
        fighter.x += amount
    fighter.x = clampf(fighter.x, -ARENA_HALF_WIDTH, ARENA_HALF_WIDTH)


func _finish(result_winner: String, reason: String) -> void:
    winner = result_winner
    finished = true
    session.record_event("result", {"winner": winner, "reason": reason})
    session.finish(reason)


func _capture_frame() -> void:
    frames.append({
        "tick": session.tick,
        "a": fighters[0].snapshot(),
        "b": fighters[1].snapshot(),
    })


func to_record() -> Dictionary:
    var record: Dictionary = session.to_record()
    record["ruleset_version"] = RULESET_VERSION
    record["godot_version"] = Engine.get_version_info()["string"]
    record["winner"] = winner
    record["fighters"] = ["musashi", "bruce_lee"]
    record["frames"] = frames.duplicate(true)
    return record
