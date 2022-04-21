import os, subprocess

import asset, constants, t3d_to_entities

class T3dType:
    force_regen = False
    file_extension = "t3d"
    category = "map"

# Kind of a hack?
class FlattenedTexturesType:
    force_regen = False
    file_extension = ""
    category = "flattened_textures"

class ObjType:
    force_regen = False
    file_extension = "obj"
    category = "map"

    @staticmethod
    def resolve_dependencies(obj_desc, t3d_desc):
        obj_desc.add_dependency_on(t3d_desc)

    @staticmethod
    def regenerate(obj_desc, t3d_desc):
        flattened_textures_dir = asset.AssetDescription(
            stage="intermediate",
            game=obj_desc.game,
            subfolder="",
            name="",
            asset_type=FlattenedTexturesType
        )
        print(flattened_textures_dir.path())
        subprocess.run([
            constants.T3D_TO_OBJ_PATH,
            "--post-scale",
            constants.T3D_SCALE * constants.SCALE,
            t3d_desc.path(),
            os.path.dirname(flattened_textures_dir.path())
        ])
        output_path = t3d_desc.path()[:-3] + ObjType.file_extension
        os.rename(output_path, obj_desc.path())

class VmapType:
    force_regen = False
    file_extension = "vmap"
    category = "map"

    @staticmethod
    def resolve_dependencies(vmap_desc, t3d_desc):
        obj_desc = t3d_desc.clone()
        obj_desc.stage = "intermediate"
        obj_desc.asset_type = ObjType
        obj_desc.resolve_dependencies(t3d_desc)
        vmap_desc.add_dependency_on(obj_desc)

    @staticmethod
    def regenerate(vmap_desc, obj_desc):
        #t3d_to_entities.convertMapFileToDMX(t3d_desc.path(), vmap_desc.path())
        pass # TODO