import os, platform

if platform.node().startswith("LAPTOP"):
    BLENDER_PATH = None # TODO
else:
    BLENDER_PATH = os.path.realpath("F:/SteamLibrary/steamapps/common/Blender/blender.exe")

SCALE = 0.75
OVERWRITE = True