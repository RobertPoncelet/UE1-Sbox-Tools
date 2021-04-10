import glob
import os
from PIL import Image

GAME_PATHS = ["..\hp1", "..\hp2"]

for game in GAME_PATHS:
    glob_path = os.path.join(game, "raw_models_textures", "**", "*.tga")
    textures = glob.glob(glob_path, recursive=True)
    for tex_path in textures:
        img = Image.open(tex_path)
        words = tex_path.split("\\")[3:]
        assert(len(words[-1].split(".")) == 2)
        words[-1] = words[-1].split(".")[0] + ".png"
        name = ".".join(words)
        out_path = os.path.join(game, "textures_png_flattened_names", name)
        img.save(out_path)
        print("Saved " + out_path)
        
