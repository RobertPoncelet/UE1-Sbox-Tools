import os, subprocess
from build_node import BuildNode, SourceFileNode
import constants

class FbxNode(BuildNode):
    def __init__(self, tree):
        assert(tree.fbx)
        assert(tree.psk)
        super().__init__(tree.fbx)
        self._dependencies = [SourceFileNode(tree.psk)]
    
    @property
    def dependencies(self):
        return self._dependencies

    def regenerate_file(self):
        script_path = os.path.realpath("blender_psk_to_fbx.py")
        print("Starting Blender...")
        p1 = subprocess.run(
            [
                constants.BLENDER_PATH,
                "-b",
                "--python",
                script_path,
                "--",
                self.dependencies[0].filepath,
                self.filepath
            ],
            stderr=subprocess.STDOUT,
            text=True)
        print("Finished Blender")