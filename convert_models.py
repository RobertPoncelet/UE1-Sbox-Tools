import argparse, glob
from dataclasses import dataclass
import multiprocessing as mp

import asset, fbx, vmat, vmdl

def build_psk(helper, regen_fbx=False, regen_vmdl=False, regen_vmat=False):
    if regen_fbx:
        fbx.FbxNode.force_regen = True
    if regen_vmdl:
        vmdl.VmdlNode.force_regen = True
    if regen_vmat:
        vmat.VmatNode.force_regen = True
    node = vmdl.VmdlNode(helper)
    node.build()
        
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

    def psk_to_vmdl_desc(psk: asset.AssetDescription):
        assert(psk.name.lower().endswith("mesh"))
        new_name = psk.name[:-4]
        if new_name.lower().startswith("sk"):
            new_name = new_name[2:]

        ret = psk.clone()
        ret.stage = "converted"
        ret.name = new_name
        ret.filetype = "vmdl"
        return ret
    
    helpers = [ModelBuildTreeHelper(psk_to_vmdl_desc(p), p) for p in psk_descs]
    helpers = helpers[:10]

    print("="*20 + " STARTING BUILD " + "="*20)

    with mp.Pool(processes=None) as pool:
        mp_args = [(h, args.regen_fbx, args.regen_vmdl, args.regen_vmat) for h in helpers]
        pool.starmap(build_psk, mp_args)

    print("Done")
