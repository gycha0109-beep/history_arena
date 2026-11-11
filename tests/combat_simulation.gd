extends SceneTree

const CombatScript = preload("res://scripts/core/combat_simulator.gd")


func _initialize() -> void:
    var checked_matches: int = 0
    for match_seed in [10, 42, 1007, 20261112]:
        var first = CombatScript.new()
        first.begin(match_seed)

        while not first.is_finished() and first.session.tick < CombatScript.MAX_TICKS:
            first.advance_tick()

        if not first.is_finished():
            _fail("모든 경기는 제한 시간 내 종료되어야 합니다.")
            return

        var record: Dictionary = first.to_record()
        if record["frames"].size() != first.session.tick + 1:
            _fail("60Hz 상태 기록과 실제 틱 수가 일치하지 않습니다.")
            return

        var hits: int = 0
        for event in record["events"]:
            if event["type"] == "hit":
                hits += 1
        if hits == 0:
            _fail("전투가 실행됐지만 타격 판정이 한 번도 발생하지 않았습니다.")
            return

        for frame in record["frames"]:
            var a: Dictionary = frame["a"]
            var b: Dictionary = frame["b"]
            if int(a["hp"]) < 0 or int(b["hp"]) < 0:
                _fail("체력이 음수가 되었습니다.")
                return
            if absf(float(a["x"]) - float(b["x"])) < 0.649:
                _fail("두 캐릭터가 허용된 거리보다 가까이 겹쳤습니다.")
                return
            if absf(float(a["x"])) > 6.501 or absf(float(b["x"])) > 6.501:
                _fail("캐릭터가 경기장 경계를 벗어났습니다.")
                return

        var second = CombatScript.new()
        second.begin(match_seed)
        while not second.is_finished() and second.session.tick < CombatScript.MAX_TICKS:
            second.advance_tick()

        if JSON.stringify(record) != JSON.stringify(second.to_record()):
            _fail("같은 난수 시드에서 경기 전개가 재현되지 않았습니다.")
            return

        checked_matches += 1

    print("PASS: %d AI matches, hit/KO, boundaries and same-seed state records" % checked_matches)
    quit(0)


func _fail(message: String) -> void:
    push_error(message)
    quit(1)
