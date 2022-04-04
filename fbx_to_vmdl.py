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
        assert(self.filepath.startswith(constants.CONVERTED_ASSETS_PATH))
        self._dependencies = [FbxNode(tree)] # TODO: add materials

    @property
    def dependencies(self):
        return self._dependencies

    def regenerate_file(self):
        # TODO: create DataModel from a template, fill it with FBX/material data from dependencies, save it in our filepath
        pass
        
# TODO: glob all psks, figure out an output vmdl path for each, put both in a ModelBuildTreeHelper, give it to a new VmdlNode
# (Note: all psks should end with "Mesh.psk", but not all of them start with "sk")
if __name__ == "__main__":
    in_paths = []
    for game in constants.GAMES:
        in_paths += glob.glob(os.path.join(constants.ORIGINAL_ASSETS_PATH, game, "**", "*.fbx"), recursive=True)
    mdlpaths = {} # Maps model path to fbx
    
    fbxpaths = ["\\".join(path.split("\\")[2:]) for path in fbxpaths] # this is necessary because this directory is not the same as the addon content directory
    for fbxpath in fbxpaths:
    #for fbxpath in glob.glob(fbxroot + "/sm36/*.fbx"):
        mdl = os.path.basename(fbxpath)
        mdl = os.path.splitext(mdl)[0]
        if mdl[:2] == "sk":
            mdl = mdl[2:]
        if mdl[-4:] == "Mesh":
            mdl = mdl[:-4]
        mdl = os.path.join("..", "hla_addon_content", "models", (mdl + ".vmdl"))
        mdlpaths[mdl] = fbxpath

    for mdl in mdlpaths:
        if not constants.OVERWRITE and os.path.isfile(mdl):
            print("Not overwriting " + mdl)
            continue
        print("Writing " + mdl)

        fbx = mdlpaths[mdl]
        mdlname = os.path.basename(mdl)[:-5]

        # A bit hacky
        prefix = "sk" if os.path.basename(fbx).startswith("sk") else ""
        mats = [prefix + mdlname + "Tex" + str(i) for i in range(10)]

        vmat_glob = os.path.join(vmatroot, "*" + prefix + mdlname + "Tex*.vmat")
        vmats = glob.glob(vmat_glob)
        #vmats = glob.glob(os.path.join(vmatroot, "*" + mdlname + "*.vmat"), recursive=True)
        vmats = [os.path.basename(path) for path in vmats]

        # Assign them whatever, we can fix manually later
        matdict = {}
        if len(vmats) != 0:
            for i in range(len(mats)):
                matdict[mats[i]] = vmats[i%len(vmats)]
        
        template = open("template.vmdl")
        mdlfile = open(mdl, "w")
        
        for line in template:
            wline = do_line(line, mdlname, fbx, matdict)
            if wline is not None:
                mdlfile.write(wline)

        template.close()
        mdlfile.close()
    print("Done")
