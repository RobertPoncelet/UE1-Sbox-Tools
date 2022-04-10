import argparse, glob
from dataclasses import dataclass

import asset, fbx, vmdl

@dataclass
class ModelBuildTreeHelper:
    vmdl: asset.AssetDescription
    psk: asset.AssetDescription
    fbx: asset.AssetDescription = None

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
        fbx.FbxNode.force_regen = True
    if args.regen_vmdl:
        vmdl.VmdlNode.force_regen = True

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
    vmdl_nodes = [vmdl.VmdlNode(helper) for helper in helpers]
    vmdl_nodes[0].build()
    print("Done")
