import argparse, glob, os
from dataclasses import dataclass

from build_node import BuildNode
import constants
import datamodel as dmx

@dataclass
class ModelBuildTreeHelper:
    vmdl_path: str
    psk_path: str
    fbx_path: str = None

class FbxNode(BuildNode):
    def __init__(self, tree):
        super().__init__(tree.fbx_path)
    
    @property
    def dependencies(self):
        return None # TODO

    def regenerate_file(self):
        pass # TODO

class VmdlNode(BuildNode):
    def __init__(self, tree):
        super().__init__(tree.vmdl_path)
        assert(self.filepath.startswith(constants.CONVERTED_ASSETS_PATH))
        self._dependencies = None#[FbxNode(tree)] 
        # TODO: add materials

    @property
    def dependencies(self):
        return self._dependencies

    def regenerate_file(self):
        # TODO: create DataModel from a template, fill it with FBX/material data from dependencies, save it in our filepath
        dm = dmx.load("template_model.vmdl")
        dm.write(self.filepath, "keyvalues2", 4)

def path_to_assetpath(path):
    path = os.path.realpath(path)
    assert(path.startswith(constants.ROOT_PATH))
    remainder = path[len(constants.ROOT_PATH):]
    print(remainder)
    if remainder.startswith(os.path.sep):
        remainder = remainder[len(os.path.sep):]
    print(remainder)
    parts = remainder.split(os.path.sep)
    print(parts)
    root = os.path.join(constants.ROOT_PATH, parts[0])
    game = parts[1]
    asset_type = parts[2]
    relative = os.path.sep.join(parts[3:])
    return AssetPath(root, game, asset_type, relative)

@dataclass
class AssetPath:
    root: str
    game: str
    asset_type: str
    relative: str
    def path(self):
        # TODO: Why doesn't os.path.join work here???
        ret = os.path.sep.join([self.root, self.game, self.asset_type, self.relative])
        ret = os.path.realpath(ret)
        return ret

def psk_to_vmdl_path(asset_path: AssetPath):
    base = os.path.basename(asset_path.relative)
    name = os.path.splitext(base)[0]

    assert(name.lower().endswith("mesh"))
    name = name[:-4]
    if name.lower().startswith("sk"):
        name = name[2:]
    
    new_relative = os.path.join(os.path.dirname(asset_path.relative), name + ".vmdl")
    new_asset_path = AssetPath(
        constants.CONVERTED_ASSETS_PATH, 
        asset_path.game, 
        constants.CONVERTED_MODELS, 
        new_relative)
    return new_asset_path
        
# TODO: glob all psks, figure out an output vmdl path for each, put both in a ModelBuildTreeHelper, give it to a new VmdlNode
# (Note: all psks should end with "Mesh.psk", but not all of them start with "sk")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert UE1 PSKs to VMDLs.")

    root = constants.ORIGINAL_ASSETS_PATH
    for game in constants.GAMES:
        asset_type = constants.ORIGINAL_MODELS
        prefix = os.path.join(root, game, asset_type)
    
    parser.add_argument("--psks", type=str, nargs="+", default="../hp*/maps/*.t3d",
                        help="Glob specifying which PSK files to convert.")
    parser.add_argument("--regen-fbx", action="store_true",
                        help="Force regeneration of intermediate FBX files.")
    parser.add_argument("--regen-vmdl", action="store_true",
                        help="Force regeneration of VMDL files.")

    args = parser.parse_args()

    psk_paths = []
    root = constants.ORIGINAL_ASSETS_PATH
    for game in constants.GAMES:
        asset_type = constants.ORIGINAL_MODELS
        prefix = os.path.join(root, game, asset_type)
        search = glob.glob(os.path.join(prefix, "**", "*.psk"), recursive=True)
        for path in search:
            assert(path.startswith(prefix))
            relative = path[len(prefix):]
            psk_paths.append(AssetPath(root, game, asset_type, relative))
    
    helpers = [ModelBuildTreeHelper(psk_to_vmdl_path(p).path(), p.path()) for p in psk_paths]
    vmdl_nodes = [VmdlNode(helper) for helper in helpers]
    vmdl_nodes[0].build()
    print("Done")
