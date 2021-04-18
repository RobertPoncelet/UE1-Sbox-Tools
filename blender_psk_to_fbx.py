import bpy
import glob
import os
import io_import_scene_unreal_psa_psk_280 as psk

ROOT_PATH = "F:/Google Drive/hp_resources"
GAMES = ["hp1", "hp2"]

for game in GAMES:
    glob_path = os.path.join(ROOT_PATH, game, "raw_models_textures", "**", "*.psk")
    psks = glob.glob(glob_path, recursive=True)
#    psks = psks[:10] # remove for all psks
    for psk_path in psks:
        print("Converting " + psk_path)
        psk.pskimport(psk_path, context=bpy.context, bDontInvertRoot=False)
        
        model_name = os.path.splitext(os.path.basename(psk_path))[0]
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.shade_smooth()
#        bpy.context.space_data.context = 'DATA'
        bpy.data.objects[model_name + ".mo"].data.use_auto_smooth=True
        bpy.data.objects[model_name + ".mo"].data.auto_smooth_angle = 1.40499
        
        #if model_name[:2] == "sk":
        #    model_name = model_name[2:]
        #if model_name[-4:] == "Mesh":
        #    model_name = model_name[:-4]
        model_name += ".fbx"
        # This bit's a bit hacky
        subfolder = psk_path.split(os.path.sep)[-2]
        out_path = os.path.join(ROOT_PATH, game, "fbx", subfolder, model_name)
        
        if not os.path.isdir(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))
        
        bpy.ops.export_scene.fbx("EXEC_DEFAULT", filepath=out_path)
        
        bpy.ops.object.delete(use_global=True, confirm=False)
