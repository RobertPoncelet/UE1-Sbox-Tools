import bpy
import argparse, os, sys
import io_import_scene_unreal_psa_psk_280 as psk

if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "psk_path",
        help="The PSK file to convert."
    )
    parser.add_argument(
        "fbx_path",
        help="The output FBX file to produce."
    )
    parser.add_argument(
        "--psa_path",
        help="The PSA file to add animations from (optional)."
    )

    args = parser.parse_args(argv)  # In this example we won't use the args

    bpy.ops.wm.read_factory_settings(use_empty=True)

    print("Converting", args.psk_path)
    psk.pskimport(args.psk_path, context=bpy.context, bDontInvertRoot=False)

    model_name = os.path.splitext(os.path.basename(args.psk_path))[0]
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.shade_smooth()
#        bpy.context.space_data.context = 'DATA'
    bpy.data.objects[model_name + ".mo"].data.use_auto_smooth=True
    bpy.data.objects[model_name + ".mo"].data.auto_smooth_angle = 1.40499

    # Do animations
    if args.psa_path and os.path.exists(args.psa_path):
        print("Converting animations:", args.psa_path)
        # TODO

    bpy.ops.export_scene.fbx("EXEC_DEFAULT", filepath=args.fbx_path)

    bpy.ops.object.delete(use_global=True, confirm=False)
