import glob, os, sys
from PIL import Image

path = sys.argv[1] if len(sys.argv) > 1 else None
hashes = {}
bmps = glob.glob(os.path.join(path, "*.png") if path else "*.png")
for path in bmps:
    im = Image.open(path)
    #im = im.quantize(colors=8)
    h = hash(im.tobytes())
    if h in hashes:
        print("found match!", path, hashes[h])
        os.remove(path)
    else:
        hashes[h] = path
print(len(bmps), len(hashes))
