import os, subprocess

import datamodel as dmx
import asset, constants, halfedge_mesh, hp_ents
from hammer import HammerClass

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
        vmap_desc.add_dependency_on(t3d_desc)
        obj_desc = t3d_desc.clone()
        obj_desc.stage = "intermediate"
        obj_desc.asset_type = ObjType
        obj_desc.resolve_dependencies(t3d_desc)
        vmap_desc.add_dependency_on(obj_desc)

    @staticmethod
    def regenerate(vmap_desc, t3d_desc, obj_desc):
        dm = dmx.load("template_map.vmap")

        globalClasses = []
        hp_ents.buildEntities(t3d_desc.path(), globalClasses, 0)
        for ent in globalClasses:
            dm.root["world"]["children"].append(ent.toEntityElement(dm))

        mesh = halfedge_mesh.from_obj(obj_desc)
        e = dm.add_element(None, "CMapMesh")

        # TODO: un-hardcode this
        e["origin"] = dmx.Vector3([0, 0, 0])
        e["angles"] = dmx.QAngle([0, 0, 0])
        e["scales"] = dmx.Vector3([0, 0, 0])
        node_id = int(dm.root["world"]["children"][-1]["nodeID"]) + 1
        e["nodeID"] = node_id
        e["referenceID"] = dmx.uint64(str(node_id))
        e["children"] = dmx.make_array(None, dmx.Element)
        e["editorOnly"] = False
        e["force_hidden"] = False
        e["transformLocked"] = False
        e["variableTargetKeys"] = dmx.make_array(None, str)
        e["variableNames"] = dmx.make_array(None, str)

        dm.write(vmap_desc.path(), "keyvalues2", 4)