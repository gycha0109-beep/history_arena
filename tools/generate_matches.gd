extends SceneTree
## Headless batch generator. Example:
## godot --headless --path . --script res://tools/generate_matches.gd -- --count 12 --first-seed 20261112

const BatchScript = preload("res://scripts/replay/match_batch.gd")


func _initialize() -> void:
    call_deferred("_run")


func _run() -> void:
    var count: int = 12
    var seed: int = 20261112
    var out_dir: String = "res://captures/matches"
    var args: PackedStringArray = OS.get_cmdline_user_args()

    for index in range(args.size()):
        if index + 1 >= args.size():
            continue
        match args[index]:
            "--count":
                if not args[index + 1].is_valid_int():
                    push_error("--count 값은 정수여야 합니다.")
                    quit(1)
                    return
                count = int(args[index + 1])
            "--first-seed":
                if not args[index + 1].is_valid_int():
                    push_error("--first-seed 값은 정수여야 합니다.")
                    quit(1)
                    return
                seed = int(args[index + 1])
            "--out-dir":
                out_dir = args[index + 1]

    var batch = BatchScript.new()
    var result: Dictionary = batch.generate(count, seed, out_dir)
    if result.is_empty():
        push_error(batch.last_error)
        quit(1)
        return
    print("추천 경기: %s%s" % [out_dir.rstrip("/"), "/" + str(result["selected_file"])])
    quit(0)
