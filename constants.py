import os, platform

if platform.node().startswith("LAPTOP"):
    REPO_DIR = os.path.realpath("D:/Google Drive/hp_resources")
    BLENDER_PATH = None # TODO
else:
    REPO_DIR = os.path.realpath("F:/Google Drive/hp_resources")
    BLENDER_PATH = os.path.realpath("F:/SteamLibrary/steamapps/common/Blender/blender.exe")

T3D_TO_OBJ_PATH = os.path.join(REPO_DIR, "t3d_to_obj", "t3d_to_obj.exe")
T3D_SCALE = 40.65040650406504065040

SCALE = 0.75
OVERWRITE = True