import os, platform

if platform.node().startswith("LAPTOP"):
    BLENDER_PATH = None # TODO
    NUM_CORES = 8
else:
    BLENDER_PATH = os.path.realpath("F:/SteamLibrary/steamapps/common/Blender/blender.exe")
    NUM_CORES = 16

SCALE = 0.75
OVERWRITE = True