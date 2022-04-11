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

class AssetDescription:
    def __init__(self,
        stage: str, # Original, intermediate, or converted
        game: str,
        subfolder: str,
        name: str):

        if not stage or not game or not subfolder or not name:
            raise InvalidAssetError("Please provide all AssetDescription parameters.")

        self.stage = stage
        self.game = game
        self.subfolder = subfolder
        self.name = name

        self.dependencies = {}

    force_regen = False

    @staticmethod
    def from_path(path):
        path = os.path.realpath(path)
        assert(path.lower().startswith(REPO_DIR.lower()))
        path = path[len(REPO_DIR):]
        parts = path.split(os.path.sep)
        if not parts[0]:
            parts = parts[1:]

        # HACK: there's no original_assets folder yet
        orig = parts[0] in GAMES
        if orig:
            parts.insert(0, "temp")

        assert(len(parts) >= 5)

        # Find value given key
        # Kinda hacky but maybe we can find a way to change it later
        def reverse_dict(d, value):
            for k, v in d.items():
                if v == value:
                    return k
            raise KeyError("No value {} in dict".format(value))

        _stage = "original" if orig else reverse_dict(ROOT_DICT, parts[0])
        _game = parts[1]
        assert(_game in GAMES)
        _subfolder = os.path.sep.join(parts[3:-1])
        _name, _filetype = os.path.splitext(parts[-1])
        _filetype = _filetype[1:]
        return AssetDescription(_stage, _game, _subfolder, _name)

    def path(self, relative_to_root=False, allow_wildcard=False):
        stage_valid = self.stage in STAGES
        game_valid = self.game in GAMES or (allow_wildcard and self.game == "*")
        category_valid = self.category in CATEGORY_DICT[self.stage] \
            or (allow_wildcard and self.category == "*")
        if not stage_valid or not game_valid or not category_valid:
            raise InvalidAssetError("Invalid stage, game or category for asset.")

        root = ROOT_DICT[self.stage]
        category = "*" if self.category == "*" else CATEGORY_DICT[self.stage][self.category]
        # TODO: Why doesn't os.path.join work here???
        ret = os.path.sep.join([
            REPO_DIR,
            root,
            self.game,
            category,
            self.subfolder,
            self.name + "." + self.filetype
        ])
        ret = os.path.realpath(ret)
        if relative_to_root:
            ret = os.path.relpath(ret, start=os.path.join(REPO_DIR, root))
        return ret

    def sbox_filepath(self):
        return self.path(relative_to_root=True).replace(os.path.sep, '/')

    def glob(self):
        paths = glob.glob(self.path(allow_wildcard=True), recursive=True)
        ret = [AssetDescription.from_path(p) for p in paths]

        # HACK: from_paths() can't currently tell the difference between original materials and models :(
        if self.stage == "original" and "*" not in self.category:
            for desc in ret:
                desc.category = self.category

        return ret

    def clone(self):
        return copy.copy(self)

    def add_dependency_on(self, key, desc):
        self.dependencies[key] = desc

    # Below attributes are dependent on the asset type

    @property
    def file_extension():
        raise NotImplementedError("Please use a subclass of AssetDescription.")

    @property
    def category():
        raise NotImplementedError("Please use a subclass of AssetDescription.")

    def regenerate():
        raise NotImplementedError("Please use a subclass of AssetDescription.")