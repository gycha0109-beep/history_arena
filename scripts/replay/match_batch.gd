extends RefCounted
## Produce real simulation records and an editorial ranking, no mocked winner.
## Each match record is independently replayable at its original 60Hz ticks.

const CombatScript = preload("res://scripts/core/combat_simulator.gd")
const ReplayReaderScript = preload("res://scripts/replay/replay_reader.gd")
const HighlightSelectorScript = preload("res://scripts/replay/highlight_selector.gd")

const MAX_BATCH_SIZE: int = 40

var last_error: String = ""


func generate(count: int, first_seed: int, output_dir: String) -> Dictionary:
    last_error = ""
    if count < 1 or count > MAX_BATCH_SIZE:
        return _reject("한 번에 생성할 경기는 1~40개입니다.")
    if first_seed < 0:
        return _reject("난수 시드는 0 이상이어야 합니다.")
    if not output_dir.begins_with("user://") and not output_dir.begins_with("res://"):
        return _reject("저장 위치는 user:// 또는 res://로 지정해야 합니다.")

    var folder: String = ProjectSettings.globalize_path(output_dir.trim_suffix("/"))
    var dir_error: Error = DirAccess.make_dir_recursive_absolute(folder)
    if dir_error != OK:
        return _reject("경기 기록을 저장할 폴더를 만들 수 없습니다.")

    var selector = HighlightSelectorScript.new()
    var records: Array = []
    var summaries: Array = []
    for offset in range(count):
        var seed: int = first_seed + offset
        var fight = CombatScript.new()
        fight.begin(seed)
        while not fight.is_finished():
            fight.advance_tick()

        var record: Dictionary = fight.to_record()
        var replay = ReplayReaderScript.new()
        if not replay.load_record(record):
            return _reject("시드 %d: 기록 검증 실패 — %s" % [seed, replay.last_error])

        var filename: String = "match_%d.json" % seed
        if not _save_json(folder.path_join(filename), record):
            return {}

        var summary: Dictionary = selector.summarize(record)
        summary["file"] = filename
        summaries.append(summary)

    var ranked: Array = selector.rank(summaries)
    var selected: Dictionary = ranked[0]
    var index: Dictionary = {
        "format": "legendary_battle_selection_v1",
        "ruleset_version": CombatScript.RULESET_VERSION,
        "count": count,
        "start_seed": first_seed,
        "selected_seed": int(selected["seed"]),
        "selected_file": str(selected["file"]),
        "score_policy": HighlightSelectorScript.SELECTION_VERSION,
        "ranking": ranked,
        "selection_is_editorial": true,
    }
    if not _save_json(folder.path_join("index.json"), index):
        return {}

    print("경기 %d개 생성 완료. 추천 시드 %d (점수 %d). 기록: %s" % [
        count, int(selected["seed"]), int(selected["score"]), folder
    ])
    return index


func _save_json(path: String, data: Dictionary) -> bool:
    var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
    if file == null:
        last_error = "파일을 저장하지 못했습니다: %s" % path
        push_error(last_error)
        return false
    file.store_string(JSON.stringify(data))
    file.flush()
    file.close()
    return true


func _reject(message: String) -> Dictionary:
    last_error = message
    push_error(message)
    return {}
