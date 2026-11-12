extends SceneTree

const WalkController = preload("res://scripts/preview/walk_five_seconds.gd")
const FootTrack = preload("res://scripts/preview/foot_contact_track.gd")

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
    if FootTrack.FOOT_LIFT > 0.10 or FootTrack.FOOT_LIFT < 0.05:
        _fail("?????? ? ?? ?????.")
        return
    for index in range(2):
        var last_contact_x: float = 0.0
        var last_contact_valid: bool = false
        var has_lift: bool = false
        for tick in range(301):
            var data: Dictionary = FootTrack.sample(
                float(tick) / WalkController.HZ, index, -3.35, WalkController.WALK_SPEED, 0)
            var pos: Vector3 = data["position"]
            if bool(data["planted"]):
                if last_contact_valid:
                    if absf(pos.x - last_contact_x) > 0.001:
                        _fail("?? ?? ?? ??? ??????.")
                        return
                last_contact_x = pos.x
                last_contact_valid = true
            else:
                last_contact_valid = false
                if pos.y > FootTrack.ANKLE_HEIGHT + 0.05:
                    has_lift = true
        if not has_lift:
            _fail("?? ??? ????? ??? ????.")
            return
    print("PASS: 300-frame 5s walk, 4.5m travel, fixed foot contact anchors and soft swing")
    quit(0)

func _fail(message: String) -> void:
    push_error(message)
    quit(1)
