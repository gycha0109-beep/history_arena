extends SceneTree
## Strict preflight. Must fail if actual rigged assets/animations are missing.
## NOT part of the CI smoke test, because no licensed GLBs are in this repository.

const CharacterVisualScript = preload("res://scripts/visuals/character_visual.gd")


func _initialize() -> void:
    for fighter_id in ["musashi", "bruce_lee"]:
        var character = CharacterVisualScript.new()
        character.name = fighter_id
        root.add_child(character)
        var path: String = "res://assets/characters/%s/character.json" % fighter_id
        if not character.load_manifest(path):
            push_error("녹화 전 검사 실패: %s" % character.status_message)
            quit(1)
            return
        if not character.ready_for_preview:
            push_error("녹화 전 검사 실패: %s의 모델 또는 필수 모션이 누락되었습니다." % fighter_id)
            quit(1)
            return
    print("PASS: 실제 GLB 모델·모션·검 소켓 연결 준비")
    quit(0)
