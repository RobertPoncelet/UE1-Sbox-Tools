# Be careful when executing that it doesn't accidentally make a bunch of
# unnecessary materials for the transparency textures!
import os, glob, constants
from PIL import Image

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

def is_opaque(tex):
    tex = os.path.join("..", "hla_addon_content", tex) # Correct it
    im = Image.open(tex)
    if len(im.mode) <= 3:
        return True
    alpha = im.split()[3]
    size = im.width * im.height
    blank_fraction = float(alpha.histogram()[0]) / float(size)
    opaque = blank_fraction < 0.05
    if not opaque:
        trans_path = tex[:-4] + "_trans.png"
        if not os.path.exists(trans_path):
            alpha.save(trans_path)
    return opaque

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
        fill = "2" if type(temp) is str and constants.HLA_TEXTURES_ROOT in temp else None
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
    elif key == "shader":
        fill = "vr_simple.vfx" if is_opaque(textures[0]) else "vr_complex.vfx"
    elif key == "alpha_test":
        fill = "0" if is_opaque(textures[0]) else "1"
    return unbrocket(line, fill) if fill is not None else None

matpaths = {} # Maps material path to a list of its textures
texpaths = glob.glob(os.path.join(constants.HLA_TEXTURES_ROOT, "*.png"), recursive=True)
#texpaths = texpaths[:10] # remove to do all textures
for texpath in texpaths:
    texpath = os.path.basename(texpath)
    texpath = os.path.join("textures_png_flattened_names", texpath)
    mat = os.path.basename(texpath)
    mat = os.path.splitext(mat)[0] # Get rid of the file extension
    mat = "_".join(mat.split("."))
    mat += ".vmat"
    mat = os.path.join("..", "hla_addon_content", mat)
    if mat not in matpaths:
        trans_path = texpath[:-4] + "_trans.png"
        matpaths[mat] = [texpath, trans_path]
    else:
        matpaths[mat].append(texpath)

for mat in matpaths:
    if not constants.OVERWRITE and os.path.isfile(mat):
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
