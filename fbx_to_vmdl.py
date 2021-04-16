import os, glob

objroot = "..\\hla_addon_content" # this is a bit messy but fuck it
vmatroot = "..\\hla_addon_content"
overwrite = True

def brocketed(s):
    if s[:4] == "<!--" or not ("<" in s and ">" in s):
        return None
    return (s.split("<"))[1].split(">")[0]

def unbrocket(s, value):
    if s[:4] == "<!--" or not ("<" in s and ">" in s):
        return s
    ret = s.split("<")[0] + "{}" + s.split(">")[1]
    return ret.format(value)

def do_line(line, mdlname, obj, matdict):
    key = brocketed(line)
    fill = None
    if key is None:
        return line
    elif key == "mesh_file":
        fill = obj.replace("\\", "/")
    elif key == "mesh_name":
        fill = mdlname
    elif key == "scale":
        fill = "0.75"
    elif key == "material_remap_list":
        fill = ""
        for mat in matdict:
            fill = fill + "\t\t\t\t\t\t\t{\n"
            fill = fill + "\t\t\t\t\t\t\t\tfrom = \"{}.vmat\"\n".format(mat)
            vmat = matdict[mat].replace("\\", "/")
            fill = fill + "\t\t\t\t\t\t\t\tto = \"{}\"\n".format(vmat)
            fill = fill + "\t\t\t\t\t\t\t},\n"
    return unbrocket(line, fill) if fill is not None else None

mdlpaths = {} # Maps model path to obj
objpaths = glob.glob(os.path.join(objroot, "**", "*.fbx"), recursive=True)
objpaths = ["\\".join(path.split("\\")[2:]) for path in objpaths] # this is necessary because this directory is not the same as the addon content directory
for objpath in objpaths:
#for objpath in glob.glob(objroot + "/sm36/*.obj"):
    mdl = os.path.basename(objpath)
    mdl = os.path.splitext(mdl)[0]
    if mdl[:2] == "sk":
        mdl = mdl[2:]
    if mdl[-4:] == "Mesh":
        mdl = mdl[:-4]
    mdl = os.path.join("..", "hla_addon_content", "models", (mdl + ".vmdl"))
    mdlpaths[mdl] = objpath

for mdl in mdlpaths:
    if not overwrite and os.path.isfile(mdl):
        print("Not overwriting " + mdl)
        continue
    print("Writing " + mdl)

    obj = mdlpaths[mdl]
    mdlname = os.path.basename(mdl)[:-5]

    mats = ["sk" + mdlname + "Tex" + str(i) for i in range(10)]

    vmat_glob = os.path.join(vmatroot, "*sk" + mdlname + "Tex*.vmat")
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
        wline = do_line(line, mdlname, obj, matdict)
        if wline is not None:
            mdlfile.write(wline)

    template.close()
    mdlfile.close()
print("Done")
