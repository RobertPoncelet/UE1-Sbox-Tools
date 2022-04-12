import copy, glob, os, platform

if platform.node().startswith("LAPTOP"):
    REPO_DIR = os.path.realpath("D:/Google Drive/hp_resources")
else:
    REPO_DIR = os.path.realpath("F:/Google Drive/hp_resources")

STAGES = ["original", "intermediate", "converted"]

GAMES = ["hp1", "hp2"]

ROOT_DICT = {
    "original": "", # HACK: change to an "original_assets" folder when we get the new style tools working
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

class InvalidAssetError(Exception):
    pass

class VoidAssetType:
    force_regen = False
    file_extension = "*"
    category = "*"

    @staticmethod
    def resolve_dependencies(*args):
        raise NotImplementedError("Please use a proper AssetType.")

    @staticmethod
    def regenerate(desc, **kwargs):
        raise NotImplementedError("Please use a proper AssetType.")

class AssetDescription:
    def __init__(self,
        stage: str, # Original, intermediate, or converted
        game: str,
        subfolder: str,
        name: str,
        asset_type: type):

        if not stage or not game or not subfolder or not name or not asset_type:
            raise InvalidAssetError("Please provide all AssetDescription parameters.")

        self.stage = stage
        self.game = game
        self.subfolder = subfolder
        self.name = name
        self.asset_type = asset_type

        self.dependencies = {}

    @staticmethod
    def from_path(path):
        path = os.path.realpath(path)
        if not path.lower().startswith(REPO_DIR.lower()):
            print(path)
            raise InvalidAssetError("Please use a path within the assets directory.")
        path = path[len(REPO_DIR):]
        parts = path.split(os.path.sep)
        if not parts[0]:
            parts = parts[1:]

        # HACK: there's no original_assets folder yet
        orig = parts[0] in GAMES
        if orig:
            parts.insert(0, "temp")

        if len(parts) < 5:
            raise InvalidAssetError("Path does not contain enough information to create an asset.")

        # Find value given key
        # Kinda hacky but maybe we can find a way to change it later
        def reverse_dict(d, value):
            for k, v in d.items():
                if v == value:
                    return k
            raise KeyError("No value {} in dict".format(value))

        _stage = "original" if orig else reverse_dict(ROOT_DICT, parts[0])
        _game = parts[1]
        if _game not in GAMES:
            raise InvalidAssetError("Game \"{}\" is not a recognised game.".format(_game))
        _subfolder = os.path.sep.join(parts[3:-1])
        _name, filetype = os.path.splitext(parts[-1])
        filetype = filetype[1:]
        _asset_type = VoidAssetType #filetype_to_asset_type(filetype) # TODO
        return AssetDescription(
            stage=_stage,
            game=_game,
            subfolder=_subfolder,
            name=_name,
            asset_type=_asset_type
        )

    def path(self, relative_to_root=False, allow_wildcard=False):
        stage_valid = self.stage in STAGES
        if not stage_valid:
            raise InvalidAssetError("Invalid stage \"{}\" for asset.".format(self.stage))

        game_valid = self.game in GAMES or (allow_wildcard and self.game == "*")
        if not game_valid:
            raise InvalidAssetError("Invalid game \"{}\" for asset.".format(self.game))

        category_valid = self.asset_type.category in CATEGORY_DICT[self.stage] \
            or (allow_wildcard and self.asset_type.category == "*")
        if not category_valid:
            raise InvalidAssetError("Invalid category \"{}\" for asset."
                .format(self.asset_type.category))

        root = ROOT_DICT[self.stage]
        category = "*" if self.asset_type.category == "*" \
            else CATEGORY_DICT[self.stage][self.asset_type.category]
        # TODO: Why doesn't os.path.join work here???
        ret = os.path.sep.join([
            REPO_DIR,
            root,
            self.game,
            category,
            self.subfolder,
            self.name + "." + self.asset_type.file_extension
        ])
        ret = os.path.realpath(ret)
        if relative_to_root:
            ret = os.path.relpath(ret, start=os.path.join(REPO_DIR, root))
        return ret

    def sbox_path(self):
        return self.path(relative_to_root=True).replace(os.path.sep, '/')

    def glob(self):
        paths = glob.glob(self.path(allow_wildcard=True), recursive=True)
        ret = [AssetDescription.from_path(p) for p in paths]

        # HACK: from_paths() can't currently tell the difference between original materials and models :(
        if self.stage == "original" and "*" not in self.asset_type.category:
            for desc in ret:
                desc.asset_type = self.asset_type

        return ret

    def clone(self):
        return copy.copy(self)

    def resolve_dependencies(self, *args):
        self.asset_type.resolve_dependencies(self, *args)

    def add_dependency_on(self, key, desc):
        self.dependencies[key] = desc

    def regenerate(self):
        self.asset_type.regenerate(self, **self.dependencies)