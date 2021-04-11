import os, glob
from PIL import Image

texroot = "..\\hla_addon_content\\textures_png_flattened_names"
overwrite = False

def textype(tex):
    return tex[:-4].split("_")[-1]

def get_tex_by_type(textures, ttype):
    for tex in textures:
        if textype(tex) == ttype:
            #FIXME return single_colour_or_tex(tex)
            return tex
    return None

def single_colour_or_tex(tex):
    im = Image.open(tex)
    ext = im.getextrema()
    if im.mode == "L":
        if abs(ext[1] - ext[0]) < 5:
            num = (ext[0] + ext[1]) / 2
            return str(float(num) / 255.)
    else:
        if not False in [abs(e[1] - e[0]) < 5 for e in ext]:
            nums = [str(float((e[0] + e[1]) / 2) / 255.) for e in ext]
            return "[" + " ".join(nums) + "]"
    return tex

def brocketed(s):
    if not ("<" in s and ">" in s):
        return None
    return (s.split("<"))[1].split(">")[0]

def unbrocket(s, value):
    if not ("<" in s and ">" in s):
        return s
    ret = s.split("<")[0] + "{}" + s.split(">")[1]
    return ret.format(value)

def do_line(line, textures):
    key = brocketed(line)
    fill = None
    if key is None:
        return line
    elif key == "enum_indirect":
        temp = get_tex_by_type(textures, "ao")
        fill = "2" if type(temp) is str and texroot in temp else None
    elif key == "bool_metalness":
        fill = "1" if get_tex_by_type(textures, "metal") is not None else None
    elif key == "bool_specular":
        fill = "1" if get_tex_by_type(textures, "refl") is not None else None
    elif key == "bool_trans":
        fill = None #"1" if get_tex_by_type(textures, "trans") is not None else None
    elif key == "tex_color":
        fill = textures[0] #get_tex_by_type(textures, "color")
    elif key == "float_metal":
        fill = None if get_tex_by_type(textures, "metal") is not None else "0.000"
    elif key == "tex_ao":
        temp = get_tex_by_type(textures, "ao")
        fill = temp if type(fill) is str else None
    elif key == "tex_refl" or key == "tex_gloss":
        fill = get_tex_by_type(textures, "refl")
    elif key == "tex_metal":
        fill = get_tex_by_type(textures, "metal")
    elif key == "tex_normal":
        fill = get_tex_by_type(textures, "normal")
    elif key == "tex_trans":
        fill = get_tex_by_type(textures, "trans")
    return unbrocket(line, fill) if fill is not None else None

print("TODO: make this not hard-coded for HP2")

matpaths = {} # Maps material path to a list of its textures
texpaths = glob.glob(os.path.join(texroot, "*.png"), recursive=True)
#texpaths = [texpaths[0]] # remove to do all textures
for texpath in texpaths:
    texpath = os.path.basename(texpath)
    texpath = os.path.join("textures_png_flattened_names", texpath)
    mat = os.path.basename(texpath)
    mat = os.path.splitext(mat)[0] # Get rid of the file extension
    mat = "_".join(mat.split("."))
    mat += ".vmat"
    mat = os.path.join("..", "hla_addon_content", mat)
    if mat not in matpaths:
        matpaths[mat] = [texpath]
    else:
        matpaths[mat].append(texpath)

for mat in matpaths:
    if not overwrite and os.path.isfile(mat):
        print("Not overwriting " + mat)
        continue
    print("Writing " + mat)
    textures = matpaths[mat]
    template = open("template.vmat")
    matfile = open(mat, "w")

    for line in template:
        wline = do_line(line, textures)
        if wline is not None:
            matfile.write(wline)

    template.close()
    matfile.close()
print("Done")
