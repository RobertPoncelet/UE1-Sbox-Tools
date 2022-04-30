import argparse, glob
import multiprocessing as mp

import asset, vmap
from build_node import BuildNode

def build_vmap(root_node, regen_vmap=False, regen_obj=False):
    if regen_vmap:
        vmap.VmapType.force_regen = True
    if regen_obj:
        vmap.ObjType.force_regen = True
    root_node.build()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert UE1 T3Ds to VMAPs.")

    parser.add_argument("--t3ds", type=str, nargs="+", default=None,
                        help="Glob specifying which T3D files to convert.")
    parser.add_argument("--regen-vmap", action="store_true",
                        help="Force regeneration of VMAP files.")
    parser.add_argument("--regen-obj", action="store_true",
                        help="Force regeneration of OBJ files.")

    args = parser.parse_args()

    if args.t3ds:
        t3d_descs = [asset.AssetDescription.from_path(path)
            for pattern in args.t3ds for path in glob.glob(pattern)]
    else:
        all_t3ds = asset.AssetDescription(
            stage="original",
            game="*",
            subfolder="**",
            name="*",
            asset_type=vmap.T3dType)
        t3d_descs = all_t3ds.glob()

    def t3d_to_vmap_desc(t3d: asset.AssetDescription):
        vmap_desc = t3d.clone()
        vmap_desc.stage = "converted"
        vmap_desc.asset_type = vmap.VmapType
        return vmap_desc

    vmap_descs = [t3d_to_vmap_desc(p) for p in t3d_descs]
    vmap_descs = vmap_descs[:1]

    print("="*20 + " RESOLVING DEPENDENCIES " + "="*20)
    for vmap_desc, t3d_desc in zip(vmap_descs, t3d_descs):
        vmap_desc.resolve_dependencies(t3d_desc)

    print("="*20 + " STARTING BUILD " + "="*20)
    with mp.Pool(processes=None) as pool:
        mp_args = [(BuildNode(v), args.regen_vmap, args.regen_obj)
            for v in vmap_descs]
        pool.starmap(build_vmap, mp_args)

    print("Done")
