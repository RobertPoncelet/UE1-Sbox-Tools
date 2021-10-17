import constants
import glob
import os

DO_CONVERSION = True

def convertMapFile(game, path):
    cwd = os.getcwd()
    
    if DO_CONVERSION:
        # Use t3d_to_obj.exe to convert the map geometry
        os.chdir("..\\t3d_to_obj")
        T3D_SCALE = 40.65040650406504065040
        is_mover = os.path.split(os.path.dirname(path))[-1] == "movers"
        movers_arg = "--movers" if is_mover else ""
        cmd = "t3d_to_obj.exe {} --post-scale {} {} {}"
        cmd = cmd.format(movers_arg, T3D_SCALE * constants.SCALE, path, os.path.join("..", game, "textures_png_flattened_names"))
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
            elif line.startswith("v "):
                nums = line.split()
                x = float(nums[1])
                z = nums[2]
                y = float(nums[3])
                f.write("v {} {} {}\n".format(y, z, -x))
            else:
                f.write(line)

    os.chdir(cwd)
    
def writeMoverMapFile(map_path, name, contents):
    map_dir = os.path.dirname(map_path)
    mover_dir = os.path.join(map_dir, "movers")
    if not os.path.isdir(mover_dir):
        os.mkdir(mover_dir)
    bits = os.path.splitext(os.path.basename(map_path))
    mover_file_name = bits[0] + "." + name + bits[1]
    out_path = os.path.join(mover_dir, mover_file_name)
    print("Writing " + out_path)
    with open(out_path, "w") as f:
        f.write("Begin Map\n")
        for line in contents:
            f.write(line)
        f.write("End Map\n")

def writeMovers(map_path):
    print("Reading movers for " + map_path)
    with open(map_path, "r") as f:
        is_mover = False
        mover_contents = []
        mover_name = None
        for line in f:
            if line.startswith("Begin Actor Class=Mover"):
                is_mover = True
                index = len("Begin Actor Class=Mover Name=")
                mover_name = line[index:].strip()
                
            if is_mover:
                mover_contents.append(line)
                
            if line.startswith("End Actor") and is_mover:
                writeMoverMapFile(map_path, mover_name, mover_contents)
                is_mover = False
                mover_contents = []
                mover_name = None

for game in constants.GAMES:
    glob_path = os.path.join("..", game, "maps", "*.t3d")
    maps = glob.glob(glob_path, recursive=True)

    #maps = [maps[0]] # remove for all maps
    
    for map_path in maps:
        writeMovers(map_path)
        
    # Now include all the generated movers
    maps = glob.glob(glob_path, recursive=True)

    for map_path in maps:
        out_map_path = map_path[:-3] + "obj"
        if not constants.OVERWRITE and os.path.isfile(out_map_path):
            print("Not overwriting " + out_map_path)
            continue
        print("Processing " + map_path)
        convertMapFile(game, map_path)
