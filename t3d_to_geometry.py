import glob
import os

GAME_PATHS = ["..\\hp1", "..\\hp2"]
DO_CONVERSION = True
OVERWRITE = False

def convertMapFile(game, path):
    cwd = os.getcwd()
    
    if DO_CONVERSION:
        # Use t3d_to_obj.exe to convert the map geometry
        os.chdir("..\\t3d_to_obj")
        cmd = "use_me_pls_python.bat {} {}".format(path, os.path.join(game, "textures_png_flattened_names"))
        print(cmd)
        os.system(cmd)

    # Hammer doesn't like the material names to have too many dots, so we need to fix that
    os.chdir(os.path.dirname(path))
    filename = os.path.basename(path)
    mapname = os.path.splitext(filename)[0]
    
    with open(mapname + ".mtl", "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line[:6] == "newmtl" and len(line.split()) > 1:
                mtl_name = line.split()[1]
                mtl_name = "_".join(mtl_name.split("."))
                f.write("newmtl " + mtl_name + "\n")
            else:
                f.write(line)

    with open(mapname + ".obj", "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line[:6] == "usemtl" and len(line.split()) > 1:
                mtl_name = line.split()[1]
                mtl_name = "_".join(mtl_name.split("."))
                f.write("usemtl " + mtl_name + "\n")
            else:
                f.write(line)

    os.chdir(cwd)

for game in GAME_PATHS:
    glob_path = os.path.join(game, "maps", "*.t3d")
    maps = glob.glob(glob_path, recursive=True)

    #maps = [maps[0]] # remove for all maps

    for map_path in maps:
        out_map_path = map_path[:-3] + "obj"
        if not OVERWRITE and os.path.isfile(out_map_path):
            print("Not overwriting " + out_map_path)
            continue
        print("Processing " + map_path)
        convertMapFile(game, map_path)
