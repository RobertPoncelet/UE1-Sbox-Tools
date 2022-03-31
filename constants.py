import os, platform

if platform.node().startswith("LAPTOP"):
    ROOT_PATH = "D:/Google Drive/hp_resources"
    NUM_CORES = 8
else:
    ROOT_PATH = "F:/Google Drive/hp_resources"
    NUM_CORES = 16
ASSETS_PATH = os.path.join(ROOT_PATH, "tp_assets")
MATERIALS_PATH = os.path.join(ASSETS_PATH, "materials")
MODELS_PATH = os.path.join(ASSETS_PATH, "models")

GAMES = ["hp1", "hp2"]
SCALE = 0.75
OVERWRITE = True

# Try not to use anymore
HLA_TEXTURES_ROOT = "..\\hla_addon_content\\textures_png_flattened_names"