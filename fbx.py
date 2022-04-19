import os, subprocess
import constants

class FbxType:
    force_regen = False
    file_extension = "fbx"
    category = "model"

    # Fill the vmdl's dependencies based on its current state so the BuildNode can access it later
    # The dependencies added should match the arguments given to regenerate (minus the VMDL itself)
    @staticmethod
    def resolve_dependencies(fbx_desc, psk_desc):
        # PSK should have no dependencies, all we need to do is add it
        fbx_desc.add_dependency_on(psk_desc)

    @staticmethod
    def regenerate(fbx_desc, psk_desc):
        script_path = os.path.realpath("blender_psk_to_fbx.py")
        p1 = subprocess.run(
            [
                constants.BLENDER_PATH,
                "-b",
                "--python",
                script_path,
                "--",
                psk_desc.path(),
                fbx_desc.path()
            ], capture_output=True)