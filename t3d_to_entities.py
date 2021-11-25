from shutil import copyfile
import argparse
import constants
import glob
import hammer
import hp_ents
import os.path
import sys
import multiprocessing as mp
import datamodel as dmx

def convertMapFile(path, format, test):
    if format == "dmx":
        extension = "vmap"
    else:
        extension = "vmf"
    out_path = os.path.splitext(path)[0] + "." + extension

    if not constants.OVERWRITE and os.path.isfile(out_path):
        print("Not overwriting " + out_path)
        return
    print("Processing " + path)
    if format == "vmf":
        convertMapFileToVMF(path, out_path, test)
    else: #elif format == "dmx":
        convertMapFileToDMX(path, out_path, test)

    if test:
        return

    # Copy it from $GAME/maps to hla_addon_content/maps
    copy_path = "..\\hla_addon_content\\maps" #os.path.join(constants.ROOT_PATH, "hla_addon_content\\maps")
    copy_path = os.path.join(copy_path, os.path.basename(out_path))
    copyfile(out_path, copy_path)
    print("Finished copying " + out_path + " to " + copy_path)

def convertMapFileToDMX(path, out_path, test):
    dm = dmx.load("template_map.vmap")

    globalClasses = []
    hp_ents.buildEntities(path, globalClasses, 0)
    for ent in globalClasses:
        dm.root["world"]["children"].append(ent.toEntityElement(dm))

    if not test:
        dm.write(out_path, "keyvalues2", 4)

def convertMapFileToVMF(path, out_path, test):
    globalClasses = []

    versioninfo = hammer.HammerClass("versioninfo")
    versioninfo.addProperty("editorversion", "400")
    versioninfo.addProperty("editorbuild", "6412")
    versioninfo.addProperty("mapversion", "1")
    versioninfo.addProperty("formatversion", "100")
    versioninfo.addProperty("prefab", "0")
    globalClasses.append(versioninfo)

    visgroups = hammer.HammerClass("visgroups")
    globalClasses.append(visgroups)

    viewsettings = hammer.HammerClass("viewsettings")
    viewsettings.addProperty("bSnapToGrid", "1")
    viewsettings.addProperty("bShowGrid", "1")
    viewsettings.addProperty("bShowLogicalGrid", "0")
    viewsettings.addProperty("nGridSpacing", "32")
    viewsettings.addProperty("bShow3DGrid", "0")
    globalClasses.append(viewsettings)

    world = hammer.HammerClass("world")
    world.addProperty("id", "1")
    world.addProperty("mapversion", "1")
    world.addProperty("classname", "worldspawn")
    world.addProperty("skyname", "sky_day01_01")
    world.addProperty("maxpropscreenwidth", "-1")
    world.addProperty("detailvbsp", "detail.vbsp")
    world.addProperty("detailmaterial", "detail/detailsprites")
    #world.classes = buildBrushes(geo) # Don't bother with brushes
    globalClasses.append(world)

    numExistingEnts = len(world.classes) + 1
    hp_ents.buildEntities(path, globalClasses, numExistingEnts)

    cameras = hammer.HammerClass("cameras")
    cameras.properties["activecamera"] = "-1"
    globalClasses.append(cameras)

    cordon = hammer.HammerClass("cordon")
    cordon.properties["mins"] = "(-1024 -1024 -1024)"
    cordon.properties["maxs"] = "(1024 1024 1024)"
    cordon.properties["active"] = "0"
    globalClasses.append(cordon)

    if not test:
        with open(out_path, "w") as f:
            for c in globalClasses:
                c.write(f, 0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a T3D file to a VMF or VMAP.")
    parser.add_argument("--maps", type=str, default="../hp*/maps/*.t3d",
                        help="Glob specifying which maps to convert.")
    parser.add_argument("--format", default="dmx",
                        help="Output format (DMX or VMF).")
    parser.add_argument("--test", action="store_true", default=False,
                        help="Only run the conversion code; don't actually write to any files")

    args = parser.parse_args()

    args.format = args.format.lower()
    if args.format != "dmx" and args.format != "vmf":
        print("Invalid format " + args.format + "; choose DMX or VMF")
        quit()

    maps = glob.glob(args.maps, recursive=True)

    if len(maps) == 0:
        print("No files match " + args.maps)
        quit()

    maps_args = [(m, args.format, args.test) for m in maps]

    with mp.Pool(processes=constants.NUM_CORES) as pool:
        pool.starmap(convertMapFile, maps_args)
