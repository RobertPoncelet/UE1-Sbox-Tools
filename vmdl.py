import os
import constants
from build_node import BuildNode
from fbx import FbxNode
from vmat import VmatNode
import datamodel as dmx

class VmdlNode(BuildNode):
    def __init__(self, tree):
        super().__init__(tree.vmdl)
        fbx_desc = tree.vmdl.clone()
        fbx_desc.stage = "converted"
        fbx_desc.filetype = "fbx"
        tree.fbx = fbx_desc
        self._fbx_node = FbxNode(tree)

        # Handle materials
        tga_glob = tree.psk.clone()
        tga_glob.category = "material"
        tga_glob.subfolder = os.path.join(tga_glob.subfolder, "Skins")
        assert(tga_glob.name.lower().endswith("mesh"))
        tga_glob.name = tga_glob.name[:-4] + "Tex*"
        tga_glob.filetype = "tga"
        tree.tgas = tga_glob.glob()

        def tga_to_vmat_desc(desc):
            ret = desc.clone()
            ret.stage = "converted"
            ret.filetype = "vmat"
            ret.subfolder = tree.vmdl.subfolder # Let's not use the "Skins" subfolder
            return ret

        tree.vmats = []
        self._vmat_nodes = []
        for tga in tree.tgas:
            vmat_desc = tga_to_vmat_desc(tga)
            tree.vmats.append(vmat_desc)
            self._vmat_nodes.append(VmatNode(vmat_desc, tree))

    @property
    def dependencies(self):
        return [self._fbx_node] + self._vmat_nodes

    def regenerate_file(self):
        dm = dmx.DataModel("modeldoc29", "3cec427c-1b0e-4d48-a90a-0436f33a6041")
        meta_root = dm.add_element(None)

        root = dm.add_element(None, "RootNode")
        root["children"] = dmx.make_array(None, dmx.Element)

        mats = dm.add_element(None, "MaterialGroupList")
        mats["children"] = dmx.make_array(None, dmx.Element)
        default_mat_grp = dm.add_element(None, "DefaultMaterialGroup")
        default_mat_grp["remaps"] = dmx.make_array(None, dmx.Element)

        for vmat in self._vmat_nodes:
            vmat_elem = dm.add_element(None)
            vmat_elem["from"] = os.path.basename(vmat.filepath)
            vmat_elem["to"] = vmat.sbox_filepath
            default_mat_grp["remaps"].append(vmat_elem)

        default_mat_grp["use_global_default"] = False
        default_mat_grp["global_default_material"] = ""
        mats["children"].append(default_mat_grp)
        root["children"].append(mats)

        mesh_list = dm.add_element(None, "RenderMeshList")
        mesh_list["children"] = dmx.make_array(None, dmx.Element)
        mesh_file = dm.add_element(None, "RenderMeshFile")
        mesh_file["filename"] = self.dependencies[0].sbox_filepath
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