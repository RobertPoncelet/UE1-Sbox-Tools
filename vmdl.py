import os
import constants
from fbx import FbxType
from vmat import VmatType
import datamodel as dmx

class UClassType:
    force_regen = False
    file_extension = "uc"
    category = "uclass"

class TgaType:
    force_regen = False
    file_extension = "tga"
    category = "material"

class PskType:
    force_regen = False
    file_extension = "psk"
    category = "model"

class VmdlType:
    force_regen = False
    file_extension = "vmdl"
    category = "model"

    # Fill the vmdl's dependencies based on its current state so the BuildNode can access it later
    # The dependencies added should match the arguments given to regenerate (minus the VMDL itself)
    @staticmethod
    def resolve_dependencies(vmdl_desc, psk_desc):
        assert(vmdl_desc.asset_type is VmdlType)
        fbx_desc = vmdl_desc.clone()
        fbx_desc.stage = "converted"
        fbx_desc.asset_type = FbxType
        fbx_desc.resolve_dependencies(psk_desc)
        vmdl_desc.add_dependency_on(fbx_desc)

        # Handle materials
        # Find the UClass, if available
        uc_desc = psk_desc.clone()
        uc_desc.asset_type = UClassType
        uc_desc.subfolder = os.path.join(uc_desc.subfolder, "Classes")
        assert(uc_desc.name[-4:].lower() == "mesh") # We need the "sk" prefix, if applicable
        uc_desc.name = uc_desc.name[:-4]
        is_masked = False
        if uc_desc.exists():
            with open(uc_desc.path()) as uc_file:
                is_masked = "STY_Masked" in uc_file.read()
        else:
            print(uc_desc.path(), "does not exist")

        # Find TGAs matching the VMDL name under the "Skins" subfolder
        tga_glob = psk_desc.clone()
        tga_glob.asset_type = TgaType
        tga_glob.subfolder = os.path.join(tga_glob.subfolder, "Skins")
        assert(psk_desc.name[-4:].lower() == "mesh") # We need the "sk" prefix, if applicable
        tga_glob.name = psk_desc.name[:-4] + "Tex*"
        tgas = tga_glob.glob()

        # Make a VMAT for each TGA, ensure it's appropriately filled in, add our dependency on it
        for tga_desc in tgas:
            vmat_desc = tga_desc.clone()
            vmat_desc.stage = "converted"
            if vmat_desc.name[:2].lower() == "sk":
                vmat_desc.name = vmat_desc.name[2:]
            vmat_desc.asset_type = VmatType
            vmat_desc.subfolder = vmdl_desc.subfolder # Let's not use the "Skins" subfolder
            vmat_desc.is_masked = is_masked
            vmat_desc.parent_tga = tga_desc
            VmatType.resolve_dependencies(vmat_desc, tga_desc)
            vmdl_desc.add_dependency_on(vmat_desc)

    @staticmethod
    def regenerate(vmdl_desc, fbx_desc, *vmat_descs):
        dm = dmx.DataModel("modeldoc29", "3cec427c-1b0e-4d48-a90a-0436f33a6041")
        meta_root = dm.add_element(None)

        root = dm.add_element(None, "RootNode")
        root["children"] = dmx.make_array(None, dmx.Element)

        mats = dm.add_element(None, "MaterialGroupList")
        mats["children"] = dmx.make_array(None, dmx.Element)
        default_mat_grp = dm.add_element(None, "DefaultMaterialGroup")
        default_mat_grp["remaps"] = dmx.make_array(None, dmx.Element)

        for vmat in vmat_descs:
            vmat_elem = dm.add_element(None)
            orig_tga_name = os.path.basename(vmat.parent_tga.path())
            vmat_elem["from"] = os.path.splitext(orig_tga_name)[0] + ".vmat"
            vmat_elem["to"] = vmat.sbox_path()
            default_mat_grp["remaps"].append(vmat_elem)

        default_mat_grp["use_global_default"] = False
        default_mat_grp["global_default_material"] = ""
        mats["children"].append(default_mat_grp)
        root["children"].append(mats)

        mesh_list = dm.add_element(None, "RenderMeshList")
        mesh_list["children"] = dmx.make_array(None, dmx.Element)
        mesh_file = dm.add_element(None, "RenderMeshFile")
        mesh_file["filename"] = fbx_desc.sbox_path()
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

        dm.write(vmdl_desc.path(), "keyvalues3", "e21c7f3c-8a33-41c5-9977-a76d3a32aa0d")