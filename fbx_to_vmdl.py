import os, glob, constants

fbxroot = "..\\hla_addon_content" # this is a bit messy but fuck it
vmatroot = "..\\hla_addon_content"

def brocketed(s):
    if s[:4] == "<!--" or not ("<" in s and ">" in s):
        return None
    return (s.split("<"))[1].split(">")[0]

def unbrocket(s, value):
    if s[:4] == "<!--" or not ("<" in s and ">" in s):
        return s
    ret = s.split("<")[0] + "{}" + s.split(">")[1]
    return ret.format(value)

def do_line(line, mdlname, fbx, matdict):
    key = brocketed(line)
    fill = None
    if key is None:
        return line
    elif key == "mesh_file":
        fill = fbx.replace("\\", "/")
    elif key == "mesh_name":
        fill = mdlname
    elif key == "scale":
        fill = constants.SCALE
    elif key == "material_remap_list":
        fill = ""
        for mat in matdict:
            fill = fill + "\t\t\t\t\t\t\t{\n"
            fill = fill + "\t\t\t\t\t\t\t\tfrom = \"{}.vmat\"\n".format(mat)
            vmat = matdict[mat].replace("\\", "/")
            fill = fill + "\t\t\t\t\t\t\t\tto = \"{}\"\n".format(vmat)
            fill = fill + "\t\t\t\t\t\t\t},\n"
    return unbrocket(line, fill) if fill is not None else None

@dataclass
class FbxMesh:
    in_path: str
    out_path: str
    game: str

if __name__ == "__main__":
    in_paths = []
    for game in constants.GAMES:
        in_paths += glob.glob(os.path.join(constants.ROOT_PATH, game, "**", "*.fbx"), recursive=True)
    mdlpaths = {} # Maps model path to fbx
    
    fbxpaths = ["\\".join(path.split("\\")[2:]) for path in fbxpaths] # this is necessary because this directory is not the same as the addon content directory
    for fbxpath in fbxpaths:
    #for fbxpath in glob.glob(fbxroot + "/sm36/*.fbx"):
        mdl = os.path.basename(fbxpath)
        mdl = os.path.splitext(mdl)[0]
        if mdl[:2] == "sk":
            mdl = mdl[2:]
        if mdl[-4:] == "Mesh":
            mdl = mdl[:-4]
        mdl = os.path.join("..", "hla_addon_content", "models", (mdl + ".vmdl"))
        mdlpaths[mdl] = fbxpath

    for mdl in mdlpaths:
        if not constants.OVERWRITE and os.path.isfile(mdl):
            print("Not overwriting " + mdl)
            continue
        print("Writing " + mdl)

        fbx = mdlpaths[mdl]
        mdlname = os.path.basename(mdl)[:-5]

        # A bit hacky
        prefix = "sk" if os.path.basename(fbx).startswith("sk") else ""
        mats = [prefix + mdlname + "Tex" + str(i) for i in range(10)]

        vmat_glob = os.path.join(vmatroot, "*" + prefix + mdlname + "Tex*.vmat")
        vmats = glob.glob(vmat_glob)
        #vmats = glob.glob(os.path.join(vmatroot, "*" + mdlname + "*.vmat"), recursive=True)
        vmats = [os.path.basename(path) for path in vmats]

        # Assign them whatever, we can fix manually later
        matdict = {}
        if len(vmats) != 0:
            for i in range(len(mats)):
                matdict[mats[i]] = vmats[i%len(vmats)]
        
        template = open("template.vmdl")
        mdlfile = open(mdl, "w")
        
        for line in template:
            wline = do_line(line, mdlname, fbx, matdict)
            if wline is not None:
                mdlfile.write(wline)

        template.close()
        mdlfile.close()
    print("Done")
