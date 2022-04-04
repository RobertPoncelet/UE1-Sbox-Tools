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

MATERIALS_PATH = {game: os.path.join(CONVERTED_ASSETS_PATH, game, "materials") for game in GAMES}
MODELS_PATH = {game: os.path.join(CONVERTED_ASSETS_PATH, game, "materials") for game in GAMES}

SCALE = 0.75
OVERWRITE = True