import os, platform
from dataclasses import dataclass

if platform.node().startswith("LAPTOP"):
    REPO_DIR = os.path.realpath("D:/Google Drive/hp_resources")
else:
    REPO_DIR = os.path.realpath("F:/Google Drive/hp_resources")

STAGES = ["original", "intermediate", "converted"]

GAMES = ["hp1", "hp2"]

ROOT_DICT = {
    "original": "", # TODO: this is hacky, change to an "original_assets" folder when we get the new style tools working
    "intermediate": "intermediate_assets",
    "converted": "tp_assets"
}

CATEGORY_DICT = {
    "original": {
        "material": "raw_models_textures",
        "model": "raw_models_textures"
    },
    "intermediate": {
        "material": "materials",
        "model": "models"
    },
    "converted": {
        "material": "materials",
        "model": "models"
    }
}

@dataclass
class AssetDescription:
    stage: str # Original, intermediate, or converted
    game: str
    category: str # Material, model etc.
    subfolder: str
    name: str
    filetype: str

    @staticmethod
    def from_path(path):
        pass # TODO

    def path(self):
        assert(self.stage in STAGES)
        assert(self.game in GAMES)
        assert(self.category in CATEGORY_DICT[self.stage])
        root = ROOT_DICT[self.stage]
        category = CATEGORY_DICT[self.stage][self.category]
        # TODO: Why doesn't os.path.join work here???
        ret = os.path.sep.join([REPO_DIR, 
            root, 
            self.game, 
            category, 
            self.subfolder, 
            self.name + "." + self.filetype
        ])
        ret = os.path.realpath(ret)
        return ret