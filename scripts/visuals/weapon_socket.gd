extends Node3D
## A non-scaling weapon socket that follows a Skeleton3D bone.
## Unlike a child of a scaled bone, the sword receives rotation + position only.

var source_skeleton: Skeleton3D
var bone_index: int = -1


func bind_to_skeleton(target: Skeleton3D, candidate_bones: Array) -> bool:
    source_skeleton = null
    bone_index = -1
    if target == null:
        return false
    for candidate in candidate_bones:
        var found: int = target.find_bone(str(candidate))
        if found >= 0:
            source_skeleton = target
            bone_index = found
            break
    if bone_index < 0:
        return false
    top_level = true
    update_socket()
    return true


func _process(_delta: float) -> void:
    update_socket()


func update_socket() -> void:
    if not is_instance_valid(source_skeleton) or bone_index < 0:
        return
    var bone_world: Transform3D = source_skeleton.global_transform * source_skeleton.get_bone_global_pose(bone_index)
    global_transform = Transform3D(bone_world.basis.orthonormalized(), bone_world.origin)
