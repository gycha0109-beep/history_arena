extends SceneTree
## Inspect a rigged 3D file imported by Godot, without assigning it to a fighter.

func _initialize() -> void:
    call_deferred("_inspect")


func _inspect() -> void:
    var args: PackedStringArray = OS.get_cmdline_user_args()
    var path: String = ""
    for i in range(args.size() - 1):
        if args[i] == "--glb":
            path = args[i + 1]
    if path.is_empty() or not ResourceLoader.exists(path):
        push_error("확인할 GLB가 없습니다. -- --glb res://경로.glb 로 지정하세요.")
        quit(1)
        return

    var scene: PackedScene = load(path) as PackedScene
    if scene == null:
        push_error("Godot에서 모델을 3D 씬으로 읽지 못했습니다.")
        quit(1)
        return

    var model: Node = scene.instantiate()
    root.add_child(model)
    var skeletons: Array[Skeleton3D] = []
    var players: Array[AnimationPlayer] = []
    var meshes: Array[MeshInstance3D] = []
    _collect_nodes(model, skeletons, players, meshes)

    print("GLB_IMPORT_OK file=%s meshes=%d skeletons=%d animation_players=%d" % [
        path, meshes.size(), skeletons.size(), players.size()
    ])
    for skel in skeletons:
        var names: Array[String] = []
        for idx in range(skel.get_bone_count()):
            names.append(skel.get_bone_name(idx))
        print("SKELETON_BONES: %s" % ", ".join(names))
    for player in players:
        print("ANIMATIONS: %s" % ", ".join(Array(player.get_animation_list())))

    if meshes.is_empty():
        push_error("파일에 메시가 없습니다.")
        quit(1)
        return
    if skeletons.is_empty() or players.is_empty():
        push_warning("모델은 로딩되었지만 전투 캐릭터에 필요한 스켈레톤 또는 모션이 없습니다.")
    quit(0)


func _collect_nodes(node: Node, skeletons: Array[Skeleton3D], players: Array[AnimationPlayer], meshes: Array[MeshInstance3D]) -> void:
    if node is Skeleton3D:
        skeletons.append(node as Skeleton3D)
    if node is AnimationPlayer:
        players.append(node as AnimationPlayer)
    if node is MeshInstance3D:
        meshes.append(node as MeshInstance3D)
    for child in node.get_children():
        _collect_nodes(child, skeletons, players, meshes)
