extends RefCounted
## Replays authoritative snapshots without re-running AI or changing combat results.
## Snapshot actions/coordinates are exact at recorded 60Hz ticks; visual motion
## retiming and camera cuts remain separate production tasks.

const SCHEMA_VERSION: int = 1
const EXPECTED_HZ: int = 60

var record: Dictionary = {}
var current_tick: int = 0
var last_error: String = ""
var events_by_tick: Dictionary = {}


func load_record(data: Dictionary) -> bool:
    record.clear()
    events_by_tick.clear()
    current_tick = 0
    last_error = ""

    if int(data.get("schema_version", -1)) != SCHEMA_VERSION:
        return _reject("지원하지 않는 경기 기록 형식입니다.")
    if int(data.get("simulation_hz", -1)) != EXPECTED_HZ:
        return _reject("60Hz 경기 기록이 아닙니다.")
    if str(data.get("ruleset_version", "")) == "":
        return _reject("전투 규칙 버전이 빠졌습니다.")
    if typeof(data.get("frames")) != TYPE_ARRAY:
        return _reject("프레임 목록이 없습니다.")

    var frames: Array = data["frames"]
    if frames.is_empty():
        return _reject("빈 경기 기록입니다.")
    if frames.size() != int(data.get("last_tick", -1)) + 1:
        return _reject("프레임 수와 경기 종료 틱이 다릅니다.")

    for tick in range(frames.size()):
        if typeof(frames[tick]) != TYPE_DICTIONARY:
            return _reject("프레임 데이터가 손상됐습니다.")
        var frame: Dictionary = frames[tick]
        if int(frame.get("tick", -1)) != tick:
            return _reject("프레임 번호가 연속적이지 않습니다.")
        for slot in ["a", "b"]:
            if typeof(frame.get(slot)) != TYPE_DICTIONARY:
                return _reject("캐릭터 상태가 누락됐습니다.")
            var fighter: Dictionary = frame[slot]
            if not fighter.has("x") or not fighter.has("hp") or not fighter.has("action"):
                return _reject("캐릭터 필수 상태가 빠졌습니다.")

    if typeof(data.get("events")) != TYPE_ARRAY:
        return _reject("경기 이벤트 기록이 없습니다.")
    var previous_tick: int = -1
    for event in data["events"]:
        if typeof(event) != TYPE_DICTIONARY:
            return _reject("경기 이벤트가 손상됐습니다.")
        var event_tick: int = int(event.get("tick", -1))
        if event_tick < previous_tick or event_tick < 0 or event_tick >= frames.size():
            return _reject("경기 이벤트 시점이 잘못됐습니다.")
        previous_tick = event_tick
        if not events_by_tick.has(event_tick):
            events_by_tick[event_tick] = []
        events_by_tick[event_tick].append(event.duplicate(true))

    if str(data.get("winner", "")) not in ["musashi", "bruce_lee", "draw"]:
        return _reject("경기 결과가 없거나 잘못됐습니다.")

    record = data.duplicate(true)
    return true


func load_file(path: String) -> bool:
    if not FileAccess.file_exists(path):
        return _reject("경기 기록 파일이 없습니다: %s" % path)
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    if typeof(data) != TYPE_DICTIONARY:
        return _reject("경기 기록 JSON이 손상됐습니다.")
    return load_record(data)


func seek(tick: int) -> Dictionary:
    if record.is_empty():
        return {}
    current_tick = clampi(tick, 0, get_last_tick())
    return get_frame(current_tick)


func get_frame(tick: int) -> Dictionary:
    if record.is_empty():
        return {}
    var index: int = clampi(tick, 0, get_last_tick())
    return record["frames"][index].duplicate(true)


func get_events_at(tick: int) -> Array:
    if not events_by_tick.has(tick):
        return []
    return events_by_tick[tick].duplicate(true)


func get_last_tick() -> int:
    if record.is_empty():
        return 0
    return int(record["last_tick"])


func get_winner() -> String:
    if record.is_empty():
        return ""
    return str(record["winner"])


func _reject(message: String) -> bool:
    last_error = message
    return false
