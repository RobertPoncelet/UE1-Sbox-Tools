import argparse, glob
from dataclasses import dataclass

from build_node import BuildNode
import asset
import datamodel as dmx

@dataclass
class ModelBuildTreeHelper:
    vmdl: asset.AssetDescription
    psk: asset.AssetDescription
    fbx: asset.AssetDescription = None

class FbxNode(BuildNode):
    def __init__(self, tree):
        super().__init__(tree.fbx)
    
    @property
    def dependencies(self):
        return None # TODO

    def regenerate_file(self):
        pass # TODO

class VmdlNode(BuildNode):
    def __init__(self, tree):
        super().__init__(tree.vmdl)
        self._dependencies = None#[FbxNode(tree)] 
        # TODO: add materials

    @property
    def dependencies(self):
        return self._dependencies

    def regenerate_file(self):
        # TODO: create DataModel from a template, fill it with FBX/material data from dependencies, save it in our filepath
        dm = dmx.DataModel("modeldoc", "29")
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

        '''relayPlugData = datamodel.add_element(None, "DmePlugList")
        relayPlugData["names"] = dmx.make_array(None, str)
        relayPlugData["dataTypes"] = dmx.make_array(None, int)
        relayPlugData["plugTypes"] = dmx.make_array(None, int)
        relayPlugData["descriptions"] = dmx.make_array(None, str)
        e["relayPlugData"] = relayPlugData
        e["connectionsData"] = dmx.make_array(None, dmx.Element)
        e["entity_properties"] = datamodel.add_element(None, "EditGameClassProps")
        e["hitNormal"] = dmx.Vector3([0, 0, 1])
        e["isProceduralEntity"] = False'''
        dm.write(self.filepath, "keyvalues2", 4)

def psk_to_vmdl_desc(desc: asset.AssetDescription):
    assert(desc.name.lower().endswith("mesh"))
    new_name = desc.name[:-4]
    if new_name.lower().startswith("sk"):
        new_name = new_name[2:]

    return asset.AssetDescription(
        "converted",
        desc.game,
        desc.category,
        desc.subfolder,
        new_name,
        "vmdl"
    )
        
# TODO: glob all psks, figure out an output vmdl path for each, put both in a ModelBuildTreeHelper, give it to a new VmdlNode
# (Note: all psks should end with "Mesh.psk", but not all of them start with "sk")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert UE1 PSKs to VMDLs.")

    parser.add_argument("--psks", type=str, nargs="+", default=None,
                        help="Glob specifying which PSK files to convert.")
    parser.add_argument("--regen-fbx", action="store_true",
                        help="Force regeneration of intermediate FBX files.")
    parser.add_argument("--regen-vmdl", action="store_true",
                        help="Force regeneration of VMDL files.")

    args = parser.parse_args()

    if args.regen_fbx:
        FbxNode.force_regen = True
    if args.regen_vmdl:
        VmdlNode.force_regen = True

    if args.psks:
        psk_descs = [asset.AssetDescription.from_path(path)
            for pattern in args.psks for path in glob.glob(pattern)]
    else:
        all_psks = asset.AssetDescription("original", "*", "model", "**", "*", "psk")
        psk_descs = [asset.AssetDescription.from_path(path)
            for path in all_psks.glob()]

    # from_path() can't currently tell the difference between original materials and models :(
    # TODO: maybe change the file structure to fix this
    for desc in psk_descs:
        desc.category = "model"
    
    helpers = [ModelBuildTreeHelper(psk_to_vmdl_desc(p), p) for p in psk_descs]
    vmdl_nodes = [VmdlNode(helper) for helper in helpers]
    vmdl_nodes[0].build()
    print("Done")
