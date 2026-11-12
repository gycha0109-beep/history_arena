extends SceneTree

const TimelineScript = preload("res://scripts/preview/five_second_timeline.gd")
const PreviewScene = preload("res://scenes/preview_five_seconds.tscn")


func _initialize() -> void:
    var timeline = TimelineScript.new()
    var first: Dictionary = timeline.sample(0)
    var approach: Dictionary = timeline.sample(75)
    var attack: Dictionary = timeline.sample(115)
    var hit: Dictionary = timeline.sample(140)
    var last: Dictionary = timeline.sample(300)

    if timeline.DURATION_FRAMES != 300 or timeline.FPS != 60:
        _fail("5초 길이 또는 60Hz 설정이 다릅니다.")
        return

    if first["phase"] != "대치" or attack["a"]["move"] != "quick_cut":
        _fail("시작 대치 또는 검격 구간이 설정과 다릅니다.")
        return

    if approach["a"]["x"] <= first["a"]["x"]:
        _fail("무사시가 상대를 향해 접근하지 않습니다.")
        return

    if hit["b"]["action"] != "stunned" or hit["b"]["hp"] >= first["b"]["hp"]:
        _fail("검격 후 이소룡 피격 반응이 없습니다.")
        return

    if last["frame"] != 300 or last["a"]["action"] != "idle":
        _fail("5초 장면이 대기 자세로 돌아오지 않습니다.")
        return

    for frame in range(301):
        var pose: Dictionary = timeline.sample(frame)
        var a_x: float = float(pose["a"]["x"])
        var b_x: float = float(pose["b"]["x"])
        if b_x - a_x < 0.65:
            _fail("캐릭터가 지나치게 겹칩니다.")
            return

    var scene = PreviewScene.instantiate()
    root.add_child(scene)
    if scene.visuals.size() != 2:
        _fail("두 캐릭터 표시 계층을 만들지 못했습니다.")
        return
    scene.set_preview_frame(140)
    if scene.frame != 140:
        _fail("미리보기 재생 위치 변경이 실패했습니다.")
        return

    print("PASS: 300-frame five-second preview, choreography and optional asset warnings")
    quit(0)


func _fail(message: String) -> void:
    push_error(message)
    quit(1)
