extends SceneTree

const MatchSessionScript = preload("res://scripts/core/match_session.gd")


func _initialize() -> void:
    var match_session = MatchSessionScript.new()
    match_session.begin(42)

    for index in range(120):
        match_session.advance_tick()

    if match_session.tick != 120:
        _fail("시뮬레이션 틱 120회가 유지되지 않았습니다.")
        return

    match_session.record_event("test_event", {"source": "smoke"})
    match_session.finish("test_complete")
    match_session.advance_tick()

    var record: Dictionary = match_session.to_record()
    if record["last_tick"] != 120:
        _fail("종료된 경기는 더 이상 진행되면 안 됩니다.")
        return
    if record["simulation_hz"] != 60 or record["schema_version"] != 1:
        _fail("기본 기록 형식이 다릅니다.")
        return
    if record["events"].size() != 3:
        _fail("경기 시작·시험·종료 이벤트가 누락됐습니다.")
        return

    print("PASS: Godot bootstrap and match-session smoke test")
    quit(0)


func _fail(message: String) -> void:
    push_error(message)
    quit(1)
