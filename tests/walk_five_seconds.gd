extends SceneTree

const WalkController = preload("res://scripts/preview/walk_five_seconds.gd")

func _initialize() -> void:
    if WalkController.FRAMES != 300 or not is_equal_approx(WalkController.HZ, 60.0):
        _fail("5초/60Hz/300프레임 규격이 틀렸습니다.")
        return
    if WalkController.WALK_SPEED < 0.5:
        _fail("실제로 앞으로 걷도록 이동 속도를 설정해야 합니다.")
        return
    var expected: float = WalkController.WALK_SPEED * 5.0
    var start: float = WalkController.root_x_at_frame(0)
    var finish: float = WalkController.root_x_at_frame(300)
    if not is_equal_approx(finish - start, expected):
        _fail("5초 전체의 실제 전진 거리와 발걸음 속도가 다릅니다.")
        return
    for frame in range(1,301):
        var step: float = WalkController.root_x_at_frame(frame) - WalkController.root_x_at_frame(frame - 1)
        if not is_equal_approx(step, WalkController.WALK_SPEED / WalkController.HZ):
            _fail("프레임 간 실제 이동 거리/속도가 일관되지 않습니다.")
            return
    print("PASS: 300-frame 5s walking trajectory, continuous 6.75m real movement")
    quit(0)

func _fail(message: String) -> void:
    push_error(message)
    quit(1)
