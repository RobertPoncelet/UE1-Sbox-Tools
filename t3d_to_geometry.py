import constants
import glob
import os
import multiprocessing as mp
from shutil import copyfile

DO_MAP_CONVERSION = True
DO_MOVER_WRITE = True
DO_MOVER_CONVERSION = True

def convertMapFile(game, path):
    out_map_path = path[:-3] + "obj"
    if not constants.OVERWRITE and os.path.isfile(out_map_path):
        print("Not overwriting " + out_map_path)
        return
    else:
        print("Processing " + path)

    cwd = os.getcwd()
    
    # Use t3d_to_obj.exe to convert the map geometry
    os.chdir("..\\t3d_to_obj")
    T3D_SCALE = 40.65040650406504065040
    is_mover = os.path.split(os.path.dirname(path))[-1] == "movers"
    movers_arg = "--movers" if is_mover else ""
    cmd = "t3d_to_obj.exe {} --post-scale {} {} {}"
    cmd = cmd.format(movers_arg, T3D_SCALE * constants.SCALE, path, os.path.join("..", game, "textures_png_flattened_names"))
    print(cmd)
    if (not is_mover and DO_MAP_CONVERSION) or (is_mover and DO_MOVER_CONVERSION):
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
                    f.write("v {} {} {}\n".format(-y, z, x))
                else:
                    f.write(line)

        os.chdir(cwd)

        # Copy it from $GAME/maps to hla_addon_content/models
        copy_path = os.path.join(constants.ROOT_PATH, ("hla_addon_content\\models\\movers" if is_mover else "hla_addon_content\\models"))
        copy_path = os.path.join(copy_path, os.path.basename(out_map_path))
        print("Copying " + out_map_path + " to " + copy_path)
        copyfile(out_map_path, copy_path)
    
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

def getActorClass(line):
    return tokenValue(line, 2)

def getActorName(line):
    return tokenValue(line, 3)

def tokenValue(line, index):
    tokens = line.split()
    if len(tokens) <= index:
        return None
    ret = tokens[index]
    return ret.split("=")[-1]

def writeMovers(map_path):
    print("Reading movers for " + map_path)
    with open(map_path, "r") as f:
        is_mover = False
        mover_contents = []
        mover_name = None
        for line in f:
            actorClass = getActorClass(line)
            if actorClass == "Mover" or actorClass == "ElevatorMover" or actorClass == "LoopMover":
                is_mover = True
                mover_name = getActorName(line)
                # t3d_to_obj.exe doesn't like non-standard movers (without the "Mover" class name), so we fake it here
                line = "Begin Actor Class=Mover Name={}\n".format(mover_name)
                mover_contents.append(line)
                continue
                
            if is_mover:
                # Don't apply any transformations - we'll do that later
                sline = line.strip()
                if not (sline.startswith("Location=") or sline.startswith("Rotation=")):
                    mover_contents.append(line)
                
            if line.startswith("End Actor") and is_mover:
                writeMoverMapFile(map_path, mover_name, mover_contents)
                is_mover = False
                mover_contents = []
                mover_name = None

if __name__ == "__main__":
    for game in constants.GAMES:
        glob_path = os.path.join("..", game, "maps", "*.t3d")
        maps = glob.glob(glob_path, recursive=True)
        
        if DO_MOVER_WRITE:
            with mp.Pool(processes=constants.NUM_CORES) as pool:
                pool.map(writeMovers, maps)
            
        # Now include all the generated movers
        glob_path = os.path.join("..", game, "maps", "movers", "*.t3d")
        maps += glob.glob(glob_path, recursive=True)

        args = [(game, map_path) for map_path in maps]
        with mp.Pool(processes=constants.NUM_CORES) as pool:
            pool.starmap(convertMapFile, args)
        