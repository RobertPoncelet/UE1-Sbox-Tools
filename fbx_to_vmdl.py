import os, glob, constants
from dataclasses import dataclass
from build_node import BuildNode
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
        #assert(self.filepath.startswith(constants.CONVERTED_ASSETS_PATH))
        self._dependencies = [FbxNode(tree)] # TODO: add materials

    @property
    def dependencies(self):
        return self._dependencies

    def regenerate_file(self):
        # TODO: create DataModel from a template, fill it with FBX/material data from dependencies, save it in our filepath
        pass

@dataclass
class AssetPath:
    root: str
    game: str
    asset_type: str
    relative: str
    def path(self):
        return os.path.join(self.root, self.game, self.asset_type, self.relative)

def psk_to_vmdl_name(asset_path: AssetPath):
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
        constants.MODELS_PATH, 
        new_relative)
    return new_asset_path.path()
        
# TODO: glob all psks, figure out an output vmdl path for each, put both in a ModelBuildTreeHelper, give it to a new VmdlNode
# (Note: all psks should end with "Mesh.psk", but not all of them start with "sk")
if __name__ == "__main__":
    psk_paths = []
    root = constants.ORIGINAL_ASSETS_PATH
    for game in constants.GAMES:
        asset_type = "raw_models_textures"
        prefix = os.path.join(root, game, asset_type)
        search = glob.glob(os.path.join(prefix, "**", "*.psk"), recursive=True)
        for path in search:
            assert(path.startswith(prefix))
            relative = path[len(prefix):]
            psk_paths.append(AssetPath(root, game, asset_type, relative))
    
    helpers = [ModelBuildTreeHelper(psk_to_vmdl_name(p), p.path()) for p in psk_paths]
    vmdl_nodes = [VmdlNode(helper) for helper in helpers]
    print(helpers)
    print("Done")
