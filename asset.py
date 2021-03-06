import copy, glob, os

import constants
from fbx import FbxType
from vmat import PngType, VmatType
from vmdl import PskType, TgaType, UClassType, VmdlType
from vmap import T3dType, VmapType

VALID_ASSET_TYPES = [FbxType, PngType, VmatType, PskType, TgaType, VmdlType, UClassType, T3dType,
                     VmapType]
def filetype_to_asset_type(filetype):
    return next((at for at in VALID_ASSET_TYPES if at.file_extension == filetype), None)

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
        "model": "raw_models_textures",
        "map": "maps",
        "uclass": "uclasses"
    },
    "intermediate": {
        "material": "materials",
        "model": "models",
        "map": "maps",
        "flattened_textures": "textures_png_flattened_names"
    },
    "converted": {
        "material": "materials",
        "model": "models",
        "map": "maps"
    }
}

class InvalidAssetError(Exception):
    pass

class VoidAssetType:
    force_regen = False
    file_extension = "*"
    category = "*"

    @staticmethod
    def resolve_dependencies(desc, *args, **kwargs):
        raise NotImplementedError("Please use a proper AssetType.")

    @staticmethod
    def regenerate(desc, *args, **kwargs):
        raise NotImplementedError("Please use a proper AssetType.")

class AssetDescription:
    def __init__(self,
        stage: str, # Original, intermediate, or converted
        game: str,
        subfolder: str,
        name: str,
        asset_type: type):

        if not stage or not game or subfolder is None or name is None or not asset_type:
            raise InvalidAssetError("Please provide all AssetDescription parameters.")

        self.stage = stage
        self.game = game
        self.subfolder = subfolder
        self.name = name
        self.asset_type = asset_type

        self._deps_args = []
        self._deps_kwargs = {}

    def __repr__(self):
        return ("AssetDescription(stage=\"{}\", game=\"{}\", subfolder=\"{}\", name=\"{}\", "
            "asset_type={})").format(
            self.stage, self.game, self.subfolder, self.name, self.asset_type.__name__
        )

    @staticmethod
    def from_path(path):
        path = os.path.realpath(path)
        if not path.lower().startswith(constants.REPO_DIR.lower()):
            print(path)
            raise InvalidAssetError("Please use a path within the assets directory.")
        path = path[len(constants.REPO_DIR):]
        parts = path.split(os.path.sep)
        if not parts[0]:
            parts = parts[1:]

        # HACK: there's no original_assets folder yet
        orig = parts[0] in GAMES
        if orig:
            parts.insert(0, "temp")

        # Handle assets in the top-level subfolder
        if len(parts) < 5:
            parts.insert(3, "")

        if len(parts) < 5:
            print(parts)
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
        _asset_type = filetype_to_asset_type(filetype)
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
            constants.REPO_DIR,
            root,
            self.game,
            category,
            self.subfolder,
            self.name + "." + self.asset_type.file_extension
        ])
        ret = os.path.realpath(ret)
        if relative_to_root:
            ret = os.path.relpath(ret, start=os.path.join(constants.REPO_DIR, root))
        return ret

    def sbox_path(self):
        return self.path(relative_to_root=True).replace(os.path.sep, '/')

    def exists(self):
        return os.path.exists(self.path())

    def deps_str(self):
        if self.dependencies:
            if len(self.dependencies) == 1:
                deps = list(self.dependencies.values())[0].deps_str()
            else:
                deps = [d.deps_str() for d in self.dependencies]
            return "{} --> {}".format(self.sbox_path(), deps)
        else:
            return self.sbox_path()

    def glob(self):
        paths = glob.glob(self.path(allow_wildcard=True), recursive=True)
        ret = [AssetDescription.from_path(p) for p in paths]

        return ret

    def clone(self):
        ret = copy.deepcopy(self)
        ret._deps_args = []
        ret._deps_kwargs = {}
        return ret

    @property
    def dependencies(self):
        return self._deps_args + list(self._deps_kwargs.values())

    def resolve_dependencies(self, *args, **kwargs):
        self.asset_type.resolve_dependencies(self, *args, **kwargs)

    def add_dependency_on(self, desc, key=None):
        if self.stage == "original":
            raise InvalidAssetError("Original assets shouldn't have dependencies")
        if desc is self:
            raise InvalidAssetError("Asset can't depend on itself!")
        if key:
            self._deps_kwargs[key] = desc
        else:
            self._deps_args.append(desc)

    def regenerate(self):
        self.asset_type.regenerate(self, *self._deps_args, **self._deps_kwargs)