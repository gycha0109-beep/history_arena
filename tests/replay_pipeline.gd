extends SceneTree

const CombatScript = preload("res://scripts/core/combat_simulator.gd")
const ReplayReaderScript = preload("res://scripts/replay/replay_reader.gd")
const SelectorScript = preload("res://scripts/replay/highlight_selector.gd")
const BatchScript = preload("res://scripts/replay/match_batch.gd")
const ReplayScene = preload("res://scenes/replay_viewer.tscn")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var batch = BatchScript.new()
    var dir: String = "user://tests/legendary_battle_replay_v1"
    var index: Dictionary = batch.generate(4, 5010, dir)
    if index.is_empty():
        _fail("경기 묶음 생성 실패: %s" % batch.last_error)
        return

    if int(index["count"]) != 4 or index["ranking"].size() != 4:
        _fail("생성한 경기 수와 순위 목록이 다릅니다.")
        return

    var first_score: int = 99999999
    for entry in index["ranking"]:
        var score: int = int(entry["score"])
        if score > first_score:
            _fail("추천 경기 점수 순서가 잘못됐습니다.")
            return
        first_score = score

    if int(index["selected_seed"]) != int(index["ranking"][0]["seed"]):
        _fail("추천 경기의 시드가 1위 기록과 다릅니다.")
        return

    var index_path: String = dir.path_join("index.json")
    var index_again: Variant = JSON.parse_string(FileAccess.get_file_as_string(index_path))
    if typeof(index_again) != TYPE_DICTIONARY:
        _fail("추천 경기 목록을 파일에서 읽지 못했습니다.")
        return
    if index_again["selected_file"] != index["selected_file"]:
        _fail("저장된 추천 경기와 메모리 결과가 다릅니다.")
        return

    for entry in index["ranking"]:
        var path: String = dir.path_join(str(entry["file"]))
        var reader = ReplayReaderScript.new()
        if not reader.load_file(path):
            _fail("경기 JSON을 다시 읽을 수 없습니다: %s" % reader.last_error)
            return
        var original_first: Dictionary = reader.get_frame(0)
        var original_last: Dictionary = reader.seek(reader.get_last_tick())
        if int(original_first["tick"]) != 0 or int(original_last["tick"]) != reader.get_last_tick():
            _fail("첫/마지막 프레임 위치가 올바르지 않습니다.")
            return
        if reader.get_winner() != entry["winner"]:
            _fail("기록의 승패와 경기 선택 목록의 승패가 다릅니다.")
            return

        var snapshot: Dictionary = reader.get_frame(0)
        snapshot["a"]["hp"] = 0
        if int(reader.get_frame(0)["a"]["hp"]) == 0:
            _fail("읽기용 프레임이 원본 기록을 바꿨습니다.")
            return

        var seed: int = int(entry["seed"])
        var simulation = CombatScript.new()
        simulation.begin(seed)
        while not simulation.is_finished():
            simulation.advance_tick()
        var expected: Dictionary = simulation.to_record()
        if JSON.stringify(expected) != JSON.stringify(reader.record):
            _fail("같은 시드의 경기와 저장된 재생 기록이 다릅니다: %d" % seed)
            return

        var summary: Dictionary = SelectorScript.new().summarize(reader.record)
        if int(summary["score"]) != int(entry["score"]):
            _fail("선별 점수가 저장된 순위와 일치하지 않습니다.")
            return

    var selected_reader = ReplayReaderScript.new()
    if not selected_reader.load_file(dir.path_join(str(index["selected_file"]))):
        _fail("추천 경기 기록을 열지 못했습니다.")
        return
    var bad: Dictionary = selected_reader.record.duplicate(true)
    bad["last_tick"] = -1
    if selected_reader.load_record(bad):
        _fail("손상된 경기 기록을 허용했습니다.")
        return

    var replay_scene = ReplayScene.instantiate()
    root.add_child(replay_scene)
    if not replay_scene.load_replay(dir.path_join(str(index["selected_file"]))):
        _fail("실제 재생 화면에 저장된 경기를 불러오지 못했습니다.")
        return
    if replay_scene.visuals.size() != 2:
        _fail("저장된 경기 화면의 두 캐릭터 연결 실패.")
        return

    print("PASS: 4 real AI matches, editorial ranking, JSON round-trip and frame replay viewer")
    quit(0)


func _fail(message: String) -> void:
    push_error(message)
    quit(1)
