import argparse, glob
from dataclasses import dataclass

import asset, fbx, vmat, vmdl

@dataclass
class ModelBuildTreeHelper:
    vmdl: asset.AssetDescription
    psk: asset.AssetDescription
    fbx: asset.AssetDescription = None
    vmats: list[asset.AssetDescription] = None
    tgas: list[asset.AssetDescription] = None

def psk_to_vmdl_desc(desc: asset.AssetDescription):
    assert(desc.name.lower().endswith("mesh"))
    new_name = desc.name[:-4]
    if new_name.lower().startswith("sk"):
        new_name = new_name[2:]

    ret = desc.clone()
    ret.stage = "converted"
    ret.name = new_name
    ret.filetype = "vmdl"
    return ret
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert UE1 PSKs to VMDLs.")

    parser.add_argument("--psks", type=str, nargs="+", default=None,
                        help="Glob specifying which PSK files to convert.")
    parser.add_argument("--regen-fbx", action="store_true",
                        help="Force regeneration of intermediate FBX files.")
    parser.add_argument("--regen-vmdl", action="store_true",
                        help="Force regeneration of VMDL files.")
    parser.add_argument("--regen-vmat", action="store_true",
                        help="Force regeneration of VMAT material files.")

    args = parser.parse_args()

    if args.regen_fbx:
        fbx.FbxNode.force_regen = True
    if args.regen_vmdl:
        vmdl.VmdlNode.force_regen = True
    if args.regen_vmat:
        vmat.VmatNode.force_regen = True

    if args.psks:
        psk_descs = [asset.AssetDescription.from_path(path)
            for pattern in args.psks for path in glob.glob(pattern)]
    else:
        all_psks = asset.AssetDescription("original", "*", "model", "**", "*", "psk")
        psk_descs = all_psks.glob()
    
    helpers = [ModelBuildTreeHelper(psk_to_vmdl_desc(p), p) for p in psk_descs]
    print("Resolving dependencies...")
    vmdl_nodes = [vmdl.VmdlNode(helper) for helper in helpers]
    print("="*20 + " STARTING BUILD " + "="*20)
    vmdl_nodes[0].build()
    print("Done")
