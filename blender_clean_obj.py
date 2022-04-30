import bpy
import argparse, sys

if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "obj_path",
        help="The OBJ file to clean."
    )

    args = parser.parse_args(argv)  # In this example we won't use the args

    bpy.ops.wm.read_factory_settings(use_empty=True)

    print("Cleaning", args.obj_path)
    bpy.ops.import_scene.obj(filepath=args.obj_path)

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')

    # This is to make sure that there is an active object in the scene:
    #----------------------------------------------
    for object in bpy.context.scene.objects:
        if not object.hide_viewport:
            bpy.context.view_layer.objects.active = object
            break
    #----------------------------------------------

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.25)
    bpy.ops.mesh.quads_convert_to_tris()

    bpy.ops.export_scene.obj("EXEC_DEFAULT", filepath=args.obj_path)

    bpy.ops.object.delete(use_global=True, confirm=False)
