import os, platform

if platform.node().startswith("LAPTOP"):
    ROOT_PATH = os.path.realpath("D:/Google Drive/hp_resources")
    NUM_CORES = 8
else:
    ROOT_PATH = os.path.realpath("F:/Google Drive/hp_resources")
    NUM_CORES = 16

GAMES = ["hp1", "hp2"]

ORIGINAL_ASSETS_PATH = ROOT_PATH # TODO: change to an "original_assets" folder when we get the new style tools working
INTERMEDIATE_ASSETS_PATH = os.path.join(ROOT_PATH, "intermediate_assets")
CONVERTED_ASSETS_PATH = os.path.join(ROOT_PATH, "tp_assets")

ORIGINAL_MATERIALS = "raw_models_textures"
ORIGINAL_MODELS = "raw_models_textures"

CONVERTED_MATERIALS = "materials"
CONVERTED_MODELS = "models"

SCALE = 0.75
OVERWRITE = True