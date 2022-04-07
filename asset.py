import os, platform
from dataclasses import dataclass

if platform.node().startswith("LAPTOP"):
    REPO_DIR = os.path.realpath("D:/Google Drive/hp_resources")
else:
    REPO_DIR = os.path.realpath("F:/Google Drive/hp_resources")

GAMES = ["hp1", "hp2"]

ORIGINAL_ASSETS_ROOT = "" # TODO: change to an "original_assets" folder when we get the new style tools working
INTERMEDIATE_ASSETS_ROOT = "intermediate_assets"
CONVERTED_ASSETS_ROOT = REPO_DIR, "tp_assets"

ORIGINAL_MATERIALS = "raw_models_textures"
ORIGINAL_MODELS = "raw_models_textures"

CONVERTED_MATERIALS = "materials"
CONVERTED_MODELS = "models"

@dataclass
class AssetDescription:
    stage: str # Original, intermediate, or converted
    game: str
    category: str # Material, model etc.
    subfolder: str
    name: str
    filetype: str
    def path(self):
        # TODO: Why doesn't os.path.join work here???
        ret = os.path.sep.join([REPO_DIR, self.root, self.game, self.asset_type, self.subfolder, self.name + "." + self.filetype])
        ret = os.path.realpath(ret)
        return ret