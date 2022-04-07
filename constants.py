import platform

if platform.node().startswith("LAPTOP"):
    NUM_CORES = 8
else:
    NUM_CORES = 16

SCALE = 0.75
OVERWRITE = True