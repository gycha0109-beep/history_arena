extends RefCounted
## Deterministic tick counter and event envelope only.
## This is NOT yet a combat engine or an exact replay implementation.

enum Phase { IDLE, RUNNING, FINISHED }

const SIMULATION_HZ: int = 60
const RECORD_SCHEMA_VERSION: int = 1

var phase: Phase = Phase.IDLE
var tick: int = 0
var seed: int = 0
var events: Array[Dictionary] = []
var rng: RandomNumberGenerator = RandomNumberGenerator.new()


func begin(match_seed: int) -> void:
    seed = match_seed
    rng.seed = seed
    tick = 0
    events.clear()
    phase = Phase.RUNNING
    record_event("match_started", {"seed": seed})


func advance_tick() -> void:
    if phase != Phase.RUNNING:
        return
    tick += 1


func record_event(event_type: String, data: Dictionary = {}) -> void:
    events.append({
        "tick": tick,
        "type": event_type,
        "data": data.duplicate(true),
    })


func finish(reason: String) -> void:
    if phase != Phase.RUNNING:
        return
    record_event("match_finished", {"reason": reason})
    phase = Phase.FINISHED


func to_record() -> Dictionary:
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "simulation_hz": SIMULATION_HZ,
        "seed": seed,
        "last_tick": tick,
        "phase": Phase.keys()[phase],
        "events": events.duplicate(true),
    }
