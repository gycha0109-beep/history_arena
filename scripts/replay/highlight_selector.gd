extends RefCounted
## Editorial ranking only. Scores NEVER influence fighting AI, hit detection or winner.

const SELECTION_VERSION: String = "highlights_v1"


func summarize(record: Dictionary) -> Dictionary:
    var events: Array = record.get("events", [])
    var frames: Array = record.get("frames", [])
    var hit_count: int = 0
    var attack_count: int = 0
    var distinct_moves: Dictionary = {}
    var hit_by_fighter: Dictionary = {"musashi": 0, "bruce_lee": 0}
    for event in events:
        if event.get("type", "") == "attack_started":
            attack_count += 1
            var started_data: Dictionary = event.get("data", {})
            distinct_moves[str(started_data.get("move", ""))] = true
        elif event.get("type", "") == "hit":
            hit_count += 1
            var hit_data: Dictionary = event.get("data", {})
            var fighter_id: String = str(hit_data.get("attacker", ""))
            if hit_by_fighter.has(fighter_id):
                hit_by_fighter[fighter_id] += 1

    var lead_changes: int = 0
    var last_leader: int = 0
    for frame in frames:
        var a: Dictionary = frame.get("a", {})
        var b: Dictionary = frame.get("b", {})
        var hp_diff: int = int(a.get("hp", 100)) - int(b.get("hp", 100))
        var leader: int = signi(hp_diff)
        if leader != 0:
            if last_leader != 0 and last_leader != leader:
                lead_changes += 1
            last_leader = leader

    var end_a: int = 100
    var end_b: int = 100
    if not frames.is_empty():
        var last_frame: Dictionary = frames.back()
        end_a = int(last_frame["a"]["hp"])
        end_b = int(last_frame["b"]["hp"])
    var health_gap: int = absi(end_a - end_b)
    var total_damage: int = 200 - end_a - end_b
    var close_finish: bool = health_gap <= 20 and hit_count > 0
    var mutual_hits: bool = int(hit_by_fighter["musashi"]) > 0 and int(hit_by_fighter["bruce_lee"]) > 0
    var winner: String = str(record.get("winner", ""))
    var duration: float = float(record.get("last_tick", 0)) / 60.0

    var score: int = hit_count * 7 + distinct_moves.size() * 6 + lead_changes * 30
    score += mini(60, total_damage) / 2
    score += 20 if close_finish else 0
    score += 18 if mutual_hits else 0
    score += 10 if winner != "draw" else 0
    score -= 15 if duration >= 70.0 else 0

    return {
        "seed": int(record.get("seed", 0)),
        "winner": winner,
        "duration_seconds": snappedf(duration, 0.01),
        "hit_count": hit_count,
        "attack_count": attack_count,
        "different_moves": distinct_moves.size(),
        "lead_changes": lead_changes,
        "mutual_hits": mutual_hits,
        "close_finish": close_finish,
        "end_hp": {"musashi": end_a, "bruce_lee": end_b},
        "score": score,
        "selection_version": SELECTION_VERSION,
    }


func rank(summaries: Array) -> Array:
    var ranked: Array = summaries.duplicate(true)
    ranked.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        if int(a["score"]) == int(b["score"]):
            return int(a["seed"]) < int(b["seed"])
        return int(a["score"]) > int(b["score"])
    )
    return ranked
