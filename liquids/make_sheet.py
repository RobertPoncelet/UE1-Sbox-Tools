import glob, os, sys
from PIL import Image

TILES_X = 8
TILES_Y = 4
tile_width = None
tile_height = None
out_image = None

path = sys.argv[1] if len(sys.argv) > 1 else None
bmps = glob.glob(os.path.join(path, "*.png") if path else "*.png")
for num, bmp_path in enumerate(bmps):
    if num >= TILES_X * TILES_Y:
        break
    im = Image.open(bmp_path)
    if tile_width == None or tile_height == None:
        tile_width = im.width
        tile_height = im.height
    if out_image == None:
        out_image = Image.new("RGB", (TILES_X * tile_width, TILES_Y * tile_height))
    out_image.paste(im, ((num % TILES_X) * tile_width, int(num / TILES_X) * tile_height))    
            
out_image.save(os.path.basename(path) + ".png")
