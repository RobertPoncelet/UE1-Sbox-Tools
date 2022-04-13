import argparse, glob
import multiprocessing as mp

import asset, fbx, vmat, vmdl
from build_node import BuildNode

def build_vmdl(root_node, regen_fbx=False, regen_vmdl=False, regen_vmat=False):
    if regen_fbx:
        fbx.FbxType.force_regen = True
    if regen_vmdl:
        vmdl.VmdlType.force_regen = True
    if regen_vmat:
        vmat.VmatType.force_regen = True
    root_node.build()
        
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
        fbx.FbxType.force_regen = True
    if args.regen_vmdl:
        vmdl.VmdlType.force_regen = True
    if args.regen_vmat:
        vmat.VmatType.force_regen = True

    if args.psks:
        psk_descs = [asset.AssetDescription.from_path(path)
            for pattern in args.psks for path in glob.glob(pattern)]
    else:
        all_psks = asset.AssetDescription(
            stage="original",
            game="*",
            subfolder="**",
            name="*",
            asset_type=vmdl.PskType)
        psk_descs = all_psks.glob()

    def psk_to_vmdl_desc(psk: asset.AssetDescription):
        assert(psk.name.lower().endswith("mesh"))
        new_name = psk.name[:-4]
        if new_name.lower().startswith("sk"):
            new_name = new_name[2:]

        vmdl_desc = psk.clone()
        vmdl_desc.stage = "converted"
        vmdl_desc.name = new_name
        vmdl_desc.asset_type = vmdl.VmdlType
        return vmdl_desc
    
    vmdl_descs = [psk_to_vmdl_desc(p) for p in psk_descs]
    vmdl_descs = vmdl_descs[:20] # Remove when we're ready to do the full thing

    print("="*20 + " RESOLVING DEPENDENCIES " + "="*20)
    for vmdl_desc, psk_desc in zip(vmdl_descs, psk_descs):
        vmdl_desc.resolve_dependencies(psk_desc)

    print("="*20 + " STARTING BUILD " + "="*20)
    with mp.Pool(processes=None) as pool:
        mp_args = [(BuildNode(v), args.regen_fbx, args.regen_vmdl, args.regen_vmat) for v in vmdl_descs]
        pool.starmap(build_vmdl, mp_args)

    print("Done")
