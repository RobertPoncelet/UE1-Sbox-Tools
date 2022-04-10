import os
import asset, constants
from build_node import BuildNode
from fbx import FbxNode
import datamodel as dmx

class VmdlNode(BuildNode):
    def __init__(self, tree):
        super().__init__(tree.vmdl)
        fbx_desc = asset.AssetDescription(
            "converted",
            tree.vmdl.game,
            tree.vmdl.category,
            tree.vmdl.subfolder,
            tree.vmdl.name,
            "fbx"
        )
        tree.fbx = fbx_desc
        self._dependencies = [FbxNode(tree)] 
        # TODO: add materials

    @property
    def dependencies(self):
        return self._dependencies

    def regenerate_file(self):
        dm = dmx.DataModel("modeldoc29", "3cec427c-1b0e-4d48-a90a-0436f33a6041")
        meta_root = dm.add_element(None)

        root = dm.add_element(None, "RootNode")
        root["children"] = dmx.make_array(None, dmx.Element)

        mats = dm.add_element(None, "MaterialGroupList")
        mats["children"] = dmx.make_array(None, dmx.Element)
        default_mat_grp = dm.add_element(None, "DefaultMaterialGroup")
        default_mat_grp["remaps"] = dmx.make_array(None, dmx.Element)
        default_mat_grp["use_global_default"] = False
        default_mat_grp["global_default_material"] = ""
        mats["children"].append(default_mat_grp)
        root["children"].append(mats)

        mesh_list = dm.add_element(None, "RenderMeshList")
        mesh_list["children"] = dmx.make_array(None, dmx.Element)
        mesh_file = dm.add_element(None, "RenderMeshFile")
        sbox_filepath = self.dependencies[0].relative_filepath
        sbox_filepath = sbox_filepath.replace(os.path.sep, '/')
        mesh_file["filename"] = sbox_filepath
        mesh_file["import_translation"] = dmx.Vector3([0, 0, 0])
        mesh_file["import_rotation"] = dmx.Vector3([0, 0, 0])
        mesh_file["import_scale"] = constants.SCALE
        import_filter = dm.add_element(None)
        import_filter["exclude_by_default"] = False
        import_filter["exception_list"] = dmx.make_array(None, dmx.Element)
        mesh_file["import_filter"] = import_filter
        mesh_list["children"].append(mesh_file)
        root["children"].append(mesh_list)

        '''anim_list = dm.add_element(None, "AnimationList")
        anim_list["children"] = dmx.make_array(None, dmx.Element)
        anim_file = dm.add_element("test", "AnimFile")
        anim_file["take"] = 0
        anim_file["source_filename"] = "hp2/models/HPModels/test.fbx"
        anim_list["children"].append(anim_file)
        root["children"].append(anim_list)'''

        meta_root["rootNode"] = root

        dm.write(self.filepath, "keyvalues3", "e21c7f3c-8a33-41c5-9977-a76d3a32aa0d")